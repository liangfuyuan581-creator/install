# HiWonder 一键配置工具

这是一个独立的 HiWonder 环境安装器，面向 Docker 或实体机中的 Ubuntu 22.04，提供：

- ROS 2 Humble Desktop
- OpenCV 4.11.0
- opencv_contrib 4.11.0
- 与自定义 OpenCV 对齐的 ROS 2 `cv_bridge`
- Ubuntu 软件源选择和环境变量自动配置
- 可扩展的模块化命令

安装器不依赖 FishROS，不安装 ROS 1，也不安装 VS Code。

## 直接使用

```bash
export HIWONDER_URL=https://raw.githubusercontent.com/liangfuyuan581-creator/install/hiwonder-ros2-opencv
wget -O hiwonder "${HIWONDER_URL}/install?cache=$(date +%s)"
bash hiwonder --plan
bash hiwonder all --mirror official
```

国内网络可以选择镜像：

```bash
bash hiwonder all --mirror aliyun
# 可选: official / aliyun / tsinghua / ustc
```

`all` 的安装顺序是：通用依赖、Ubuntu 软件源、ROS 2 Humble、OpenCV 4.11.0、`cv_bridge`、环境配置、验证。OpenCV 从源码编译，耗时和磁盘占用都明显高于普通 apt 安装。

## 分模块执行

```bash
bash hiwonder common
bash hiwonder source --mirror aliyun
bash hiwonder ros2
bash hiwonder opencv
bash hiwonder vision
bash hiwonder env
bash hiwonder verify
```

也可以不带参数进入交互菜单：

```bash
bash hiwonder
```

安装完成后重新打开终端，或手动加载：

```bash
source /etc/profile.d/hiwonder-ros2.sh
```

环境文件会设置：

```text
ROS_DISTRO=humble
HIWONDER_OPENCV_VERSION=4.11.0
OpenCV_DIR=/opt/hiwonder/opencv-4.11.0/lib/cmake/opencv4
```

## Docker

仓库中的 `Dockerfile` 会基于 `ubuntu:22.04` 构建完整的 ROS 2 Humble + OpenCV 4.11.0 环境：

```bash
docker build --build-arg HIWONDER_MIRROR=official -t hiwonder-ros2-humble:22.04 .
docker run --name hiwonder-ros2-humble -it hiwonder-ros2-humble:22.04
```

国内网络：

```bash
docker build --build-arg HIWONDER_MIRROR=aliyun -t hiwonder-ros2-humble:22.04 .
```

这个镜像提供完整的命令行和 ROS 开发环境。桌面、GNOME、NoMachine 属于 Docker 运行层配置，不由这个安装器强制安装。

## 开发和测试

新模块应加入 `install.py` 的 `MODULES` 注册表，并为纯配置逻辑增加测试。运行测试：

```bash
python3 -m unittest discover -s tests -p 'test_hiwonder_installer.py' -v
python3 -m py_compile install.py
bash -n install
```

执行安装前可以用 `--plan` 查看目标流程，不会执行 apt、源码下载或编译：

```bash
python3 install.py all --plan
```
