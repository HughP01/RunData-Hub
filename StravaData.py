import pandas as pd
import requests
import os
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

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
    
    def load_activities(self, pages=3):
        """Load Strava activities"""
        # Test connection first
        connected, message = self.test_connection()
        if not connected:
            print(f"Failure: {message}")
            return None
        
        print(f"Success:{message}")
        print("Loading Strava activities...")
        
        all_activities = []
        for page in range(1, pages + 1):
            print(f"Loading page {page}...", end=" ")
            activities = self._get_activities_page(page)
            if activities:
                all_activities.extend(activities)
                print(f"Found {len(activities)} activities")
            else:
                print("No more activities or error occurred")
                break
                
        self.activities_df = self._activities_to_dataframe(all_activities)
        
        if not self.activities_df.empty:
            print(f"Successfully loaded {len(self.activities_df)} activities!")
            return self.activities_df
        else:
            print("No activities loaded")
            return None
    
    def _get_activities_page(self, page=1, per_page=30):
        """Fetch one page of activities"""
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
    
    def _activities_to_dataframe(self, activities):
        """Convert JSON activities to DataFrame"""
        if not activities:
            return pd.DataFrame()
            
        activity_data = []
        for activity in activities:
            info = {
                'id': activity['id'],
                'name': activity['name'],
                'type': activity['type'],
                'distance_km': activity['distance'] / 1000,
                'moving_time_min': activity['moving_time'] / 60,
                'elevation_gain': activity['total_elevation_gain'],
                'start_date': pd.to_datetime(activity['start_date']),
                'average_speed_kmh': (activity.get('average_speed', 0) * 3.6),
                'max_speed_kmh': (activity.get('max_speed', 0) * 3.6),
                'average_heartrate': activity.get('average_heartrate'),
                'max_heartrate': activity.get('max_heartrate'),
                'suffer_score': activity.get('suffer_score'),
                'kudos_count': activity.get('kudos_count', 0),
            }
            
            if info['distance_km'] > 0:
                info['pace_min_per_km'] = info['moving_time_min'] / info['distance_km']
            
            activity_data.append(info)
        
        df = pd.DataFrame(activity_data)
        
        if not df.empty:
            df['year'] = df['start_date'].dt.year
            df['month'] = df['start_date'].dt.month
            df['day_of_week'] = df['start_date'].dt.day_name()
            df['hour'] = df['start_date'].dt.hour
            
        return df

    def show_summary(self):
        """Show summary statistics"""
        if self.activities_df is None or self.activities_df.empty:
            print("No activities loaded. Call load_activities() first.")
            return
            
        df = self.activities_df
        
        print("=" * 50)
        print("STRAVA ACTIVITY SUMMARY")
        print("=" * 50)
        print(f"Total activities: {len(df)}")
        print(f"Date range: {df['start_date'].min().date()} to {df['start_date'].max().date()}")
        print(f"Total distance: {df['distance_km'].sum():.1f} km")
        print(f"Total moving time: {df['moving_time_min'].sum():.1f} minutes ({df['moving_time_min'].sum()/60:.1f} hours)")
        print(f"Total elevation gain: {df['elevation_gain'].sum():.0f} m")
        
        print("\nActivities by type:")
        for activity_type in df['type'].unique():
            type_data = df[df['type'] == activity_type]
            count = len(type_data)
            distance = type_data['distance_km'].sum()
            print(f"  {activity_type:12} {count:3} activities, {distance:6.1f} km")

    def plot_activities(self):
        """Create some basic plots"""
        if self.activities_df is None or self.activities_df.empty:
            print("No data to plot!")
            return
            
        df = self.activities_df
        
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        
        # Plot 1: Distance over time
        for activity_type in df['type'].unique():
            type_data = df[df['type'] == activity_type]
            axes[0,0].scatter(type_data['start_date'], type_data['distance_km'], 
                            label=activity_type, alpha=0.7)
        axes[0,0].set_title('Distance Over Time')
        axes[0,0].set_ylabel('Distance (km)')
        axes[0,0].legend()
        axes[0,0].tick_params(axis='x', rotation=45)
        
        # Plot 2: Activity type distribution
        df['type'].value_counts().plot(kind='pie', ax=axes[0,1], autopct='%1.1f%%')
        axes[0,1].set_title('Activity Types')
        axes[0,1].set_ylabel('')
        
        # Plot 3: Weekly distance
        weekly_distance = df.groupby(pd.Grouper(key='start_date', freq='W'))['distance_km'].sum()
        axes[1,0].plot(weekly_distance.index, weekly_distance.values, marker='o')
        axes[1,0].set_title('Weekly Distance')
        axes[1,0].set_ylabel('Distance (km)')
        axes[1,0].tick_params(axis='x', rotation=45)
        
        # Plot 4: Time of day
        df['hour'].value_counts().sort_index().plot(kind='bar', ax=axes[1,1])
        axes[1,1].set_title('Activity Start Time')
        axes[1,1].set_xlabel('Hour of Day')
        
        plt.tight_layout()
        plt.show()

def main():
    """Main function to run the analyzer"""
    print("Strava Data Analyzer")
    print("=" * 30)
    
    # Check if we have an access token
    if not os.getenv('STRAVA_ACCESS_TOKEN'):
        print("No access token found. Please run strava_token_helper.py first to get your token.")
        return
    
    # Initialize and load data
    analyzer = StravaAnalyzer()
    
    # Load activities
    df = analyzer.load_activities(pages=3)
    
    if df is not None:
        # Show summary
        analyzer.show_summary()
        
        # Show some data
        print("\nRecent activities:")
        print(df[['name', 'type', 'distance_km', 'start_date']].head(5))
        
        # Create plots
        print("\nCreating plots...")
        analyzer.plot_activities()
        
        # The DataFrame is now available for your own analysis!
        print(f"\nYou can access data with: analyzer.activities_df")
        print(f"   Total rows: {len(analyzer.activities_df)}")
        print(f"   Columns: {list(analyzer.activities_df.columns)}")

if __name__ == "__main__":
    main()
