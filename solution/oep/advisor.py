from __future__ import annotations

import json
import urllib.request
import urllib.error

from .config import AppConfig


def _prompt_from_data(oep_data: dict) -> str:
    return (
        "Resume en español técnico y breve las 3 principales mejoras para un operador de pala minera. "
        "Usa solo las métricas entregadas. Datos: " + json.dumps(oep_data["dimensions"], ensure_ascii=False)
    )


def get_ai_advice(oep_data: dict, config: AppConfig) -> str | None:
    if not config.use_ai_advisor:
        return None
    prompt = _prompt_from_data(oep_data)
    if config.openai_api_key:
        try:
            payload = json.dumps({
                "model": config.openai_model,
                "input": prompt,
            }).encode()
            req = urllib.request.Request(
                "https://api.openai.com/v1/responses",
                data=payload,
                headers={"Authorization": f"Bearer {config.openai_api_key}", "Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode())
            text = data.get("output", [])
            pieces = []
            for item in text:
                for content in item.get("content", []):
                    if content.get("type") == "output_text":
                        pieces.append(content.get("text", ""))
            return "\n".join(pieces).strip() or None
        except Exception:
            return None
    try:
        payload = json.dumps({"model": config.ollama_model, "prompt": prompt, "stream": False}).encode()
        req = urllib.request.Request(
            f"{config.ollama_base_url}/api/generate",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())
        return data.get("response", "").strip() or None
    except Exception:
        return None
