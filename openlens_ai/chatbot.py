import os
import json
from typing import Optional, Type, Dict, Any, Union
from typing_extensions import Literal
from loguru import logger
import asyncio
import time
from datetime import datetime
import dotenv
import requests
import traceback
from copy import deepcopy

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import ToolMessage, HumanMessage, AIMessage
from langchain_core.messages.utils import count_tokens_approximately, get_buffer_string
from langgraph.graph.state import CompiledStateGraph
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.load.dump import dumps
from langchain.load.load import loads

from .state import State, load_state, get_subplan
from .utils.frontend_utils import frontend_add_message, frontend_add_tool_call
from .utils.config import Config

import numpy as np

dotenv.load_dotenv()




def react_pre_model_wrapper(vector_search_question: str):
    """
    创建一个预处理模型的包装器，用于在将消息传递给模型之前进行处理
    
    Args:
        vector_search_question: 用于向量搜索的问题
        
    Returns:
        一个预处理函数，用于处理状态中的消息
    """
    def react_pre_model_hook(state):
        """
        在模型调用前处理状态中的消息，特别是处理过长的工具消息
        """
        logger.info(f"React pre model hook called with llm input message len {len(state['messages'])}")
        # 如果工具返回信息太多，用向量搜索
        max_tool_token_cnt = int(os.environ.get("MAX_TOOL_TOKEN_CNT", 2000))
        for message_i, message in enumerate(state["messages"]):
            if isinstance(message, ToolMessage):
                token_cnt = count_tokens_approximately([message])
                if token_cnt > max_tool_token_cnt * 2:
                    short_message = vector_search_match_type(message, vector_search_question, token_cnt=max_tool_token_cnt)
                    logger.info(f"Message is too long ({token_cnt}), "
                                f"use vector search to summarize to ({count_tokens_approximately([short_message])})")
                    state["messages"][message_i] = short_message
        return state

    return react_pre_model_hook


def vector_search_match_type(message: str, query: str, token_cnt: int = 10000):
    """
    根据消息类型执行向量搜索并保持消息类型一致
    
    Args:
        message: 原始消息
        query: 查询语句
        token_cnt: 最大token数量
        
    Returns:
        处理后的消息，保持原始消息类型
    """
    message_type = type(message)
    short_messages = vector_search([message], query, token_cnt=token_cnt)
    # 合并
    all_content = [message.content for message in short_messages]
    if message_type == ToolMessage:
        return message_type(content="\n".join(all_content), tool_call_id=message.tool_call_id, name=message.name, status=message.status)
    else:
        return message_type("\n".join(all_content))
    

def perform_rerank(all_docs_str: list[str], query: str, token_cnt: int):
    if len(query) > 2000:
        logger.warning("Query is too long, truncating to 2000 characters: " + query[:2000])
        query = query[:2000]
    
    all_messages_with_score = []
    # for doc_str in all_docs_str:
    # 如果len(all_docs_str)大于32，就分成很多个大小为32的块
    all_docs_chunks = [all_docs_str[i:i+32] for i in range(0, len(all_docs_str), 32)]   
    
    for docs_chunk in all_docs_chunks:
        
        # 创建向量存储
        input_doc_list = docs_chunk
        payload = {
            "model": os.environ.get("RERANK_MODEL", "bge-reranker-v2-m3"),
            "query": query,
            "documents": input_doc_list,
            "return_raw_scores": True
        }
        api_key = os.environ.get("RERANK_API_KEY", "")
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        url = os.environ.get("RERANK_BASE_URL", "") + "rerank"
        # url = "https://cloud.infini-ai.com/maas/v1/rerank"
        
        messages_with_score = []
        for try_i in range(10):
            response = requests.post(url, json=payload, headers=headers)
            try:
                messages_with_score = []
                for res in response.json()["results"]:
                    if ("document" in res) and isinstance(res["document"], str):
                        messages_with_score.append(
                            {
                                "text": res["document"],
                                "score": res["relevance_score"]
                            }
                        )
                        
                    elif ("document" in res) and ("text" in res["document"]) and \
                        isinstance(res["document"], dict) and isinstance(res["document"]["text"], str):
                            
                        messages_with_score.append(
                            {
                                "text": res["document"]["text"],
                                "score": res["relevance_score"]
                            }
                        )
                    elif ("index" in res):
                        messages_with_score.append(
                            {
                                "text": input_doc_list[int(res["index"])],
                                "score": res["relevance_score"]
                            }
                        )
                    else:
                        raise ValueError("Invalid document type")
                    
                break
            except Exception as e:
                logger.warning(f"Get rerank result error: {e}")
                logger.warning(traceback.format_exc())
                logger.warning(f"Retrying... {try_i}/10")
                logger.warning(response.json())
                time.sleep(10)
                continue
                
        if not messages_with_score:
            logger.warning("Rerank failed, setting score to 0.0")
            for doc_str in all_docs_str:
                messages_with_score = [{"score": 0.0, "text": doc_str}]
        all_messages_with_score.extend(messages_with_score)
    all_messages_with_score = sorted(all_messages_with_score, key=lambda x: x["score"], reverse=True)
    logger.info(f"All rerank scores: {[m['score'] for m in all_messages_with_score]}")
    
    all_messages = []
    current_token_cnt = 0
    for msg in all_messages_with_score:
        msg_token_cnt = count_tokens_approximately([HumanMessage(content=msg["text"])])
        if current_token_cnt + msg_token_cnt > token_cnt:
            break
        all_messages.append(HumanMessage(content=msg["text"]))
        current_token_cnt += msg_token_cnt
    return all_messages


