"""
Error handling utilities for NBA Performance Predictor.
Provides user-friendly error messages and graceful degradation.
"""

import streamlit as st
import functools
from typing import Callable, Any, Optional
from logger import get_logger

logger = get_logger(__name__)


class APIError(Exception):
    """Custom exception for API-related errors"""
    pass


class DataError(Exception):
    """Custom exception for data-related errors"""
    pass


def handle_api_errors(operation_name: str, show_error: bool = True):
    """
    Decorator for handling API errors with user-friendly messages.
    
    Args:
        operation_name: Name of the operation for error messages
        show_error: Whether to show error message in Streamlit UI
    
    Usage:
        @handle_api_errors("player search")
        def search_player(name):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            try:
                return func(*args, **kwargs)
            except APIError as e:
                logger.error(f"API error in {operation_name}: {e}", exc_info=True)
                if show_error:
                    st.error(f"🚫 **API Error**: Unable to {operation_name}. {str(e)}")
                return None
            except Exception as e:
                logger.error(f"Unexpected error in {operation_name}: {e}", exc_info=True)
                if show_error:
                    st.error(f"❌ **Error**: Something went wrong while trying to {operation_name}. Please try again.")
                return None
        return wrapper
    return decorator


def safe_api_call(func: Callable, *args, default_return=None, error_message: Optional[str] = None, **kwargs) -> Any:
    """
    Safely execute an API call with error handling.
    
    Args:
        func: Function to call
        *args: Positional arguments for the function
        default_return: Value to return on error
        error_message: Custom error message to display
        **kwargs: Keyword arguments for the function
    
    Returns:
        Function result or default_return on error
    """
    try:
        result = func(*args, **kwargs)
        
        # Check if result indicates failure
        if result is None and default_return is not None:
            if error_message:
                st.warning(f"⚠️ {error_message}")
        
        return result if result is not None else default_return
        
    except Exception as e:
        logger.error(f"Error in safe_api_call: {e}", exc_info=True)
        if error_message:
            st.error(f"❌ {error_message}")
        else:
            st.error(f"❌ An unexpected error occurred. Please try again.")
        return default_return


def show_data_quality_warning(data, data_type: str = "data", min_size: int = 5):
    """
    Display warning if data quality is low.
    
    Args:
        data: Data to check (list, dict, or DataFrame)
        data_type: Type of data for message
        min_size: Minimum acceptable data size
    
    Returns:
        bool: True if data quality is acceptable
    """
    try:
        if data is None:
            st.warning(f"⚠️ No {data_type} available.")
            return False
        
        # Check data size
        if hasattr(data, '__len__'):
            size = len(data)
            if size == 0:
                st.warning(f"⚠️ No {data_type} found.")
                return False
            elif size < min_size:
                st.info(f"ℹ️ Limited {data_type} available ({size} items). Results may be less reliable.")
                return True
        
        return True
        
    except Exception as e:
        logger.error(f"Error checking data quality: {e}")
        return False


def show_loading(message: str = "Loading..."):
    """
    Context manager for showing loading spinner.
    
    Usage:
        with show_loading("Fetching player data"):
            data = fetch_data()
    """
    return st.spinner(f"⏳ {message}")


def validate_player_data(player_data: dict) -> bool:
    """
    Validate that player data has required fields.
    
    Args:
        player_data: Dictionary containing player information
    
    Returns:
        bool: True if valid, False otherwise
    """
    if not player_data:
        st.error("❌ No player data available.")
        return False
    
    required_fields = ['player', 'season_stats', 'recent_games']
    missing_fields = [field for field in required_fields if field not in player_data]
    
    if missing_fields:
        st.error(f"❌ Incomplete player data. Missing: {', '.join(missing_fields)}")
        return False
    
    return True


def show_connection_status(api_client) -> bool:
    """
    Display API connection status.
    
    Args:
        api_client: Instance of NBAAPIClient
    
    Returns:
        bool: True if connection is healthy
    """
    try:
        # Try a simple API call to check connection
        with st.spinner("Checking connection..."):
            result = api_client._make_request("players", params={"per_page": 1})
        
        if result:
            st.success("✅ API Connected")
            return True
        else:
            st.error("❌ API Connection Failed")
            st.caption("Some features may not work properly.")
            return False
            
    except Exception as e:
        logger.error(f"Connection check failed: {e}")
        st.warning("⚠️ Unable to verify connection")
        return False


def handle_empty_data(data, data_name: str, suggestions: list = None):
    """
    Handle case where data is empty with helpful suggestions.
    
    Args:
        data: Data to check
        data_name: Name of the data for messages
        suggestions: List of suggestion strings to show user
    """
    if not data or (hasattr(data, '__len__') and len(data) == 0):
        st.warning(f"⚠️ No {data_name} available.")
        
        if suggestions:
            st.info("**Suggestions:**")
            for suggestion in suggestions:
                st.write(f"• {suggestion}")
        
        return True
    
    return False


def retry_operation(func: Callable, max_attempts: int = 3, delay: float = 1.0) -> Any:
    """
    Retry an operation with exponential backoff.
    
    Args:
        func: Function to retry
        max_attempts: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
    
    Returns:
        Function result or None on failure
    """
    import time
    
    for attempt in range(max_attempts):
        try:
            return func()
        except Exception as e:
            if attempt == max_attempts - 1:
                logger.error(f"Operation failed after {max_attempts} attempts: {e}")
                st.error(f"❌ Operation failed after {max_attempts} attempts. Please try again later.")
                return None
            
            wait_time = delay * (2 ** attempt)  # Exponential backoff
            logger.warning(f"Attempt {attempt + 1} failed, retrying in {wait_time}s...")
            time.sleep(wait_time)
    
    return None


