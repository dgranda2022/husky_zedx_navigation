# calculate_rmse.py
import pandas as pd
import numpy as np
from scipy.interpolate import interp1d

# --- Configuration ---
ZED_PATH_FILE = 'zed_path.csv'
OPTITRACK_PATH_FILE = 'optitrack_path.csv'

def align_path(df):
    """
    Aligns a trajectory to start at (0,0) with an initial heading of 0 radians.
    """
    if df.empty:
        return df, 0, 0, 0
    
    x_offset = df['x'].iloc[0]
    y_offset = df['y'].iloc[0]
    theta_offset = df['theta'].iloc[0]
    
    # Translate
    df['x_trans'] = df['x'] - x_offset
    df['y_trans'] = df['y'] - y_offset
    
    # Rotate
    cos_theta = np.cos(-theta_offset)
    sin_theta = np.sin(-theta_offset)
    df['x_aligned'] = df['x_trans'] * cos_theta - df['y_trans'] * sin_theta
    df['y_aligned'] = df['x_trans'] * sin_theta + df['y_trans'] * cos_theta
    
    # Also align the heading values
    df['theta_aligned'] = np.unwrap(df['theta'] - theta_offset)
    
    return df

def calculate_rmse():
    """
    Loads, aligns, and calculates the RMSE of the Absolute Trajectory Error (ATE)
    between the ZED (perceived) and OptiTrack (ground truth) paths.
    """
    try:
        zed_df = pd.read_csv(ZED_PATH_FILE)
        optitrack_df = pd.read_csv(OPTITRACK_PATH_FILE)
        print(f"Loaded {len(zed_df)} ZED points and {len(optitrack_df)} OptiTrack points.")
    except FileNotFoundError as e:
        print(f"Error: Could not find file '{e.filename}'.")
        return

    # --- 1. Align both trajectories to their own start point ---
    zed_aligned_df = align_path(zed_df.copy())
    optitrack_aligned_df = align_path(optitrack_df.copy())
    
    # --- 2. Synchronize Timestamps ---
    # We need to find the overlapping time range between the two recordings.
    start_time = max(zed_aligned_df['timestamp'].min(), optitrack_aligned_df['timestamp'].min())
    end_time = min(zed_aligned_df['timestamp'].max(), optitrack_aligned_df['timestamp'].max())
    
    # Filter both dataframes to only include the overlapping time
    zed_sync_df = zed_aligned_df[(zed_aligned_df['timestamp'] >= start_time) & (zed_aligned_df['timestamp'] <= end_time)]
    optitrack_sync_df = optitrack_aligned_df[(optitrack_aligned_df['timestamp'] >= start_time) & (optitrack_aligned_df['timestamp'] <= end_time)]

    if zed_sync_df.empty or optitrack_sync_df.empty:
        print("Error: No overlapping timestamps found between the two files.")
        return

    # --- 3. Interpolate Ground Truth to Match Perceived Timestamps ---
    # This creates a ground truth point for every single ZED point.
    # We create interpolation functions for the OptiTrack data.
    f_x = interp1d(optitrack_sync_df['timestamp'], optitrack_sync_df['x_aligned'], kind='linear', fill_value="extrapolate")
    f_y = interp1d(optitrack_sync_df['timestamp'], optitrack_sync_df['y_aligned'], kind='linear', fill_value="extrapolate")
    f_theta = interp1d(optitrack_sync_df['timestamp'], optitrack_sync_df['theta_aligned'], kind='linear', fill_value="extrapolate")

    # Use these functions to generate the interpolated ground truth points
    interpolated_optitrack_x = f_x(zed_sync_df['timestamp'])
    interpolated_optitrack_y = f_y(zed_sync_df['timestamp'])
    interpolated_optitrack_theta = f_theta(zed_sync_df['timestamp'])
    
    print(f"Synchronized and interpolated data to {len(zed_sync_df)} matching points.")

    # --- 4. Calculate Errors ---
    # Position Error (Absolute Trajectory Error)
    error_x = interpolated_optitrack_x - zed_sync_df['x_aligned']
    error_y = interpolated_optitrack_y - zed_sync_df['y_aligned']
    position_errors = np.sqrt(error_x**2 + error_y**2)

    # Heading Error
    heading_errors = np.unwrap(interpolated_optitrack_theta - zed_sync_df['theta_aligned'])

    # --- 5. Calculate Root Mean Squared Error (RMSE) ---
    position_rmse = np.sqrt(np.mean(position_errors**2))
    heading_rmse_rad = np.sqrt(np.mean(heading_errors**2))
    heading_rmse_deg = np.rad2deg(heading_rmse_rad)

    # --- 6. Print Results ---
    print("\n--- Trajectory Error Analysis ---")
    print(f"Absolute Trajectory Error (ATE) for Position:")
    print(f"  RMSE: {position_rmse:.4f} meters")
    print(f"  Mean Error: {np.mean(position_errors):.4f} meters")
    print(f"  Max Error: {np.max(position_errors):.4f} meters")
    
    print(f"\nAbsolute Trajectory Error (ATE) for Heading:")
    print(f"  RMSE: {heading_rmse_rad:.4f} radians ({heading_rmse_deg:.2f} degrees)")
    print(f"  Mean Error: {np.mean(np.abs(heading_errors)):.4f} radians ({np.rad2deg(np.mean(np.abs(heading_errors))):.2f} degrees)")
    print(f"  Max Error: {np.max(np.abs(heading_errors)):.4f} radians ({np.rad2deg(np.max(np.abs(heading_errors))):.2f} degrees)")
    print("---------------------------------")

if __name__ == '__main__':
    calculate_rmse()