def vector_search(messages: Union[list, str], query: str, token_cnt: int = 10000):
    """
    使用向量搜索对长消息进行摘要，保留最相关的内容
    
    Args:
        messages: 消息列表
        query: 查询语句，用于确定相关内容
        token_cnt: 最大token数量限制
        
    Returns:
        经过向量搜索处理后的消息列表
    """
    
    
    
    if isinstance(messages, str):
        messages = [HumanMessage(content=messages)]

    this_token_cnt = count_tokens_approximately(messages)
    if this_token_cnt < token_cnt:
        logger.info(f"No need to use vector search, because token count ({this_token_cnt}) is less than {token_cnt}")
        return messages
    
    
    # 文本切块
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=5000, chunk_overlap=1000)
    # 获取所有消息的文本内容
    all_docs = []
    for message in messages:
        message_texts = get_buffer_string([message])
        message_doc = Document(page_content=message_texts)
        all_splits = text_splitter.split_documents([message_doc])
        all_docs.extend(all_splits)
    
    all_docs_str = [doc.page_content for doc in all_docs]
    logger.info(f"All split document length: {str([len(doc) for doc in all_docs_str])}")
    relevant_messages = perform_rerank(all_docs_str, query, token_cnt)
        
    logger.info(f"Message number: {len(messages)}, split number: {len(all_docs)}, "
                f"Relevant message number: {len(relevant_messages)}")
    return relevant_messages[::-1] # 倒序


