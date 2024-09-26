import requests

def make_api_request():
    # Replace with your actual API URL
    url = 'https://104.167.17.2:47919/sdapi/v1/txt2img'

    # The value of $OPEN_BUTTON_TOKEN is actually the response of jupyter_token from the VastAI API response
    token = 'b88a80e7d073c5c848f6f4d6d1e35491be9f89e2dc5fbf50e356e46b0c3a4329'
    
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}',
    }
    
    payload = {
        "prompt": "An island with a huge volcano eruption",
        "steps": 50,
        "width": 512,
        "height": 512
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, verify=False)
        
        # Check if the response is JSON
        try:
            response_data = response.json()
        except ValueError:
            print("Response is not in JSON format.")
            print("Response text:", response.text)
            return

        # Check the status code
        if response.status_code == 200:
            return response_data
        else:
            print(f"Request failed with status code {response.status_code}")
            print("Response:", response_data)

    except requests.ConnectionError as e:
        print(f"Request failed: {e}")
    except requests.RequestException as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    x = make_api_request()
    for k, v in x.items():
        print(k)
    print(x["images"][0])
