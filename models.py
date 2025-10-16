import numpy as np
import pandas as pd
from typing import Dict, List, Tuple
from scipy import stats
from scipy.stats import beta
from statistics import StatisticsEngine

class InverseFrequencyModel:
    """Implementation of inverse-frequency probability model for regression analysis"""
    
    def __init__(self):
        self.stats_engine = StatisticsEngine()
    
    def calculate_inverse_frequency_probabilities(self, games_df: pd.DataFrame, 
                                                thresholds: Dict[str, List[float]], 
                                                alpha: float = 0.85) -> Dict:
        """
        Calculate inverse-frequency probabilities for given thresholds
        
        P_inv(x) = 1 - f(x), where f(x) = (1/N) * Σ I[stat_i >= threshold]
        
        Args:
            games_df: DataFrame with game statistics
            thresholds: Dictionary of stat -> threshold values
            alpha: Recency weighting factor (0 < alpha <= 1)
        
        Returns:
            Dictionary with frequency and inverse probability results
        """
        results = {}
        
        for stat, threshold_list in thresholds.items():
            if stat not in games_df.columns:
                continue
                
            stat_values = games_df[stat].dropna().values
            if len(stat_values) == 0:
                continue
            
            results[stat] = {}
            
            # Calculate recency weights
            n_games = len(stat_values)
            weights = self._calculate_recency_weights(n_games, alpha)
            
            for threshold in threshold_list:
                # Calculate frequency (proportion of games >= threshold)
                exceeds_threshold = (stat_values >= threshold).astype(float)
                
                # Unweighted frequency
                frequency = np.mean(exceeds_threshold)
                
                # Weighted frequency using recency weights
                weighted_frequency = np.sum(weights * exceeds_threshold)
                
                # Inverse probabilities (cool-off probability)
                inverse_probability = 1 - frequency
                weighted_inverse_probability = 1 - weighted_frequency
                
                # Calculate confidence intervals using binomial proportion
                ci_lower, ci_upper = self._calculate_confidence_interval(
                    int(np.sum(exceeds_threshold)), n_games, confidence=0.95
                )
                
                # Statistical significance test (binomial test)
                p_value = self._binomial_test(int(np.sum(exceeds_threshold)), n_games)
                
                # Apply Bayesian smoothing for small samples (< 10 games)
                bayesian_result = None
                if n_games < 10:
                    bayesian_result = self.apply_bayesian_smoothing(
                        int(np.sum(exceeds_threshold)), n_games,
                        prior_alpha=2.0, prior_beta=2.0  # Mildly informative prior
                    )
                
                results[stat][threshold] = {
                    'frequency': frequency,
                    'inverse_probability': inverse_probability,
                    'weighted_frequency': weighted_frequency,
                    'weighted_inverse_probability': weighted_inverse_probability,
                    'n_games': n_games,
                    'n_exceeds': int(np.sum(exceeds_threshold)),
                    'ci_lower': ci_lower,
                    'ci_upper': ci_upper,
                    'p_value': p_value,
                    'significant': p_value < 0.05,
                    'bayesian_smoothed': bayesian_result
                }
        
        return results
    
    def calculate_dynamic_threshold_probabilities(self, games_df: pd.DataFrame,
                                                dynamic_thresholds: Dict,
                                                alpha: float = 0.85) -> Dict:
        """Calculate probabilities for dynamic thresholds (μ, μ+σ, μ+2σ, μ+3σ)"""
        results = {}
        
        for stat, threshold_data in dynamic_thresholds.items():
            if stat not in games_df.columns:
                continue
            
            stat_values = games_df[stat].dropna().values
            if len(stat_values) == 0:
                continue
            
            results[stat] = {}
            n_games = len(stat_values)
            weights = self._calculate_recency_weights(n_games, alpha)
            
            # Define threshold levels
            threshold_levels = ['mean', 'plus_1_std', 'plus_2_std', 'plus_3_std']
            
            for level in threshold_levels:
                if level not in threshold_data:
                    continue
                
                threshold = threshold_data[level]
                exceeds_threshold = (stat_values >= threshold).astype(float)
                
                frequency = np.mean(exceeds_threshold)
                weighted_frequency = np.sum(weights * exceeds_threshold)
                
                results[stat][level] = {
                    'threshold_value': threshold,
                    'frequency': frequency,
                    'inverse_probability': 1 - frequency,
                    'weighted_frequency': weighted_frequency,
                    'weighted_inverse_probability': 1 - weighted_frequency
                }
        
        return results
    
    def apply_career_phase_weighting(self, games_df: pd.DataFrame, career_phase: str,
                                   base_probabilities: Dict, lambda_params: Dict = None) -> Dict:
        """
        Apply career phase weighting to base probability calculations
        
        w_i = e^(-λ(T-t_i)) where λ varies by career phase
        """
        adjusted_results = {}
        
        n_games = len(games_df)
        career_weights = self.stats_engine.calculate_career_phase_weights(career_phase, n_games, lambda_params)
        
        for stat, stat_results in base_probabilities.items():
            if stat not in games_df.columns:
                continue
            
            stat_values = games_df[stat].dropna().values
            adjusted_results[stat] = {}
            
            for threshold, data in stat_results.items():
                exceeds_threshold = (stat_values >= threshold).astype(float)
                
                # Apply career phase weights
                career_weighted_freq = np.sum(career_weights * exceeds_threshold)
                career_weighted_inverse = 1 - career_weighted_freq
                
                adjusted_results[stat][threshold] = {
                    **data,  # Include original data
                    'career_weighted_frequency': career_weighted_freq,
                    'career_weighted_inverse_probability': career_weighted_inverse,
                    'career_phase': career_phase
                }
        
        return adjusted_results
    
    def analyze_fatigue_curve(self, games_df: pd.DataFrame, window_size: int = 10) -> Dict:
        """
        Analyze fatigue/load curve effects on performance sustainability
        
        Detects if rolling average exceeds long-term mean + 1σ, indicating regression risk
        """
        if len(games_df) < window_size:
            return {'regression_risk': 0.0, 'sustainability_factor': 1.0}
        
        # Sort by date
        df_sorted = games_df.sort_values('date') if 'date' in games_df.columns else games_df
        
        # Focus on points for fatigue analysis
        stat_values = df_sorted['pts'].dropna().values
        
        if len(stat_values) < window_size:
            return {'regression_risk': 0.0, 'sustainability_factor': 1.0}
        
        # Calculate rolling average for recent window
        recent_rolling_mean = np.mean(stat_values[-window_size:])
        
        # Calculate long-term statistics
        long_term_mean = np.mean(stat_values)
        long_term_std = np.std(stat_values)
        
        # Calculate regression risk
        if long_term_std > 0:
            z_score = (recent_rolling_mean - long_term_mean) / long_term_std
            
            # Sigmoid function to convert z-score to regression probability
            regression_risk = 1 / (1 + np.exp(-1.5 * (z_score - 1)))
        else:
            regression_risk = 0.0
        
        # Sustainability factor (inverse of regression risk)
        sustainability_factor = 1 - regression_risk
        
        return {
            'regression_risk': regression_risk,
            'sustainability_factor': sustainability_factor,
            'recent_rolling_mean': recent_rolling_mean,
            'long_term_mean': long_term_mean,
            'z_score': z_score if long_term_std > 0 else 0.0,
            'performance_above_mean': recent_rolling_mean > long_term_mean
        }
    
    def analyze_minutes_trend(self, games_df: pd.DataFrame, window_size: int = 10) -> Dict:
        """
        Analyze minutes played trend to detect injury/load management effects
        """
        if 'min' not in games_df.columns or len(games_df) < window_size:
            return {
                'declining_trend': False,
                'trend_slope': 0.0,
                'sustainability_factor': 1.0
            }
        
        # Sort by date
        df_sorted = games_df.sort_values('date') if 'date' in games_df.columns else games_df
        minutes_values = df_sorted['min'].dropna().values
        
        if len(minutes_values) < window_size:
            return {
                'declining_trend': False,
                'trend_slope': 0.0,
                'sustainability_factor': 1.0
            }
        
        # Calculate trend using linear regression on recent games
        recent_minutes = minutes_values[-window_size:]
        x = np.arange(len(recent_minutes))
        
        try:
            slope, intercept, r_value, p_value, std_err = stats.linregress(x, recent_minutes)
            
            # Determine if trend is significantly declining
            declining_trend = (slope < -0.5) and (p_value < 0.1)
            
            # Calculate sustainability factor based on minutes trend
            if declining_trend:
                # More negative slope = lower sustainability
                sustainability_factor = max(0.3, 1 + slope / 10)
            else:
                sustainability_factor = 1.0
            
            return {
                'declining_trend': declining_trend,
                'trend_slope': slope,
                'sustainability_factor': sustainability_factor,
                'correlation': r_value,
                'p_value': p_value,
                'recent_minutes_avg': np.mean(recent_minutes)
            }
            
        except Exception:
            return {
                'declining_trend': False,
                'trend_slope': 0.0,
                'sustainability_factor': 1.0
            }
    
    def calculate_non_stationarity_adjustment(self, games_df: pd.DataFrame, 
                                            lookback_window: int = 20) -> Dict:
        """
        Handle non-stationarity by re-fitting baselines and using recency weighting
        """
        adjustments = {}
        
        stats_to_analyze = ['pts', 'reb', 'ast']
        
        for stat in stats_to_analyze:
            if stat not in games_df.columns:
                continue
            
            stat_values = games_df[stat].dropna().values
            
            if len(stat_values) < lookback_window:
                continue
            
            # Recent window statistics
            recent_values = stat_values[-lookback_window:]
            recent_mean = np.mean(recent_values)
            recent_std = np.std(recent_values)
            
            # Full period statistics
            full_mean = np.mean(stat_values)
            full_std = np.std(stat_values)
            
            # Detect regime change
            if full_std > 0:
                regime_change_z = abs(recent_mean - full_mean) / full_std
                regime_change_detected = regime_change_z > 1.5
            else:
                regime_change_detected = False
            
            adjustments[stat] = {
                'recent_mean': recent_mean,
                'recent_std': recent_std,
                'full_mean': full_mean,
                'full_std': full_std,
                'regime_change_detected': regime_change_detected,
                'regime_change_magnitude': regime_change_z if full_std > 0 else 0.0,
                'adjustment_factor': 0.7 if regime_change_detected else 1.0
            }
        
        return adjustments
    
    def _calculate_recency_weights(self, n_games: int, alpha: float) -> np.ndarray:
        """Calculate recency weights using exponential decay: α^(N-i)"""
        if n_games <= 0:
            return np.array([])
        
        # Create weights: α^(N-i) for i in [0, N-1]
        weights = np.array([alpha ** (n_games - i - 1) for i in range(n_games)])
        
        # Normalize to sum to 1
        weights = weights / weights.sum()
        
        return weights
    
    def _calculate_confidence_interval(self, successes: int, trials: int, 
                                      confidence: float = 0.95) -> Tuple[float, float]:
        """Calculate confidence interval for binomial proportion using Wilson score interval"""
        if trials == 0:
            return (0.0, 0.0)
        
        # Use Wilson score interval for better coverage with small samples
        p = successes / trials
        z = stats.norm.ppf((1 + confidence) / 2)
        
        denominator = 1 + z**2 / trials
        center = (p + z**2 / (2 * trials)) / denominator
        margin = z * np.sqrt((p * (1 - p) / trials + z**2 / (4 * trials**2))) / denominator
        
        ci_lower = max(0, center - margin)
        ci_upper = min(1, center + margin)
        
        return (ci_lower, ci_upper)
    
    def _binomial_test(self, successes: int, trials: int, p0: float = 0.5) -> float:
        """Perform binomial test for statistical significance"""
        if trials == 0:
            return 1.0
        
        # Two-tailed binomial test
        try:
            p_value = stats.binom_test(successes, trials, p0, alternative='two-sided')
            return p_value
        except:
            return 1.0
    
    def apply_bayesian_smoothing(self, successes: int, trials: int, 
                                 prior_alpha: float = 1.0, prior_beta: float = 1.0) -> Dict:
        """
        Apply Bayesian smoothing for probability estimates on small sample sizes
        Uses Beta-Binomial conjugate prior for robust estimation
        
        Args:
            successes: Number of successful trials (games >= threshold)
            trials: Total number of trials (total games)
            prior_alpha: Beta distribution alpha parameter (prior successes)
            prior_beta: Beta distribution beta parameter (prior failures)
        
        Returns:
            Dictionary with smoothed probability, credible interval, and effective sample size
        """
        if trials == 0:
            return {
                'smoothed_probability': 0.5,
                'credible_interval_lower': 0.0,
                'credible_interval_upper': 1.0,
                'effective_sample_size': 0
            }
        
        # Posterior parameters using Beta-Binomial conjugate
        posterior_alpha = prior_alpha + successes
        posterior_beta = prior_beta + (trials - successes)
        
        # Posterior mean (Bayesian estimate)
        smoothed_prob = posterior_alpha / (posterior_alpha + posterior_beta)
        
        # 95% credible interval
        credible_lower = beta.ppf(0.025, posterior_alpha, posterior_beta)
        credible_upper = beta.ppf(0.975, posterior_alpha, posterior_beta)
        
        # Effective sample size (precision of posterior)
        effective_n = posterior_alpha + posterior_beta
        
        return {
            'smoothed_probability': smoothed_prob,
            'credible_interval_lower': credible_lower,
            'credible_interval_upper': credible_upper,
            'effective_sample_size': effective_n,
            'shrinkage_factor': (prior_alpha + prior_beta) / effective_n
        }
    
    def calculate_comprehensive_regression_model(self, games_df: pd.DataFrame,
                                               season_stats: Dict,
                                               career_phase: str,
                                               thresholds: Dict,
                                               lambda_params: Dict = None) -> Dict:
        """
        Comprehensive regression-to-mean model incorporating all adjustments
        """
        if len(games_df) == 0:
            return {}
        
        # Step 1: Basic inverse-frequency probabilities
        base_probabilities = self.calculate_inverse_frequency_probabilities(
            games_df, thresholds, alpha=0.85
        )
        
        # Step 2: Apply career phase weighting
        career_adjusted = self.apply_career_phase_weighting(
            games_df, career_phase, base_probabilities, lambda_params
        )
        
        # Step 3: Fatigue/load analysis
        fatigue_analysis = self.analyze_fatigue_curve(games_df)
        
        # Step 4: Minutes trend analysis
        minutes_analysis = self.analyze_minutes_trend(games_df)
        
        # Step 5: Non-stationarity adjustments
        stationarity_adjustments = self.calculate_non_stationarity_adjustment(games_df)
        
        # Step 6: Calculate final composite regression probabilities
        final_results = {}
        
        for stat in base_probabilities.keys():
            final_results[stat] = {}
            
            for threshold, data in base_probabilities[stat].items():
                base_inverse_prob = data['weighted_inverse_probability']
                
                # Apply fatigue adjustment
                fatigue_multiplier = 1 + (fatigue_analysis['regression_risk'] * 0.3)
                
                # Apply minutes trend adjustment
                minutes_multiplier = 2 - minutes_analysis['sustainability_factor']
                
                # Apply non-stationarity adjustment
                stationarity_multiplier = stationarity_adjustments.get(stat, {}).get('adjustment_factor', 1.0)
                
                # Composite regression probability
                composite_regression_prob = min(0.95, base_inverse_prob * fatigue_multiplier * 
                                              minutes_multiplier * stationarity_multiplier)
                
                final_results[stat][threshold] = {
                    **data,
                    'composite_regression_probability': composite_regression_prob,
                    'fatigue_adjustment': fatigue_multiplier,
                    'minutes_adjustment': minutes_multiplier,
                    'stationarity_adjustment': stationarity_multiplier,
                    'final_sustainability_score': 1 - composite_regression_prob
                }
        
        # Add meta information
        final_results['_meta'] = {
            'career_phase': career_phase,
            'fatigue_analysis': fatigue_analysis,
            'minutes_analysis': minutes_analysis,
            'model_version': 'comprehensive_v1.0',
            'n_games_analyzed': len(games_df)
        }
        
        return final_results
