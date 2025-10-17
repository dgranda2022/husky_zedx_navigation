from setuptools import find_packages, setup
import os
from glob import glob

package_name = 'husky_navigation_v2'

# Create the resource file if it doesn't exist
# This is a marker file used by ament to identify the package
resource_file = os.path.join('resource', package_name)
if not os.path.exists(resource_file):
    os.makedirs('resource', exist_ok=True)
    with open(resource_file, 'w') as f:
        pass

setup(
    name=package_name, # This must match the name of your package
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
        (os.path.join('share', package_name, 'config'), glob('config/*.yaml')),
    ],
    install_requires=['setuptools'], # setuptools itself is a dependency
    zip_safe=True,
    maintainer='danielg',
    maintainer_email='dgranda2022@fau.edu',
    description='Version 2 of the Husky waypoint navigation controller.',
    license='Apache-2.0',
    tests_require=['pytest'], # Standard for ament_python, ignore UserWarning during build
    entry_points={
        'console_scripts': [
            'waypoint_recorder = husky_navigation_v2.waypoint_recorder_node:main',
            'waypoint_navigator = husky_navigation_v2.waypoint_navigator_node:main',
        ],
    },
)
