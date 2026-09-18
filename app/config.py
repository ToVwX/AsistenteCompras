from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()

# Compatibilidad con el agente anterior del mismo workspace. Solo se usa si la
# clave no fue definida en el .env de este proyecto o en el entorno del sistema.
legacy_env = Path(__file__).resolve().parents[2] / "Mi primer ia" / ".env"
if not (os.getenv("GROQ_API_KEY") or os.getenv("API_KEY_GROQ")) and legacy_env.exists():
    load_dotenv(legacy_env, override=False)


def _default_provider() -> str:
    has_key = bool(os.getenv("GROQ_API_KEY") or os.getenv("API_KEY_GROQ"))
    return "groq" if has_key else "mock"


@dataclass(frozen=True)
class Settings:
    """Configuracion obtenida de variables de entorno."""

    provider: str = os.getenv("AGENT_PROVIDER", _default_provider()).strip().lower()
    groq_api_key: str | None = os.getenv("GROQ_API_KEY") or os.getenv("API_KEY_GROQ")
    groq_model: str | None = os.getenv("GROQ_MODEL", "qwen/qwen3.8-27b")
    max_output_tokens: int = int(os.getenv("GROQ_MAX_OUTPUT_TOKENS", "500"))
    max_history_messages: int = int(os.getenv("MAX_HISTORY_MESSAGES", "12"))

    def validate(self) -> None:
        if self.provider not in {"mock", "groq"}:
            raise ValueError("AGENT_PROVIDER debe ser 'mock' o 'groq'.")
        if self.max_history_messages < 2:
            raise ValueError("MAX_HISTORY_MESSAGES debe ser igual o mayor que 2.")
        if not 64 <= self.max_output_tokens <= 900:
            raise ValueError("GROQ_MAX_OUTPUT_TOKENS debe estar entre 64 y 900.")
        if self.provider == "groq" and not self.groq_api_key:
            raise ValueError("Falta GROQ_API_KEY para usar AGENT_PROVIDER=groq.")
        if self.provider == "groq" and not self.groq_model:
            raise ValueError("Falta GROQ_MODEL para usar AGENT_PROVIDER=groq.")


settings = Settings()
