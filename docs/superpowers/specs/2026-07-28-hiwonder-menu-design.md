# HiWonder Menu Design

## Goal

Make `bash hiwonder` feel like a one-click installer: users select a small number of user-facing features, while dependency installation, environment setup, and verification run automatically in the background.

The target remains Ubuntu 22.04, ROS 2 Humble, OpenCV 4.11.0, and matching `opencv_contrib` 4.11.0.

## Main Menu

The default command opens a bilingual interactive menu with an ASCII HiWonder logo. The logo and borders stay ASCII-safe; Chinese labels are paired with English labels so the intended interface is still clear when a terminal cannot render Chinese.

```text
========================================
        HiWonder 一键安装工具
        HiWonder one-click installer
========================================
Target: Ubuntu 22.04
ROS: ROS 2 Humble
OpenCV: 4.11.0

[1] 安装 ROS 2 Humble / Install ROS 2 Humble
[2] 配置 Ubuntu 系统源 / Configure Ubuntu apt source
[3] 安装 OpenCV 4.11.0 / Install OpenCV 4.11.0
[4] 配置 ROS / OpenCV 环境 / Configure ROS / OpenCV environment
[5] 一键安装完整环境 / Install complete robot environment
[0] 退出 / Exit
```

The internal modules `common`, `vision`, and `verify` are not shown as top-level choices. Existing command-line module names remain available for automation and backward compatibility.

## Submenus

### ROS 2

```text
[1] ROS 2 Humble Desktop 完整版 / Desktop
[2] ROS 2 Humble 基础版 / Base
[0] 返回 / Back
```

The Desktop choice installs the requested desktop metapackage and common robotics packages. The base choice installs the ROS development tools without the desktop metapackage. Both choices install only ROS 2 Humble packages.

### Ubuntu Source

```text
[1] 官方源 / official
[2] 阿里云 / aliyun
[3] 清华 / tsinghua
[4] 中科大 / ustc
[0] 返回 / Back
```

The source module detects the Ubuntu codename, writes a HiWonder-owned apt source file, and runs `apt-get update`. It supports the source selection independently and is also used by the complete installation flow.

### OpenCV

```text
[1] OpenCV 4.11.0
[2] OpenCV 4.11.0 + opencv_contrib
[0] 返回 / Back
```

The contrib choice remains the recommended option for robot vision workloads. Both repositories use the exact `4.11.0` tag. The complete environment chooses the contrib build automatically.

## Complete Installation Flow

Selecting `[5]` runs the following hidden steps in order:

1. Ask for the Ubuntu apt source.
2. Install common dependencies.
3. Install ROS 2 Humble Desktop.
4. Build and install OpenCV 4.11.0 with `opencv_contrib` 4.11.0.
5. Build `vision_opencv/cv_bridge` against the custom OpenCV.
6. Generate `/etc/profile.d/hiwonder-ros2.sh`.
7. Verify the ROS, OpenCV, and cv_bridge installation.

## Non-interactive Compatibility

`--plan` remains a preview-only command and never prompts or changes the system. Existing direct commands continue to work:

```bash
bash hiwonder all --mirror aliyun
bash hiwonder ros2
bash hiwonder opencv
```

The interactive menu is the preferred user-facing path.

## Error Handling

- Invalid input is rejected and the same menu is shown again.
- `0` returns from a submenu or exits from the main menu.
- EOF exits cleanly without starting an installation.
- Any installation failure stops the current flow and prints the failing command.

## Testing

Add tests for menu rendering, valid numeric selections, submenu back behavior, the complete-flow module order, and preservation of the non-interactive `--plan` behavior. Existing package, OpenCV tag, environment, and bootstrap tests remain unchanged.
