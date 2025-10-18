# Testing Guide

## Prerequisites

You need Python 3.11+ with the following packages installed. Based on your `pyproject.toml`:

```bash
pip install streamlit pandas numpy scipy plotly requests
```

Or if you're using `uv`:
```bash
uv sync
```

## Set Environment Variable

Before running, set your NBA API key:

**Windows (PowerShell):**
```powershell
$env:NBA_API_KEY = "your-api-key-here"
```

**Windows (CMD):**
```cmd
set NBA_API_KEY=your-api-key-here
```

**Linux/Mac:**
```bash
export NBA_API_KEY="your-api-key-here"
```

## Running Tests

### 1. Run Unit Tests

Test the statistical models and new features:

```bash
python run_tests.py
```

Or run specific tests:
```bash
python -m unittest tests.test_models
python -m unittest tests.test_statistics
```

Expected output: All tests should pass ✓

### 2. Run the Main Application

Start the Streamlit app:

```bash
streamlit run app.py
```

Or:
```bash
python -m streamlit run app.py
```

The app should open in your browser at `http://localhost:8501`

## What to Test

### ✅ Configuration System
1. The app should start without errors (using new config.py)
2. Check console for log messages (new logging system)

### ✅ Logging System
Look for log messages in the console like:
```
2024-10-17 - nba_api - INFO - Loading default league averages for season 2024
2024-10-17 - nba_api - DEBUG - API request successful: players
```

### ✅ API Call Tracking
In the app:
1. Search for a player
2. The API call counter is now being tracked (will be displayed in future UI update)

### ✅ Prediction Tracking (Backend Ready)
The database now has prediction tracking tables. Future UI will let you:
- Save predictions
- Verify them after games
- View accuracy metrics

### ✅ Better Error Handling
API errors now show detailed logs instead of just crashing

## Troubleshooting

### Issue: "No module named 'config'"
**Solution:** Make sure you're in the project directory:
```bash
cd C:\Users\Son\Downloads\HoopsInsight
```

### Issue: "NBA_API_KEY not set"
**Solution:** Set the environment variable (see Prerequisites above)

### Issue: "sqlite3.OperationalError: table predictions already exists"
**Solution:** This is fine - the table was already created. The app will work normally.

### Issue: Import errors
**Solution:** Install missing packages:
```bash
pip install <missing-package>
```

## Quick Start (All-in-One)

```powershell
# Windows PowerShell - Run all at once
cd C:\Users\Son\Downloads\HoopsInsight
$env:NBA_API_KEY = "your-api-key-here"
python run_tests.py
streamlit run app.py
```

## Expected Results

### Unit Tests
```
test_bayesian_smoothing (tests.test_models.TestInverseFrequencyModel) ... ok
test_confidence_interval_calculation (tests.test_models.TestInverseFrequencyModel) ... ok
test_fatigue_analysis (tests.test_models.TestInverseFrequencyModel) ... ok
...
----------------------------------------------------------------------
Ran 25 tests in 0.5s

OK
```

### Streamlit App
- App loads successfully ✓
- Player search works ✓
- Statistics display correctly ✓
- Charts render properly ✓
- Console shows log messages ✓

## New Features to Look For

While the UI hasn't changed visibly, these improvements are working under the hood:

1. **Better Logging** - Check your console/terminal for detailed logs
2. **Configuration** - All settings centralized in config.py
3. **API Tracking** - API calls are being counted (use `api_client.get_api_call_count()`)
4. **Prediction Database** - Tables created, ready for future UI
5. **Tested Code** - 25+ unit tests ensuring reliability

## Next Steps

After confirming everything works:
1. Try searching for different players
2. Check that statistics load correctly
3. Verify charts display properly
4. Look at console logs to see the new logging system in action

## Need Help?

If you encounter issues:
1. Check the console/terminal for error messages
2. Make sure NBA_API_KEY is set
3. Verify all dependencies are installed
4. Check Python version (requires 3.11+)


