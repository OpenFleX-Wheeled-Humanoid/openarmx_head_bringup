# openarmx_head_bringup

[English](./README.md) | 中文

---

![封面](./image/cover.gif)


OpenArmX 2自由度头部（偏航 + 俯仰）的启动文件和控制器配置包。

## 概述

本包启动 OpenArmX 头部完整的 ros2_control 控制栈，包括：

- Robot State Publisher（基于 URDF/xacro）
- ros2_control Controller Manager（100 Hz 更新频率）
- `joint_state_broadcaster` 用于发布关节状态
- `head_forward_position_controller`（ForwardCommandController）用于位置指令
- 可选的 RViz2 可视化

启动文件自动处理控制器的启动顺序，避免竞争条件。

## 依赖

- `openarmx_head_description`（URDF）
- `openarmx_head_hardware`（硬件接口插件）
- `controller_manager`、`joint_state_broadcaster`、`forward_command_controller`
- `robot_state_publisher`、`xacro`、`rviz2`

## 编译

```bash
cd ~/openflex_ws
colcon build --packages-select openarmx_head_bringup
source install/setup.bash
```

## 启动

```bash
ros2 launch openarmx_head_bringup head.launch.py
```

### 启动参数

| 参数 | 默认值 | 描述 |
|------|--------|------|
| `can_interface` | `can2` | 头部电机使用的 CAN 总线接口 |
| `use_fake_hardware` | `false` | 使用仿真硬件（无需真实电机） |
| `can_fd` | `false` | 启用 CAN-FD 模式 |
| `control_mode` | `csp` | 底层电机控制模式：`mit` 或 `csp` |
| `launch_rviz` | `true` | 启动 RViz2 显示头部模型 |

### 使用示例

```bash
# 真实硬件，can2 接口，CSP 模式

---
ros2 launch openarmx_head_bringup head.launch.py

# 仿真硬件，用于测试

---
ros2 launch openarmx_head_bringup head.launch.py use_fake_hardware:=true

# MIT 控制模式，使用 can0 接口

---
ros2 launch openarmx_head_bringup head.launch.py can_interface:=can0 control_mode:=mit
```

## 控制器

在 `config/head_controllers.yaml` 中配置：

- **joint_state_broadcaster**：向 `/joint_states` 发布关节状态
- **head_forward_position_controller**：接收 `openarmx_head_yaw_joint` 和 `openarmx_head_pitch_joint` 的位置指令

### 指令话题

```
/head_forward_position_controller/commands  [std_msgs/Float64MultiArray]
```

数据数组顺序：`[yaw, pitch]`（弧度）

## 话题

| 话题 | 类型 | 方向 | 描述 |
|------|------|------|------|
| `/joint_states` | `sensor_msgs/JointState` | 发布 | 当前关节位置、速度、力矩 |
| `/head_forward_position_controller/commands` | `std_msgs/Float64MultiArray` | 订阅 | 位置指令 [yaw, pitch]（弧度） |
| `/robot_description` | `std_msgs/String` | 发布 | URDF 机器人描述 |

## TF 坐标系

- `world` -> `head_base_link`（固定）
- `head_base_link` -> `head_pitch_link`（旋转关节，俯仰）
- `head_pitch_link` -> `head_yaw_link`（旋转关节，偏航）

## 注意事项

- 启动前需确保 CAN 接口已启用，例如：`sudo ip link set can2 up type can bitrate 1000000`
- 控制器按序启动：joint_state_broadcaster 在 controller_manager 就绪后启动，head_forward_position_controller 在 joint_state_broadcaster 加载完成后启动。

## 许可证

本作品采用知识共享 署名-非商业性使用-相同方式共享 4.0 国际许可协议 (CC BY-NC-SA 4.0) 进行许可。

版权所有 (c) 2026 成都长数机器人有限公司 (Chengdu Changshu Robot Co., Ltd.)

详情请参阅 [LICENSE_CN.md](LICENSE) 文件或访问：http://creativecommons.org/licenses/by-nc-sa/4.0/

## 致谢

本包是 OpenArmX 机器人平台生态系统的一部分，专为协作机器人领域的研究和工业应用而开发。

---

## 📞 联系我们

### 成都长数机器人有限公司
**Chengdu Changshu Robotics Co., Ltd.**

| 联系方式 | 信息 |
|---------|------|
| 📧 邮箱 | openarmrobot@gmail.com |
| 📱 电话/微信 | +86-17746530375 |
| 🌐 官网 | <https://openarmx.com/> |
| 🌐 文档 | <http://docs.openarmx.com/> |
| 📍 地址 | 天津经济技术开发区西区新业八街11号华诚机械厂 |
| 👤 联系人 | 王先生 |
