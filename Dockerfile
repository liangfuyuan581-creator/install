FROM ubuntu:22.04

ARG HIWONDER_MIRROR=official
ENV DEBIAN_FRONTEND=noninteractive \
    LANG=en_US.UTF-8 \
    LC_ALL=en_US.UTF-8 \
    HIWONDER_UBUNTU_MIRROR=${HIWONDER_MIRROR}

# Bootstrap dependencies are intentionally small; the HiWonder runner installs
# the complete ROS 2 and OpenCV build dependencies in the next layer.
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates curl python3 \
    && rm -rf /var/lib/apt/lists/*

COPY install.py /opt/hiwonder-installer/install.py
COPY install /usr/local/bin/hiwonder

RUN chmod +x /usr/local/bin/hiwonder \
    && python3 /opt/hiwonder-installer/install.py all --mirror ${HIWONDER_MIRROR} \
    && rm -rf /opt/hiwonder/src /opt/hiwonder/build /var/lib/apt/lists/* /tmp/* \
    && apt-get clean

WORKDIR /workspace
ENTRYPOINT ["/bin/bash"]
