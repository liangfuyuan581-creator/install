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
