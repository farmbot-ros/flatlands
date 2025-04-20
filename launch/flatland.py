import os
import yaml

from launch import LaunchDescription
from launch.substitutions import LaunchConfiguration
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
import random

pkg_share = get_package_share_directory("farmbot_flatlands")
config_file = os.path.join(pkg_share, "config", "simulation.yaml")

print(config_file)

with open(config_file, "r") as f:
    config = yaml.safe_load(f)

robots = config.get("global", {}).get("ros__parameters", {}).get("robots", [])


def generate_launch_description():

    num_robots_arg = DeclareLaunchArgument(
        "num_robots",
        default_value=str(len(robots)),
        description="Number of robots to simulate",
    )

    # Create the main launch description
    ld = LaunchDescription()
    ld.add_action(num_robots_arg)

    # Add ann OpaqueFunction to the launch description
    ld.add_action(OpaqueFunction(function=launch_setup))

    return ld


def launch_setup(context, *args, **kwargs):
    num_robots = LaunchConfiguration("num_robots").perform(context)

    actions = []

    robot_node = Node(
        package="farmbot_flatlands",
        executable="simulator",
        name="simulator",
        parameters=[
            {
                "publish_rate": 10.0,
                "num_robots": int(num_robots),
            },
        ],
        output="screen",
    )
    actions.append(robot_node)

    random.shuffle(robots)

    return actions
