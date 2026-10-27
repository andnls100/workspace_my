"""Check DeepSeek API credentials, model listing, and a minimal completion."""
from __future__ import annotations
import os, sys
from .common import load_env

def main() -> int:
    load_env()
    key = os.getenv("DEEPSEEK_API_KEY", "").strip()
    base = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com").strip()
    model = os.getenv("DEEPSEEK_MODEL", "").strip()
    if not key:
        print("缺少 DEEPSEEK_API_KEY；请在本地 .env 设置，不要提交密钥。", file=sys.stderr)
        return 2
    try:
        from openai import OpenAI
        client = OpenAI(api_key=key, base_url=base, timeout=30, max_retries=1)
        listing = client.models.list()
        ids = sorted({m.id for m in listing.data})
        print(f"API 可连接。Base URL: {base}")
        print("账户可见模型：")
        for item in ids:
            print(" -", item)
        if not model:
            print("尚未设置 DEEPSEEK_MODEL；请从上方列表选择可用模型后设置。")
            return 0
        if model not in ids:
            print(f"警告：配置模型 {model!r} 不在模型列表中。不要假定别名可用；请核实官方当前文档。")
            return 3
        result = client.chat.completions.create(
            model=model,
            messages=[{"role":"user","content":"只回复 OK"}],
            max_tokens=8,
            temperature=0,
        )
        print("最小请求成功。返回模型字段:", getattr(result, "model", None))
        print("响应:", (result.choices[0].message.content or "").strip())
        return 0
    except Exception as exc:
        print(f"API 检查失败: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
