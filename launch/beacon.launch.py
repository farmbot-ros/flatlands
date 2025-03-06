import os
import yaml

from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, GroupAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from ament_index_python.packages import get_package_share_directory

pkg_share = get_package_share_directory("farmbot_flatlands")
config_file = os.path.join(pkg_share, "config", "simulation.yaml")

print(config_file)

with open(config_file, "r") as f:
    config = yaml.safe_load(f)

robots = config.get("global", {}).get("ros__parameters", {}).get("robots", [])

# print(robots)


def generate_launch_description():
    # Get the package share directory and config file path

    # Load the YAML configuration file
    with open(config_file, "r") as f:
        config = yaml.safe_load(f)

    # Extract the number of robots from the config file
    num_robots_param = (
        config.get("global", {}).get("ros__parameters", {}).get("num_robots", 1)
    )

    num_robots_arg = DeclareLaunchArgument(
        "num_robots",
        default_value=str(num_robots_param),
        description="Number of robots to spawn",
    )

    function_arg = DeclareLaunchArgument(
        "function",
        default_value="harvester",
        description="Function of the beacon",
    )

    color_arg = DeclareLaunchArgument(
        "color",
        default_value="#ff0000",
        description="Color of the beacon",
    )

    offline_arg = DeclareLaunchArgument(
        "offline",
        default_value="60s",
        description="Offline time of the beacon",
    )

    # Path to the localization.launch.py file

    # Create the main launch description
    ld = LaunchDescription()
    ld.add_action(num_robots_arg)
    ld.add_action(function_arg)
    ld.add_action(color_arg)
    ld.add_action(offline_arg)

    # Add ann OpaqueFunction to the launch description
    ld.add_action(OpaqueFunction(function=launch_setup))

    return ld


def launch_setup(context, *args, **kwargs):
    num_robots = int(LaunchConfiguration("num_robots").perform(context))
    function = LaunchConfiguration("function").perform(context)
    color = LaunchConfiguration("color").perform(context)
    offline = LaunchConfiguration("offline").perform(context)

    pkg_share_coverage = get_package_share_directory("farmbot_lighthouse")
    coverage_launch_file = os.path.join(
        pkg_share_coverage, "launch", "beacon.launch.py"
    )

    actions = []

    for robot in robots:
        namespace = robot.get("namespace", "robot_default")
        info = robot.get("info", {})
        uuid = info.get("uuid", "00000000-0000-0000-0000-000000000000")
        # rci = info.get("rci", 0)
        function = info.get("function", "harvester")
        color = info.get("color", "#ff0000")

        robot_launch = GroupAction(
            [
                # PushRosNamespace(namespace),  # Push the namespace for this robot
                IncludeLaunchDescription(
                    PythonLaunchDescriptionSource(coverage_launch_file),
                    launch_arguments=(
                        {
                            "namespace": namespace,
                            "function": function,
                            "color": color,
                            "uuid": uuid,
                            "offline": offline,
                        }.items()
                    ),
                )
            ]
        )
        actions.append(robot_launch)

    return actions
