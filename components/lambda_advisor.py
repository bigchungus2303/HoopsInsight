"""
Lambda Parameter Advisor

Automatically recommends optimal λ (decay rate) parameters based on:
- Player's career phase
- Age
- Recent performance variance
- Minutes played trends
- Injury/load management patterns
"""

import pandas as pd
import numpy as np
from datetime import datetime


def calculate_optimal_lambda(player, career_stats, recent_games, season_stats, career_phase):
    """
    Calculate optimal λ parameters based on player characteristics.
    
    Args:
        player: Player info dict
        career_stats: List of career season stats
        recent_games: List of recent game stats
        season_stats: Current season stats
        career_phase: Detected career phase (early/rising/peak/late/unknown)
    
    Returns:
        dict: {
            'early': float,
            'peak': float, 
            'late': float,
            'recommended': float (for current phase),
            'reasoning': str,
            'confidence': str
        }
    """
    # Base lambda values
    lambda_early = 0.02
    lambda_peak = 0.05
    lambda_late = 0.08
    
    reasoning_parts = []
    
    # Factor 1: Career Phase (primary)
    if career_phase == 'early':
        recommended = 0.02
        reasoning_parts.append("Early career - low decay to capture growth trajectory")
    elif career_phase == 'rising':
        recommended = 0.03
        reasoning_parts.append("Rising player - moderate decay to weight recent improvement")
    elif career_phase == 'peak':
        recommended = 0.05
        reasoning_parts.append("Peak performance - balanced decay")
    elif career_phase == 'late':
        recommended = 0.08
        reasoning_parts.append("Late career - higher decay to focus on current form")
    else:
        recommended = 0.05
        reasoning_parts.append("Unknown phase - using balanced default")
    
    # Factor 2: Age adjustment
    if career_stats and len(career_stats) > 0:
        years_in_league = len(career_stats)
        
        if years_in_league >= 15:
            # Veteran (15+ years) - increase decay significantly
            age_adjustment = 0.04
            reasoning_parts.append(f"Veteran ({years_in_league} seasons) - increased decay")
        elif years_in_league >= 10:
            # Experienced (10-14 years) - moderate increase
            age_adjustment = 0.02
            reasoning_parts.append(f"Experienced ({years_in_league} seasons) - slight decay increase")
        elif years_in_league <= 3:
            # Rookie/Sophomore - decrease decay
            age_adjustment = -0.01
            reasoning_parts.append(f"Young player ({years_in_league} seasons) - reduced decay")
        else:
            age_adjustment = 0
    else:
        age_adjustment = 0
    
    # Factor 3: Recent performance variance
    if recent_games and len(recent_games) >= 10:
        try:
            games_df = pd.DataFrame(recent_games)
            if 'pts' in games_df.columns:
                pts_values = pd.to_numeric(games_df['pts'], errors='coerce').dropna()
                
                if len(pts_values) >= 10:
                    # Calculate coefficient of variation
                    cv = pts_values.std() / pts_values.mean() if pts_values.mean() > 0 else 0
                    
                    if cv > 0.4:
                        # High variance - increase decay to focus on recent
                        variance_adjustment = 0.03
                        reasoning_parts.append(f"High variance (CV={cv:.2f}) - increased decay")
                    elif cv > 0.3:
                        variance_adjustment = 0.01
                        reasoning_parts.append(f"Moderate variance (CV={cv:.2f}) - slight decay increase")
                    else:
                        variance_adjustment = 0
                        reasoning_parts.append(f"Low variance (CV={cv:.2f}) - consistent performance")
                else:
                    variance_adjustment = 0
            else:
                variance_adjustment = 0
        except:
            variance_adjustment = 0
    else:
        variance_adjustment = 0
    
    # Factor 4: Minutes played trend (load management detection)
    if recent_games and len(recent_games) >= 10:
        try:
            games_df = pd.DataFrame(recent_games)
            if 'min' in games_df.columns:
                # Parse minutes
                def parse_min(m):
                    if pd.isna(m):
                        return 0
                    if isinstance(m, (int, float)):
                        return float(m)
                    if isinstance(m, str) and ':' in m:
                        parts = m.split(':')
                        return int(parts[0]) + int(parts[1]) / 60.0
                    return 0
                
                minutes = games_df['min'].apply(parse_min)
                
                if len(minutes) >= 10:
                    # Check for DNPs or significant minute reductions
                    dnp_count = (minutes < 1).sum()
                    recent_5 = minutes.tail(5).mean()
                    season_avg = minutes.mean()
                    
                    if dnp_count >= 3:
                        # Load management detected
                        load_adjustment = 0.04
                        reasoning_parts.append(f"Load management detected ({dnp_count} DNPs) - high decay")
                    elif season_avg > 0 and recent_5 < season_avg * 0.7:
                        # Minutes declining significantly
                        load_adjustment = 0.02
                        reasoning_parts.append(f"Minutes declining (recent: {recent_5:.1f}, avg: {season_avg:.1f}) - increased decay")
                    else:
                        load_adjustment = 0
                else:
                    load_adjustment = 0
            else:
                load_adjustment = 0
        except:
            load_adjustment = 0
    else:
        load_adjustment = 0
    
    # Calculate final recommended lambda (with bounds)
    recommended = recommended + age_adjustment + variance_adjustment + load_adjustment
    recommended = max(0.01, min(0.25, recommended))  # Bound between 0.01 and 0.25
    
    # Update phase-specific lambdas for late career
    if career_phase == 'late':
        lambda_late = recommended
    
    # Determine confidence
    num_factors = len(reasoning_parts)
    if num_factors >= 4:
        confidence = "High"
    elif num_factors >= 2:
        confidence = "Medium"
    else:
        confidence = "Low"
    
    reasoning = " • ".join(reasoning_parts)
    
    return {
        'early': lambda_early,
        'peak': lambda_peak,
        'late': lambda_late,
        'recommended': round(recommended, 3),
        'reasoning': reasoning,
        'confidence': confidence,
        'adjustments': {
            'age': age_adjustment,
            'variance': variance_adjustment,
            'load_management': load_adjustment
        }
    }


