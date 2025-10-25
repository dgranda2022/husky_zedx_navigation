import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    pkgshare = get_package_share_directory('husky_navigation_v2')
    
    params_file_path = os.path.join(pkgshare, 'config', 'navigator_params.yaml')
    return LaunchDescription([
        Node(
            package = 'husky_navigation_v2', 
            executable = 'waypoint_navigator_node', 
            name = 'waypoint_navigator_pd_node', 
            output = 'screen', 
            parameters = [params_file_path]

        )

    ])