"""
Logging configuration for NBA Player Performance Predictor
Provides consistent logging across all modules
"""

import logging
import sys
from config import LOG_LEVEL, LOG_FORMAT, LOG_DATE_FORMAT


def setup_logger(name: str, level: str = LOG_LEVEL) -> logging.Logger:
    """
    Set up and configure a logger with consistent formatting
    
    Args:
        name: Name of the logger (usually __name__)
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Only add handler if logger doesn't have any (prevents duplicate logs)
    if not logger.handlers:
        # Convert string level to logging constant
        numeric_level = getattr(logging, level.upper(), logging.INFO)
        logger.setLevel(numeric_level)
        
        # Create console handler
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(numeric_level)
        
        # Create formatter
        formatter = logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)
        handler.setFormatter(formatter)
        
        # Add handler to logger
        logger.addHandler(handler)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get or create a logger for the given name
    
    Args:
        name: Name of the logger (usually __name__)
    
    Returns:
        Logger instance
    """
    return setup_logger(name)

