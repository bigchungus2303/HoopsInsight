import pandas as pd
import json
from typing import Dict, List
from datetime import datetime

def export_player_stats_csv(player_data: Dict, season_stats: Dict, recent_games: List[Dict]) -> str:
    """Export player statistics to CSV format"""
    
    # Create season stats dataframe
    season_df = pd.DataFrame([{
        'Player': f"{player_data['first_name']} {player_data['last_name']}",
        'Team': player_data['team']['abbreviation'],
        'Season': season_stats.get('season', 'N/A'),
        'Games Played': season_stats.get('games_played'),
        'PPG': season_stats.get('pts'),
        'RPG': season_stats.get('reb'),
        'APG': season_stats.get('ast'),
        'FG%': season_stats.get('fg_pct'),
        '3P%': season_stats.get('fg3_pct'),
        'FT%': season_stats.get('ft_pct'),
        'MPG': season_stats.get('min')
    }])
    
    # Create recent games dataframe
    games_data = []
    for game in recent_games:
        games_data.append({
            'Date': game.get('game', {}).get('date'),
            'Points': game.get('pts'),
            'Rebounds': game.get('reb'),
            'Assists': game.get('ast'),
            'FG%': game.get('fg_pct'),
            '3PM': game.get('fg3m'),
            'Minutes': game.get('min')
        })
    
    games_df = pd.DataFrame(games_data)
    
    # Combine into single CSV
    csv_data = "SEASON STATISTICS\n"
    csv_data += season_df.to_csv(index=False)
    csv_data += "\n\nRECENT GAMES\n"
    csv_data += games_df.to_csv(index=False)
    
    return csv_data

def export_probability_analysis_csv(probability_results: Dict, player_name: str) -> str:
    """Export probability analysis to CSV format"""
    
    rows = []
    
    for stat, thresholds in probability_results.items():
        if stat == '_meta':
            continue
            
        for threshold, data in thresholds.items():
            if isinstance(data, dict):
                rows.append({
                    'Player': player_name,
                    'Stat': stat.upper(),
                    'Threshold': threshold,
                    'Frequency': data.get('frequency', 0),
                    'Inverse Probability': data.get('inverse_probability', 0),
                    'Weighted Frequency': data.get('weighted_frequency', 0),
                    'Weighted Inverse Probability': data.get('weighted_inverse_probability', 0),
                    'N Games': data.get('n_games', 0)
                })
    
    df = pd.DataFrame(rows)
    return df.to_csv(index=False)

def export_comparison_csv(player1_data: Dict, player2_data: Dict, 
                          stats1: Dict, stats2: Dict) -> str:
    """Export player comparison to CSV format"""
    
    player1_name = f"{player1_data['first_name']} {player1_data['last_name']}"
    player2_name = f"{player2_data['first_name']} {player2_data['last_name']}"
    
    comparison_data = []
    
    stats_to_compare = [
        ('PPG', 'pts'),
        ('RPG', 'reb'),
        ('APG', 'ast'),
        ('FG%', 'fg_pct'),
        ('3P%', 'fg3_pct'),
        ('FT%', 'ft_pct'),
        ('MPG', 'min'),
        ('Games Played', 'games_played')
    ]
    
    for label, key in stats_to_compare:
        comparison_data.append({
            'Statistic': label,
            player1_name: stats1.get(key, 'N/A'),
            player2_name: stats2.get(key, 'N/A'),
            'Difference': stats1.get(key, 0) - stats2.get(key, 0) if stats1.get(key) and stats2.get(key) else 'N/A'
        })
    
    df = pd.DataFrame(comparison_data)
    return df.to_csv(index=False)

def export_player_stats_json(player_data: Dict, season_stats: Dict, 
                             recent_games: List[Dict], probability_results: Dict = None) -> str:
    """Export player statistics to JSON format"""
    
    export_data = {
        'player': {
            'id': player_data['id'],
            'name': f"{player_data['first_name']} {player_data['last_name']}",
            'team': player_data['team']['full_name'],
            'position': player_data.get('position'),
            'height': f"{player_data.get('height_feet', 'N/A')}'{player_data.get('height_inches', 'N/A')}\"",
            'weight': player_data.get('weight_pounds')
        },
        'season_stats': season_stats,
        'recent_games': recent_games,
        'export_timestamp': datetime.now().isoformat()
    }
    
    if probability_results:
        export_data['probability_analysis'] = probability_results
    
    return json.dumps(export_data, indent=2)

def export_comparison_json(player1_data: Dict, player2_data: Dict, 
                           stats1: Dict, stats2: Dict) -> str:
    """Export player comparison to JSON format"""
    
    comparison = {
        'player1': {
            'id': player1_data['id'],
            'name': f"{player1_data['first_name']} {player1_data['last_name']}",
            'team': player1_data['team']['full_name'],
            'stats': stats1
        },
        'player2': {
            'id': player2_data['id'],
            'name': f"{player2_data['first_name']} {player2_data['last_name']}",
            'team': player2_data['team']['full_name'],
            'stats': stats2
        },
        'comparison_timestamp': datetime.now().isoformat()
    }
    
    return json.dumps(comparison, indent=2)
