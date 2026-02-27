"""
LifeOS LLM 客户端
基于 LiteLLM 支持 Ollama / OpenAI / Anthropic / 任意兼容接口
"""
from __future__ import annotations
import os
from typing import Optional, AsyncIterator
import httpx


class LLMClient:
    """
    统一 LLM 调用接口
    配置优先级：Ollama（本地）> OpenAI > Anthropic
    """

    def __init__(self):
        self.ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
        self.ollama_chat_model = os.getenv("CHAT_MODEL", "llama3.1:8b")
        self.openai_key = os.getenv("OPENAI_API_KEY", "")
        self.anthropic_key = os.getenv("ANTHROPIC_API_KEY", "")
        self.openai_model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self._use_ollama: Optional[bool] = None

    async def _check_ollama(self) -> bool:
        if self._use_ollama is not None:
            return self._use_ollama
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                resp = await client.get(f"{self.ollama_url}/api/tags")
                tags = resp.json().get("models", [])
                model_names = [t.get("name", "") for t in tags]
                # 检查指定模型是否已拉取
                self._use_ollama = any(
                    self.ollama_chat_model in name for name in model_names
                )
        except Exception:
            self._use_ollama = False
        return self._use_ollama

    async def chat(
        self,
        messages: list[dict],
        system: str = "",
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> str:
        """发送聊天请求，返回文本响应"""
        if system:
            messages = [{"role": "system", "content": system}] + messages

        if await self._check_ollama():
            return await self._chat_ollama(messages, temperature, max_tokens)
        elif self.anthropic_key:
            return await self._chat_anthropic(messages, temperature, max_tokens)
        elif self.openai_key:
            return await self._chat_openai(messages, temperature, max_tokens)
        else:
            return "⚠️ 未配置 LLM。请在设置中配置 Ollama 或 API Key。"

    async def _chat_ollama(self, messages, temperature, max_tokens) -> str:
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                resp = await client.post(
                    f"{self.ollama_url}/api/chat",
                    json={
                        "model": self.ollama_chat_model,
                        "messages": messages,
                        "stream": False,
                        "options": {
                            "temperature": temperature,
                            "num_predict": max_tokens,
                        }
                    }
                )
                data = resp.json()
                return data["message"]["content"]
        except Exception as e:
            self._use_ollama = False
            return f"Ollama 调用失败: {e}"

    async def _chat_openai(self, messages, temperature, max_tokens) -> str:
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={"Authorization": f"Bearer {self.openai_key}"},
                    json={
                        "model": self.openai_model,
                        "messages": messages,
                        "temperature": temperature,
                        "max_tokens": max_tokens,
                    }
                )
                data = resp.json()
                return data["choices"][0]["message"]["content"]
        except Exception as e:
            return f"OpenAI 调用失败: {e}"

    async def _chat_anthropic(self, messages, temperature, max_tokens) -> str:
        try:
            system_msg = ""
            filtered = []
            for m in messages:
                if m["role"] == "system":
                    system_msg = m["content"]
                else:
                    filtered.append(m)

            payload = {
                "model": "claude-3-5-haiku-20241022",
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": filtered,
            }
            if system_msg:
                payload["system"] = system_msg

            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": self.anthropic_key,
                        "anthropic-version": "2023-06-01",
                    },
                    json=payload
                )
                data = resp.json()
                return data["content"][0]["text"]
        except Exception as e:
            return f"Anthropic 调用失败: {e}"

    async def get_available_provider(self) -> str:
        if await self._check_ollama():
            return f"Ollama ({self.ollama_chat_model})"
        elif self.anthropic_key:
            return "Anthropic Claude"
        elif self.openai_key:
            return f"OpenAI ({self.openai_model})"
        return "未配置"


_llm_client: Optional[LLMClient] = None

def get_llm_client() -> LLMClient:
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client
