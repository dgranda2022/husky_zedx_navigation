# Husky + Zed Navigation

## For the ROS1 netnet:
rosbag record -a -O optitrack_ground_truth.bag

## For the ROS2 zed:
ros2 bag record -a -o husky_and_zed_data

### To extract run:
In ROS2:
python3 extract_ros2_bag.py

And in ROS1:
python3 extract_ros1_bag.py

#### To plot all, put the extracted ros1 file into the same folder as waypoints.csv and the ros2 extraction
Run: 
python3 plot_all_paths.py


## Actual Experimental Procedure:

1. Turn on **In this order** Husky, Laptop, Optitrack, and log in and put all on **same network**

2. SSH into the husky laptop and then run: `ros2 launch /etc/clearpath/platform/launch/platform-service.launch.py` 

3. SSH into jetson and run zed wrapper: `ros2 launch zed_wrapper zed_camera.launch.py camera_model:=zedx`

4. Run `ros2 topic list` and expect to see all of the zed topics and the husky topics 

5. On desktop with ROS1:
    ```bash
     source ~/catkin_ws/devel/setup.bash
     roslaunch natnet_ros_cpp gui_natnet_ros.launch
     ``
6. Set up IPs of computer on same network as Motive, run

7. **On the laptop** run the recorder node in the directory of 'husky_nav_ros2': `python3 waypoint_recorder_node.py`

8. Press X to record, Run the desired path

9. Stop recording with Square, dont move from this location. 

10. Run two rosbags, one for the ROS2 on the laptop and the other on the ROS1 desktop

13. Run `python3 waypoint_navigator_node.py`

14. Stop all nodes. 

15. Extract data and plot. 