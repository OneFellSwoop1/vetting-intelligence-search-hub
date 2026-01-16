"""Application configuration management with Pydantic validation."""

import os
import logging
from typing import Optional, List, Dict, Any
from pydantic import Field, validator, SecretStr
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    Uses Pydantic for validation and type safety.
    Automatically loads from environment.env file.
    """
    
    # Application Metadata
    APP_NAME: str = "Vetting Intelligence Search Hub"
    APP_VERSION: str = "2.0.0"
    ENVIRONMENT: str = Field("development", env="ENVIRONMENT")
    LOG_LEVEL: str = Field("INFO", env="LOG_LEVEL")
    DEBUG: bool = Field(False, env="DEBUG")
    
    # API Configuration
    API_HOST: str = Field("0.0.0.0", env="API_HOST")
    API_PORT: int = Field(8000, env="API_PORT")
    API_PREFIX: str = "/api/v1"
    
    # Security Configuration
    JWT_SECRET_KEY: SecretStr = Field(..., env="JWT_SECRET_KEY")  # Required!
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_HOURS: int = Field(24, env="JWT_EXPIRE_HOURS")
    SECRET_KEY: str = Field("change_this_to_a_random_secret_key", env="SECRET_KEY")
    
    # Database Configuration
    DATABASE_URL: Optional[str] = Field(None, env="DATABASE_URL")
    DATABASE_POOL_SIZE: int = Field(10, env="DATABASE_POOL_SIZE")
    DATABASE_MAX_OVERFLOW: int = Field(20, env="DATABASE_MAX_OVERFLOW")
    
    # Redis Configuration
    REDIS_URL: str = Field("redis://localhost:6379/0", env="REDIS_URL")
    CACHE_TTL_SECONDS: int = Field(3600, env="CACHE_TTL_SECONDS")
    
    # Rate Limiting Configuration
    IP_RATE_LIMIT_PER_MINUTE: int = Field(60, env="IP_RATE_LIMIT_PER_MINUTE")
    GUEST_REQUESTS_PER_HOUR: int = Field(50, env="GUEST_REQUESTS_PER_HOUR")
    GUEST_REQUESTS_PER_DAY: int = Field(200, env="GUEST_REQUESTS_PER_DAY")
    REGISTERED_REQUESTS_PER_HOUR: int = Field(200, env="REGISTERED_REQUESTS_PER_HOUR")
    REGISTERED_REQUESTS_PER_DAY: int = Field(1000, env="REGISTERED_REQUESTS_PER_DAY")
    PREMIUM_REQUESTS_PER_HOUR: int = Field(1000, env="PREMIUM_REQUESTS_PER_HOUR")
    PREMIUM_REQUESTS_PER_DAY: int = Field(10000, env="PREMIUM_REQUESTS_PER_DAY")
    
    # Search Configuration
    MAX_RESULTS_PER_SOURCE: int = Field(50, env="MAX_RESULTS_PER_SOURCE")
    MAX_SEARCH_TIMEOUT: int = Field(30, env="MAX_SEARCH_TIMEOUT")
    ENABLE_SEARCH_HISTORY: bool = Field(True, env="ENABLE_SEARCH_HISTORY")
    DEFAULT_SEARCH_LIMIT: int = Field(50, env="DEFAULT_SEARCH_LIMIT")
    
    # Data Source API Keys
    SOCRATA_APP_TOKEN: Optional[str] = Field(None, env="SOCRATA_APP_TOKEN")
    SOCRATA_API_KEY_ID: Optional[str] = Field(None, env="SOCRATA_API_KEY_ID")
    SOCRATA_API_KEY_SECRET: Optional[str] = Field(None, env="SOCRATA_API_KEY_SECRET")
    LDA_API_KEY: Optional[str] = Field(None, env="LDA_API_KEY")
    FEC_API_KEY: Optional[str] = Field(None, env="FEC_API_KEY")
    
    # API Rate Limits (requests per second)
    SENATE_LDA_RATE_LIMIT: float = Field(0.25, env="SENATE_LDA_RATE_LIMIT")
    CHECKBOOK_RATE_LIMIT: float = Field(0.5, env="CHECKBOOK_RATE_LIMIT")
    NYS_ETHICS_RATE_LIMIT: float = Field(1.0, env="NYS_ETHICS_RATE_LIMIT")
    NYC_LOBBYIST_RATE_LIMIT: float = Field(1.0, env="NYC_LOBBYIST_RATE_LIMIT")
    FEC_RATE_LIMIT: float = Field(0.28, env="FEC_RATE_LIMIT")  # 1000/hour = ~0.28/second
    
    # CORS Configuration
    CORS_ORIGINS: str = Field(
        "http://localhost:3000,http://localhost:8000,http://127.0.0.1:8000",
        env="CORS_ORIGINS"
    )
    
    # HTTP Client Configuration
    HTTP_TIMEOUT_CONNECT: int = Field(10, env="HTTP_TIMEOUT_CONNECT")
    HTTP_TIMEOUT_READ: int = Field(30, env="HTTP_TIMEOUT_READ")
    HTTP_POOL_CONNECTIONS: int = Field(10, env="HTTP_POOL_CONNECTIONS")
    HTTP_POOL_MAXSIZE: int = Field(20, env="HTTP_POOL_MAXSIZE")
    
    # Monitoring and Logging
    ENABLE_PERFORMANCE_MONITORING: bool = Field(True, env="ENABLE_PERFORMANCE_MONITORING")
    LOG_SQL_QUERIES: bool = Field(False, env="LOG_SQL_QUERIES")
    METRICS_RETENTION_DAYS: int = Field(30, env="METRICS_RETENTION_DAYS")
    
    @validator("CORS_ORIGINS", pre=True)
    def parse_cors_origins(cls, v):
        """Parse CORS origins from comma-separated string."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    @validator("JWT_SECRET_KEY")
    def validate_jwt_secret(cls, v):
        """Validate JWT secret key length and strength."""
        secret = v.get_secret_value() if hasattr(v, 'get_secret_value') else str(v)
        
        if len(secret) < 32:
            raise ValueError("JWT_SECRET_KEY must be at least 32 characters long")
        
        # Check for common weak patterns
        weak_patterns = [
            "your_secure_64_character_jwt_secret_key_here",
            "change_this_to_a_random_secret_key",
            "development_key_only",
            "test_key"
        ]
        
        if any(pattern in secret.lower() for pattern in weak_patterns):
            raise ValueError(
                "JWT_SECRET_KEY appears to be a placeholder. "
                "Generate a secure key with: python -c 'import secrets; print(secrets.token_urlsafe(64))'"
            )
        
        return v
    
    @validator("LDA_API_KEY")
    def validate_lda_api_key(cls, v):
        """Validate LDA API key format if provided."""
        if v and not v.startswith('065'):
            raise ValueError("LDA_API_KEY should start with '065' for correct format")
        return v
    
    @validator("DATABASE_URL")
    def validate_database_url(cls, v):
        """Validate database URL format."""
        if v and not any(v.startswith(prefix) for prefix in ['postgresql://', 'sqlite://', 'mysql://']):
            raise ValueError("DATABASE_URL must start with postgresql://, sqlite://, or mysql://")
        return v
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.ENVIRONMENT.lower() == "production"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.ENVIRONMENT.lower() == "development"
    
    @property
    def is_testing(self) -> bool:
        """Check if running in testing environment."""
        return self.ENVIRONMENT.lower() == "testing"
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Get CORS origins as a list."""
        if isinstance(self.CORS_ORIGINS, list):
            return self.CORS_ORIGINS
        if isinstance(self.CORS_ORIGINS, str):
            return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
        return ["http://localhost:3000"]
    
    @property
    def database_url_sync(self) -> str:
        """Get synchronous database URL."""
        if not self.DATABASE_URL:
            return "sqlite:///./vetting_intelligence.db"
        return self.DATABASE_URL
    
    @property
    def database_url_async(self) -> str:
        """Get asynchronous database URL."""
        if not self.DATABASE_URL:
            return "sqlite+aiosqlite:///./vetting_intelligence.db"
        
        # Convert PostgreSQL URL to async version
        if self.DATABASE_URL.startswith("postgresql://"):
            return self.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
        
        return self.DATABASE_URL
    
    def get_rate_limit_config(self) -> Dict[str, Dict[str, int]]:
        """Get rate limit configuration for all user tiers."""
        return {
            "guest": {
                "requests_per_hour": self.GUEST_REQUESTS_PER_HOUR,
                "requests_per_day": self.GUEST_REQUESTS_PER_DAY,
                "concurrent_searches": 1,
                "export_limit": 100
            },
            "registered": {
                "requests_per_hour": self.REGISTERED_REQUESTS_PER_HOUR,
                "requests_per_day": self.REGISTERED_REQUESTS_PER_DAY,
                "concurrent_searches": 3,
                "export_limit": 1000
            },
            "premium": {
                "requests_per_hour": self.PREMIUM_REQUESTS_PER_HOUR,
                "requests_per_day": self.PREMIUM_REQUESTS_PER_DAY,
                "concurrent_searches": 10,
                "export_limit": 10000
            },
            "enterprise": {
                "requests_per_hour": -1,  # Unlimited
                "requests_per_day": -1,
                "concurrent_searches": 20,
                "export_limit": -1
            }
        }
    
    def validate_configuration(self) -> List[str]:
        """
        Validate configuration and return list of warnings/errors.
        
        Returns:
            List of validation messages
        """
        issues = []
        
        # Check required fields for production
        if self.is_production:
            if self.JWT_SECRET_KEY.get_secret_value() == "your_secure_64_character_jwt_secret_key_here":
                issues.append("CRITICAL: JWT_SECRET_KEY is still using placeholder value in production")
            
            if not self.DATABASE_URL:
                issues.append("WARNING: No DATABASE_URL set, using SQLite fallback")
            
            if self.DEBUG:
                issues.append("WARNING: DEBUG mode enabled in production")
        
        # Check API keys
        if not self.SOCRATA_APP_TOKEN:
            issues.append("INFO: SOCRATA_APP_TOKEN not set, some features may be limited")
        
        if not self.LDA_API_KEY:
            issues.append("INFO: LDA_API_KEY not set, federal lobbying data may be limited")
        
        return issues
    
    class Config:
        """Pydantic configuration."""
        env_file = "environment.env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        # Allow extra fields for backward compatibility
        extra = "ignore"
        # ✅ Don't fail if env file doesn't exist (important for CI)
        # Pydantic will still read from system environment variables
        validate_assignment = True


# Global settings instance
try:
    settings = Settings()
    
    # Log configuration validation
    validation_issues = settings.validate_configuration()
    if validation_issues:
        logger = logging.getLogger(__name__)
        for issue in validation_issues:
            if issue.startswith("CRITICAL"):
                logger.error(issue)
            elif issue.startswith("WARNING"):
                logger.warning(issue)
            else:
                logger.info(issue)
                
except Exception as e:
    # Fallback configuration if environment loading fails
    print(f"❌ Failed to load configuration: {e}")
    print("Using fallback configuration...")
    
    class FallbackSettings:
        APP_NAME = "Vetting Intelligence Search Hub"
        APP_VERSION = "2.0.0"
        ENVIRONMENT = "development"
        LOG_LEVEL = "INFO"
        API_HOST = "0.0.0.0"
        API_PORT = 8000
        JWT_EXPIRE_HOURS = 24
        IP_RATE_LIMIT_PER_MINUTE = 60
        MAX_RESULTS_PER_SOURCE = 50
        is_production = False
        is_development = True
        cors_origins_list = ["http://localhost:3000", "http://localhost:8000"]
        database_url_sync = "sqlite:///./vetting_intelligence.db"
        database_url_async = "sqlite+aiosqlite:///./vetting_intelligence.db"
    
    settings = FallbackSettings()
