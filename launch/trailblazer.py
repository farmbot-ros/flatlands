import rclpy
import time
import sys
import os

from rclpy.node import Node
from farmbot_interfaces.msg import Beacons

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
            Beacons,
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

    count = 10
    print(f"Sleeping for {count}s... ")
    while count > 0:
        sys.stdout.write(f"\r{count}s remaining...")  # Overwrites the same line
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

    angle = DeclareLaunchArgument(
        "angle",
        default_value="45",
        description="Angle to generate swaths",
    )
    ld.add_action(angle)

    ld.add_action(OpaqueFunction(function=launch_setup))
    return ld


def launch_setup(context, *args, **kwargs):
    angle = str(LaunchConfiguration("angle").perform(context))

    pgk_share = get_package_share_directory("farmbot_trailblazer")
    launch_file = os.path.join(pgk_share, "launch", "coverage.launch.py")

    actions = []

    for robot in beacons.beacons:
        namespace = robot.name
        # GroupAction to launch the coverage.launch.py file under the given namespace
        robot_launch = GroupAction(
            [
                # PushRosNamespace(namespace),  # Push the namespace for this robot
                IncludeLaunchDescription(
                    PythonLaunchDescriptionSource(launch_file),
                    launch_arguments=(
                        {
                            "namespace": namespace,
                        }.items()
                        if robot.name != "robot0"
                        else {
                            "namespace": namespace,
                            "angle": angle,
                            "num_robots": str(len(beacons.beacons)),
                            "alternate_freq": str(len(beacons.beacons)),
                            "calculator": str(1),
                        }.items()
                    ),
                )
            ]
        )

        actions.append(robot_launch)

    return actions
