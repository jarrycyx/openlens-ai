import os
import json
from typing import Optional, Type, Dict, Any, Union
from typing_extensions import Literal
from loguru import logger
import time
from datetime import datetime

import requests
import traceback
from copy import deepcopy

from langchain_core.messages import ToolMessage, HumanMessage, AIMessage
from langchain_core.messages.utils import count_tokens_approximately, get_buffer_string
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

import numpy as np


def vector_search_match_type(message: str, rerank_model: str, rerank_api_key: str, rerank_base_url: str, query: str, token_cnt: int = 10000):
    """
    Perform vector search based on message type and maintain message type consistency

    Args:
        message: Original message
        query: Query string
        token_cnt: Maximum token count

    Returns:
        Processed message, maintaining the original message type
    """
    message_type = type(message)
    short_messages = vector_search([message], rerank_model, rerank_api_key, rerank_base_url, query, token_cnt=token_cnt)
    # Merge
    all_content = [message.content for message in short_messages]
    if message_type == ToolMessage:
        return message_type(content="\n".join(all_content), tool_call_id=message.tool_call_id, name=message.name, status=message.status)
    else:
        return message_type("\n".join(all_content))


def perform_rerank(all_docs_str: list[str], query: str, token_cnt: int, rerank_model: str, rerank_api_key: str, rerank_base_url: str):
    if len(query) > 2000:
        logger.warning("Query is too long, truncating to 2000 characters: " + query[:2000])
        query = query[:2000]

    all_messages_with_score = []
    # for doc_str in all_docs_str:
    # If len(all_docs_str) is greater than 32, split into chunks of size 32
    all_docs_chunks = [all_docs_str[i : i + 32] for i in range(0, len(all_docs_str), 32)]

    for docs_chunk in all_docs_chunks:

        # Create vector storage
        input_doc_list = docs_chunk
        payload = {"model": rerank_model, "query": query, "documents": input_doc_list, "return_raw_scores": True}
        api_key = rerank_api_key
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}
        url = rerank_base_url + "rerank"
        # url = "https://cloud.infini-ai.com/maas/v1/rerank"

        messages_with_score = []
        for try_i in range(10):
            response = requests.post(url, json=payload, headers=headers)
            try:
                messages_with_score = []
                for res in response.json()["results"]:
                    if ("document" in res) and isinstance(res["document"], str):
                        messages_with_score.append({"text": res["document"], "score": res["relevance_score"]})

                    elif ("document" in res) and ("text" in res["document"]) and isinstance(res["document"], dict) and isinstance(res["document"]["text"], str):

                        messages_with_score.append({"text": res["document"]["text"], "score": res["relevance_score"]})
                    elif "index" in res:
                        messages_with_score.append({"text": input_doc_list[int(res["index"])], "score": res["relevance_score"]})
                    else:
                        raise ValueError("Invalid document type")

                break
            except Exception as e:
                logger.warning(f"Get rerank result error: {e}")
                logger.warning(traceback.format_exc())
                logger.warning(f"Retrying... {try_i}/10")
                try:
                    logger.warning(response.json())
                except:
                    logger.warning(str(response))
                time.sleep(10)
                continue

        if not messages_with_score:
            logger.warning("Rerank failed, setting score to 0.0")
            for doc_str in all_docs_str:
                messages_with_score = [{"score": 0.0, "text": doc_str}]
        all_messages_with_score.extend(messages_with_score)
    all_messages_with_score = sorted(all_messages_with_score, key=lambda x: x["score"], reverse=True)
    all_rerank_scores = [m["score"] for m in all_messages_with_score]
    logger.info(f"All rerank scores max: {max(all_rerank_scores):.3f}, min: {min(all_rerank_scores):.3f}, avg: {sum(all_rerank_scores) / len(all_rerank_scores):.3f}")



    all_str = []
    current_token_cnt = 0
    for msg in all_messages_with_score:
        msg_token_cnt = count_tokens_approximately([HumanMessage(content=msg["text"])])
        if current_token_cnt + msg_token_cnt > token_cnt:
            break
        all_str.append(msg["text"])
        current_token_cnt += msg_token_cnt
    return all_str


def vector_search(messages: Union[list, str], rerank_model: str, rerank_api_key: str, rerank_base_url: str, query: str, token_cnt: int = 10000):
    """
    Use vector search to summarize long messages, retaining the most relevant content

    Args:
        messages: Message list
        query: Query string to determine relevant content
        token_cnt: Maximum token count limit

    Returns:
        Message list processed by vector search
    """

    if isinstance(messages, str):
        messages = [HumanMessage(content=messages)]

    this_token_cnt = count_tokens_approximately(messages)
    if this_token_cnt < token_cnt:
        logger.info(f"No need to use vector search, because token count ({this_token_cnt}) is less than {token_cnt}")
        return messages

    # Text chunking
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=3000, chunk_overlap=500)
    # Get text content of all messages
    all_docs = []
    for message in messages:
        message_texts = get_buffer_string([message])
        message_doc = Document(page_content=message_texts)
        all_splits = text_splitter.split_documents([message_doc])
        all_docs.extend(all_splits)

    all_docs_str = [doc.page_content for doc in all_docs]
    logger.info(f"All split document length: {str([len(doc) for doc in all_docs_str])}")
    relevant_strs = perform_rerank(all_docs_str, query, token_cnt, rerank_model, rerank_api_key, rerank_base_url)
    relevant_messages = [HumanMessage(content=msg) for msg in relevant_strs]

    logger.info(f"Message number: {len(messages)}, split number: {len(all_docs)}, " f"Relevant message number: {len(relevant_messages)}")
    return relevant_messages[::-1]  # Reverse order