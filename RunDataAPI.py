import requests
import webbrowser
import os

def get_strava_tokens():
    """
    Get a fresh Strava access token using your environment variables
    """
    # Get your credentials from environment variables
    client_id = os.getenv("StravaClientID")
    client_secret = os.getenv("StravaClientSecret")
    
    if not client_id or not client_secret:
        print("Error: StravaClientID or StravaClientSecret not found in environment variables")
        return None
    
    print("Strava credentials in environment variables found")
    print(f"Client ID: {client_id}")
    
    #1: Get authorization code
    auth_url = (
        f"https://www.strava.com/oauth/authorize?"
        f"client_id={client_id}"
        f"&response_type=code"
        f"&redirect_uri=http://localhost"
        f"&scope=activity:read_all"
        f"&approval_prompt=force"
    )
    
    print("Opening browser for Strava authorization...")
    print("If browser doesn't open, visit this URL manually:")
    print(auth_url)
    
    webbrowser.open(auth_url)
    
    print("\nAfter authorizing, you'll be redirected to localhost.")
    print("Copy the ENTIRE URL from your browser address bar (it will look like: http://localhost/?code=abc123&scope=read,activity:read_all)")
    print("Paste it below:")
    
    redirect_url = input("Paste the URL here: ").strip()
    
    #Extract the code from the URL
    if 'code=' in redirect_url:
        code = redirect_url.split('code=')[1].split('&')[0]
        print(f"Got authorization code: {code}")
    else:
        print(" Error: Could not find authorization code in URL")
        return None
    
    #2: Exchange code for tokens
    print("\nStep 2: Getting access token...")
    token_url = "https://www.strava.com/oauth/token"
    
    data = {
        'client_id': client_id,
        'client_secret': client_secret,
        'code': code,
        'grant_type': 'authorization_code'
    }
    
    try:
        response = requests.post(token_url, data=data)
        if response.status_code == 200:
            token_data = response.json()
            
            print("\nSuccess! Here are your tokens:")
            print("=" * 50)
            print(f"Access Token: {token_data['access_token']}")
            print(f"Refresh Token: {token_data['refresh_token']}")
            print(f"Expires At: {datetime.fromtimestamp(token_data['expires_at'])}")
            print(f"Athlete: {token_data['athlete']['firstname']} {token_data['athlete']['lastname']}")
            print("=" * 50)
            
            #Save to environment variable for current session
            os.environ['STRAVA_ACCESS_TOKEN'] = token_data['access_token']
            print(f"\nAccess token saved to environment variable: STRAVA_ACCESS_TOKEN")
            
            return token_data
        else:
            print(f"Error getting access token: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"Request failed: {e}")
        return None

if __name__ == "__main__":
    from datetime import datetime
    get_strava_tokens()
