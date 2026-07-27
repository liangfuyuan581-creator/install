# HiWonder 测试

测试覆盖安装器的纯配置逻辑和命令计划，不会执行 apt、源码下载或 OpenCV 编译。

```bash
python3 -m unittest discover -s tests -p 'test_hiwonder_installer.py' -v
python3 install.py all --plan
```

完整 Docker 构建会安装 ROS 2 Humble、源码版 OpenCV 4.11.0 和 `opencv_contrib` 4.11.0，耗时较长，不作为每次提交的 CI 测试。
