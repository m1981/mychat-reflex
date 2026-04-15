"""
Core Domain Module.

This module contains pure business logic, interfaces (ports), and domain entities.
Strictly NO infrastructure or framework dependencies (like Anthropic or OpenAI SDKs)
are allowed here.

Adapters have been moved to mychat_reflex.infrastructure.llm_adapters.
"""

from .database import DatabaseConfig
from .llm_ports import (
    Role,
    LLMConfig,
    ILLMService,
)

__all__ = [
    # Database
    "DatabaseConfig",
    # LLM Ports (Interfaces & Domain Entities)
    "Role",
    "LLMConfig",
    "ILLMService",
]
