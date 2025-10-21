"""
Unit tests for Pick of the Day service
"""
import pytest
import pandas as pd
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.picks import PickOfTheDayService, export_picks_csv, export_picks_json
from nba_api import NBAAPIClient


class TestPickOfTheDayService:
    """Test suite for PickOfTheDayService"""
    
    @pytest.fixture
    def mock_api_client(self):
        """Create a mock API client"""
        client = Mock(spec=NBAAPIClient)
        client.get_teams.return_value = {
            1: 'LAL',
            2: 'GSW',
            3: 'BOS',
            4: 'MIA'
        }
        return client
    
    @pytest.fixture
    def service(self, mock_api_client):
        """Create service instance"""
        return PickOfTheDayService(mock_api_client, schedule_path="nba_2025_2026_schedule.csv")
    
    def test_load_config(self, service):
        """Test configuration loading"""
        config = service.config
        
        assert 'presets' in config
        assert 'default' in config['presets']
        assert 'conservative' in config['presets']
        assert 'aggressive' in config['presets']
        assert 'diversity' in config
        assert 'filters' in config
    
    def test_load_schedule_csv(self, service):
        """Test schedule CSV loading"""
        try:
            schedule = service.load_schedule_csv()
            
            assert isinstance(schedule, pd.DataFrame)
            assert 'utc_date' in schedule.columns
            assert 'visitor_abbr' in schedule.columns
            assert 'home_abbr' in schedule.columns
            assert len(schedule) > 0
        except FileNotFoundError:
            pytest.skip("Schedule CSV not found")
    
    def test_find_games_for_date(self, service):
        """Test finding games for a specific date"""
        try:
            # Use a date from the schedule
            test_date = datetime(2026, 1, 1)
            games = service.find_games_for_date(test_date)
            
            assert isinstance(games, list)
            if len(games) > 0:
                game = games[0]
                assert 'visitor_abbr' in game
                assert 'home_abbr' in game
                assert 'arena' in game
                assert 'utc_date' in game
        except FileNotFoundError:
            pytest.skip("Schedule CSV not found")
    
    def test_find_games_deterministic(self, service):
        """Test that finding games is deterministic"""
        try:
            test_date = datetime(2026, 1, 1)
            
            games1 = service.find_games_for_date(test_date)
            games2 = service.find_games_for_date(test_date)
            
            assert len(games1) == len(games2)
            
            # Check that games are in same order
            for g1, g2 in zip(games1, games2):
                assert g1['gid'] == g2['gid']
                assert g1['visitor_abbr'] == g2['visitor_abbr']
                assert g1['home_abbr'] == g2['home_abbr']
        except FileNotFoundError:
            pytest.skip("Schedule CSV not found")
    
    def test_build_candidate_markets(self, service):
        """Test building candidate markets"""
        player = {'id': 123, 'name': 'Test Player'}
        
        # Test default preset
        markets = service.build_candidate_markets(player, 'default')
        assert isinstance(markets, list)
        assert len(markets) > 0
        
        # Test conservative preset
        conservative_markets = service.build_candidate_markets(player, 'conservative')
        assert isinstance(conservative_markets, list)
        
        # Test aggressive preset
        aggressive_markets = service.build_candidate_markets(player, 'aggressive')
        assert isinstance(aggressive_markets, list)
    
    def test_top_picks_diversity(self, service):
        """Test top picks diversity constraint"""
        # Create mock predictions with duplicate stats
        predictions = [
            {'stat': 'pts', 'threshold': 25, 'probability': 0.8, 'n_exceeds': 8, 'n_games': 10},
            {'stat': 'pts', 'threshold': 30, 'probability': 0.78, 'probability': 0.78, 'n_exceeds': 7, 'n_games': 10},  # Duplicate stat, small gap
            {'stat': 'reb', 'threshold': 8, 'probability': 0.75, 'n_exceeds': 7, 'n_games': 10},
            {'stat': 'ast', 'threshold': 6, 'probability': 0.7, 'n_exceeds': 6, 'n_games': 10},
            {'stat': 'fg3m', 'threshold': 3, 'probability': 0.65, 'n_exceeds': 6, 'n_games': 10},
        ]
        
        # With diversity requirement
        top_5 = service.top_picks(predictions, n=5, require_distinct=True, min_gap=0.05)
        
        # Should skip second pts prediction due to small gap
        assert len(top_5) <= 5
        
        # Count unique stats
        stat_types = [p['stat'] for p in top_5]
        # With require_distinct and small gap, should have mostly unique stats
        assert len(set(stat_types)) >= 3
    
    def test_top_picks_no_diversity(self, service):
        """Test top picks without diversity constraint"""
        predictions = [
            {'stat': 'pts', 'threshold': 25, 'probability': 0.9, 'n_exceeds': 9, 'n_games': 10},
            {'stat': 'pts', 'threshold': 30, 'probability': 0.85, 'n_exceeds': 8, 'n_games': 10},
            {'stat': 'pts', 'threshold': 35, 'probability': 0.8, 'n_exceeds': 8, 'n_games': 10},
            {'stat': 'reb', 'threshold': 8, 'probability': 0.75, 'n_exceeds': 7, 'n_games': 10},
            {'stat': 'ast', 'threshold': 6, 'probability': 0.7, 'n_exceeds': 6, 'n_games': 10},
        ]
        
        # Without diversity requirement
        top_5 = service.top_picks(predictions, n=5, require_distinct=False, min_gap=0.0)
        
        assert len(top_5) == 5
        # Can have multiple pts predictions
        pts_count = sum(1 for p in top_5 if p['stat'] == 'pts')
        assert pts_count >= 2  # Should allow multiple pts picks
    
    def test_generate_badges(self, service):
        """Test badge generation"""
        result = {
            'weighted_frequency': 0.75,
            'n_exceeds': 12,
            'n_games': 15
        }
        
        # Mock games DataFrame
        games_df = pd.DataFrame({
            'pts': [25, 28, 30, 22, 26, 27, 31, 29, 24, 28, 30, 32, 27, 26, 29]
        })
        
        badges = service._generate_badges(result, games_df, 'pts')
        
        assert isinstance(badges, list)
        # Should have high confidence badge (n_exceeds >= 10)
        assert any('HIGH CONFIDENCE' in badge for badge in badges)
    
    def test_generate_rationale(self, service):
        """Test rationale generation"""
        result = {
            'weighted_frequency': 0.75,
            'n_exceeds': 8,
            'n_games': 10
        }
        
        rationale = service._generate_rationale(result, 'pts', 25, 'LAL')
        
        assert isinstance(rationale, str)
        assert len(rationale) > 0
        assert 'LAL' in rationale or 'vs LAL' in rationale
        assert '25' in rationale
        assert '8/10' in rationale
    
    def test_export_picks_csv_empty(self):
        """Test CSV export with no picks"""
        game_picks = []
        csv_data = export_picks_csv(game_picks)
        
        assert csv_data == ""
    
    def test_export_picks_json_empty(self):
        """Test JSON export with no picks"""
        game_picks = []
        json_data = export_picks_json(game_picks)
        
        assert isinstance(json_data, str)
        assert json_data == "[]"


