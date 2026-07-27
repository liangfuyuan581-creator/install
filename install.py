#!/usr/bin/env python3
"""HiWonder one-click installer for Ubuntu 22.04 and ROS 2 Humble.

The runner is intentionally self-contained so it can be fetched by the shell
bootstrap without depending on FishROS or any other installer at runtime.
"""

from __future__ import annotations

import argparse
import os
import platform
import shlex
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path, PurePosixPath


PROJECT_NAME = "HiWonder"
ROS_DISTRO = "humble"
OPENCV_VERSION = "4.11.0"
PREFIX = PurePosixPath("/opt/hiwonder")
OPENCV_PREFIX = PREFIX / f"opencv-{OPENCV_VERSION}"
OPENCV_SOURCE = PREFIX / "src" / f"opencv-{OPENCV_VERSION}"
OPENCV_CONTRIB_SOURCE = PREFIX / "src" / f"opencv_contrib-{OPENCV_VERSION}"
ROS_WORKSPACE = PREFIX / "ros2_ws"
VISION_SOURCE = ROS_WORKSPACE / "src" / "vision_opencv"
ENV_FILE = PurePosixPath("/etc/profile.d/hiwonder-ros2.sh")

COMMON_PACKAGES = [
    "ca-certificates",
    "curl",
    "wget",
    "git",
    "gnupg",
    "lsb-release",
    "software-properties-common",
    "build-essential",
    "cmake",
    "ninja-build",
    "pkg-config",
    "python3",
    "python3-dev",
    "python3-numpy",
    "python3-pip",
    "locales",
]

OPENCV_PACKAGES = [
    "build-essential",
    "cmake",
    "ninja-build",
    "git",
    "pkg-config",
    "python3-dev",
    "python3-numpy",
    "libgtk-3-dev",
    "libavcodec-dev",
    "libavformat-dev",
    "libswscale-dev",
    "libv4l-dev",
    "libxvidcore-dev",
    "libx264-dev",
    "libjpeg-dev",
    "libpng-dev",
    "libtiff-dev",
    "libopenexr-dev",
    "libatlas-base-dev",
    "libopenblas-dev",
    "gfortran",
    "libtbb-dev",
    "libeigen3-dev",
    "libgstreamer1.0-dev",
    "libgstreamer-plugins-base1.0-dev",
    "libdc1394-dev",
    "libprotobuf-dev",
    "protobuf-compiler",
    "libhdf5-dev",
    "libusb-1.0-0-dev",
]

ROS_PACKAGES = [
    "ros-humble-desktop",
    "ros-dev-tools",
    "python3-colcon-common-extensions",
    "python3-rosdep",
    "python3-vcstool",
    "ros-humble-image-transport",
    "ros-humble-camera-info-manager",
    "ros-humble-vision-msgs",
    "ros-humble-tf2-ros",
    "ros-humble-tf2-tools",
    "ros-humble-xacro",
    "ros-humble-robot-state-publisher",
    "ros-humble-joint-state-publisher",
    "ros-humble-joint-state-publisher-gui",
    "ros-humble-geometry-msgs",
    "ros-humble-sensor-msgs",
    "ros-humble-std-msgs",
    "ros-humble-nav-msgs",
    "ros-humble-trajectory-msgs",
    "ros-humble-control-msgs",
]

ALL_MODULES = ["common", "source", "ros2", "opencv", "vision", "env", "verify"]
MODULE_DESCRIPTIONS = {
    "common": "安装通用构建、Python 和网络依赖",
    "source": "选择并配置 Ubuntu 系统软件源",
    "ros2": "安装 ROS 2 Humble Desktop 和常用机器人包",
    "opencv": "从源码安装 OpenCV 4.11.0 + opencv_contrib 4.11.0",
    "vision": "构建与自定义 OpenCV 对齐的 ROS 2 cv_bridge",
    "env": "生成 ROS 2 和 OpenCV 环境配置",
    "verify": "检查 ROS 2、OpenCV 和 cv_bridge 安装结果",
}


def command_prefix() -> str:
    return "" if os.geteuid() == 0 else "sudo "


def run(command: str, *, dry_run: bool = False, check: bool = True) -> None:
    """Print and execute one shell command with predictable error handling."""
    print(f"\n[HiWonder]$ {command}", flush=True)
    if dry_run:
        return
    completed = subprocess.run(command, shell=True, executable="/bin/bash")
    if check and completed.returncode != 0:
        raise RuntimeError(f"命令执行失败，退出码 {completed.returncode}: {command}")


def apt_install(packages: list[str], *, dry_run: bool = False) -> None:
    package_text = " ".join(shlex.quote(item) for item in packages)
    run(f"{command_prefix()}apt-get update", dry_run=dry_run)
    run(
        f"DEBIAN_FRONTEND=noninteractive {command_prefix()}apt-get install -y {package_text}",
        dry_run=dry_run,
    )


