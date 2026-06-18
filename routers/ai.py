"""
AI 问答路由 - 提供 RAG（检索增强生成）聊天接口
================================================================
流程: 用户提问 → FAISS 检索相关新闻 → 拼接上下文 → Qwen3-max 生成回答 → SSE 流式返回
依赖: utils.vector_store (向量检索), DashScope API (LLM)
================================================================

接口:
  POST /api/ai/chat  — 聊天（支持流式 SSE 和非流式）
"""
import os
import json
from typing import Any
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from openai import OpenAI

from utils import vector_store

# ========== 路由定义 ==========
router = APIRouter(prefix="/api/ai", tags=["ai"])

# ========== 配置 ==========
API_KEY = os.environ.get("DASHSCOPE_API_KEY", "")
BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"

# DashScope LLM 客户端
client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

# 系统提示词：约束 AI 只基于检索到的新闻回答
SYSTEM_PROMPT = """你是一个新闻助手。根据以下新闻内容回答用户的问题。

规则：
1. 只根据提供的新闻内容回答，不要编造信息
2. 如果新闻中没有相关信息，如实告知用户
3. 回答时引用新闻中的具体内容
4. 如果涉及多条新闻，可以用列表形式呈现
"""


# ========== 请求模型 ==========
class ChatRequest(BaseModel):
    """聊天请求体"""
    messages: list[dict[str, Any]]  # 对话历史 [{role, content}, ...]
    stream: bool = True             # 是否流式返回


# ========== 接口 ==========

@router.post("/chat")
async def ai_chat(req: ChatRequest):
    """
    AI 聊天接口（RAG 增强）

    工作流程:
      1. 提取用户最后一条消息
      2. 调用 vector_store.search_news() 检索 5 篇最相关新闻
      3. 将检索到的新闻拼接为上下文，注入 system prompt
      4. 调用 Qwen3-max 流式生成回答
      5. 通过 SSE (Server-Sent Events) 实时推送文本到前端

    请求示例:
      POST /api/ai/chat
      {"messages": [{"role":"user","content":"最近科技新闻有什么"}], "stream": true}

    响应格式 (SSE):
      data: {"choices":[{"delta":{"content":"根据..."}}]}
      data: [DONE]
    """
    user_message = req.messages[-1]["content"] if req.messages else ""

    # 1. 检索相关新闻（从 FAISS 向量库中找最相关的 5 篇）
    search_results = vector_store.search_news(user_message, k=5)

    # 2. 拼接检索结果作为上下文
    context_parts = []
    for i, result in enumerate(search_results):
        meta = result["metadata"]
        source = meta.get("author", "未知")
        context_parts.append(
            f"【新闻{i+1}】（来源：{source}）\n{result['content']}"
        )
    context = "\n\n".join(context_parts) if context_parts else "暂无相关新闻"

    # 3. 构建完整对话消息
    # system: 角色设定 + 检索到的新闻上下文
    # 历史消息: 最近 10 条（保留对话记忆但不超出 token 限制）
    # user: 当前提问
    chat_messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "system", "content": f"当前可参考的新闻：\n{context}"},
    ]
    for msg in req.messages[-10:-1]:
        chat_messages.append(msg)
    chat_messages.append({"role": "user", "content": user_message})

    # 4. 调用 LLM
    if req.stream:
        return StreamingResponse(
            _stream_response(chat_messages),
            media_type="text/event-stream",  # SSE 格式
        )
    else:
        completion = client.chat.completions.create(
            model="qwen3-max",
            messages=chat_messages,
            stream=False,
        )
        reply = completion.choices[0].message.content
        return {"reply": reply, "sources": len(search_results)}


async def _stream_response(messages: list[dict]):
    """
    SSE 流式响应生成器
    逐 token 推送 LLM 的输出，前端实时渲染
    格式: data: {"choices":[{"delta":{"content":"片段"}}]}\n\n
    """
    try:
        stream = client.chat.completions.create(
            model="qwen3-max",
            messages=messages,
            stream=True,
        )
        for chunk in stream:
            delta = chunk.choices[0].delta
            if delta.content:
                data = json.dumps({
                    "choices": [{"delta": {"content": delta.content}}]
                }, ensure_ascii=False)
                yield f"data: {data}\n\n"
        yield "data: [DONE]\n\n"
    except Exception as e:
        error_data = json.dumps({"error": str(e)}, ensure_ascii=False)
        yield f"data: {error_data}\n\n"
