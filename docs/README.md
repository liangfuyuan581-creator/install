# HiWonder 安装器文档

HiWonder 安装器面向 Ubuntu 22.04，当前固定支持：

- ROS 2 Humble Desktop
- OpenCV 4.11.0
- opencv_contrib 4.11.0
- ROS 2 `cv_bridge` 自定义 OpenCV 构建

## 一键命令

```bash
export HIWONDER_URL=https://raw.githubusercontent.com/liangfuyuan581-creator/install/hiwonder-ros2-opencv
wget -O hiwonder "${HIWONDER_URL}/install?cache=$(date +%s)"
bash hiwonder all --mirror official
```

执行 `bash hiwonder --plan` 可以先查看步骤。安装器不会安装 ROS 1、VS Code，也不依赖任何第三方安装器运行时服务。

## 模块

直接运行 `bash hiwonder` 会进入中英文并列的数字菜单。主菜单只显示用户功能，基础依赖、`cv_bridge` 和验证步骤会在后台自动执行。

```text
[1] 安装 ROS 2 Humble / Install ROS 2 Humble
[2] 配置 Ubuntu 系统源 / Configure Ubuntu apt source
[3] 安装 OpenCV 4.11.0 / Install OpenCV 4.11.0
[4] 配置 ROS / OpenCV 环境 / Configure environment
[5] 一键安装完整环境 / Install complete environment
[0] 退出 / Exit
```

| 模块 | 作用 |
| --- | --- |
| `common` | 通用依赖 |
| `source` | Ubuntu 软件源选择 |
| `ros2` | ROS 2 Humble |
| `opencv` | OpenCV 4.11.0 + contrib 4.11.0 |
| `vision` | 与自定义 OpenCV 对齐的 `cv_bridge` |
| `env` | 自动生成 `/etc/profile.d/hiwonder-ros2.sh` |
| `verify` | 安装验证 |

完整 Docker 构建方式请查看仓库根目录的 `README.md` 和 `Dockerfile`。
