import importlib.util
import pathlib
import subprocess
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
        self.assertNotIn("fishros", bootstrap)
        self.assertNotIn("mirror.fishros.com", bootstrap)

    def test_registry_exposes_only_supported_hiwonder_modules(self):
        self.assertEqual(
            set(self.installer.MODULES),
            {"common", "source", "ros2", "opencv", "vision", "env", "verify"},
        )
        self.assertNotIn("ros1", self.installer.MODULES)
        self.assertNotIn("vscode", self.installer.MODULES)
        self.assertEqual(self.installer.ROS_DISTRO, "humble")
        self.assertEqual(self.installer.OPENCV_VERSION, "4.11.0")

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
        self.assertIn("HiWonder 安装计划", result.stdout)
        self.assertIn("ROS 2 humble", result.stdout)

    def test_dockerfile_targets_the_requested_image(self):
        dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8").lower()
        self.assertIn("from ubuntu:22.04", dockerfile)
        self.assertIn("install.py all", dockerfile)
        self.assertNotIn("fishros.com", dockerfile)


if __name__ == "__main__":
    unittest.main()