def chatbot_with_context_manager(
    config: Config, llm: BaseChatModel, prompt: str, context_manage: Literal["token_cnt", "token_cnt_large", "last_message", "last_tool_message", "vector_search"] = "vector_search", only_last_human_message: bool = True,
):
    """
    创建一个带上下文管理功能的聊天机器人
    
    Args:
        config: 配置对象
        llm: 语言模型
        prompt: 提示词
        context_manage: 上下文管理策略
        only_last_human_message: 是否只保留最后一条人类消息
        
    Returns:
        聊天机器人函数
    """
    
    def detect_error_message(state: State):
        """
        检测状态中是否有错误消息
        
        Args:
            state: 当前状态
            
        Returns:
            如果有错误消息则返回该消息，否则返回False
        """
        if ("messages" in state) and (len(state["messages"]) > 0):
            last_message = state["messages"][-1]
            if isinstance(last_message, ToolMessage):
                if "error" in last_message.status:
                    return last_message
        return False

    def clamp_token_cnt(messages: list[dict], max_token_cnt: int):
        """
        根据最大token数量限制消息列表
        
        Args:
            messages: 消息列表
            max_token_cnt: 最大token数量
            
        Returns:
            裁剪后的消息列表
        """
        token_cnt = 0
        context_messages = []
        for message in messages[::-1]:
            token_cnt += count_tokens_approximately([message])
            if token_cnt > max_token_cnt:
                break
            context_messages.insert(0, message)
        return context_messages

    def call_react(state: State, message_to_llm: list):
        """
        调用React LLM处理消息
        
        Args:
            state: 当前状态
            message_to_llm: 发送给LLM的消息列表
            
        Returns:
            更新后的状态
        """
        # max_react_tool_call = int(os.environ.get("REACT_MAX_TOOL_CALL", 10))
        tool_call_interval = 5
        for _ in range(5):
            try:
                if "literature_tool_call_counter" not in state:
                    state["literature_tool_call_counter"] = 0
                
                for event in llm.stream({"messages": message_to_llm}, config={"recursion_limit": 100}):
                    node_name = list(event.keys())[0]
                    new_state = event[node_name]
                    all_messages = new_state["messages"]
                    if len(all_messages) > 0:
                        show_message = all_messages[-1]
                        frontend_add_message(show_message, config)
                        if isinstance(show_message, AIMessage):
                            if show_message.tool_calls:
                                for tool_call in show_message.tool_calls:
                                    frontend_add_tool_call(tool_call["name"], tool_call["args"], config)
                    
                    logger.info(f"Streaming: {node_name}, "
                                f"tool call #{state['literature_tool_call_counter']}, "
                                f"wait for {tool_call_interval} seconds, "
                                f"token cnt: {count_tokens_approximately(all_messages)}")
                    
                    # 必须要完成了工具调用再中断
                    if node_name == "tools":
                        state["literature_tool_call_counter"] += 1
                        time.sleep(tool_call_interval)
            except Exception as e:
                # 有报错，则重试
                logger.warning(f"React LLM error: {e}")
                logger.warning(traceback.format_exc())
                logger.warning("Retrying...")
                tool_call_interval = min(tool_call_interval * 2, 60)
                time.sleep(10)
                continue
            # 如果没遇到报错就跳出循环
            break
        state["messages"] += all_messages
        return state

    
    def format_prompt(state: State):
        """
        格式化提示词，替换其中的占位符
        
        Args:
            state: 当前状态
            
        Returns:
            格式化后的提示词
        """
        data_show = state["data_show"] if "data_show" in state else ""
        plan = state["plan"] if "plan" in state else ""
        question = state["question"] if "question" in state else ""
        subplan = get_subplan(state)
        literature_report = state["literature_report"] if "literature_report" in state else ""

        this_prompt = deepcopy(prompt)
        
        if "{data_show}" in this_prompt:
            try:
                if len(data_show) > 32000*4:
                    logger.warning("data_show is too long, clamping with vector search")
                    data_show = vector_search(data_show, prompt, token_cnt=32000)
                this_prompt = this_prompt.replace("{data_show}", str(data_show))
            except Exception as e:
                logger.warning("Error occurred when formatting data show", str(e))
                logger.warning(traceback.format_exc())
            
        if "{literature_report}" in this_prompt:
            try:
                if len(literature_report) > 4000*4:
                    logger.warning("Literature report is too long, clamping with vector search")
                    literature_report = vector_search(literature_report, prompt, token_cnt=4000)
                this_prompt = this_prompt.replace("{literature_report}", str(literature_report))
            except Exception as e:
                logger.warning("Error occurred when formatting literature report", str(e))
                logger.warning(traceback.format_exc())
          
        if "{plan}" in this_prompt:  
            try:
                plan_str = json.dumps(plan)
                if len(plan_str) > 4000*4:
                    logger.warning("Plan is too long, clamping with vector search")
                    plan_str = vector_search(plan_str, prompt, token_cnt=4000)
                this_prompt = this_prompt.replace("{plan}", str(plan_str))
            except Exception as e:
                logger.warning("Error occurred when formatting plan", str(e))
                logger.warning(traceback.format_exc())
            
        if "{question}" in this_prompt:
            try:
                this_prompt = this_prompt.replace("{question}", question)
            except Exception as e:
                logger.warning("Error occurred when formatting question", str(e))
                logger.warning(traceback.format_exc())
            
        if "{subplan}" in this_prompt:
            try:
                this_prompt = this_prompt.replace("{subplan}", subplan)
            except Exception as e:
                logger.warning("Error occurred when formatting subplan", str(e))
                logger.warning(traceback.format_exc())
        
        return this_prompt
        
    def chatbot(state: State):
        """
        聊天机器人主函数，处理不同类型的消息和上下文管理策略
        
        Args:
            state: 当前状态
            
        Returns:
            更新后的状态
        """
        this_prompt = format_prompt(state)

        logger.info(f"Context management: {context_manage}")
        if context_manage == "last_message":
            # 只保留最后一条消息
            logger.info("Only keep the last message")
            message_to_llm = state["messages"][-1:]
        elif context_manage == "last_tool_message":
            # 只保留最后一条tool消息（如果有的话）
            logger.info("Keep to the last tool message")
            # tool_messages = [msg for msg in state["messages"] if isinstance(msg, ToolMessage)]
            last_tool_message_index = 0
            for msg_i in range(len(state["messages"]) - 1, -1, -1):
                if isinstance(state["messages"][msg_i], ToolMessage):
                    last_tool_message_index = msg_i
                    break
            message_to_llm = state["messages"][last_tool_message_index:]
        elif context_manage == "vector_search":
            # 使用向量搜索选择最相关的历史消息
            logger.info("Using vector search for context management")
            # 使用当前prompt作为查询，搜索最相关的5条历史消息
            message_to_llm = vector_search(state["messages"], this_prompt, token_cnt=int(os.environ.get("MAX_CONTEXT_TOKEN_CNT", 10000)))
        elif context_manage == "token_cnt_large":
            max_context_token_cnt_large = int(os.environ.get("MAX_CONTEXT_TOKEN_CNT_LARGE", 96000))
            logger.info(f"Use max_context_token_cnt_large: {max_context_token_cnt_large}")
            message_to_llm = clamp_token_cnt(state["messages"], max_context_token_cnt_large)
        else:   # 默认为 token_cnt
            max_context_token_cnt = int(os.environ.get("MAX_CONTEXT_TOKEN_CNT", 64000))
            logger.info(f"Use max_context_token_cnt: {max_context_token_cnt}")
            message_to_llm = clamp_token_cnt(state["messages"], max_context_token_cnt)

        last_error_message = detect_error_message(state)
        if last_error_message:
            logger.warning("Error message detected, do not add prompt to context.")
            message_to_llm.append(last_error_message)
        else:
            # state["messages"].append({"role": "user", "content": this_prompt})
            state["messages"].append(HumanMessage(content=this_prompt))
            message_to_llm.append(state["messages"][-1])
            if not isinstance(llm, CompiledStateGraph):
                frontend_add_message(state["messages"][-1], config)
            logger.info(f"Prompt: {this_prompt[:1000]}...")
        
        # 只保留最后一条HumanMessage
        if only_last_human_message:
            if isinstance(message_to_llm[-1], HumanMessage):
                last_human_message = message_to_llm[-1]
                message_no_human = [msg for msg in message_to_llm if not isinstance(msg, HumanMessage)]
                message_to_llm = message_no_human + [last_human_message]
                logger.info("Only keep the last human message")
        
        logger.info(f"Message count to LLM: {len(message_to_llm)}, token count: {count_tokens_approximately(message_to_llm)}")

        time_stamp = datetime.now().strftime("%Y%m%d%H%M%S")
        save_path = os.path.join(config.save_path, "llm_calls", f"{time_stamp}.json")
        os.makedirs(os.path.dirname(save_path), exist_ok=True)

        with open(save_path, "w") as f:
            # f.write(get_buffer_string(message_to_llm))
            f.write(dumps(message_to_llm, indent=4))
        
        with open(save_path, "r") as f:
            message_to_llm = loads(f.read())

        if isinstance(llm, CompiledStateGraph):
            assert "pre_model_hook" in llm.nodes, "React LLM graph must have a pre_model_hook node"
            state = call_react(state, message_to_llm)
        else:
            for try_i in range(10):
                try:
                    state["messages"].append(llm.invoke(message_to_llm))
                    frontend_add_message(state["messages"][-1], config)
                    break
                except Exception as e:
                    logger.warning(f"Error when calling llm: {e}")
                    logger.warning(traceback.format_exc())
                    logger.warning("Retrying...")
                    time.sleep(5)
                    continue

        with open(save_path, "w") as f:
            f.write(dumps(message_to_llm + [state["messages"][-1]], indent=4))

        return state

    return chatbot


if __name__ == "__main__":
    res = vector_search(
        [
            HumanMessage(content="What is the meaning of life?"),
            HumanMessage(content="The meaning of life is 42."),
            HumanMessage(content="What is the meaning of water?"),
        ],
        "What is the meaning of life?",
        k=1
    )
    print(res)