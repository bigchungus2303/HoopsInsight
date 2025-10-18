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
        st.caption("Use sliders to set prediction thresholds for each stat category")
        
        # Points thresholds - Interactive sliders
        st.markdown("**🏀 Points Thresholds**")
        pts_col1, pts_col2, pts_col3, pts_col4 = st.columns(4)
        with pts_col1:
            pts_t1 = st.slider("PTS 1", 5, 50, 10, 1, key="pts_t1", help="First points threshold")
        with pts_col2:
            pts_t2 = st.slider("PTS 2", 5, 50, 15, 1, key="pts_t2", help="Second points threshold")
        with pts_col3:
            pts_t3 = st.slider("PTS 3", 5, 50, 20, 1, key="pts_t3", help="Third points threshold")
        with pts_col4:
            pts_t4 = st.slider("PTS 4", 5, 50, 25, 1, key="pts_t4", help="Fourth points threshold (optional)")
        
        # Rebounds thresholds - Interactive sliders
        st.markdown("**💪 Rebounds Thresholds**")
        reb_col1, reb_col2, reb_col3, reb_col4 = st.columns(4)
        with reb_col1:
            reb_t1 = st.slider("REB 1", 1, 20, 4, 1, key="reb_t1", help="First rebounds threshold")
        with reb_col2:
            reb_t2 = st.slider("REB 2", 1, 20, 6, 1, key="reb_t2", help="Second rebounds threshold")
        with reb_col3:
            reb_t3 = st.slider("REB 3", 1, 20, 8, 1, key="reb_t3", help="Third rebounds threshold")
        with reb_col4:
            reb_t4 = st.slider("REB 4", 1, 20, 10, 1, key="reb_t4", help="Fourth rebounds threshold")
        
        # Assists thresholds - Interactive sliders
        st.markdown("**🎯 Assists Thresholds**")
        ast_col1, ast_col2, ast_col3, ast_col4 = st.columns(4)
        with ast_col1:
            ast_t1 = st.slider("AST 1", 1, 20, 4, 1, key="ast_t1", help="First assists threshold")
        with ast_col2:
            ast_t2 = st.slider("AST 2", 1, 20, 6, 1, key="ast_t2", help="Second assists threshold")
        with ast_col3:
            ast_t3 = st.slider("AST 3", 1, 20, 8, 1, key="ast_t3", help="Third assists threshold")
        with ast_col4:
            ast_t4 = st.slider("AST 4", 1, 20, 10, 1, key="ast_t4", help="Fourth assists threshold")
        
        # 3-pointers thresholds - Interactive sliders
        st.markdown("**🎯 3-Pointers Thresholds**")
        fg3m_col1, fg3m_col2, fg3m_col3, fg3m_col4 = st.columns(4)
        with fg3m_col1:
            fg3m_t1 = st.slider("3PM 1", 0, 15, 2, 1, key="fg3m_t1", help="First 3-pointers threshold")
        with fg3m_col2:
            fg3m_t2 = st.slider("3PM 2", 0, 15, 3, 1, key="fg3m_t2", help="Second 3-pointers threshold")
        with fg3m_col3:
            fg3m_t3 = st.slider("3PM 3", 0, 15, 5, 1, key="fg3m_t3", help="Third 3-pointers threshold")
        with fg3m_col4:
            fg3m_t4 = st.slider("3PM 4", 0, 15, 7, 1, key="fg3m_t4", help="Fourth 3-pointers threshold (optional)")
        
        st.divider()
        
        # Alpha (recency weight)
        alpha_value = st.slider(
            "Recency Weight (α)", 
            min_value=0.5, 
            max_value=1.0, 
            value=0.85, 
            step=0.05,
            help="Higher values give more weight to recent games"
        )
        
        st.divider()
        st.subheader("Career Phase Decay")
        
        use_career_phase = st.checkbox(
            "🤖 Enable AI-Powered Career Phase Analysis",
            value=False,
            help="Auto-adjusts predictions based on player's career stage (early/peak/late)"
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
                    help="Lower = trust potential, Higher = weight recent form",
                    key="lambda_early_slider"
                )
                
                lambda_peak = st.slider(
                    "λ Peak Career (Established)",
                    min_value=0.01,
                    max_value=0.15,
                    value=current_lambda_peak,
                    step=0.01,
                    help="Balanced weighting for consistent performers",
                    key="lambda_peak_slider"
                )
                
                lambda_late = st.slider(
                    "λ Late Career (Veteran/Aging)",
                    min_value=0.01,
                    max_value=0.25,
                    value=current_lambda_late,
                    step=0.01,
                    help="Higher = focus on recent form vs career average",
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
        
        # Collect threshold values from sliders and sort them
        # Remove duplicates and sort for consistent ordering
        st.session_state.custom_thresholds = {
            'pts': sorted(list(set([pts_t1, pts_t2, pts_t3, pts_t4]))),
            'reb': sorted(list(set([reb_t1, reb_t2, reb_t3, reb_t4]))),
            'ast': sorted(list(set([ast_t1, ast_t2, ast_t3, ast_t4]))),
            'fg3m': sorted(list(set([fg3m_t1, fg3m_t2, fg3m_t3, fg3m_t4])))
        }
        st.session_state.alpha = alpha_value
        st.session_state.use_career_phase = use_career_phase
        st.session_state.lambda_params = {
            'early': lambda_early,
            'peak': lambda_peak,
            'late': lambda_late
        }

