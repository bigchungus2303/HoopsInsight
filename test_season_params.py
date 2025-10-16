import requests
import os

API_KEY = os.getenv('NBA_API_KEY', '3a703743-3082-4c76-bd8e-1857be22aef2')
headers = {'Authorization': API_KEY}

print("Testing season_averages endpoint parameter formats...\n")

# Test 1: season parameter
print("Test 1: Using 'season' parameter")
url = "https://api.balldontlie.io/v1/season_averages"
params = {
    'season': 2024,
    'player_ids[]': 15,
    'per_page': 100
}
response = requests.get(url, params=params, headers=headers, timeout=10)
print(f"  Status: {response.status_code}")
if response.status_code != 200:
    print(f"  Error: {response.text[:300]}")
else:
    print(f"  ✅ Success! Data: {len(response.json().get('data', []))} records")

# Test 2: seasons[] parameter
print("\nTest 2: Using 'seasons[]' parameter")
params = {
    'seasons[]': 2024,
    'player_ids[]': 15,
    'per_page': 100
}
response = requests.get(url, params=params, headers=headers, timeout=10)
print(f"  Status: {response.status_code}")
if response.status_code != 200:
    print(f"  Error: {response.text[:300]}")
else:
    print(f"  ✅ Success! Data: {len(response.json().get('data', []))} records")

# Test 3: No season parameter (check if it works)
print("\nTest 3: No season parameter")
params = {
    'player_ids[]': 15,
    'per_page': 100
}
response = requests.get(url, params=params, headers=headers, timeout=10)
print(f"  Status: {response.status_code}")
if response.status_code != 200:
    print(f"  Error: {response.text[:300]}")
else:
    data = response.json().get('data', [])
    print(f"  ✅ Success! Data: {len(data)} records")
    if data:
        print(f"  Seasons in response: {[d.get('season') for d in data[:3]]}")
