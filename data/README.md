# Data Directory

This directory contains data files used by the application.

## Files

### `nba_2025_2026_schedule.csv`
- **Source**: NBA 2025-2026 season schedule
- **Format**: CSV with game dates, teams, arena info, broadcasters
- **Columns**: 
  - `game_date_local` - Local game date (used for matching)
  - `utc_date`, `utc_time` - UTC timestamps
  - `visitor_abbr`, `home_abbr` - Team abbreviations
  - `visitor_team`, `home_team` - Full team names
  - `arena`, `city`, `state` - Venue information
  - `broadcasters_tv`, `broadcasters_natltv` - Broadcast info
- **Used by**: Pick of the Day feature
- **Size**: 1,271 games

## Usage

The schedule is loaded by `services/picks.py`:
```python
service = PickOfTheDayService(api_client, schedule_path="data/nba_2025_2026_schedule.csv")
```

## Note

**To move the schedule file here:**
1. Stop the Streamlit app
2. Run: `move nba_2025_2026_schedule.csv data\`
3. Restart the app

The code is already updated to look in `data/` folder.

