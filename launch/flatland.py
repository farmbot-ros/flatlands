import os
import yaml
import random

from launch import LaunchDescription
from launch.actions import OpaqueFunction
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory

# Path to the existing simulation config
param_file = os.path.join(
    get_package_share_directory("farmbot_flatlands"),
    "config",
    "simulation.yaml",
)

# Load robots list from config at import time
with open(param_file, "r") as f:
    config = yaml.safe_load(f)
robots = config.get("global", {}).get("ros__parameters", {}).get("robots", [])


def launch_setup(context, *args, **kwargs):

    # Create simulator node with the requested number of robots
    node = Node(
        package="farmbot_flatlands",
        executable="simulator",
        name="simulator",
        parameters=[
            {
                "publish_rate": 10.0,
                "num_robots": 1,
            }
        ],
        output="screen",
    )

    # Shuffle robot list (same behavior as before, though not passed into node)
    random.shuffle(robots)

    return [node]


def generate_launch_description():
    # Build and return the launch description
    return LaunchDescription(
        [
            OpaqueFunction(function=launch_setup),
        ]
    )
