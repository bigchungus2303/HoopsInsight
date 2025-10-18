"""
Unit tests for statistics engine (statistics.py)
Tests the StatisticsEngine class and its methods
"""

import unittest
import pandas as pd
import numpy as np
from statistics import StatisticsEngine


class TestStatisticsEngine(unittest.TestCase):
    """Test cases for StatisticsEngine"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.engine = StatisticsEngine()
        
        # Sample player stats
        self.player_stats = pd.DataFrame({
            'pts': [25.3],
            'reb': [10.2],
            'ast': [8.5],
            'fg_pct': [0.485],
            'fg3_pct': [0.380],
            'ft_pct': [0.850],
            'min': [36.5]
        })
        
        self.league_averages = {
            'pts': 11.5, 'pts_std': 8.5,
            'reb': 4.2, 'reb_std': 3.2,
            'ast': 2.8, 'ast_std': 2.9,
            'fg_pct': 0.462, 'fg_pct_std': 0.087,
            'fg3_pct': 0.367, 'fg3_pct_std': 0.112,
            'ft_pct': 0.783, 'ft_pct_std': 0.125,
            'min': 20.5, 'min_std': 9.8
        }
    
    def test_z_score_calculation(self):
        """Test z-score normalization"""
        result = self.engine.calculate_z_scores(self.player_stats, self.league_averages)
        
        # Should have z-score columns
        self.assertIn('pts_z', result.columns)
        self.assertIn('reb_z', result.columns)
        self.assertIn('ast_z', result.columns)
        
        # Calculate expected z-score for pts
        expected_pts_z = (25.3 - 11.5) / 8.5
        self.assertAlmostEqual(result['pts_z'].iloc[0], expected_pts_z, places=2)
        
        # Player above average should have positive z-scores
        self.assertGreater(result['pts_z'].iloc[0], 0)
        self.assertGreater(result['reb_z'].iloc[0], 0)
        self.assertGreater(result['ast_z'].iloc[0], 0)
    
    def test_league_averages_caching(self):
        """Test league averages are cached properly"""
        # First call
        avg1 = self.engine.get_league_averages(2024)
        
        # Second call should return cached version
        avg2 = self.engine.get_league_averages(2024)
        
        # Should be the same object
        self.assertEqual(id(avg1), id(avg2))
        
        # Should have all required keys
        required_keys = ['pts', 'reb', 'ast', 'fg_pct', 'fg3_pct', 'ft_pct', 'min']
        for key in required_keys:
            self.assertIn(key, avg1)
            self.assertIn(f'{key}_std', avg1)
    
    def test_parse_minutes_format(self):
        """Test parsing minutes from MM:SS format"""
        # Test various formats
        self.assertAlmostEqual(self.engine._parse_minutes("34:30"), 34.5, places=2)
        self.assertAlmostEqual(self.engine._parse_minutes("25:15"), 25.25, places=2)
        self.assertEqual(self.engine._parse_minutes("0:00"), 0.0)
        self.assertAlmostEqual(self.engine._parse_minutes("40:00"), 40.0, places=2)
        
        # Test numeric input (already converted)
        self.assertEqual(self.engine._parse_minutes(35.5), 35.5)
        self.assertEqual(self.engine._parse_minutes(28), 28.0)
        
        # Test invalid input
        self.assertEqual(self.engine._parse_minutes(None), 0.0)
        self.assertEqual(self.engine._parse_minutes(""), 0.0)
        self.assertEqual(self.engine._parse_minutes("invalid"), 0.0)
    
    def test_career_phase_weights(self):
        """Test career phase weight calculation"""
        # Test different phases
        early_weights = self.engine.calculate_career_phase_weights('early', 10)
        peak_weights = self.engine.calculate_career_phase_weights('peak', 10)
        late_weights = self.engine.calculate_career_phase_weights('late', 10)
        
        # All should sum to 1
        self.assertAlmostEqual(np.sum(early_weights), 1.0, places=10)
        self.assertAlmostEqual(np.sum(peak_weights), 1.0, places=10)
        self.assertAlmostEqual(np.sum(late_weights), 1.0, places=10)
        
        # All should have 10 weights
        self.assertEqual(len(early_weights), 10)
        self.assertEqual(len(peak_weights), 10)
        self.assertEqual(len(late_weights), 10)
        
        # Recent games should have higher weight
        for weights in [early_weights, peak_weights, late_weights]:
            self.assertGreater(weights[-1], weights[0])
        
        # Late career should have more decay (bigger difference between recent and old)
        early_ratio = early_weights[-1] / early_weights[0]
        late_ratio = late_weights[-1] / late_weights[0]
        self.assertGreater(late_ratio, early_ratio)
    
    def test_consistency_metrics(self):
        """Test consistency metric calculation"""
        games_data = pd.DataFrame({
            'pts': [20, 22, 21, 19, 23, 20, 21, 22, 20, 21],
            'reb': [8, 10, 7, 9, 11, 8, 9, 10, 8, 9],
            'ast': [5, 7, 6, 5, 8, 6, 7, 6, 5, 6]
        })
        
        metrics = self.engine.calculate_consistency_metrics(games_data)
        
        # Should have metrics for each stat
        for stat in ['pts', 'reb', 'ast']:
            self.assertIn(f'{stat}_mean', metrics)
            self.assertIn(f'{stat}_std', metrics)
            self.assertIn(f'{stat}_cv', metrics)
            self.assertIn(f'{stat}_median', metrics)
            self.assertIn(f'{stat}_range', metrics)
            self.assertIn(f'{stat}_consistency', metrics)
        
        # Consistency should be between 0 and 1
        self.assertGreater(metrics['pts_consistency'], 0)
        self.assertLessEqual(metrics['pts_consistency'], 1)
        
        # CV should be non-negative
        self.assertGreaterEqual(metrics['pts_cv'], 0)
    
    def test_momentum_calculation(self):
        """Test momentum indicator calculation"""
        # Improving trend
        improving = [15, 17, 19, 21, 23]
        momentum = self.engine.calculate_momentum(improving, window_size=5)
        
        self.assertEqual(momentum['trend'], 'improving')
        self.assertGreater(momentum['momentum_score'], 0)
        self.assertGreater(momentum['slope'], 0)
        
        # Declining trend
        declining = [25, 23, 21, 19, 17]
        momentum = self.engine.calculate_momentum(declining, window_size=5)
        
        self.assertEqual(momentum['trend'], 'declining')
        self.assertLess(momentum['slope'], 0)
        
        # Stable trend
        stable = [20, 21, 20, 21, 20]
        momentum = self.engine.calculate_momentum(stable, window_size=5)
        
        self.assertEqual(momentum['trend'], 'stable')
    
    def test_outlier_detection_iqr(self):
        """Test IQR outlier detection method"""
        data = [20, 21, 22, 20, 21, 100, 19, 20, 21, 22]  # 100 is outlier
        outliers = self.engine.detect_outliers(data, method='iqr')
        
        # Should detect the outlier at index 5
        self.assertTrue(outliers[5])
        
        # Most other values should not be outliers
        non_outliers = sum(1 for i, o in enumerate(outliers) if not o and i != 5)
        self.assertGreater(non_outliers, 7)
    
    def test_outlier_detection_zscore(self):
        """Test z-score outlier detection method"""
        data = [20, 21, 22, 20, 21, 50, 19, 20, 21, 22]  # 50 is outlier
        outliers = self.engine.detect_outliers(data, method='zscore')
        
        # Should detect the outlier
        self.assertTrue(any(outliers))
    
    def test_outlier_detection_small_sample(self):
        """Test outlier detection with small sample"""
        small_data = [20, 21, 22]
        outliers = self.engine.detect_outliers(small_data, method='iqr')
        
        # Should return all False for small sample
        self.assertEqual(outliers, [False, False, False])
    
    def test_seasonal_normalization(self):
        """Test seasonal normalization"""
        games = pd.DataFrame({
            'pts': [20, 25, 18, 22, 24],
            'reb': [8, 10, 7, 9, 8],
            'ast': [5, 7, 4, 6, 5]
        })
        
        season_avg = 22.0
        result = self.engine.calculate_seasonal_normalization(games, season_avg)
        
        # Should have z-score columns
        self.assertIn('pts_zscore', result.columns)
        
        # Original columns should still exist
        self.assertIn('pts', result.columns)


if __name__ == '__main__':
    unittest.main()