def show_lambda_advisor(player, career_stats, recent_games, season_stats, career_phase):
    """
    DEPRECATED: UI display is now handled in app.py.
    Use calculate_optimal_lambda() instead.
    
    Calculate and return lambda recommendations.
    UI display is handled in app.py for cleaner layout.
    
    Returns:
        dict: Recommended lambda parameters
    """
    return calculate_optimal_lambda(
        player, career_stats, recent_games, season_stats, career_phase
    )


def get_lambda_rule_of_thumb(career_phase, years_in_league=None):
    """
    Get rule of thumb text for manual adjustment.
    
    Args:
        career_phase: Career phase (early/peak/late)
        years_in_league: Optional years in league
    
    Returns:
        str: Rule of thumb guidance
    """
    rules = {
        'early': """
        **Rule of Thumb for Early Career (λ = 0.01-0.03):**
        • Use 0.01-0.02: Rookie/sophomore showing growth
        • Use 0.02-0.03: Established young player
        • Lower = trust potential, Higher = trust recent form
        """,
        'peak': """
        **Rule of Thumb for Peak Career (λ = 0.04-0.07):**
        • Use 0.04-0.05: Consistent All-Star (e.g., Kawhi)
        • Use 0.05-0.06: Standard peak player
        • Use 0.06-0.07: Peak but showing variance
        • Lower = trust consistency, Higher = weight recent changes
        """,
        'late': """
        **Rule of Thumb for Late Career (λ = 0.08-0.20):**
        • Use 0.08-0.10: Aging but consistent (e.g., CP3)
        • Use 0.10-0.12: Normal late career (e.g., LeBron)
        • Use 0.12-0.15: Declining or injury concerns
        • Use 0.15-0.20: Load management or high variance
        • Higher = focus almost entirely on last 5-10 games
        """
    }
    
    base = rules.get(career_phase, rules['peak'])
    
    if years_in_league:
        if years_in_league >= 15:
            base += f"\n\n**Veteran ({years_in_league} seasons):** Recommend λ ≥ 0.12"
        elif years_in_league >= 10:
            base += f"\n\n**Experienced ({years_in_league} seasons):** Recommend λ = 0.08-0.12"
    
    return base

