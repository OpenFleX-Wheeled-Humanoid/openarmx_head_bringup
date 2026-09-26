import os
import xacro

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription, LaunchContext
from launch.actions import DeclareLaunchArgument, OpaqueFunction, RegisterEventHandler
from launch.conditions import IfCondition
from launch.event_handlers import OnProcessExit, OnProcessStart
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_robot_description(context: LaunchContext, can_interface,
                               use_fake_hardware, can_fd, control_mode):
    can_interface_str = context.perform_substitution(can_interface)
    use_fake_hardware_str = context.perform_substitution(use_fake_hardware)
    can_fd_str = context.perform_substitution(can_fd)
    control_mode_str = context.perform_substitution(control_mode)

    xacro_path = os.path.join(
        get_package_share_directory("openarmx_head_description"),
        "urdf", "head.urdf.xacro"
    )

    robot_description = xacro.process_file(
        xacro_path,
        mappings={
            "can_interface": can_interface_str,
            "use_fake_hardware": use_fake_hardware_str,
            "can_fd": can_fd_str,
            "control_mode": control_mode_str,
        }
    ).toprettyxml(indent="  ")

    return robot_description


def robot_nodes_spawner(context: LaunchContext, can_interface, use_fake_hardware,
                        controllers_file, can_fd, control_mode):
    robot_description = generate_robot_description(
        context, can_interface, use_fake_hardware, can_fd, control_mode
    )

    controllers_file_str = context.perform_substitution(controllers_file)
    robot_description_param = {"robot_description": robot_description}

    robot_state_pub_node = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        name="robot_state_publisher",
        output="screen",
        parameters=[robot_description_param],
    )

    control_node = Node(
        package="controller_manager",
        executable="ros2_control_node",
        output="both",
        parameters=[robot_description_param, controllers_file_str],
    )

    # joint_state_broadcaster 必须先起来，否则后续控制器有概率在
    # controller_manager 尚未准备好时抢先加载，导致偶发加载失败。
    joint_state_broadcaster_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=[
            "joint_state_broadcaster",
            "--controller-manager",
            "/controller_manager",
            "--controller-manager-timeout",
            "30",
        ],
    )

    # head_forward_position_controller 依赖 controller_manager 和
    # joint_state_broadcaster 都已可用，因此这里不再使用固定延时，
    # 而是在 JSB spawner 成功退出后再启动它。
    head_controller_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=[
            "head_forward_position_controller",
            "--controller-manager",
            "/controller_manager",
            "--controller-manager-timeout",
            "30",
        ],
    )

    # 这里用进程启动事件代替 TimerAction。目的不是为了更快启动，
    # 而是为了把时序依赖从“猜一个秒数”改成“明确等待 control_node 已启动”。
    start_jsb_after_control_manager = RegisterEventHandler(
        OnProcessStart(
            target_action=control_node,
            on_start=[joint_state_broadcaster_spawner],
        )
    )

    # JSB spawner 退出意味着 joint_state_broadcaster 已经完成加载并激活。
    # 到这个时刻再拉起 head controller，可以稳定规避之前的控制器竞争条件。
    start_head_controller_after_jsb = RegisterEventHandler(
        OnProcessExit(
            target_action=joint_state_broadcaster_spawner,
            on_exit=[head_controller_spawner],
        )
    )

    return [
        robot_state_pub_node,
        control_node,
        start_jsb_after_control_manager,
        start_head_controller_after_jsb,
    ]


def generate_launch_description():
    declared_arguments = [
        DeclareLaunchArgument(
            "can_interface",
            default_value="can2",
            description="CAN interface for head motors.",
        ),
        DeclareLaunchArgument(
            "use_fake_hardware",
            default_value="false",
            description="Use fake hardware instead of real hardware.",
        ),
        DeclareLaunchArgument(
            "can_fd",
            default_value="false",
            description="Enable CAN-FD.",
        ),
        DeclareLaunchArgument(
            "control_mode",
            default_value="csp",
            choices=["mit", "csp"],
            description="Low-level control mode: mit or csp.",
        ),
        DeclareLaunchArgument(
            "launch_rviz",
            default_value="true",
            description="Launch RViz2 with the head robot model.",
        ),
    ]

    can_interface = LaunchConfiguration("can_interface")
    use_fake_hardware = LaunchConfiguration("use_fake_hardware")
    can_fd = LaunchConfiguration("can_fd")
    control_mode = LaunchConfiguration("control_mode")
    launch_rviz = LaunchConfiguration("launch_rviz")

    controllers_file = PathJoinSubstitution(
        [FindPackageShare("openarmx_head_bringup"), "config", "head_controllers.yaml"]
    )

    rviz_config_file = PathJoinSubstitution(
        [FindPackageShare("openarmx_head_bringup"), "config", "head.rviz"]
    )

    robot_nodes_spawner_func = OpaqueFunction(
        function=robot_nodes_spawner,
        args=[can_interface, use_fake_hardware, controllers_file, can_fd, control_mode]
    )

    rviz_node = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        output="screen",
        arguments=["-d", rviz_config_file],
        condition=IfCondition(launch_rviz),
    )

    return LaunchDescription(
        declared_arguments + [
            robot_nodes_spawner_func,
            rviz_node,
        ]
    )
