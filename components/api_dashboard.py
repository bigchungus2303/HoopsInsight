"""
API Usage Dashboard Component

Displays real-time API usage statistics including:
- API call count
- Cache hit count
- Total requests
- Cache hit rate with visual indicators
"""

import streamlit as st
from error_handler import show_connection_status


def show_api_dashboard(api_client):
    """
    Display API usage statistics and connection status.
    
    Args:
        api_client: Instance of NBAAPIClient
    """
    with st.expander("📊 API Usage & Status", expanded=True):
        is_connected = show_connection_status(api_client)
        if not is_connected:
            st.caption("⚠️ Some features may not work properly without API connection.")
        
        # Display API usage statistics
        st.divider()
        cache_stats = api_client.get_cache_stats()
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("API Calls", cache_stats['api_calls'])
            st.metric("Cache Hits", cache_stats['cache_hits'])
        with col2:
            st.metric("Total Requests", cache_stats['total_requests'])
            st.metric("Cache Hit Rate", f"{cache_stats['cache_hit_rate']:.1f}%")
        
        # Visual indicator for cache performance
        if cache_stats['total_requests'] > 0:
            if cache_stats['cache_hit_rate'] >= 70:
                st.success("✅ Excellent cache performance")
            elif cache_stats['cache_hit_rate'] >= 40:
                st.info("ℹ️ Good cache performance")
            else:
                st.warning("⚠️ Low cache utilization")

