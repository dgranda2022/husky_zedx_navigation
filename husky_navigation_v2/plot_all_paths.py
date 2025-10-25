# plot_all_paths.py
import pandas as pd # type: ignore
import matplotlib.pyplot as plt
import numpy as np  # Import numpy for trigonometric functions

# --- Configuration ---
WAYPOINTS_FILE = 'waypoints.csv'
ZED_PATH_FILE = 'zed_path.csv'
OPTITRACK_PATH_FILE = 'optitrack_path.csv'

# Manual offset for waypoints on the controller performance plot.
MANUAL_X_OFFSET_WAYPOINTS = 1.36

def align_path(df):
    """
    Aligns a trajectory to start at (0,0) with an initial heading of 0 radians.
    This involves both translation and rotation.
    """
    if df.empty:
        return df
    
    # --- 1. Translation ---
    x_offset = df['x'].iloc[0]
    y_offset = df['y'].iloc[0]
    df['x_translated'] = df['x'] - x_offset
    df['y_translated'] = df['y'] - y_offset
    
    # --- 2. Rotation ---
    theta_offset = df['theta'].iloc[0]
    cos_theta = np.cos(-theta_offset)
    sin_theta = np.sin(-theta_offset)
    
    df['x_aligned'] = df['x_translated'] * cos_theta - df['y_translated'] * sin_theta
    df['y_aligned'] = df['x_translated'] * sin_theta + df['y_translated'] * cos_theta
    
    return df

