import rclpy
import time
import sys
import os

from rclpy.node import Node
from farmbot_interfaces.msg import Agents

from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, GroupAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from ament_index_python.packages import get_package_share_directory

# Global variable to store the topic message
beacons = None


class TopicListener(Node):
    def __init__(self):
        super().__init__("topic_listener")
        self.subscription = self.create_subscription(
            Agents,
            "/beacons/rci",
            self.listener_callback,
            10,
        )

    def listener_callback(self, msg):
        global beacons
        beacons = msg  # Store received message


def wait_for_topic():
    """Function to wait for a specific topic message before launching nodes."""
    global beacons
    rclpy.init()
    node = TopicListener()

    count = 15
    while count > 0:
        sys.stdout.write(f"\rListening {count}s for beacons...")
        sys.stdout.flush()
        time.sleep(1)
        count -= 1
    print("\rTime's up! Now launching nodes...")

    while beacons is None:
        rclpy.spin_once(node, timeout_sec=1.0)  # Wait for the message

    rclpy.shutdown()


def generate_launch_description():
    # listener_thread = threading.Thread(target=wait_for_topic)
    # listener_thread.start()
    wait_for_topic()
    print(f"{len(beacons.agents)} robot(s) found")

    ld = LaunchDescription()

    autodatum = DeclareLaunchArgument(
        "autodatum",
        default_value="datum",
        description="Autodatum type to use",
    )
    ld.add_action(autodatum)

    ld.add_action(OpaqueFunction(function=launch_setup))
    return ld


def launch_setup(context, *args, **kwargs):
    # autodatum = LaunchConfiguration("autodatum").perform(context)

    pkg_share_localization = get_package_share_directory("farmbot_trailblazer")
    coverage_launch_file = os.path.join(
        pkg_share_localization, "launch", "coverage.launch.py"
    )

    actions = []

    for robot in beacons.agents:
        namespace = robot.name
        robot_launch = GroupAction(
            [
                IncludeLaunchDescription(
                    PythonLaunchDescriptionSource(coverage_launch_file),
                    launch_arguments={
                        "namespace": namespace,
                    }.items(),
                )
            ]
        )

        actions.append(robot_launch)

    return actions
