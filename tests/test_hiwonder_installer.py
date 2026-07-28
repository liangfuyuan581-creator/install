import importlib.util
import os
import pathlib
import subprocess
import sys
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]


def load_installer():
    spec = importlib.util.spec_from_file_location("hiwonder_install", ROOT / "install.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class HiWonderInstallerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.installer = load_installer()

    def test_bootstrap_is_independent_from_fishros(self):
        bootstrap = (ROOT / "install").read_text(encoding="utf-8").lower()
        self.assertIn("hiwonder", bootstrap)
        self.assertIn("/hiwonder-ros2-opencv", bootstrap)
        self.assertNotIn("fishros", bootstrap)
        self.assertNotIn("mirror.fishros.com", bootstrap)

    def test_bootstrap_retries_curl_and_falls_back_to_wget(self):
        bootstrap = (ROOT / "install").read_text(encoding="utf-8")
        self.assertIn("--retry-all-errors", bootstrap)
        self.assertIn("if wget", bootstrap)
        self.assertIn("--tries=5", bootstrap)
        self.assertIn("download_runner", bootstrap)
        self.assertIn("HIWONDER_CACHE_BUSTER", bootstrap)
        self.assertIn("?hiwonder=", bootstrap)

    def test_bootstrap_forces_utf8_for_docker_terminals(self):
        bootstrap = (ROOT / "install").read_text(encoding="utf-8")
        self.assertIn('export LANG="C.UTF-8"', bootstrap)
        self.assertIn('export LC_ALL="C.UTF-8"', bootstrap)
        self.assertIn('export PYTHONIOENCODING="UTF-8"', bootstrap)
        self.assertIn("stty iutf8", bootstrap)

    def test_bootstrap_explains_root_requirement_for_non_passwordless_docker_users(self):
        bootstrap = (ROOT / "install").read_text(encoding="utf-8")
        self.assertIn("/.dockerenv", bootstrap)
        self.assertIn("sudo -n -v", bootstrap)
        self.assertIn("docker exec -u 0 -it", bootstrap)
        self.assertIn("Root privileges are required inside Docker", bootstrap)

    def test_interactive_menu_remains_readable_with_ascii_parent_encoding(self):
        environment = os.environ.copy()
        environment.update(
            {
                "LANG": "C",
                "LC_ALL": "C",
                "PYTHONIOENCODING": "ascii",
                "NO_COLOR": "1",
            }
        )
        result = subprocess.run(
            [sys.executable, str(ROOT / "install.py")],
            input=b"0\n",
            capture_output=True,
            env=environment,
            check=True,
        )
        output = result.stdout.decode("utf-8")
        self.assertIn("请选择", output)
        self.assertIn("退出", output)

    def test_registry_exposes_only_supported_hiwonder_modules(self):
        self.assertEqual(
            set(self.installer.MODULES),
            {"common", "source", "ros2", "opencv", "vision", "env", "verify"},
        )
        self.assertNotIn("ros1", self.installer.MODULES)
        self.assertNotIn("vscode", self.installer.MODULES)
        self.assertEqual(self.installer.ROS_DISTRO, "humble")
        self.assertEqual(self.installer.OPENCV_VERSION, "4.11.0")

    def test_main_menu_is_bilingual_and_uses_compact_installer_layout(self):
        menu = self.installer.main_menu_text()
        self.assertIn("HiWonder", menu)
        self.assertIn("HiWonder 一键安装工具 / HiWonder one-click installer", menu)
        self.assertIn("============================================================", menu)
        self.assertIn(
            "[1] 安装 ROS 2 Humble 完整功能包 / Install full ROS 2 Humble packages",
            menu,
        )
        self.assertIn(
            "[2] 配置 Ubuntu 系统源 / Configure Ubuntu apt source",
            menu,
        )
        self.assertIn("安装 ROS 2 Humble", menu)
        self.assertIn("[5]", menu)
        self.assertIn("[0]", menu)
        self.assertIn("H I W O N D E R", menu)

    def test_ros_menu_explains_package_scope_without_desktop_ambiguity(self):
        menu = self.installer.ros_menu_text()
        self.assertIn("ROS 2 Humble 软件包类型 / ROS 2 Humble package type", menu)
        self.assertIn(
            "[1] ROS 2 Humble 完整功能包（含 RViz2 等工具） / Full ROS 2 Humble packages (includes RViz2 tools)",
            menu,
        )
        self.assertIn(
            "[2] ROS 2 Humble 基础功能包 / Base ROS 2 Humble packages",
            menu,
        )
        self.assertIn(
            "只安装 ROS 2 软件包，不安装 Docker 或 Ubuntu 桌面",
            menu,
        )

    def test_main_menu_prompt_matches_compact_interactive_style(self):
        self.assertIn("请选择 / Select [5]:", self.installer.MAIN_MENU_PROMPT)

    def test_hiwonder_logo_is_a_readable_ascii_wordmark(self):
        logo = self.installer.HIWONDER_LOGO
        self.assertNotIn("█", logo)
        self.assertTrue(logo.isascii())
        self.assertIn("@", logo)
        self.assertIn("H I W O N D E R", logo)
        self.assertIn("|     @   @  @@@@   @   @", logo)
        self.assertIn("+", logo)
        self.assertNotIn("##", logo)
        self.assertNotIn("_   _ _  __", logo)
        self.assertNotIn("�", logo)
        self.assertGreaterEqual(len(logo.splitlines()), 9)
        self.assertLessEqual(max(map(len, logo.splitlines())), 68)
        self.assertTrue(all(not line.endswith(" ") for line in logo.splitlines()))
        self.assertTrue(
            all(len(line) == 64 for line in logo.splitlines() if line)
        )

    def test_framed_brand_area_is_ascii_and_menu_text_has_no_mojibake(self):
        menu_texts = (
            self.installer.main_menu_text(),
            self.installer.mirror_menu_text(),
            self.installer.ros_menu_text(),
            self.installer.opencv_menu_text(),
        )
        mojibake_markers = ("涓", "閿", "瀹", "绯", "鐜", "鍏", "锛", "鈥", "�")
        for menu in menu_texts:
            self.assertFalse(any(marker in menu for marker in mojibake_markers))
            self.assertNotIn("�", menu)

    def test_main_menu_hides_internal_implementation_modules(self):
        menu = self.installer.main_menu_text()
        self.assertNotIn("[2] common", menu)
        self.assertNotIn("[5] vision", menu)
        self.assertNotIn("[7] verify", menu)

    def test_submenu_choices_are_user_facing_and_stable(self):
        self.assertEqual(
            self.installer.ROS_MENU_CHOICES,
            {"1": "desktop", "2": "base", "0": None},
        )
        self.assertEqual(
            self.installer.OPENCV_MENU_CHOICES,
            {"1": False, "2": True, "0": None},
        )
        self.assertEqual(
            self.installer.MIRROR_MENU_CHOICES,
            {"1": "official", "2": "aliyun", "3": "tsinghua", "4": "ustc", "0": None},
        )

    def test_all_has_a_stable_install_order(self):
        self.assertEqual(
            self.installer.ALL_MODULES,
            ["common", "source", "ros2", "opencv", "vision", "env", "verify"],
        )

    def test_opencv_build_is_pinned_to_matching_tags_and_contrib(self):
        args = self.installer.opencv_cmake_args()
        self.assertIn("-DOPENCV_EXTRA_MODULES_PATH=/opt/hiwonder/src/opencv_contrib-4.11.0/modules", args)
        self.assertIn("-DCMAKE_INSTALL_PREFIX=/opt/hiwonder/opencv-4.11.0", args)
        self.assertIn("-DBUILD_opencv_python3=ON", args)
        self.assertNotIn("opencv-python", " ".join(self.installer.OPENCV_PACKAGES))
        self.assertNotIn("opencv-contrib-python", " ".join(self.installer.OPENCV_PACKAGES))
        self.assertNotIn("libopencv-dev", " ".join(self.installer.OPENCV_PACKAGES))

    def test_opencv_sources_use_the_same_exact_version(self):
        commands = self.installer.opencv_source_commands()
        joined = "\n".join(commands)
        self.assertIn("opencv.git", joined)
        self.assertIn("opencv_contrib.git", joined)
        self.assertEqual(joined.count("4.11.0"), 8)

    def test_ros_repository_is_ros2_only(self):
        repository = self.installer.ros2_repository_text("jammy", "amd64")
        self.assertIn("packages.ros.org/ros2/ubuntu", repository)
        self.assertNotIn("packages.ros.org/ros/ubuntu", repository)
        self.assertNotIn("ros1", repository.lower())

    def test_environment_script_selects_humble_and_custom_opencv(self):
        script = self.installer.environment_script()
        self.assertIn("/opt/ros/humble/setup.bash", script)
        self.assertIn("HIWONDER_OPENCV_VERSION=4.11.0", script)
        self.assertIn("/opt/hiwonder/opencv-4.11.0/lib", script)
        self.assertIn("OpenCV_DIR=/opt/hiwonder/opencv-4.11.0/lib/cmake/opencv4", script)

    def test_vision_source_is_inside_the_colcon_workspace(self):
        self.assertEqual(
            str(self.installer.VISION_SOURCE),
            "/opt/hiwonder/ros2_ws/src/vision_opencv",
        )

    def test_plan_is_non_interactive_and_contains_all_modules(self):
        result = subprocess.run(
            ["python", str(ROOT / "install.py"), "all", "--plan"],
            capture_output=True,
            text=True,
            check=True,
        )
        self.assertIn("common", result.stdout)
        self.assertIn("ros2", result.stdout)
        self.assertIn("opencv", result.stdout)
        self.assertIn("verify", result.stdout)

    def test_default_plan_does_not_open_the_interactive_menu(self):
        result = subprocess.run(
            ["python", str(ROOT / "install.py"), "--plan"],
            capture_output=True,
            text=True,
            check=True,
        )
        self.assertIn("HiWonder installation plan", result.stdout)
        self.assertIn("ROS 2 humble", result.stdout)

    def test_default_plan_output_is_ascii_safe_for_docker_terminals(self):
        result = subprocess.run(
            ["python", str(ROOT / "install.py"), "--plan"],
            capture_output=True,
            text=True,
            check=True,
        )
        self.assertTrue(result.stdout.isascii())

    def test_dockerfile_targets_the_requested_image(self):
        dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8").lower()
        self.assertIn("from ubuntu:22.04", dockerfile)
        self.assertIn("install.py all", dockerfile)
        self.assertNotIn("fishros.com", dockerfile)


if __name__ == "__main__":
    unittest.main()