def require_ubuntu_jammy() -> None:
    if not Path("/etc/os-release").exists():
        raise RuntimeError("无法识别系统：缺少 /etc/os-release")
    values = {}
    for line in Path("/etc/os-release").read_text(encoding="utf-8").splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            values[key] = value.strip('"')
    if values.get("ID") != "ubuntu" or values.get("VERSION_ID") != "22.04":
        raise RuntimeError(
            "HiWonder 当前目标环境是 Ubuntu 22.04，检测到 "
            f"{values.get('ID', 'unknown')} {values.get('VERSION_ID', 'unknown')}"
        )


def ubuntu_codename() -> str:
    values = {}
    for line in Path("/etc/os-release").read_text(encoding="utf-8").splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            values[key] = value.strip('"')
    return values.get("VERSION_CODENAME", "jammy")


def ubuntu_architecture() -> str:
    return {"x86_64": "amd64", "aarch64": "arm64"}.get(platform.machine(), platform.machine())


def ros2_repository_text(codename: str, architecture: str) -> str:
    return (
        f"deb [arch={architecture} signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] "
        f"http://packages.ros.org/ros2/ubuntu {codename} main\n"
    )


def opencv_source_commands() -> list[str]:
    return [
        f"git clone --branch {OPENCV_VERSION} --depth 1 https://github.com/opencv/opencv.git {OPENCV_SOURCE}",
        f"git clone --branch {OPENCV_VERSION} --depth 1 https://github.com/opencv/opencv_contrib.git {OPENCV_CONTRIB_SOURCE}",
        f"git -C {OPENCV_SOURCE} checkout {OPENCV_VERSION}",
        f"git -C {OPENCV_CONTRIB_SOURCE} checkout {OPENCV_VERSION}",
    ]


def opencv_cmake_args() -> list[str]:
    return [
        "-G Ninja",
        "-DCMAKE_BUILD_TYPE=Release",
        f"-DCMAKE_INSTALL_PREFIX={OPENCV_PREFIX}",
        f"-DOPENCV_EXTRA_MODULES_PATH={OPENCV_CONTRIB_SOURCE}/modules",
        "-DOPENCV_ENABLE_NONFREE=ON",
        "-DBUILD_TESTS=OFF",
        "-DBUILD_PERF_TESTS=OFF",
        "-DBUILD_EXAMPLES=OFF",
        "-DBUILD_opencv_python3=ON",
        f"-DPYTHON3_PACKAGES_PATH={OPENCV_PREFIX}/lib/python3/site-packages",
        "-DWITH_TBB=ON",
        "-DWITH_GSTREAMER=ON",
        "-DWITH_V4L=ON",
        "-DWITH_OPENGL=ON",
        "-DOPENCV_GENERATE_PKGCONFIG=ON",
    ]


def environment_script() -> str:
    return textwrap.dedent(
        f"""\
        # Generated by HiWonder installer. Safe to source more than once.
        if [ -f /opt/ros/{ROS_DISTRO}/setup.bash ]; then
            . /opt/ros/{ROS_DISTRO}/setup.bash
        fi
        if [ -f {ROS_WORKSPACE}/install/setup.bash ]; then
            . {ROS_WORKSPACE}/install/setup.bash
        fi

        export HIWONDER_ROS_DISTRO={ROS_DISTRO}
        export HIWONDER_OPENCV_VERSION={OPENCV_VERSION}
        export HIWONDER_OPENCV_PREFIX={OPENCV_PREFIX}
        export OpenCV_DIR={OPENCV_PREFIX}/lib/cmake/opencv4
        export PATH={OPENCV_PREFIX}/bin:$PATH
        export LD_LIBRARY_PATH={OPENCV_PREFIX}/lib:${{LD_LIBRARY_PATH:-}}
        export PKG_CONFIG_PATH={OPENCV_PREFIX}/lib/pkgconfig:${{PKG_CONFIG_PATH:-}}
        export PYTHONPATH={OPENCV_PREFIX}/lib/python3/site-packages:${{PYTHONPATH:-}}
        """
    )


def write_environment(*, dry_run: bool = False) -> None:
    content = environment_script()
    print(f"\n[HiWonder] 写入环境文件: {ENV_FILE}")
    write_privileged_file(ENV_FILE, content, dry_run=dry_run)


def write_privileged_file(path: PurePosixPath, content: str, *, dry_run: bool = False) -> None:
    """Write an /etc file whether the runner is root or uses sudo."""
    if dry_run:
        print(f"\n[HiWonder] 写入文件: {path}")
        return
    target = Path(str(path))
    if os.geteuid() == 0:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return
    temporary = Path("/tmp") / f"hiwonder-{target.name}"
    temporary.write_text(content, encoding="utf-8")
    run(f"sudo install -m 644 {temporary} {path}")
    temporary.unlink(missing_ok=True)


