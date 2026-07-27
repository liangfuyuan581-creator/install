# HiWonder Installer Contributor Guide

## Project overview

HiWonder is a self-contained installer for Ubuntu 22.04 in Docker or on a host machine. The public entry points are:

- `install`: shell bootstrap fetched by users with `wget`.
- `install.py`: module runner and installer implementation.
- `Dockerfile`: reproducible Ubuntu 22.04 image build.
- `tests/test_hiwonder_installer.py`: fast unit and configuration tests.

The runtime must not depend on FishROS, ROS 1, VS Code, or a remote installer framework.

## Supported stack

- Ubuntu 22.04 (`jammy`)
- ROS 2 Humble
- OpenCV 4.11.0
- `opencv_contrib` 4.11.0

## Development commands

```bash
python3 -m unittest discover -s tests -p 'test_hiwonder_installer.py' -v
python3 -m py_compile install.py
bash -n install
python3 install.py all --plan
```

Do not run `python3 install.py all` on a development workstation unless a full ROS and OpenCV source build is intended. The plan mode does not modify the system.

## Adding a module

Add a focused function to `install.py`, register it in `MODULES`, add its description to `MODULE_DESCRIPTIONS`, and update `ALL_MODULES` only when it belongs in the full installation. Add a test before changing behavior.

Installation commands must be idempotent where practical, use noninteractive apt flags, and avoid installing apt or pip OpenCV packages that conflict with the required source build.
