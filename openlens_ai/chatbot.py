import os
import json
from typing import Optional, Type, Dict, Any, Union
from typing_extensions import Literal
from loguru import logger
import asyncio
import time
from datetime import datetime

import numpy as np
import requests
import traceback
from copy import deepcopy

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import ToolMessage, HumanMessage, AIMessage
from langchain_core.messages.utils import count_tokens_approximately, get_buffer_string
from langgraph.graph.state import CompiledStateGraph
from langchain.load.dump import dumps
from langchain.load.load import loads
from langgraph.errors import GraphRecursionError

from .state import State, load_state, get_subplan, track_node_call
from .utils.frontend_messages import frontend_add_message, frontend_add_tool_call
from .utils.config import Config, get_lang_prompt
from .utils.embedding import vector_search_match_type, perform_rerank, vector_search





def react_pre_model_wrapper(vector_search_question: str, config: Config):
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
        max_tool_token_cnt = config.context.max_tool_token_cnt
        logger.info(f"React pre model hook called with llm input message len {len(state['messages'])}")
        # 如果工具返回信息太多，用向量搜索
        for message_i, message in enumerate(state["messages"]):
            if isinstance(message, ToolMessage):
                token_cnt = count_tokens_approximately([message])
                if token_cnt > max_tool_token_cnt * 2:
                    short_message = vector_search_match_type(message, config.rerank.rerank_model, config.rerank.rerank_api_key, config.rerank.rerank_base_url, vector_search_question, config.context.max_tool_token_cnt)
                    logger.info(f"Message is too long ({token_cnt}), " f"use vector search to summarize to ({count_tokens_approximately([short_message])})")
                    state["messages"][message_i] = short_message
        return state

    return react_pre_model_hook


def chatbot_with_context_manager(
    config: Config,
    llm: BaseChatModel,
    prompt: str,
    context_manage: Literal["token_cnt", "token_cnt_large", "last_message", "last_tool_message", "vector_search"] = "vector_search",
    only_last_human_message: bool = False,
    calling_subgraph: str = "",
    force_stringify_context: bool = False,
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
            this_token_cnt = count_tokens_approximately([message])
            if token_cnt + this_token_cnt > max_token_cnt:
                message_clamped = message.copy()
                try:
                    message_clamped.content = message_clamped.content[:(max_token_cnt - token_cnt)*4]
                    logger.debug(f"Clamped message content from {len(message.content)} to {len(message_clamped.content)}")
                    context_messages.insert(0, message_clamped)
                except Exception as e:
                    logger.warning(f"Error clamping message content: {e}")
                    pass
                break
            else:
                context_messages.insert(0, message)
                token_cnt += this_token_cnt
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
        # max_react_tool_call = int(config.max_tool_call) if hasattr(config, 'max_tool_call') else 10
        tool_call_interval = 5
        for _ in range(5):
            try:
                if "literature_tool_call_counter" not in state:
                    state["literature_tool_call_counter"] = 0

                for event in llm.stream({"messages": message_to_llm}, config={"recursion_limit": 50}):
                    node_name = list(event.keys())[0]
                    new_state = event[node_name]
                    all_messages = new_state["messages"]
                    
                    
                    time_stamp = datetime.now().strftime("%Y%m%d%H%M%S")
                    save_path = os.path.join(config.save_path, "llm_calls", f"{time_stamp}.json")
                    os.makedirs(os.path.dirname(save_path), exist_ok=True)

                    with open(save_path, "w") as f:
                        # f.write(get_buffer_string(message_to_llm))
                        f.write(dumps(all_messages, indent=4, ensure_ascii=False))
                    
                    if len(all_messages) > 0:
                        show_message = all_messages[-1]
                        frontend_add_message(show_message, config)
                        if isinstance(show_message, AIMessage):
                            if show_message.tool_calls:
                                for tool_call in show_message.tool_calls:
                                    frontend_add_tool_call(tool_call["name"], tool_call["args"], config)

                    logger.info(
                        f"Streaming: {node_name}, "
                        f"tool call #{state['literature_tool_call_counter']}, "
                        f"wait for {tool_call_interval} seconds, "
                        f"token cnt: {count_tokens_approximately(all_messages)}"
                    )

                    # 必须要完成了工具调用再中断
                    if node_name == "tools":
                        state["literature_tool_call_counter"] += 1
                        time.sleep(tool_call_interval)
            except GraphRecursionError as e:
                logger.warning(f"React LLM exceeds recursion limit: {e}")
                break
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
                if len(data_show) > 32000 * 4:
                    logger.warning("data_show is too long, clamping with vector search")
                    data_show = vector_search(data_show, config.rerank.rerank_model, config.rerank.rerank_api_key, config.rerank.rerank_base_url, prompt, token_cnt=32000)
                this_prompt = this_prompt.replace("{data_show}", str(data_show))
            except Exception as e:
                logger.warning("Error occurred when formatting data show", str(e))
                logger.warning(traceback.format_exc())

        if "{literature_report}" in this_prompt:
            try:
                if len(literature_report) > 4000 * 4:
                    logger.warning("Literature report is too long, clamping with vector search")
                    literature_report = vector_search(
                        literature_report, config.rerank.rerank_model, config.rerank.rerank_api_key, config.rerank.rerank_base_url, prompt, token_cnt=4000
                    )
                this_prompt = this_prompt.replace("{literature_report}", str(literature_report))
            except Exception as e:
                logger.warning("Error occurred when formatting literature report", str(e))
                logger.warning(traceback.format_exc())

        if "{plan}" in this_prompt:
            try:
                plan_str = json.dumps(plan, ensure_ascii=False, indent=4)
                if len(plan_str) > 4000 * 4:
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

        # 添加语言提示
        this_prompt += get_lang_prompt(config.llm.language)
        if config.important:
            this_prompt += "\n## Important Instructions\n" + config.important

        return this_prompt

    @track_node_call(calling_subgraph)
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
            message_to_llm = vector_search(
                state["messages"], config.rerank.rerank_model, config.rerank.rerank_api_key, config.rerank.rerank_base_url, this_prompt, token_cnt=config.context.max_context_token_cnt
            )
        elif context_manage == "token_cnt_large":
            max_context_token_cnt_large = config.context.max_context_token_cnt_large
            logger.info(f"Use max_context_token_cnt_large: {max_context_token_cnt_large}")
            message_to_llm = clamp_token_cnt(state["messages"], max_context_token_cnt_large)
        else:  # 默认为 token_cnt
            max_context_token_cnt = config.context.max_context_token_cnt
            logger.info(f"Use max_context_token_cnt: {max_context_token_cnt}")
            message_to_llm = clamp_token_cnt(state["messages"], max_context_token_cnt)
            
        if force_stringify_context:
            logger.warning("Force stringify context, this may cause loss of information.")
            message_to_llm = [HumanMessage(content=str(message_to_llm))]

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
            f.write(dumps(message_to_llm, indent=4, ensure_ascii=False))

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
            f.write(dumps(message_to_llm + [state["messages"][-1]], indent=4, ensure_ascii=False))

        return state

    return chatbot


if __name__ == "__main__":
    config = Config.from_toml("config.toml")
    res = vector_search(
        [
            HumanMessage(content="What is the meaning of life?"),
            HumanMessage(content="The meaning of life is 42."),
            HumanMessage(content="What is the meaning of water?"),
        ],
        config.rerank.rerank_model, config.rerank.rerank_api_key, config.rerank.rerank_base_url,
        "What is the meaning of life?",
        k=1,
    )
    print(res)
