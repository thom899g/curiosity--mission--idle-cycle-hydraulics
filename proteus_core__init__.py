"""
PROJECT PROTEUS - Verifiable Financial Calculus Layer
Core Package Initialization
"""
__version__ = "0.1.0"
__author__ = "Evolution Ecosystem - Proteus Team"
__license__ = "Proprietary - Internal Use Only"

import logging
from pathlib import Path

# Configure package-wide logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)

# Package constants
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
CACHE_DIR = PROJECT_ROOT / "cache"
CONFIG_DIR = PROJECT_ROOT / "config"

# Ensure directories exist
for directory in [DATA_DIR, CACHE_DIR, CONFIG_DIR]:
    directory.mkdir(exist_ok=True, parents=True)

logger.info(f"Proteus Core v{__version__} initialized")