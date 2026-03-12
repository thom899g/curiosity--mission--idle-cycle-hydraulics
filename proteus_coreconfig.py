"""
Configuration Management for Project Proteus
Centralized configuration with environment variable fallbacks
"""
import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
import logging
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

class Config:
    """Singleton configuration manager"""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        # Load environment variables
        env_path = Path(__file__).parent.parent / ".env"
        if env_path.exists():
            load_dotenv(dotenv_path=env_path)
            logger.info(f"Loaded environment from {env_path}")
        else:
            logger.warning(f"No .env file found at {env_path}")
        
        # Core Configuration
        self.node_env = os.getenv("NODE_ENV", "development")
        self.debug = os.getenv("DEBUG", "False").lower() == "true"
        
        # Firebase Configuration
        self.firebase_credentials_path = os.getenv(
            "FIREBASE_CREDENTIALS_PATH", 
            str(Path(__file__).parent.parent / "config" / "firebase-credentials.json")
        )
        self.firebase_project_id = os.getenv("FIREBASE_PROJECT_ID", "proteus-core")
        
        # Web3 Configuration
        self.polygon_rpc_url = os.getenv(
            "POLYGON_RPC_URL", 
            "https://polygon-rpc.com"
        )
        self.treasury_contract_address = os.getenv(
            "TREASURY_CONTRACT_ADDRESS", 
            ""
        )
        
        # External APIs
        self.moralis_api_key = os.getenv("MORALIS_API_KEY", "")
        self.moralis_rate_limit_per_minute = int(os.getenv("MORALIS_RATE_LIMIT", "30"))
        
        # Computation Settings
        self.max_compute_time_seconds = int(os.getenv("MAX_COMPUTE_TIME", "300"))
        self.max_dataset_size_mb = int(os.getenv("MAX_DATASET_SIZE_MB", "100"))
        self.cache_ttl_hours = int(os.getenv("CACHE_TTL_HOURS", "24"))
        
        # Bidding System
        self.min_bid_usd = float(os.getenv("MIN_BID_USD", "0.10"))
        self.priority_fee_multiplier = float(os.getenv("PRIORITY_FEE_MULTIPLIER", "1.5"))
        self.scheduler_interval_seconds = int(os.getenv("SCHEDULER_INTERVAL", "60"))
        
        # Security
        self.commitment_secret_key = os.getenv("COMMITMENT_SECRET_KEY", "")
        if not self.commitment_secret_key and self.node_env == "production":
            raise ValueError("COMMITMENT_SECRET_KEY must be set in production")
        
        # Monitoring
        self.telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        self.telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID", "")
        
        # AWS Configuration (if using S3 for results)
        self.aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID", "")
        self.aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY", "")
        self.s3_bucket_name = os.getenv("S3_BUCKET_NAME", "proteus-results")
        
        # Validate critical configurations
        self._validate_config()
        
        self._initialized = True
        logger.info("Configuration initialized successfully")
    
    def _validate_config(self) -> None:
        """Validate critical configuration values"""
        validation_errors = []
        
        # Check Firebase credentials file exists
        if not Path(self.firebase_credentials_path).exists():
            validation_errors.append(f"Firebase credentials not found at {self.firebase_credentials_path}")
        
        # Check Moralis API key for production
        if self.node_env == "production" and not self.moralis_api_key:
            validation_errors.append("MORALIS_API_KEY required in production")
        
        # Check Polygon RPC connectivity
        if not self.polygon_rpc_url.startswith(("http://", "https://")):
            validation_errors.append("POLYGON_RPC_URL must be a valid URL")
        
        if validation_errors:
            error_msg = "Configuration validation failed:\n" + "\n".join(validation_errors)
            logger.error(error_msg)
            if self.node_env == "production":
                raise ValueError(error_msg)
    
    def to_dict(self) -> Dict[str, Any]:
        """Return configuration as dictionary (excluding sensitive fields)"""
        config_dict = {}
        for key in dir(self):
            if not key.startswith('_') and not callable(getattr(self, key)):
                value = getattr(self, key)
                # Mask sensitive data
                if any(sensitive in key.lower() for sensitive in ['key', 'secret', 'token', 'password']):
                    if value:
                        config_dict[key] = "***MASKED***"
                    else:
                        config_dict[key] = value
                else:
                    config_dict[key] = value
        return config_dict

# Global configuration instance
config = Config()