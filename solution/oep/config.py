from __future__ import annotations

from dataclasses import dataclass
import os


@dataclass(frozen=True)
class AppConfig:
    inputs_dir: str = "inputs"
    outputs_dir: str = "outputs"
    dashboard_dir: str = "outputs/dashboard"
    left_video: str = "inputs/shovel_left.mp4"
    right_video: str = "inputs/shovel_right.mp4"
    imu_file: str = "inputs/imu_data.npy"
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
    ollama_model: str = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY")
    use_ai_advisor: bool = os.getenv("USE_AI_ADVISOR", "0") == "1"


CONFIG = AppConfig()
