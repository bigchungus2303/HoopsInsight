import os
import requests

API_KEY = os.getenv('NBA_API_KEY')
headers = {'Authorization': API_KEY} if API_KEY else {}

print("Testing different API endpoints and seasons...\n")

# Test 1: Old v1 API for 2024 data
print("=" * 60)
print("TEST 1: Old v1 stats endpoint for 2024")
print("=" * 60)
url = "https://api.balldontlie.io/v1/stats"
params = {
    'player_ids[]': 15,  # Giannis
    'seasons[]': 2024,
    'per_page': 5
}

try:
    response = requests.get(url, params=params, headers=headers, timeout=10)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json().get('data', [])
        print(f"✅ Found {len(data)} games")
        if data:
            print(f"   Sample game date: {data[0].get('game', {}).get('date', 'N/A')}")
    else:
        print(f"❌ Error: {response.text[:200]}")
except Exception as e:
    print(f"❌ Exception: {e}")

# Test 2: New NBA v1 API for 2024
print("\n" + "=" * 60)
print("TEST 2: New NBA v1 season_averages/general for 2024")
print("=" * 60)
url = "https://api.balldontlie.io/nba/v1/season_averages/general"
params = {
    'season': 2024,
    'season_type': 'regular',
    'type': 'base',
    'player_ids[]': 15  # Giannis
}

try:
    response = requests.get(url, params=params, headers=headers, timeout=10)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json().get('data', [])
        print(f"✅ Found {len(data)} season records")
        if data:
            stats = data[0]
            print(f"   Games: {stats.get('games_played', 0)}, PPG: {stats.get('pts', 0)}")
    else:
        print(f"❌ Error: {response.text[:200]}")
except Exception as e:
    print(f"❌ Exception: {e}")

# Test 3: Old v1 API for 2025 data
print("\n" + "=" * 60)
print("TEST 3: Old v1 stats endpoint for 2025")
print("=" * 60)
url = "https://api.balldontlie.io/v1/stats"
params = {
    'player_ids[]': 15,  # Giannis
    'seasons[]': 2025,
    'per_page': 5
}

try:
    response = requests.get(url, params=params, headers=headers, timeout=10)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json().get('data', [])
        print(f"Result: {len(data)} games found")
        if data:
            print(f"✅ 2025 data exists!")
            for game in data[:3]:
                print(f"   Game date: {game.get('game', {}).get('date', 'N/A')}, Pts: {game.get('pts', 'N/A')}")
        else:
            print(f"❌ No 2025 games in response")
    else:
        print(f"❌ Error: {response.text[:200]}")
except Exception as e:
    print(f"❌ Exception: {e}")

# Test 4: Check for preseason 2025
print("\n" + "=" * 60)
print("TEST 4: Old v1 stats for 2025 PRESEASON")
print("=" * 60)
url = "https://api.balldontlie.io/v1/stats"
params = {
    'player_ids[]': 15,  # Giannis
    'seasons[]': 2025,
    'season_types[]': 'preseason',
    'per_page': 10
}

try:
    response = requests.get(url, params=params, headers=headers, timeout=10)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json().get('data', [])
        print(f"Result: {len(data)} preseason games found")
        if data:
            print(f"✅ 2025 PRESEASON data exists!")
            for game in data[:5]:
                print(f"   Game date: {game.get('game', {}).get('date', 'N/A')}, Pts: {game.get('pts', 'N/A')}")
        else:
            print(f"❌ No 2025 preseason games")
    else:
        print(f"❌ Error: {response.text[:200]}")
except Exception as e:
    print(f"❌ Exception: {e}")

print("\n" + "=" * 60)
