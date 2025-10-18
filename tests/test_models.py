"""
Unit tests for statistical models (models.py)
Tests the InverseFrequencyModel class and its methods
"""

import unittest
import pandas as pd
import numpy as np
from models import InverseFrequencyModel


class TestInverseFrequencyModel(unittest.TestCase):
    """Test cases for InverseFrequencyModel"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.model = InverseFrequencyModel()
        
        # Create sample game data
        self.sample_games = pd.DataFrame({
            'pts': [20, 25, 18, 30, 22, 15, 28, 19, 24, 21],
            'reb': [8, 10, 6, 12, 7, 5, 11, 8, 9, 7],
            'ast': [5, 7, 4, 9, 6, 3, 8, 5, 7, 6],
            'fg3m': [2, 3, 1, 4, 2, 1, 3, 2, 3, 2],
            'min': [32, 35, 28, 38, 30, 25, 36, 31, 34, 32],
            'date': pd.date_range('2024-01-01', periods=10)
        })
        
        self.test_thresholds = {
            'pts': [15, 20, 25],
            'reb': [5, 8, 10],
            'ast': [5, 7],
            'fg3m': [2, 3]
        }
    
    def test_calculate_recency_weights(self):
        """Test recency weight calculation"""
        weights = self.model._calculate_recency_weights(5, alpha=0.9)
        
        # Should return 5 weights
        self.assertEqual(len(weights), 5)
        
        # Weights should sum to 1
        self.assertAlmostEqual(np.sum(weights), 1.0, places=10)
        
        # Most recent game should have highest weight
        self.assertGreater(weights[-1], weights[0])
        
        # All weights should be positive
        self.assertTrue(np.all(weights > 0))
    
    def test_inverse_frequency_basic(self):
        """Test basic inverse frequency probability calculation"""
        results = self.model.calculate_inverse_frequency_probabilities(
            self.sample_games, self.test_thresholds, alpha=0.85
        )
        
        # Should have results for all stats
        self.assertIn('pts', results)
        self.assertIn('reb', results)
        self.assertIn('ast', results)
        self.assertIn('fg3m', results)
        
        # Check pts threshold results
        pts_results = results['pts']
        self.assertIn(15, pts_results)
        self.assertIn(20, pts_results)
        self.assertIn(25, pts_results)
        
        # Frequencies should be between 0 and 1
        for threshold, data in pts_results.items():
            self.assertGreaterEqual(data['frequency'], 0)
            self.assertLessEqual(data['frequency'], 1)
            self.assertGreaterEqual(data['inverse_probability'], 0)
            self.assertLessEqual(data['inverse_probability'], 1)
    
    def test_inverse_frequency_all_exceed(self):
        """Test when all games exceed threshold"""
        low_threshold = {'pts': [10]}  # All games exceed this
        results = self.model.calculate_inverse_frequency_probabilities(
            self.sample_games, low_threshold, alpha=0.85
        )
        
        # Frequency should be 1.0 (or very close)
        self.assertAlmostEqual(results['pts'][10]['frequency'], 1.0, places=1)
        # Inverse probability should be 0.0 (or very close)
        self.assertLess(results['pts'][10]['inverse_probability'], 0.1)
    
    def test_inverse_frequency_none_exceed(self):
        """Test when no games exceed threshold"""
        high_threshold = {'pts': [100]}  # No games exceed this
        results = self.model.calculate_inverse_frequency_probabilities(
            self.sample_games, high_threshold, alpha=0.85
        )
        
        # Frequency should be 0.0
        self.assertEqual(results['pts'][100]['frequency'], 0.0)
        # Inverse probability should be 1.0
        self.assertEqual(results['pts'][100]['inverse_probability'], 1.0)
    
    def test_confidence_interval_calculation(self):
        """Test confidence interval calculation"""
        ci_lower, ci_upper = self.model._calculate_confidence_interval(7, 10, confidence=0.95)
        
        # CI should be valid range
        self.assertGreaterEqual(ci_lower, 0)
        self.assertLessEqual(ci_upper, 1)
        self.assertLess(ci_lower, ci_upper)
        
        # Test edge cases
        ci_lower_all, ci_upper_all = self.model._calculate_confidence_interval(10, 10)
        self.assertGreater(ci_lower_all, 0.5)  # Should be high when all succeed
        
        ci_lower_none, ci_upper_none = self.model._calculate_confidence_interval(0, 10)
        self.assertLess(ci_upper_none, 0.5)  # Should be low when none succeed
    
    def test_bayesian_smoothing(self):
        """Test Bayesian smoothing for small samples"""
        # Test with small sample: 2 successes out of 5 trials
        result = self.model.apply_bayesian_smoothing(2, 5, prior_alpha=2.0, prior_beta=2.0)
        
        self.assertIn('smoothed_probability', result)
        self.assertIn('credible_interval_lower', result)
        self.assertIn('credible_interval_upper', result)
        self.assertIn('effective_sample_size', result)
        
        # Smoothed probability should be between raw probability and prior
        raw_prob = 2 / 5  # 0.4
        prior_mean = 2 / (2 + 2)  # 0.5
        smoothed = result['smoothed_probability']
        
        # Smoothed should be between raw and prior
        self.assertGreater(smoothed, min(raw_prob, prior_mean) - 0.1)
        self.assertLess(smoothed, max(raw_prob, prior_mean) + 0.1)
        
        # Effective sample size should be trials + prior
        self.assertEqual(result['effective_sample_size'], 9)  # 5 + 2 + 2
    
    def test_fatigue_analysis(self):
        """Test fatigue curve analysis"""
        fatigue_results = self.model.analyze_fatigue_curve(self.sample_games, window_size=5)
        
        self.assertIn('regression_risk', fatigue_results)
        self.assertIn('sustainability_factor', fatigue_results)
        self.assertIn('recent_rolling_mean', fatigue_results)
        self.assertIn('long_term_mean', fatigue_results)
        
        # Regression risk should be between 0 and 1
        self.assertGreaterEqual(fatigue_results['regression_risk'], 0)
        self.assertLessEqual(fatigue_results['regression_risk'], 1)
        
        # Sustainability is inverse of regression risk
        expected_sustainability = 1 - fatigue_results['regression_risk']
        self.assertAlmostEqual(fatigue_results['sustainability_factor'], expected_sustainability)
    
    def test_minutes_trend_analysis(self):
        """Test minutes played trend analysis"""
        # Create data with declining minutes
        declining_games = self.sample_games.copy()
        declining_games['min'] = [38, 36, 34, 32, 30, 28, 26, 24, 22, 20]
        
        trend_results = self.model.analyze_minutes_trend(declining_games, window_size=10)
        
        self.assertIn('declining_trend', trend_results)
        self.assertIn('trend_slope', trend_results)
        self.assertIn('sustainability_factor', trend_results)
        
        # Should detect declining trend
        self.assertTrue(trend_results['declining_trend'])
        self.assertLess(trend_results['trend_slope'], 0)
        
        # Sustainability should be reduced
        self.assertLess(trend_results['sustainability_factor'], 1.0)
    
    def test_non_stationarity_adjustment(self):
        """Test non-stationarity detection"""
        # Create data with regime change (first half low, second half high)
        regime_change_games = self.sample_games.copy()
        regime_change_games['pts'] = [15, 16, 14, 15, 17, 28, 30, 29, 31, 28]
        
        adjustments = self.model.calculate_non_stationarity_adjustment(
            regime_change_games, lookback_window=5
        )
        
        self.assertIn('pts', adjustments)
        pts_adj = adjustments['pts']
        
        self.assertIn('recent_mean', pts_adj)
        self.assertIn('full_mean', pts_adj)
        self.assertIn('regime_change_detected', pts_adj)
        
        # Should detect regime change
        self.assertTrue(pts_adj['regime_change_detected'])
        
        # Recent mean should be much higher than full mean
        self.assertGreater(pts_adj['recent_mean'], pts_adj['full_mean'])
    
    def test_empty_games_dataframe(self):
        """Test handling of empty games data"""
        empty_df = pd.DataFrame()
        results = self.model.calculate_inverse_frequency_probabilities(
            empty_df, self.test_thresholds, alpha=0.85
        )
        
        # Should return empty results without crashing
        self.assertEqual(len(results), 0)
    
    def test_missing_stat_columns(self):
        """Test handling of missing stat columns"""
        partial_df = self.sample_games[['pts']].copy()  # Only pts column
        thresholds = {'pts': [20], 'reb': [8]}  # Request pts and reb
        
        results = self.model.calculate_inverse_frequency_probabilities(
            partial_df, thresholds, alpha=0.85
        )
        
        # Should have pts results but not reb
        self.assertIn('pts', results)
        self.assertNotIn('reb', results)


class TestStatisticsEngineIntegration(unittest.TestCase):
    """Integration tests combining model with statistics engine"""
    
    def setUp(self):
        """Set up test fixtures"""
        from statistics import StatisticsEngine
        
        self.model = InverseFrequencyModel()
        self.stats_engine = StatisticsEngine()
        
        self.sample_games = pd.DataFrame({
            'pts': [20, 25, 18, 30, 22],
            'reb': [8, 10, 6, 12, 7],
            'ast': [5, 7, 4, 9, 6],
            'date': pd.date_range('2024-01-01', periods=5)
        })
        
        self.season_stats = {
            'pts': 23.0,
            'reb': 8.6,
            'ast': 6.2
        }
    
    def test_dynamic_thresholds_calculation(self):
        """Test dynamic threshold generation"""
        thresholds = self.stats_engine.calculate_dynamic_thresholds(self.season_stats)
        
        self.assertIn('pts', thresholds)
        self.assertIn('reb', thresholds)
        self.assertIn('ast', thresholds)
        
        # Check pts thresholds structure
        pts_thresh = thresholds['pts']
        self.assertIn('mean', pts_thresh)
        self.assertIn('plus_1_std', pts_thresh)
        self.assertIn('plus_2_std', pts_thresh)
        self.assertIn('plus_3_std', pts_thresh)
        
        # Mean should match season stats
        self.assertEqual(pts_thresh['mean'], 23.0)
        
        # Thresholds should be increasing
        self.assertLess(pts_thresh['mean'], pts_thresh['plus_1_std'])
        self.assertLess(pts_thresh['plus_1_std'], pts_thresh['plus_2_std'])
        self.assertLess(pts_thresh['plus_2_std'], pts_thresh['plus_3_std'])
    
    def test_career_phase_detection(self):
        """Test career phase determination"""
        # Rising career
        rising_career = [
            {'season': 2020, 'pts': 10},
            {'season': 2021, 'pts': 15},
            {'season': 2022, 'pts': 20},
            {'season': 2023, 'pts': 25}
        ]
        phase = self.stats_engine.calculate_career_phase(rising_career)
        self.assertEqual(phase, 'rising')
        
        # Late career (declining)
        late_career = [
            {'season': 2015, 'pts': 28},
            {'season': 2016, 'pts': 27},
            {'season': 2017, 'pts': 25},
            {'season': 2018, 'pts': 23},
            {'season': 2019, 'pts': 20},
            {'season': 2020, 'pts': 18},
            {'season': 2021, 'pts': 16},
            {'season': 2022, 'pts': 14},
            {'season': 2023, 'pts': 12},
            {'season': 2024, 'pts': 10}
        ]
        phase = self.stats_engine.calculate_career_phase(late_career)
        self.assertEqual(phase, 'late')
        
        # Early career
        early_career = [
            {'season': 2023, 'pts': 12},
            {'season': 2024, 'pts': 14}
        ]
        phase = self.stats_engine.calculate_career_phase(early_career)
        self.assertEqual(phase, 'early')


if __name__ == '__main__':
    unittest.main()

