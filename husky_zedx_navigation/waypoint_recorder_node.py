import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped
from sensor_msgs.msg import Joy
import math
import sys
import os

from robot_math_utils import get_yaw_from_quaternion, normalize_angle_radians, distance_2d

# --- Configuration for Joystick ---
JOYSTICK_BUTTON_START_RECORDING = 0  # PS4 'Cross' button
JOYSTICK_BUTTON_STOP_RECORDING = 2   # PS4 'Square' button
WAYPOINTS_FILENAME = "waypoints.csv" 

class WaypointPathRecorderSimplified(Node):
    def __init__(self):
        super().__init__('waypoint_path_recorder_simplified_node')
        self.get_logger().info("Simplified Waypoint Path Recorder initializing...")
        
        self.is_recording = False
        self.raw_trajectory_poses = []
        self.processed_waypoints = []

        self.pose_subscriber = self.create_subscription(
            PoseStamped,
            "/zed/zed_node/pose", # Using ZED camera for pose
            self.pose_callback,
            10
        )
        self.joystick_subscriber = self.create_subscription(
            Joy,
            "/a200_1046/joy_teleop/joy",
            self.joystick_callback,
            10
        )

        self.get_logger().info(f"Subscribed to pose topic: /zed/zed_node/pose")
        self.get_logger().info(f"Subscribed to joystick topic: /joy")
        self.get_logger().info(f"Press Joystick Button {JOYSTICK_BUTTON_START_RECORDING} to START recording.")
        self.get_logger().info(f"Press Joystick Button {JOYSTICK_BUTTON_STOP_RECORDING} to STOP recording and save.")
        self.get_logger().info(f"Waypoints will be saved to: {os.path.abspath(WAYPOINTS_FILENAME)}")
        self.get_logger().info("Node initialized successfully.")

    def joystick_callback(self, joy_msg: Joy):
        start_pressed = False
        stop_pressed = False

        if len(joy_msg.buttons) > JOYSTICK_BUTTON_START_RECORDING and \
           joy_msg.buttons[JOYSTICK_BUTTON_START_RECORDING] == 1:
            start_pressed = True
        
        if len(joy_msg.buttons) > JOYSTICK_BUTTON_STOP_RECORDING and \
           joy_msg.buttons[JOYSTICK_BUTTON_STOP_RECORDING] == 1:
            stop_pressed = True

        if start_pressed:
            if not self.is_recording:
                self.start_recording_path()
        elif stop_pressed:
            if self.is_recording:
                self.stop_recording_and_save_path()

    def start_recording_path(self):
        self.is_recording = True
        self.raw_trajectory_poses = []
        self.processed_waypoints = []
        self.get_logger().info("--------------------------------------")
        self.get_logger().info("START pressed: Path recording started.")
        self.get_logger().info("--------------------------------------")

    def stop_recording_and_save_path(self):
        self.is_recording = False
        self.get_logger().info("--------------------------------------")
        self.get_logger().info(f"STOP pressed: Path recording stopped. Recorded {len(self.raw_trajectory_poses)} poses.")
        
        if not self.raw_trajectory_poses:
            self.get_logger().warn("No poses were recorded. Nothing to process or save.")
            self.get_logger().info("--------------------------------------")
            return

        self.get_logger().info("Processing trajectory...")
        self.convert_trajectory_to_euler()
        self.select_sparse_waypoints_from_path()
        self.save_waypoints_to_file()
        self.get_logger().info("--------------------------------------")

    def pose_callback(self, msg: PoseStamped):
        if self.is_recording:
            self.raw_trajectory_poses.append(msg)
 
    def convert_trajectory_to_euler(self):
        temp_converted_list = []
        if not self.raw_trajectory_poses:
            self.get_logger().warn("Raw trajectory is empty for Euler conversion.")
            return
        
        self.get_logger().info (f"Converting {len(self.raw_trajectory_poses)} raw poses...")
        for pose_stamped_msg in self.raw_trajectory_poses:
            actual_pose_data = pose_stamped_msg.pose
            header = pose_stamped_msg.header
            
            yaw_angle_raw = get_yaw_from_quaternion(actual_pose_data.orientation)
            normalized_yaw = normalize_angle_radians(yaw_angle_raw)
            
            timestamp_sec = header.stamp.sec
            timestamp_nanosec_str = str(header.stamp.nanosec).zfill(9)

            temp_converted_list.append({
                'x': actual_pose_data.position.x,
                'y': actual_pose_data.position.y,
                'theta': normalized_yaw,
                'timestamp': f"{timestamp_sec}.{timestamp_nanosec_str}"
            })
        self.processed_waypoints = temp_converted_list
        self.get_logger().info(f"Successfully converted {len(self.processed_waypoints)} poses.")

    def select_sparse_waypoints_from_path(self, min_distance_thresh=0.5, min_angle_thresh_rad=0.3):
        if not self.processed_waypoints:
            self.get_logger().warn("Processed waypoints list is empty. Cannot select sparse waypoints.")
            return

        self.get_logger().info(f"Selecting sparse waypoints from {len(self.processed_waypoints)} converted poses...")
        
        sparse_waypoints_list = [self.processed_waypoints[0]]
        last_selected_waypoint = self.processed_waypoints[0]

        for current_point in self.processed_waypoints[1:]:
            actual_distance = distance_2d(
                last_selected_waypoint['x'], last_selected_waypoint['y'],
                current_point['x'], current_point['y']
            )
            angle_difference_raw = current_point['theta'] - last_selected_waypoint['theta']
            angle_difference_normalized = normalize_angle_radians(angle_difference_raw)
            
            if actual_distance >= min_distance_thresh or \
               abs(angle_difference_normalized) >= min_angle_thresh_rad:
                sparse_waypoints_list.append(current_point)
                last_selected_waypoint = current_point
        
        self.processed_waypoints = sparse_waypoints_list
        self.get_logger().info(f"Selected {len(self.processed_waypoints)} sparse waypoints.")

    def save_waypoints_to_file(self):
        if not self.processed_waypoints:
            self.get_logger().warn("No processed waypoints to save.")
            return

        full_path = os.path.abspath(WAYPOINTS_FILENAME)
        try:
            with open(WAYPOINTS_FILENAME, 'w') as f:
                for wp in self.processed_waypoints:
                    f.write(f"{wp['x']},{wp['y']},{wp['theta']}\n")
            self.get_logger().info(f"Successfully saved {len(self.processed_waypoints)} waypoints to {full_path}")
        except IOError as e:
            self.get_logger().error(f"Could not write waypoints to file {full_path}: {e}")

    def on_shutdown(self):
        self.get_logger().info("Simplified Waypoint Path Recorder shutting down...")
        self.get_logger().info("Shutdown complete.")

def main(args=None):
    rclpy.init(args=args if args is not None else sys.argv)
    recorder_node = WaypointPathRecorderSimplified()
    try:
        rclpy.spin(recorder_node)
    except KeyboardInterrupt:
        recorder_node.get_logger().info('Keyboard interrupt, shutting down recorder.')
    finally:
        recorder_node.on_shutdown()
        if rclpy.ok():
            recorder_node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()

if __name__ == '__main__':
    main()
husky_nav_ros2/husky_nav_ros2/waypoint_recorder_node.py