def plot_all_paths():
    """
    Reads, aligns, and creates three separate plots for analysis:
    1. ZED (Perceived) vs. OptiTrack (Actual) to show localization drift.
    2. Waypoints (Desired) vs. ZED (Perceived) to show controller tracking error.
    3. Waypoints (Desired) vs. OptiTrack (Actual) to show overall system error.
    """
    try:
        # Load all three CSV files
        waypoints_df = pd.read_csv(WAYPOINTS_FILE, header=None, names=['x', 'y', 'theta'])
        zed_path_df = pd.read_csv(ZED_PATH_FILE)
        optitrack_path_df = pd.read_csv(OPTITRACK_PATH_FILE)
        
        print(f"Loaded {len(waypoints_df)} waypoints.")
        print(f"Loaded {len(zed_path_df)} ZED path points.")
        print(f"Loaded {len(optitrack_path_df)} OptiTrack path points.")

    except FileNotFoundError as e:
        print(f"Error: Could not find a file. Make sure '{e.filename}' is in the same directory.")
        return
    except Exception as e:
        print(f"An error occurred while reading the files: {e}")
        return

    # --- Align all paths to a common starting pose (0,0) with 0 heading ---
    waypoints_aligned_df = align_path(waypoints_df.copy())
    zed_aligned_df = align_path(zed_path_df.copy())
    optitrack_aligned_df = align_path(optitrack_path_df.copy())
    print("Aligned all trajectories to a common start pose (0,0) with 0 heading.")

    # --- Apply an additional 90-degree CCW rotation to the ZED path ---
    angle_rad = np.pi / 2
    cos_rot = np.cos(angle_rad)
    sin_rot = np.sin(angle_rad)
    
    x_original_aligned = zed_aligned_df['x_aligned'].copy()
    y_original_aligned = zed_aligned_df['y_aligned'].copy()
    
    zed_aligned_df['x_aligned'] = x_original_aligned * cos_rot - y_original_aligned * sin_rot
    zed_aligned_df['y_aligned'] = x_original_aligned * sin_rot + y_original_aligned * cos_rot
    print("Applied a 90-degree counter-clockwise rotation to the ZED path.")
    
    # --- Plot 1: ZED vs. OptiTrack (Localization Error) ---
    plt.figure(figsize=(10, 10))
    plt.plot(optitrack_aligned_df['x_aligned'].values, optitrack_aligned_df['y_aligned'].values, 
             label='Actual Path (Ground Truth - OptiTrack)', color='blue', linestyle='-', linewidth=2.5)
    plt.plot(zed_aligned_df['x_aligned'].values, zed_aligned_df['y_aligned'].values, 
             label='Perceived Path (ZED VIO)', color='green', linestyle='--', linewidth=2)
    plt.scatter(0, 0, label='Aligned Start', color='cyan', marker='o', s=200, edgecolors='black', zorder=5)
    
    # Draw arrows to indicate final direction
    if len(optitrack_aligned_df) > 1:
        last_pt = optitrack_aligned_df.iloc[-1]
        prev_pt = optitrack_aligned_df.iloc[-2]
        plt.arrow(prev_pt['x_aligned'], prev_pt['y_aligned'], 
                  last_pt['x_aligned'] - prev_pt['x_aligned'], 
                  last_pt['y_aligned'] - prev_pt['y_aligned'],
                  head_width=0.1, head_length=0.15, fc='blue', ec='blue', zorder=10)
    if len(zed_aligned_df) > 1:
        last_pt = zed_aligned_df.iloc[-1]
        prev_pt = zed_aligned_df.iloc[-2]
        plt.arrow(prev_pt['x_aligned'], prev_pt['y_aligned'], 
                  last_pt['x_aligned'] - prev_pt['x_aligned'], 
                  last_pt['y_aligned'] - prev_pt['y_aligned'],
                  head_width=0.1, head_length=0.15, fc='green', ec='green', zorder=10)

    plt.title('Localization Performance: Perceived Path vs. Ground Truth', fontsize=16, fontweight='bold')
    plt.xlabel('X Position (meters)', fontsize=12)
    plt.ylabel('Y Position (meters)', fontsize=12)
    plt.legend(fontsize=10)
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.axis('equal')
    plt.tight_layout()

    # --- Plot 2: Waypoints vs. ZED (Tracking Error) ---
    plt.figure(figsize=(10, 10))
    plt.plot(zed_aligned_df['x_aligned'].values, zed_aligned_df['y_aligned'].values, 
             label='Perceived Path (ZED VIO)', color='green', linestyle='--', linewidth=2)
    
    waypoints_x_offset = waypoints_aligned_df['x_aligned'].values + MANUAL_X_OFFSET_WAYPOINTS
    waypoints_y_offset = waypoints_aligned_df['y_aligned'].values
    
    plt.scatter(waypoints_x_offset, waypoints_y_offset, 
                label='Desired Waypoints (Offset)', color='red', marker='x', s=50, linewidth=2)
    
    plt.scatter(0, 0, label='Aligned Start', color='cyan', marker='o', s=200, edgecolors='black', zorder=5)
    
    # ADDED: Arrow for ZED path on Plot 2
    if len(zed_aligned_df) > 1:
        last_pt = zed_aligned_df.iloc[-1]
        prev_pt = zed_aligned_df.iloc[-2]
        plt.arrow(prev_pt['x_aligned'], prev_pt['y_aligned'], 
                  last_pt['x_aligned'] - prev_pt['x_aligned'], 
                  last_pt['y_aligned'] - prev_pt['y_aligned'],
                  head_width=0.1, head_length=0.15, fc='green', ec='green', zorder=10)

    plt.title('Controller Performance: Desired Waypoints vs. Perceived Path', fontsize=16, fontweight='bold')
    plt.xlabel('X Position (meters)', fontsize=12)
    plt.ylabel('Y Position (meters)', fontsize=12)
    plt.legend(fontsize=10)
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.axis('equal')
    plt.tight_layout()

    # --- Plot 3: Waypoints vs. OptiTrack (Overall System Error) ---
    plt.figure(figsize=(10, 10))
    plt.plot(optitrack_aligned_df['x_aligned'].values, optitrack_aligned_df['y_aligned'].values, 
             label='Actual Path (Ground Truth - OptiTrack)', color='blue', linestyle='-', linewidth=2.5)
    
    # Use the same offset waypoints for this plot
    plt.scatter(waypoints_x_offset, waypoints_y_offset, 
                label='Desired Waypoints (Offset)', color='red', marker='x', s=50, linewidth=2)
    
    plt.scatter(0, 0, label='Aligned Start', color='cyan', marker='o', s=200, edgecolors='black', zorder=5)

    # ADDED: Arrow for OptiTrack path on Plot 3
    if len(optitrack_aligned_df) > 1:
        last_pt = optitrack_aligned_df.iloc[-1]
        prev_pt = optitrack_aligned_df.iloc[-2]
        plt.arrow(prev_pt['x_aligned'], prev_pt['y_aligned'], 
                  last_pt['x_aligned'] - prev_pt['x_aligned'], 
                  last_pt['y_aligned'] - prev_pt['y_aligned'],
                  head_width=0.1, head_length=0.15, fc='blue', ec='blue', zorder=10)

    plt.title('Overall Performance: Desired Waypoints vs. Ground Truth', fontsize=16, fontweight='bold')
    plt.xlabel('X Position (meters)', fontsize=12)
    plt.ylabel('Y Position (meters)', fontsize=12)
    plt.legend(fontsize=10)
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.axis('equal')
    plt.tight_layout()

    print("\nDisplaying plots. Close each plot window to exit the script.")
    plt.show()

if __name__ == '__main__':
    plot_all_paths()