#!/usr/bin/env python
# extract_ros1_bag.py
import rosbag
import csv
import os
import sys
import tf.transformations

BAG_FILENAME = 'optitrack_ground_truth.bag'
POSE_TOPIC = '/natnet_ros/husky/pose' # Make sure this matches your bag
OUTPUT_CSV_FILE = 'optitrack_path.csv'

# ... (get_yaw_from_quaternion function is the same)

def extract_data():
    # ... (rest of the script is the same)
    
    with open(OUTPUT_CSV_FILE, 'w', newline='') as csvfile:
        csv_writer = csv.writer(csvfile)
        # ADDED: timestamp column
        csv_writer.writerow(['timestamp', 'x', 'y', 'theta']) 

        for topic, msg, t in bag.read_messages(topics=[POSE_TOPIC]):
            # Convert ROS Time to seconds
            timestamp = t.to_sec() 
            
            pos_x = msg.pose.position.x
            pos_y = msg.pose.position.y
            yaw = get_yaw_from_quaternion(msg.pose.orientation)
            
            # ADDED: Write timestamp as the first column
            csv_writer.writerow([timestamp, pos_x, pos_y, yaw])
    # ... (rest of the script is the same)

if __name__ == '__main__':
    extract_data()