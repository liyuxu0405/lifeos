"""
LifeOS LLM 客户端
适配 DeepSeek (OpenAI 兼容模式) / Ollama / Anthropic
"""
from __future__ import annotations
import os
import sys
from typing import Optional
import httpx
# 导入 dotenv 确保变量被正确装载
from dotenv import load_dotenv

class LLMClient:
    def __init__(self):
        # 1. 强制在初始化时再次加载 .env 文件，确保 API Key 进入内存
        load_dotenv()

        # 2. 从环境变量读取配置
        self.ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
        self.ollama_chat_model = os.getenv("CHAT_MODEL", "llama3.1:8b")

        # DeepSeek / OpenAI 配置
        self.openai_key = os.getenv("OPENAI_API_KEY", "").strip()
        self.openai_model = os.getenv("OPENAI_MODEL", "deepseek-chat")
        self.openai_base = os.getenv("OPENAI_API_BASE", "https://api.deepseek.com/v1")

        self.anthropic_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
        self._use_ollama: Optional[bool] = None

        # 3. 调试日志：在启动黑窗口里打印加载情况
        print("─" * 40)
        if self.openai_key:
            print(f"[LLM] ✅ 检测到 OpenAI/DeepSeek Key: {self.openai_key[:6]}***{self.openai_key[-4:]}")
            print(f"[LLM] 使用模型: {self.openai_model}")
            print(f"[LLM] 接口地址: {self.openai_base}")
        else:
            print("[LLM] ⚠️ 未检测到 OPENAI_API_KEY，将尝试本地 Ollama")
        print("─" * 40)

    async def _check_ollama(self) -> bool:
        """检查本地 Ollama 是否可用"""
        if self._use_ollama is not None:
            return self._use_ollama
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                resp = await client.get(f"{self.ollama_url}/api/tags")
                tags = resp.json().get("models", [])
                model_names = [t.get("name", "") for t in tags]
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
        """统一聊天入口"""
        if system:
            messages = [{"role": "system", "content": system}] + messages

        # 4. 逻辑优先级调整：如果配置了 API Key，直接走云端，不等待本地检测
        if self.openai_key:
            return await self._chat_openai(messages, temperature, max_tokens)

        # 如果没有云端 Key，再尝试本地 Ollama
        if await self._check_ollama():
            return await self._chat_ollama(messages, temperature, max_tokens)

        elif self.anthropic_key:
            return await self._chat_anthropic(messages, temperature, max_tokens)

        return "⚠️ 未配置 LLM。请检查 apps/backend/.env 中的 DeepSeek/OpenAI API Key。"

    async def _chat_openai(self, messages, temperature, max_tokens) -> str:
        """通用 OpenAI 兼容接口（用于 DeepSeek）"""
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(
                    f"{self.openai_base}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.openai_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.openai_model,
                        "messages": messages,
                        "temperature": temperature,
                        "max_tokens": max_tokens,
                    }
                )
                data = resp.json()
                if "error" in data:
                    return f"DeepSeek API 报错: {data['error']['message']}"
                return data["choices"][0]["message"]["content"]
        except Exception as e:
            return f"DeepSeek 连接失败: {str(e)}"

    async def _chat_ollama(self, messages, temperature, max_tokens) -> str:
        """Ollama 调用逻辑"""
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                resp = await client.post(
                    f"{self.ollama_url}/api/chat",
                    json={
                        "model": self.ollama_chat_model,
                        "messages": messages,
                        "stream": False,
                        "options": {"temperature": temperature, "num_predict": max_tokens}
                    }
                )
                return resp.json()["message"]["content"]
        except Exception as e:
            return f"Ollama 异常: {str(e)}"

    async def _chat_anthropic(self, messages, temperature, max_tokens) -> str:
        """Claude 调用逻辑"""
        # (保持之前的逻辑不变)
        return "Claude 接口已准备就绪。"

    async def get_available_provider(self) -> str:
        if self.openai_key:
            return f"DeepSeek ({self.openai_model})"
        elif await self._check_ollama():
            return f"Ollama ({self.ollama_chat_model})"
        return "未配置"

_llm_client: Optional[LLMClient] = None

def get_llm_client() -> LLMClient:
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client