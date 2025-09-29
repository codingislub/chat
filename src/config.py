"""Configuration management for the invoice chatbot."""

import os
import logging
from pathlib import Path
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings


logger = logging.getLogger(__name__)


class OpenAIConfig(BaseSettings):
    """OpenAI API configuration."""
    
    api_key: str = Field(..., env="OPENAI_API_KEY")
    vision_model: str = Field("gpt-4o-mini", env="OPENAI_VISION_MODEL")
    text_model: str = Field("gpt-4o-mini", env="OPENAI_TEXT_MODEL")
    timeout: int = Field(30, env="OPENAI_TIMEOUT")
    max_retries: int = Field(3, env="OPENAI_MAX_RETRIES")
    
    @field_validator('api_key')
    @classmethod
    def validate_api_key(cls, v):
        if not v or not v.strip():
            raise ValueError("OpenAI API key cannot be empty")
        return v.strip()
    
    @field_validator('timeout')
    @classmethod
    def validate_timeout(cls, v):
        if v <= 0:
            raise ValueError("Timeout must be positive")
        return v
    
    @field_validator('max_retries')
    @classmethod
    def validate_max_retries(cls, v):
        if v < 0:
            raise ValueError("Max retries cannot be negative")
        return v

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


class AppConfig(BaseSettings):
    """Application configuration."""
    
    # Data settings
    default_invoices_path: str = Field("data/invoices.sample.json", env="INVOICES_JSON")
    
    # Logging settings
    log_level: str = Field("INFO", env="LOG_LEVEL")
    log_format: str = Field(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        env="LOG_FORMAT"
    )
    
    # Query engine settings
    enable_data_validation: bool = Field(True, env="ENABLE_DATA_VALIDATION")
    cache_query_results: bool = Field(False, env="CACHE_QUERY_RESULTS")
    
    # UI settings
    use_rich_output: bool = Field(True, env="USE_RICH_OUTPUT")
    show_debug_info: bool = Field(False, env="SHOW_DEBUG_INFO")
    
    @field_validator('log_level')
    @classmethod
    def validate_log_level(cls, v):
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of: {valid_levels}")
        return v.upper()
    
    @field_validator('default_invoices_path')
    @classmethod
    def validate_invoices_path(cls, v):
        if not v or not v.strip():
            raise ValueError("Invoices path cannot be empty")
        return v.strip()

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


class Config:
    """Main configuration class combining all settings."""
    
    def __init__(self, env_file: Optional[str] = None):
        """Initialize configuration from environment variables and .env file."""
        self._env_file = env_file or ".env"
        self._load_config()
    
    def _load_config(self) -> None:
        """Load configuration from environment and .env file."""
        try:
            # Load OpenAI config (will raise error if API key missing)
            try:
                self.openai = OpenAIConfig(_env_file=self._env_file)
                logger.info("OpenAI configuration loaded successfully")
            except Exception as e:
                logger.warning(f"OpenAI configuration incomplete: {e}")
                # Create a partial config for non-image processing use
                self.openai = None
            
            # Load app config
            self.app = AppConfig(_env_file=self._env_file)
            logger.info("Application configuration loaded successfully")
            
            # Set up logging based on config
            self._configure_logging()
            
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            raise
    
    def _configure_logging(self) -> None:
        """Configure logging based on app settings."""
        try:
            level = getattr(logging, self.app.log_level)
            logging.basicConfig(
                level=level,
                format=self.app.log_format,
                force=True  # Override any existing configuration
            )
            logger.info(f"Logging configured at {self.app.log_level} level")
        except Exception as e:
            logger.error(f"Failed to configure logging: {e}")
    
    def get_openai_config(self) -> OpenAIConfig:
        """Get OpenAI configuration, raising error if not available."""
        if self.openai is None:
            raise RuntimeError(
                "OpenAI configuration not available. "
                "Please set OPENAI_API_KEY environment variable."
            )
        return self.openai
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary for debugging."""
        result = {
            'app': self.app.dict() if self.app else None,
            'openai_available': self.openai is not None,
        }
        
        if self.openai:
            openai_dict = self.openai.dict()
            # Mask API key for security
            if 'api_key' in openai_dict:
                openai_dict['api_key'] = f"{openai_dict['api_key'][:8]}..." if len(openai_dict['api_key']) > 8 else "***"
            result['openai'] = openai_dict
        
        return result


# Global configuration instance
config: Optional[Config] = None


def get_config(env_file: Optional[str] = None, force_reload: bool = False) -> Config:
    """
    Get global configuration instance.
    
    Args:
        env_file: Optional .env file path
        force_reload: Whether to reload configuration
        
    Returns:
        Configuration instance
    """
    global config
    
    if config is None or force_reload:
        config = Config(env_file=env_file)
    
    return config


def load_config_from_file(config_file: str) -> Dict[str, Any]:
    """
    Load additional configuration from JSON file.
    
    Args:
        config_file: Path to JSON configuration file
        
    Returns:
        Configuration dictionary
    """
    config_path = Path(config_file)
    
    if not config_path.exists():
        logger.warning(f"Configuration file not found: {config_file}")
        return {}
    
    try:
        import json
        with open(config_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        logger.info(f"Loaded additional configuration from {config_file}")
        return data
        
    except Exception as e:
        logger.error(f"Failed to load configuration file {config_file}: {e}")
        return {}


