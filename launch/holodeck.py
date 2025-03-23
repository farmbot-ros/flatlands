import rclpy
import time
import sys
import os

from rclpy.node import Node
from farmbot_interfaces.msg import Agents

from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, GroupAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
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
    print(f"{len(beacons.beacons)} robot(s) found")

    ld = LaunchDescription()

    tcp_arg = DeclareLaunchArgument(
        "tcp",
        default_value="127.0.0.0:9876",
        description="TCP address to connect to the rerun server",
    )
    ld.add_action(tcp_arg)

    ld.add_action(OpaqueFunction(function=launch_setup))
    return ld


def launch_setup(context, *args, **kwargs):
    tcp = str(LaunchConfiguration("tcp").perform(context))

    pgk_share = get_package_share_directory("farmbot_holodeck")
    launch_file = os.path.join(pgk_share, "launch", "pose.launch.py")

    actions = []

    for robot in beacons.beacons:
        namespace = robot.name
        color = robot.color
        navigation_launch = GroupAction(
            [
                IncludeLaunchDescription(
                    PythonLaunchDescriptionSource(launch_file),
                    launch_arguments={
                        "namespace": namespace,
                        "tcp": tcp,
                        "color": color,
                    }.items(),
                )
            ]
        )
        actions.append(navigation_launch)

    field_launch_file = os.path.join(pgk_share, "launch", "field.launch.py")
    field_launch = GroupAction(
        [
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(field_launch_file),
                launch_arguments={"namespace": namespace, "tcp": tcp}.items(),
            )
        ]
    )
    actions.append(field_launch)

    return actions
