import requests

# Test specific API key with new NBA v1 endpoints
API_KEY = "3a703743-3082-4c76-bd8e-1857be22aef2"
headers = {'Authorization': API_KEY}

print("Testing NBA v1 endpoints with provided key...\n")

# Test 1: New NBA v1 season averages for 2024
print("=" * 60)
print("TEST: New NBA v1 season_averages/general for 2024")
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
        if data:
            stats = data[0]
            print(f"✅ SUCCESS! Found season stats")
            print(f"   Games: {stats.get('games_played', 0)}")
            print(f"   PPG: {stats.get('pts', 0)}")
            print(f"   RPG: {stats.get('reb', 0)}")
            print(f"   APG: {stats.get('ast', 0)}")
        else:
            print(f"⚠️  API works but no data returned")
    else:
        print(f"❌ Error {response.status_code}: {response.text[:200]}")
except Exception as e:
    print(f"❌ Exception: {e}")

# Test 2: Check if 2025 data exists
print("\n" + "=" * 60)
print("TEST: Check for 2025 data")
print("=" * 60)
url = "https://api.balldontlie.io/v1/stats"
params = {
    'player_ids[]': 15,
    'seasons[]': 2025,
    'per_page': 10
}

try:
    response = requests.get(url, params=params, headers=headers, timeout=10)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json().get('data', [])
        if data:
            print(f"✅ 2025 data found: {len(data)} games")
            for game in data[:3]:
                print(f"   {game.get('game', {}).get('date')}: {game.get('pts')} pts")
        else:
            print(f"❌ No 2025 data available yet")
except Exception as e:
    print(f"❌ Exception: {e}")

print("\n" + "=" * 60)
print("Key validation complete")
print("=" * 60)
