import pandas as pd
import requests
import os
from datetime import datetime
import time

class StravaAnalyzer:
    def __init__(self, access_token=None):
        """
        Initialize Strava analyzer
        
        Args:
            access_token: Your Strava access token. If None, uses STRAVA_ACCESS_TOKEN env var
        """
        self.access_token = access_token or os.getenv('STRAVA_ACCESS_TOKEN')
        self.activities_df = None
        
    def test_connection(self):
        """Test if we can connect to Strava API"""
        if not self.access_token:
            return False, "No access token provided. Run strava_token_helper.py first."
            
        headers = {'Authorization': f'Bearer {self.access_token}'}
        url = "https://www.strava.com/api/v3/athlete"
        
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                athlete_data = response.json()
                name = f"{athlete_data.get('firstname', '')} {athlete_data.get('lastname', '')}"
                return True, f"Connected as {name}"
            else:
                return False, f"API Error {response.status_code}: Check if token is valid"
        except Exception as e:
            return False, f"Connection failed: {e}"
    
    def load_activities(self, pages=3, detailed=True, delay=0.2):
        """Load Strava activities, optionally fetching detailed info for each"""
        connected, message = self.test_connection()
        if not connected:
            print(f"Failure: {message}")
            return None
        
        print(f"Success: {message}")
        print("Loading Strava activities...")

        all_activities = []
        for page in range(1, pages + 1):
            print(f"Fetching page {page}...", end=" ")
            activities = self._get_activities_page(page)
            if activities:
                print(f"found {len(activities)} items")
                if detailed:
                    for activity in activities:
                        details = self._get_activity_details(activity["id"])
                        if details:
                            all_activities.append(details)
                        time.sleep(delay)  # avoid hitting rate limits
                else:
                    all_activities.extend(activities)
            else:
                print("No more activities or error occurred.")
                break

        self.activities_df = self._activities_to_dataframe(all_activities)
        
        if not self.activities_df.empty:
            print(f"Successfully loaded {len(self.activities_df)} activities!")
            return self.activities_df
        else:
            print("No activities loaded.")
            return None

    def _get_activities_page(self, page=1, per_page=30):
        """Fetch one page of summary activities"""
        headers = {'Authorization': f'Bearer {self.access_token}'}
        url = "https://www.strava.com/api/v3/athlete/activities"
        params = {'per_page': per_page, 'page': page}
        try:
            response = requests.get(url, headers=headers, params=params)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Error {response.status_code}")
                return None
        except Exception as e:
            print(f"Request failed: {e}")
            return None

    def _get_activity_details(self, activity_id):
        """Fetch full detail for a single activity"""
        headers = {'Authorization': f'Bearer {self.access_token}'}
        url = f"https://www.strava.com/api/v3/activities/{activity_id}"
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Error fetching {activity_id}: {response.status_code}")
                return None
        except Exception as e:
            print(f"Failed fetching {activity_id}: {e}")
            return None

    def _activities_to_dataframe(self, activities):
        """Convert JSON activities to DataFrame"""
        if not activities:
            return pd.DataFrame()

        df = pd.json_normalize(activities)
        df['start_date'] = pd.to_datetime(df['start_date'], errors='coerce')

        # Add derived metrics
        if 'distance' in df.columns:
            df['distance_km'] = df['distance'] / 1000
        if 'moving_time' in df.columns:
            df['moving_time_min'] = df['moving_time'] / 60
        if 'average_speed' in df.columns:
            df['average_speed_kmh'] = df['average_speed'] * 3.6
        if 'max_speed' in df.columns:
            df['max_speed_kmh'] = df['max_speed'] * 3.6
        if 'distance' in df.columns and 'moving_time' in df.columns:
            df['pace_min_per_km'] = (df['moving_time'] / 60) / (df['distance'] / 1000)
        
        # Add date/time breakdown
        df['year'] = df['start_date'].dt.year
        df['month'] = df['start_date'].dt.month
        df['day_of_week'] = df['start_date'].dt.day_name()
        df['hour'] = df['start_date'].dt.hour

        return df

    def save_to_csv(self, output_dir="."):
        """Save the DataFrame to a dated CSV file"""
        if self.activities_df is None or self.activities_df.empty:
            print("No data to save.")
            return None

        os.makedirs(output_dir, exist_ok=True)
        current_date = datetime.now().strftime("%Y-%m-%d")
        filename = os.path.join(output_dir, f"Strava_Activities_{current_date}.csv")
        self.activities_df.to_csv(filename, index=False)
        print(f"Saved {len(self.activities_df)} activities to {filename}")
        print(f"Columns: {len(self.activities_df.columns)} total")
        return filename


def main():
    print("Strava Data Analyzer")
    print("=" * 30)

    if not os.getenv('STRAVA_ACCESS_TOKEN'):
        print("No access token found. Please run strava_token_helper.py first.")
        return

    analyzer = StravaAnalyzer()

    df = analyzer.load_activities(pages=3, detailed=True)
    if df is not None:
        analyzer.save_to_csv()
        print("\nSample data:")
        print(df[['name', 'type', 'distance_km', 'start_date']].head())


if __name__ == "__main__":
    main()
