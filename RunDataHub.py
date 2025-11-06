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
        """Convert JSON activities to DataFrame with enhanced data"""
        if not activities:
            return pd.DataFrame()

        df = pd.json_normalize(activities)
        df['start_date'] = pd.to_datetime(df['start_date'], errors='coerce')

        # Add derived metrics
        if 'distance' in df.columns:
            df['distance_km'] = df['distance'] / 1000
        
        # TIME METRICS - with elapsed time as priority
        if 'elapsed_time' in df.columns:
            df['elapsed_time_min'] = df['elapsed_time'] / 60
        if 'moving_time' in df.columns:
            df['moving_time_min'] = df['moving_time'] / 60
        
        # Calculate efficiency ratio (moving time vs elapsed time)
        if 'elapsed_time' in df.columns and 'moving_time' in df.columns:
            df['efficiency_ratio'] = df['moving_time'] / df['elapsed_time']
        
        if 'average_speed' in df.columns:
            df['average_speed_kmh'] = df['average_speed'] * 3.6
        if 'max_speed' in df.columns:
            df['max_speed_kmh'] = df['max_speed'] * 3.6
        
        # Pace based on elapsed time (more realistic for total activity time)
        if 'distance' in df.columns and 'elapsed_time' in df.columns:
            df['pace_min_per_km_elapsed'] = (df['elapsed_time'] / 60) / (df['distance'] / 1000)
        
        # Also keep moving pace for comparison
        if 'distance' in df.columns and 'moving_time' in df.columns:
            df['pace_min_per_km_moving'] = (df['moving_time'] / 60) / (df['distance'] / 1000)
        
        # Add date/time breakdown
        df['year'] = df['start_date'].dt.year
        df['month'] = df['start_date'].dt.month
        df['day_of_week'] = df['start_date'].dt.day_name()
        df['hour'] = df['start_date'].dt.hour

        #  Heart rate metrics
        if 'average_heartrate' in df.columns:
            df['has_hr_data'] = df['average_heartrate'].notna()
        
        #  Elevation data
        if 'total_elevation_gain' in df.columns:
            df['elevation_gain_km'] = df['total_elevation_gain'] / 1000
        
        #  Segment efforts count
        if 'segment_efforts' in df.columns:
            df['segment_efforts_count'] = df['segment_efforts'].apply(
                lambda x: len(x) if isinstance(x, list) else 0
            )
        
        #  Social engagement metrics
        engagement_columns = ['kudos_count', 'comment_count', 'athlete_count', 'photo_count']
        for col in engagement_columns:
            if col in df.columns:
                df[col] = df[col].fillna(0).astype(int)
        
        #  Achievement metrics
        achievement_columns = ['achievement_count', 'pr_count']
        for col in achievement_columns:
            if col in df.columns:
                df[col] = df[col].fillna(0).astype(int)
        
        #  Training metrics
        if 'suffer_score' in df.columns:
            df['suffer_score'] = df['suffer_score'].fillna(0).astype(int)
        
        #  Workout type classification
        if 'workout_type' in df.columns:
            # Map workout_type codes to descriptive names
            workout_type_map = {
                0: 'Default',
                1: 'Race',
                2: 'Long Run',
                3: 'Workout'
            }
            df['workout_type_name'] = df['workout_type'].map(workout_type_map).fillna('Default')
        
        #  Manual activity flag
        if 'manual' in df.columns:
            df['is_manual'] = df['manual'].fillna(False)
        
        #  Device info (simplified)
        if 'device_name' in df.columns:
            df['device_name'] = df['device_name'].fillna('Unknown')
        
        #  Temperature data
        if 'average_temp' in df.columns:
            df['temperature_c'] = df['average_temp']
        
        #  Running cadence (if available)
        if 'average_cadence' in df.columns:
            df['cadence_rpm'] = df['average_cadence']
        
        #  Location data (city level only)
        location_columns = ['location_city', 'location_state', 'location_country']
        for col in location_columns:
            if col in df.columns:
                df[col] = df[col].fillna('Unknown')

        return df

    def get_activity_statistics(self):
        """Generate summary statistics from the loaded activities"""
        if self.activities_df is None or self.activities_df.empty:
            print("No activities loaded. Run load_activities() first.")
            return {}
        
        stats = {
            'total_activities': len(self.activities_df),
            'total_distance_km': self.activities_df['distance_km'].sum() if 'distance_km' in self.activities_df else 0,
            'total_elapsed_time_hrs': self.activities_df['elapsed_time_min'].sum() / 60 if 'elapsed_time_min' in self.activities_df else 0,
            'total_moving_time_hrs': self.activities_df['moving_time_min'].sum() / 60 if 'moving_time_min' in self.activities_df else 0,
            'avg_efficiency_ratio': self.activities_df['efficiency_ratio'].mean() if 'efficiency_ratio' in self.activities_df else 0,
            'activity_types': self.activities_df['type'].value_counts().to_dict(),
            'total_kudos': self.activities_df['kudos_count'].sum() if 'kudos_count' in self.activities_df else 0,
            'activities_with_hr': self.activities_df['has_hr_data'].sum() if 'has_hr_data' in self.activities_df else 0,
            'total_elevation_gain_km': self.activities_df['elevation_gain_km'].sum() if 'elevation_gain_km' in self.activities_df else 0,
            'total_segment_efforts': self.activities_df['segment_efforts_count'].sum() if 'segment_efforts_count' in self.activities_df else 0,
        }
        
        return stats

    def save_to_csv(self, output_dir="."):
        """Save the DataFrame to a dated CSV file"""
        if self.activities_df is None or self.activities_df.empty:
            print("No data to save.")
            return None

        os.makedirs(output_dir, exist_ok=True)
        current_date = datetime.now().strftime("%Y-%m-%d")
        filename = os.path.join(output_dir, f"Strava_Activities_{current_date}.csv")
        self.activities_df.to_csv(filename, index=False)
        print(f" Saved {len(self.activities_df)} activities to {filename}")
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
        
        # Display enhanced statistics
        stats = analyzer.get_activity_statistics()
        print("\n Activity Statistics:")
        print(f"Total Activities: {stats['total_activities']}")
        print(f"Total Distance: {stats['total_distance_km']:.1f} km")
        print(f"Total Elapsed Time: {stats['total_elapsed_time_hrs']:.1f} hours")
        print(f"Total Moving Time: {stats['total_moving_time_hrs']:.1f} hours")
        print(f"Average Efficiency Ratio: {stats['avg_efficiency_ratio']:.2f}")
        print(f"Total Elevation Gain: {stats['total_elevation_gain_km']:.1f} km")
        print(f"Activities with HR data: {stats['activities_with_hr']}")
        print(f"Total Kudos Received: {stats['total_kudos']}")
        print(f"Total Segment Efforts: {stats['total_segment_efforts']}")
        
        print("\nSample data:")
        sample_cols = ['name', 'type', 'distance_km', 'elapsed_time_min', 'moving_time_min', 'efficiency_ratio', 'start_date']
        available_cols = [col for col in sample_cols if col in df.columns]
        print(df[available_cols].head())


if __name__ == "__main__":
    main()
