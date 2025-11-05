import requests
import webbrowser

#credentials - get these from https://www.strava.com/settings/api
CLIENT_ID = os.getenv("StravaClientID")
CLIENT_SECRET = os.getenv("StravaClientSecret")

def get_authorization_code():
    """Step 1: Get the authorization code from Strava"""
    auth_url = (
        f"https://www.strava.com/oauth/authorize?"
        f"client_id={CLIENT_ID}"
        f"&response_type=code"
        f"&redirect_uri=http://localhost"
        f"&scope=activity:read_all"
        f"&approval_prompt=force"
    )
    
    print("Opening browser for Strava authorization...")
    print("If browser doesn't open, visit this URL manually:")
    print(auth_url)
    print("\nAfter authorizing, you'll be redirected to localhost.")
    print("Copy the ENTIRE URL from your browser address bar and paste it below.")
    
    webbrowser.open(auth_url)
    
    #URL from user
    redirect_url = input("\nPaste the redirect URL here: ")
    
    #get code from URL
    if 'code=' in redirect_url:
        code = redirect_url.split('code=')[1].split('&')[0]
        return code
    else:
        print("Error: Could not find authorization code in URL")
        return None

def get_access_token(authorization_code):
    """Step 2: Exchange authorization code for access token"""
    token_url = "https://www.strava.com/oauth/token"
    
    data = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'code': authorization_code,
        'grant_type': 'authorization_code'
    }
    
    response = requests.post(token_url, data=data)
    
    if response.status_code == 200:
        token_data = response.json()
        print("\nSuccess! Here are your tokens:")
        print(f"Access Token: {token_data['access_token']}")
        print(f"Refresh Token: {token_data['refresh_token']}")
        print(f"Expires At: {token_data['expires_at']}")
        
        return token_data
    else:
        print(f"Error getting access token: {response.status_code}")
        print(response.text)
        return None

if __name__ == "__main__":
    print("Strava Token Generator")
    print("=" * 50)
    
    # Replace these with your actual credentials
    if CLIENT_ID == None:
        print("\nPlease update CLIENT_ID and CLIENT_SECRET in your stsyem variables")
        print("Get them from: https://www.strava.com/settings/api")
    else:
        auth_code = get_authorization_code()
        if auth_code:
            token_data = get_access_token(auth_code)
            if token_data:
                print(f"\nSuccess! Use this access token in the main script:")
                print(f"analyzer = StravaAnalyzer(access_token='{token_data['access_token']}')")
