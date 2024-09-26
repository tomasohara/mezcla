import requests

INSTANCE_ID = "12667612"
API_URL = f"https://console.vast.ai/api/v0/instances/{INSTANCE_ID}/"
# API_KEY for team member account
API_KEY = "ea52d02ab1e9ae7c1d495759a67bd95cc947955bb83b376a3a6e96e53f3c255d"

headers = {
    'Content-Type': 'application/json',
    'Authorization': f'Bearer {API_KEY}',
}

# If you're retrieving data, typically it's a GET request
response = requests.get(API_URL, headers=headers)
response_json = response.json()

if response.status_code == 200:
    print("Response:", response.json())
else:
    print("Failed with status code:", response.status_code)
