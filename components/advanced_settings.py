"""
Advanced Settings Component

Provides interactive controls for:
- Custom thresholds (Points, Rebounds, Assists, 3-Pointers)
- Recency weight (alpha parameter)
- Career phase decay parameters
"""

import streamlit as st
from components.lambda_advisor import get_lambda_rule_of_thumb


def show_advanced_settings():
    """
    Display advanced settings panel with threshold sliders and career phase parameters.
    
    Returns:
        None (stores values in st.session_state)
    """
    with st.expander("⚙️ Advanced Settings"):
        st.subheader("Custom Thresholds")
        st.caption("Set your target threshold for each stat category")
        
        # Single threshold per category - cleaner and simpler
        col1, col2 = st.columns(2)
        
        with col1:
            pts_threshold = st.number_input(
                "🏀 Points Threshold", 
                min_value=5, 
                max_value=50, 
                value=20, 
                step=1,
                help="Set to 25 → Predicts probability of scoring OVER 25 points"
            )
            
            reb_threshold = st.number_input(
                "💪 Rebounds Threshold", 
                min_value=1, 
                max_value=20, 
                value=8, 
                step=1,
                help="Set to 10 → Predicts probability of grabbing OVER 10 rebounds"
            )
        
        with col2:
            ast_threshold = st.number_input(
                "🎯 Assists Threshold", 
                min_value=1, 
                max_value=20, 
                value=6, 
                step=1,
                help="Set to 8 → Predicts probability of dishing OVER 8 assists"
            )
            
            fg3m_threshold = st.number_input(
                "🎯 3-Pointers Threshold", 
                min_value=0, 
                max_value=15, 
                value=3, 
                step=1,
                help="Set to 4 → Predicts probability of making OVER 4 three-pointers"
            )
        
        st.divider()
        
        # Alpha (recency weight)
        alpha_value = st.slider(
            "Recency Weight (α)", 
            min_value=0.5, 
            max_value=1.0, 
            value=0.85, 
            step=0.05,
            help="🔥 0.50-0.75: Hot streak  |  ⚖️ 0.85 (Default): Balanced  |  📊 1.00: Pure average"
        )
        
        st.divider()
        st.subheader("Career Phase Decay")
        
        use_career_phase = st.checkbox(
            "🤖 Enable AI-Powered Career Phase Analysis",
            value=False,
            help="🌱 Young: Trust growth  |  ⭐ Prime: Most reliable  |  🌅 Aging: Trust recent form"
        )
        
        if not use_career_phase:
            st.caption("💡 Enable this for smarter predictions that adapt to player age and form")
        
        # Get current values from session state or use defaults
        current_lambda_early = st.session_state.get('lambda_early_value', 0.02)
        current_lambda_peak = st.session_state.get('lambda_peak_value', 0.05)
        current_lambda_late = st.session_state.get('lambda_late_value', 0.08)
        
        if use_career_phase:
            st.caption("⚙️ Advanced: Manually adjust decay rates (or use Auto button when viewing player)")
            
            with st.expander("🔧 Manual Lambda Controls"):
                lambda_early = st.slider(
                    "λ Early Career (Young/Improving)",
                    min_value=0.01,
                    max_value=0.10,
                    value=current_lambda_early,
                    step=0.01,
                    help="Lower = trust growth  |  Higher = recent form  |  Typical: 0.02",
                    key="lambda_early_slider"
                )
                
                lambda_peak = st.slider(
                    "λ Peak Career (Established)",
                    min_value=0.01,
                    max_value=0.15,
                    value=current_lambda_peak,
                    step=0.01,
                    help="Balanced weighting for prime years  |  Typical: 0.05",
                    key="lambda_peak_slider"
                )
                
                lambda_late = st.slider(
                    "λ Late Career (Veteran/Aging)",
                    min_value=0.01,
                    max_value=0.25,
                    value=current_lambda_late,
                    step=0.01,
                    help="Higher = trust recent form over career average  |  Typical: 0.08",
                    key="lambda_late_slider"
                )
                
                st.caption("💡 Higher λ = more weight on recent games, Lower λ = trust historical average")
        else:
            # Set default values when disabled
            lambda_early = current_lambda_early
            lambda_peak = current_lambda_peak
            lambda_late = current_lambda_late
        
        # Store slider values separately so they persist
        st.session_state.lambda_early_value = lambda_early
        st.session_state.lambda_peak_value = lambda_peak
        st.session_state.lambda_late_value = lambda_late
        
        # Store single threshold per category as a list for compatibility
        st.session_state.custom_thresholds = {
            'pts': [pts_threshold],
            'reb': [reb_threshold],
            'ast': [ast_threshold],
            'fg3m': [fg3m_threshold]
        }
        st.session_state.alpha = alpha_value
        st.session_state.use_career_phase = use_career_phase
        st.session_state.lambda_params = {
            'early': lambda_early,
            'peak': lambda_peak,
            'late': lambda_late
        }

