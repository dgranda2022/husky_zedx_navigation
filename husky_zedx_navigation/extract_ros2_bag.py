import rclpy
from rclpy.serialization import deserialize_message
from rosidl_runtime_py.utilities import get_message
import rosbag2_py
import csv
import os
import sys

# Make sure robot_math_utils.py is in the same directory or Python path
try:
    from robot_math_utils import get_yaw_from_quaternion, normalize_angle_radians
except ImportError:
    print("\n--- ERROR ---")
    print("Could not import from 'robot_math_utils.py'.")
    print("Please make sure that file is in the same directory as this script.")
    print("-------------")
    sys.exit(1)


# --- Configuration ---
BAG_FILE_DIR = 'husky_and_zed_data'
POSE_TOPIC = '/zed/zed_node/pose'
OUTPUT_CSV_FILE = 'zed_path.csv'

def extract_data():
    if not os.path.exists(BAG_FILE_DIR):
        print(f"Error: Bag file directory '{BAG_FILE_DIR}' not found.")
        return

    # The entire process is wrapped in a single try block
    try:
        # --- Setup the bag reader ---
        storage_options = rosbag2_py.StorageOptions(uri=BAG_FILE_DIR, storage_id='sqlite3')
        converter_options = rosbag2_py.ConverterOptions(input_serialization_format='cdr', output_serialization_format='cdr')
        reader = rosbag2_py.SequentialReader()
        reader.open(storage_options, converter_options)

        # Get topic types from the bag
        topic_types = reader.get_all_topics_and_types()
        type_map = {topic.name: topic.type for topic in topic_types}

        if POSE_TOPIC not in type_map:
            print(f"Error: Topic '{POSE_TOPIC}' not found in the bag file.")
            print(f"Available topics are: {[t.name for t in topic_types]}")
            return

        # Get the message type definition for the pose topic
        msg_type = get_message(type_map[POSE_TOPIC])

        print(f"Extracting data from topic '{POSE_TOPIC}'...")
        
        # --- Open the CSV and read the bag ---
        with open(OUTPUT_CSV_FILE, 'w', newline='') as csvfile:
            csv_writer = csv.writer(csvfile)
            csv_writer.writerow(['timestamp', 'x', 'y', 'theta']) # Write header

            # This loop will only be reached if the reader was successfully created
            while reader.has_next():
                (topic, data, t) = reader.read_next()
                if topic == POSE_TOPIC:
                    msg = deserialize_message(data, msg_type)
                    
                    timestamp = t / 1e9 # Convert nanoseconds to seconds
                    
                    pos_x = msg.pose.position.x
                    pos_y = msg.pose.position.y
                    yaw_raw = get_yaw_from_quaternion(msg.pose.orientation)
                    yaw_normalized = normalize_angle_radians(yaw_raw)
                    
                    csv_writer.writerow([timestamp, pos_x, pos_y, yaw_normalized])
        
        print(f"Data extraction complete. Saved to '{OUTPUT_CSV_FILE}'.")

    except Exception as e:
        print(f"An error occurred during bag processing: {e}")

if __name__ == '__main__':
    extract_data()
