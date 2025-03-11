import os
import yaml

from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, GroupAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
from launch.actions import TimerAction
import random

pkg_share = get_package_share_directory("farmbot_flatlands")
config_file = os.path.join(pkg_share, "config", "simulation.yaml")

print(config_file)

with open(config_file, "r") as f:
    config = yaml.safe_load(f)

robots = config.get("global", {}).get("ros__parameters", {}).get("robots", [])


def generate_launch_description():
    offline_arg = DeclareLaunchArgument(
        "offline",
        default_value="60s",
        description="Offline time of the beacon",
    )
    num_robots_arg = DeclareLaunchArgument(
        "num_robots",
        default_value=str(len(robots)),
        description="Number of robots to simulate",
    )

    chain_domain_arg = DeclareLaunchArgument(
        "chain_domain",
        default_value="1",
        description="Chain domain",
    )

    blockchain_arg = DeclareLaunchArgument(
        "blockchain",
        default_value="true",
        description="Blockchain",
    )

    # Create the main launch description
    ld = LaunchDescription()
    ld.add_action(offline_arg)
    ld.add_action(num_robots_arg)
    ld.add_action(chain_domain_arg)
    ld.add_action(blockchain_arg)

    # Add ann OpaqueFunction to the launch description
    ld.add_action(OpaqueFunction(function=launch_setup))

    return ld


def launch_setup(context, *args, **kwargs):
    offline = LaunchConfiguration("offline").perform(context)
    num_robots = LaunchConfiguration("num_robots").perform(context)
    chain_domain = LaunchConfiguration("chain_domain").perform(context)
    blockchain_arg = LaunchConfiguration("blockchain").perform(context)

    pkg_share_coverage = get_package_share_directory("farmbot_lighthouse")
    coverage_launch_file = os.path.join(
        pkg_share_coverage, "launch", "beacon.launch.py"
    )

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

    for i, robot in enumerate(robots):
        if i >= int(num_robots):
            break
        namespace = robot.get("namespace", "robot_default")
        key_file = robot.get("key_file", "")
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
                            "chain_domain": chain_domain,
                            "key_file": key_file,
                            "blockchain": blockchain_arg,
                        }.items()
                    ),
                )
            ]
        )
        # actions.append(robot_launch)

        # Add a delay of few seconds before launching the next robot
        # rnd = random.randint(2, 8)
        actions.append(TimerAction(period=float(i * 11), actions=[robot_launch]))

        visualize_node = Node(
            package="farmbot_flatlands",
            executable="visualize",
            name="visualize_robot",
            namespace=namespace,
            parameters=[
                {"robot_name": namespace},
                {"robot_color": "blue"},
                {"robot_width": 0.5},
                {"robot_length": 0.5},
                {"robot_height": 0.5},
            ],
            output="screen",
        )
        actions.append(visualize_node)

    return actions