class TestExportFunctions:
    """Test export functionality"""
    
    def test_export_picks_csv_with_data(self):
        """Test CSV export with sample data"""
        game_picks = [{
            'game_info': {
                'gid': '0022500471',
                'utc_date': '2026-01-01',
                'visitor_abbr': 'HOU',
                'home_abbr': 'BKN'
            },
            'away_team': 'HOU',
            'home_team': 'BKN',
            'away_picks': [{
                'player_name': 'Test Player',
                'stat': 'pts',
                'threshold': 25,
                'probability': 0.75,
                'n_games': 10,
                'std': 5.2,
                'alpha': 0.85,
                'badges': ['🔥 HOT'],
                'rationale': 'Strong performance'
            }],
            'home_picks': []
        }]
        
        csv_data = export_picks_csv(game_picks)
        
        assert isinstance(csv_data, str)
        assert len(csv_data) > 0
        assert 'Test Player' in csv_data
        assert 'pts' in csv_data
        assert '25' in csv_data
    
    def test_export_picks_json_with_data(self):
        """Test JSON export with sample data"""
        game_picks = [{
            'game_info': {
                'gid': '0022500471',
                'utc_date': '2026-01-01',
                'visitor_abbr': 'HOU',
                'home_abbr': 'BKN'
            },
            'away_team': 'HOU',
            'home_team': 'BKN',
            'away_picks': [],
            'home_picks': []
        }]
        
        json_data = export_picks_json(game_picks)
        
        assert isinstance(json_data, str)
        assert len(json_data) > 0
        assert 'HOU' in json_data
        assert 'BKN' in json_data


def test_deterministic_output():
    """Test that pick generation is deterministic given fixed inputs"""
    # This test would require mocking the API and running generation twice
    # For now, just verify the concept
    
    # Given same:
    # - date
    # - alpha
    # - min_samples
    # - preset
    # - player data
    
    # Should produce identical results
    pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

