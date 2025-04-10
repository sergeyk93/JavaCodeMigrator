import os
from configparser import ConfigParser
from dataclasses import dataclass
from functools import lru_cache


class ConfigError(Exception):
    pass


@dataclass(frozen=True)
class AppConfig:
    openai_key: str
    openai_model: str
    temperature: float
    cache_llm_responses: bool
    # The name of the project to migrate. Must be the directory name of the project inside the `input` directory.
    input_project: str
    # Comma separated file extensions
    file_extensions_to_analyze: str
    file_extensions_to_migrate: str
    # Output all the LLM responses to a file for debugging/auditing
    log_llm_responses: bool


@lru_cache(maxsize=1)
def get_config() -> AppConfig:
    parser = ConfigParser()
    path = "config.ini"

    if not os.path.exists(path):
        raise ConfigError(f"Config file not found: {path}")

    parser.read(path)

    try:
        return AppConfig(
            openai_key=parser.get("openai", "api_key", fallback="development"),
            openai_model=parser.get("openai", "model", fallback="gpt-4o-mini"),
            temperature=parser.getfloat("openai", "temperature", fallback=0.0),
            cache_llm_responses=parser.getboolean("general", "cache_llm_responses", fallback=False),
            input_project=parser.get("general", "input_project"),
            file_extensions_to_analyze=parser.get("general", "file_extensions_to_analyze"),
            file_extensions_to_migrate=parser.get("general", "file_extensions_to_migrate"),
            log_llm_responses=parser.getboolean("general", "log_llm_responses", fallback=False),
        )
    except Exception as e:
        raise ConfigError(f"Invalid config: {e}")