def install_common(*, dry_run: bool = False) -> None:
    apt_install(COMMON_PACKAGES, dry_run=dry_run)
    run("locale-gen en_US.UTF-8", dry_run=dry_run, check=False)


def configure_sources(*, mirror: str | None = None, dry_run: bool = False) -> None:
    mirrors = {
        "official": "http://archive.ubuntu.com/ubuntu",
        "aliyun": "https://mirrors.aliyun.com/ubuntu",
        "tsinghua": "https://mirrors.tuna.tsinghua.edu.cn/ubuntu",
        "ustc": "https://mirrors.ustc.edu.cn/ubuntu",
    }
    mirror = mirror or os.environ.get("HIWONDER_UBUNTU_MIRROR")
    if mirror is None and not dry_run:
        print("\n请选择 Ubuntu 软件源：")
        options = list(mirrors)
        for index, name in enumerate(options, 1):
            print(f"  {index}. {name} ({mirrors[name]})")
        choice = input("选择 [1]: ").strip() or "1"
        try:
            mirror = options[int(choice) - 1]
        except (ValueError, IndexError):
            raise RuntimeError("无效的软件源选项")
    mirror = mirror or "official"
    if mirror not in mirrors:
        raise RuntimeError(f"不支持的软件源: {mirror}")

    codename = ubuntu_codename()
    lines = [
        f"deb {mirrors[mirror]} {codename} main restricted universe multiverse",
        f"deb {mirrors[mirror]} {codename}-updates main restricted universe multiverse",
        f"deb {mirrors[mirror]} {codename}-backports main restricted universe multiverse",
        f"deb http://security.ubuntu.com/ubuntu {codename}-security main restricted universe multiverse",
    ]
    source_file = PurePosixPath("/etc/apt/sources.list.d/hiwonder-ubuntu.list")
    content = "\n".join(lines) + "\n"
    print(f"\n[HiWonder] 配置 Ubuntu 软件源: {mirror}")
    if dry_run:
        return
    write_privileged_file(source_file, content)
    run(f"{command_prefix()}apt-get update")


def install_ros2(*, dry_run: bool = False) -> None:
    require_ubuntu_jammy()
    key_path = PurePosixPath("/usr/share/keyrings/ros-archive-keyring.gpg")
    list_path = PurePosixPath("/etc/apt/sources.list.d/ros2.list")
    architecture = ubuntu_architecture()
    repository = ros2_repository_text(ubuntu_codename(), architecture)
    run(f"{command_prefix()}mkdir -p {key_path.parent}", dry_run=dry_run)
    run(
        "curl -fsSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key "
        f"| {command_prefix()}gpg --dearmor --yes -o {key_path}",
        dry_run=dry_run,
    )
    print(f"\n[HiWonder] 写入 ROS 2 软件源: {list_path}")
    write_privileged_file(list_path, repository, dry_run=dry_run)
    apt_install(ROS_PACKAGES, dry_run=dry_run)
    run(
        f"{command_prefix()}rosdep init",
        dry_run=dry_run,
        check=False,
    )
    run("rosdep update", dry_run=dry_run, check=False)


def clone_or_update(url: str, tag: str, destination: PurePosixPath, *, dry_run: bool = False) -> None:
    destination_path = Path(str(destination))
    if destination_path.exists() and (destination_path / ".git").exists():
        run(f"git -C {destination} fetch --depth 1 origin tag {tag}", dry_run=dry_run)
        run(f"git -C {destination} checkout {tag}", dry_run=dry_run)
        return
    if destination_path.exists() and not dry_run:
        shutil.rmtree(destination_path)
    run(
        f"git clone --branch {tag} --depth 1 {url} {destination}",
        dry_run=dry_run,
    )


def install_opencv(*, dry_run: bool = False) -> None:
    apt_install(OPENCV_PACKAGES, dry_run=dry_run)
    if not dry_run:
        Path(str(PREFIX / "src")).mkdir(parents=True, exist_ok=True)
    clone_or_update(
        "https://github.com/opencv/opencv.git",
        OPENCV_VERSION,
        OPENCV_SOURCE,
        dry_run=dry_run,
    )
    clone_or_update(
        "https://github.com/opencv/opencv_contrib.git",
        OPENCV_VERSION,
        OPENCV_CONTRIB_SOURCE,
        dry_run=dry_run,
    )
    build_dir = PREFIX / "build" / f"opencv-{OPENCV_VERSION}"
    if not dry_run:
        Path(str(build_dir)).mkdir(parents=True, exist_ok=True)
    args = " ".join(shlex.quote(item) for item in opencv_cmake_args())
    run(f"cmake -S {OPENCV_SOURCE} -B {build_dir} {args}", dry_run=dry_run)
    run(f"cmake --build {build_dir} --parallel", dry_run=dry_run)
    run(f"{command_prefix()}cmake --install {build_dir}", dry_run=dry_run)
    run(f"{command_prefix()}ldconfig", dry_run=dry_run)


