import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from datetime import datetime, timedelta

def format_pace_min_sec(pace_decimal):
    """
    Convert pace from decimal minutes to minutes:seconds format
    """
    if pd.isna(pace_decimal):
        return "N/A"
    
    minutes = int(pace_decimal)
    seconds = int((pace_decimal - minutes) * 60)
    return f"{minutes}:{seconds:02d}"

def convert_elevation_km_to_m(elevation_km):
    """
    Convert elevation from kilometers to meters
    """
    if pd.isna(elevation_km):
        return 0
    return elevation_km * 1000

def analyze_recent_running_insights(df, sport_type_filter='Run', weeks=3):
    """
    Analyze running data from the last 3 weeks only with pace in min:sec format
    Also corrected elevation (km to m)
    """
    
    df['start_date'] = pd.to_datetime(df['start_date'])
    cutoff_date = df['start_date'].max() - timedelta(weeks=weeks)
    recent_runs = df[(df['sport_type'] == sport_type_filter) & 
                     (df['start_date'] >= cutoff_date)].copy()
    
    if recent_runs.empty:
        print(f"No {sport_type_filter} activities found in the last {weeks} weeks!")
        return
    
    recent_runs['elevation_gain_m'] = recent_runs['elevation_gain_km'].apply(convert_elevation_km_to_m)
    
    print("=" * 60)
    print(f"LAST {weeks} WEEKS RUNNING ANALYSIS")
    print(f"Running Activities: {len(recent_runs)}")
    print(f"Date Range: {recent_runs['start_date'].min().strftime('%Y-%m-%d')} to {recent_runs['start_date'].max().strftime('%Y-%m-%d')}")
    print("=" * 60)
    
    recent_runs['week_number'] = recent_runs['start_date'].dt.isocalendar().week
    recent_runs['week_label'] = 'Week ' + recent_runs['week_number'].astype(str)
    
    print("\nWEEKLY summary stats:")
    for week_num, week_data in recent_runs.groupby('week_number'):
        week_runs = week_data
        avg_pace = week_runs['pace_min_per_km_moving'].mean()
        total_elevation_m = week_runs['elevation_gain_m'].sum()
        
        print(f"Week {week_num} ({week_runs['start_date'].min().strftime('%m/%d')} - {week_runs['start_date'].max().strftime('%m/%d')}):")
        print(f"  Runs: {len(week_runs)}")
        print(f"  Total distance: {week_runs['distance_km'].sum():.1f} km")
        print(f"  Average pace: {format_pace_min_sec(avg_pace)} min/km")
        print(f"  Elevation gain: {total_elevation_m:.0f} m")
    
    print("\nRECENT TRENDS:")
    if len(recent_runs) >= 2:
        first_half = recent_runs.iloc[:len(recent_runs)//2]
        second_half = recent_runs.iloc[len(recent_runs)//2:]
        
        pace_trend = second_half['pace_min_per_km_moving'].mean() - first_half['pace_min_per_km_moving'].mean()
        distance_trend = second_half['distance_km'].mean() - first_half['distance_km'].mean()
        elevation_trend = second_half['elevation_gain_m'].mean() - first_half['elevation_gain_m'].mean()
        
        trend_direction = "improving" if pace_trend < 0 else "slowing"
        print(f"Pace trend: {format_pace_min_sec(abs(pace_trend))} min/km ({trend_direction})")
        print(f"Distance trend: {distance_trend:+.2f} km per run")
        print(f"Elevation trend: {elevation_trend:+.0f} m per run")
    
    print("\nCURRENT FITNESS SNAPSHOT:")
    current_avg_pace = recent_runs['pace_min_per_km_moving'].mean()
    total_elevation_m = recent_runs['elevation_gain_m'].sum()
    
    print(f"Average weekly distance: {recent_runs['distance_km'].sum() / weeks:.1f} km")
    print(f"Average runs per week: {len(recent_runs) / weeks:.1f}")
    print(f"Current average pace: {format_pace_min_sec(current_avg_pace)} min/km")
    print(f"Longest recent run: {recent_runs['distance_km'].max():.1f} km")
    print(f"Total elevation gain: {total_elevation_m:.0f} m")
    print(f"Average elevation per run: {recent_runs['elevation_gain_m'].mean():.0f} m")
    
    print("\nBEST RECENT PERFORMANCES:")
    if len(recent_runs) > 0:
        best_pace_run = recent_runs.loc[recent_runs['pace_min_per_km_moving'].idxmin()]
        longest_run = recent_runs.loc[recent_runs['distance_km'].idxmax()]
        most_elevation_run = recent_runs.loc[recent_runs['elevation_gain_m'].idxmax()]
        
        print(f"Fastest run: {format_pace_min_sec(best_pace_run['pace_min_per_km_moving'])} min/km ({best_pace_run['distance_km']:.1f} km)")
        print(f"Longest run: {longest_run['distance_km']:.1f} km on {longest_run['start_date'].strftime('%m/%d')}")
        print(f"Most elevation: {most_elevation_run['elevation_gain_m']:.0f} m on {most_elevation_run['start_date'].strftime('%m/%d')} ({most_elevation_run['distance_km']:.1f} km)")
    
    print("\nPACE DISTRIBUTION:")
    pace_stats = recent_runs['pace_min_per_km_moving'].describe()
    print(f"Fastest: {format_pace_min_sec(pace_stats['min'])} min/km")
    print(f"Slowest: {format_pace_min_sec(pace_stats['max'])} min/km")
    print(f"Median: {format_pace_min_sec(pace_stats['50%'])} min/km")
    
    print("\nELEVATION ANALYSIS:")
    elevation_stats = recent_runs['elevation_gain_m'].describe()
    print(f"Highest elevation run: {elevation_stats['max']:.0f} m")
    print(f"Average elevation per run: {elevation_stats['mean']:.0f} m")
    print(f"Total elevation: {recent_runs['elevation_gain_m'].sum():.0f} m")
    
    print("\nRECENT CONSISTENCY:")
    days_between_runs = recent_runs['start_date'].sort_values().diff().dt.days.dropna()
    avg_days_between = days_between_runs.mean() if not days_between_runs.empty else 0
    
    print(f"Average days between runs: {avg_days_between:.1f}")
    print(f"Running frequency: {len(recent_runs) / (weeks * 7):.2f} runs per day")
    
    if avg_days_between <= 2:
        print("Excellent consistency!")
    elif avg_days_between <= 4:
        print("Good consistency, could be more regular")
    else:
        print("Consider running more frequently")
    
    print("\nRECOMMENDATIONS FOR NEXT WEEK:")
    avg_weekly_distance = recent_runs['distance_km'].sum() / weeks
    avg_runs_per_week = len(recent_runs) / weeks
    avg_weekly_elevation = recent_runs['elevation_gain_m'].sum() / weeks
    
    if avg_weekly_distance < 20:
        print(f"Maintain or gradually increase to {avg_weekly_distance + 5:.0f} km/week")
    elif avg_weekly_distance < 40:
        print(f"Good volume! Consider adding speed work")
    else:
        print(f"High volume! Ensure proper recovery")
    
    if avg_runs_per_week < 3:
        print(f"Aim for 3-4 runs per week")
    elif avg_runs_per_week < 5:
        print(f"Good frequency! Maintain consistency")
    else:
        print(f"Consider adding cross-training or rest days")
    
    if avg_weekly_elevation < 500:
        print(f"Consider adding some hill work ({avg_weekly_elevation:.0f}m/week)")
    elif avg_weekly_elevation > 1500:
        print(f"Good hill training! ({avg_weekly_elevation:.0f}m/week)")
    
    pace_std = recent_runs['pace_min_per_km_moving'].std()
    if pace_std < 0.5:
        print("Add pace variety: try intervals or tempo runs")
    else:
        print("Good pace variety!")
    
    return recent_runs

def create_recent_running_visualizations(recent_runs, weeks=3):
    """Create visualizations for the last 3 weeks of running data with corrected elevation"""
    
    if recent_runs.empty:
        print("No data to visualize!")
        return
    
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    fig.suptitle(f'Running Analysis - Last {weeks} Weeks', fontsize=16, fontweight='bold')
    
    weekly_totals = recent_runs.groupby('week_label')['distance_km'].sum()
    axes[0,0].bar(weekly_totals.index, weekly_totals.values, color='skyblue', alpha=0.7)
    axes[0,0].set_title('Weekly Distance')
    axes[0,0].set_ylabel('Distance (km)')
    axes[0,0].tick_params(axis='x', rotation=45)
    
    for i, v in enumerate(weekly_totals.values):
        axes[0,0].text(i, v + 0.1, f'{v:.1f}km', ha='center', va='bottom')
    
    axes[0,1].plot(recent_runs['start_date'], recent_runs['pace_min_per_km_moving'], 
                   'o-', linewidth=2, markersize=8, alpha=0.7)
    axes[0,1].set_title('Pace Trend (lower = faster)')
    axes[0,1].set_ylabel('Pace (min/km)')
    axes[0,1].tick_params(axis='x', rotation=45)
    
    def pace_formatter(x, pos):
        minutes = int(x)
        seconds = int((x - minutes) * 60)
        return f"{minutes}:{seconds:02d}"
    
    axes[0,1].yaxis.set_major_formatter(plt.FuncFormatter(pace_formatter))
    axes[0,1].invert_yaxis()
    
    weekly_elevation = recent_runs.groupby('week_label')['elevation_gain_m'].sum()
    axes[1,0].bar(weekly_elevation.index, weekly_elevation.values, color='orange', alpha=0.7)
    axes[1,0].set_title('Weekly Elevation Gain')
    axes[1,0].set_ylabel('Elevation (m)')
    axes[1,0].tick_params(axis='x', rotation=45)
    
    for i, v in enumerate(weekly_elevation.values):
        axes[1,0].text(i, v + 5, f'{v:.0f}m', ha='center', va='bottom')
    
    scatter = axes[1,1].scatter(recent_runs['distance_km'], 
                               recent_runs['pace_min_per_km_moving'],
                               c=recent_runs['elevation_gain_m'],
                               cmap='viridis', alpha=0.7, s=60)
    axes[1,1].set_title('Distance vs Pace (color = elevation)')
    axes[1,1].set_xlabel('Distance (km)')
    axes[1,1].set_ylabel('Pace (min/km)')
    axes[1,1].yaxis.set_major_formatter(plt.FuncFormatter(pace_formatter))
    axes[1,1].invert_yaxis()
    plt.colorbar(scatter, ax=axes[1,1], label='Elevation Gain (m)')
    
    plt.tight_layout()
    plt.show()
    
    print(f"\nWEEKLY SUMMARY TABLE:")
    print(f"{'Week':<10} {'Runs':<6} {'Total km':<8} {'Avg km':<8} {'Avg Pace':<10} {'Elevation':<10}")
    print("-" * 60)
    for week_label, week_data in recent_runs.groupby('week_label'):
        runs_count = len(week_data)
        total_km = week_data['distance_km'].sum()
        avg_km = week_data['distance_km'].mean()
        avg_pace = week_data['pace_min_per_km_moving'].mean()
        elevation = week_data['elevation_gain_m'].sum()
        
        print(f"{week_label:<10} {runs_count:<6} {total_km:<8.1f} {avg_km:<8.1f} {format_pace_min_sec(avg_pace):<10} {elevation:<10.0f}")

def show_recent_run_details(recent_runs):
    """Show details of individual runs with formatted pace and corrected elevation"""
    if recent_runs.empty:
        return
    
    print(f"\nINDIVIDUAL RUN DETAILS (Last {len(recent_runs)} runs):")
    print(f"{'Date':<12} {'Distance':<10} {'Pace':<10} {'Elevation':<10} {'Time':<8}")
    print("-" * 60)
    
    for _, run in recent_runs.sort_values('start_date').iterrows():
        date_str = run['start_date'].strftime('%m/%d')
        distance = run['distance_km']
        pace = format_pace_min_sec(run['pace_min_per_km_moving'])
        elevation = run['elevation_gain_m']
        time_min = run['moving_time_min']
        
        hours = int(time_min // 60)
        minutes = int(time_min % 60)
        time_str = f"{hours}:{minutes:02d}" if hours > 0 else f"{minutes}min"
        
        print(f"{date_str:<12} {distance:<10.1f} {pace:<10} {elevation:<10.0f} {time_str:<8}")

def complete_recent_analysis(df, weeks=3):
    """Run complete recent analysis with visualizations, formatted pace, and corrected elevation"""
    recent_data = analyze_recent_running_insights(df, weeks=weeks)
    if recent_data is not None and not recent_data.empty:
        create_recent_running_visualizations(recent_data, weeks=weeks)
        show_recent_run_details(recent_data)
    return recent_data
