import requests
import os

API_KEY = os.getenv('NBA_API_KEY', '3a703743-3082-4c76-bd8e-1857be22aef2')
headers = {'Authorization': API_KEY}

print("Testing CORRECT season_averages parameters...\n")

url = "https://api.balldontlie.io/v1/season_averages"

# Correct format with player_id (singular)
params = {
    'player_id': 15,  # Giannis - SINGULAR!
    'season': 2024
}

response = requests.get(url, params=params, headers=headers, timeout=10)
print(f"Status: {response.status_code}")

if response.status_code == 200:
    data = response.json().get('data', [])
    print(f"✅ SUCCESS! Found {len(data)} records")
    if data:
        stats = data[0]
        print(f"\nGiannis 2024 Stats:")
        print(f"  Games: {stats.get('games_played', 'N/A')}")
        print(f"  PPG: {stats.get('pts', 'N/A')}")
        print(f"  RPG: {stats.get('reb', 'N/A')}")
        print(f"  APG: {stats.get('ast', 'N/A')}")
else:
    print(f"❌ Error: {response.text}")