def install_vision(*, dry_run: bool = False) -> None:
    """Build cv_bridge against HiWonder's OpenCV instead of Ubuntu's old one."""
    source = VISION_SOURCE
    if not dry_run:
        Path(str(ROS_WORKSPACE / "src")).mkdir(parents=True, exist_ok=True)
    clone_or_update(
        "https://github.com/ros-perception/vision_opencv.git",
        ROS_DISTRO,
        source,
        dry_run=dry_run,
    )
    run(
        f"source /opt/ros/{ROS_DISTRO}/setup.bash && "
        f"cd {ROS_WORKSPACE} && "
        f"rosdep install --from-paths src --ignore-src -r -y --skip-keys=opencv2 && "
        f"colcon build --symlink-install --cmake-args "
        f"-DOpenCV_DIR={OPENCV_PREFIX}/lib/cmake/opencv4 "
        f"-DCMAKE_BUILD_TYPE=Release",
        dry_run=dry_run,
    )


def verify_installation(*, dry_run: bool = False) -> None:
    commands = [
        f"test -f /opt/ros/{ROS_DISTRO}/setup.bash",
        f"test -f {OPENCV_PREFIX}/lib/cmake/opencv4/OpenCVConfig.cmake",
        f"source {ENV_FILE} && printenv HIWONDER_OPENCV_VERSION",
        f"source {ENV_FILE} && python3 -c 'import cv2; assert cv2.__version__.startswith(\"{OPENCV_VERSION}\"); print(cv2.__version__)'",
    ]
    for command in commands:
        run(command, dry_run=dry_run)


MODULES = {
    "common": install_common,
    "source": configure_sources,
    "ros2": install_ros2,
    "opencv": install_opencv,
    "vision": install_vision,
    "env": write_environment,
    "verify": verify_installation,
}


def print_plan(modules: list[str]) -> None:
    print(f"{PROJECT_NAME} 安装计划")
    print(f"目标系统: Ubuntu 22.04 | ROS 2 {ROS_DISTRO} | OpenCV {OPENCV_VERSION}")
    for index, name in enumerate(modules, 1):
        print(f"{index}. {name}: {MODULE_DESCRIPTIONS[name]}")


def select_modules() -> list[str]:
    print(f"\n{PROJECT_NAME} 一键配置工具")
    print("目标环境: Ubuntu 22.04 + ROS 2 Humble + OpenCV 4.11.0")
    print("\n可用模块：")
    print("  1. all     一键安装完整环境")
    for index, name in enumerate(ALL_MODULES, 2):
        print(f"  {index}. {name:<7} {MODULE_DESCRIPTIONS[name]}")
    choice = input("\n请选择 [1]: ").strip() or "1"
    if choice == "1" or choice.lower() == "all":
        return ALL_MODULES
    if choice.isdigit() and 2 <= int(choice) <= len(ALL_MODULES) + 1:
        return [ALL_MODULES[int(choice) - 2]]
    if choice in MODULES:
        return [choice]
    raise RuntimeError("无效的模块选择")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="HiWonder Ubuntu 22.04 / ROS 2 Humble installer")
    parser.add_argument(
        "module",
        nargs="?",
        choices=["all", *MODULES.keys(), "menu"],
        default="menu",
        help="要执行的模块，默认进入交互菜单",
    )
    parser.add_argument("--plan", action="store_true", help="只显示命令计划，不执行安装")
    parser.add_argument("--mirror", choices=["official", "aliyun", "tsinghua", "ustc"], help="Ubuntu 软件源")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.module == "all" or (args.module == "menu" and args.plan):
        modules = ALL_MODULES
    elif args.module == "menu":
        modules = select_modules()
    else:
        modules = [args.module]
    print_plan(modules)
    if args.plan:
        return 0
    if args.mirror and "source" not in modules:
        print("[HiWonder] --mirror 仅在 source 模块中生效")
    for module in modules:
        print(f"\n===== HiWonder: {module} =====")
        if module == "source":
            selected_mirror = args.mirror
            if args.module == "all" and selected_mirror is None:
                selected_mirror = os.environ.get("HIWONDER_UBUNTU_MIRROR", "official")
            configure_sources(mirror=selected_mirror)
        else:
            MODULES[module]()
    print("\nHiWonder 配置完成。重新打开终端，或执行: source /etc/profile.d/hiwonder-ros2.sh")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\n用户取消操作")
        raise SystemExit(130)
    except Exception as error:
        print(f"\n[HiWonder] 安装失败: {error}", file=sys.stderr)
        raise SystemExit(1)
