FROM jenkins/jenkins:lts

USER root


RUN apt-get update && apt-get install -y --no-install-recommends \
        qemu-system-arm qemu-utils \
        python3 python3-pip python3-venv \
        ipmitool netcat-openbsd \
        chromium chromium-driver \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Устанавливаем питоновские библиотеки
RUN pip3 install --break-system-packages \
    pytest requests locust selenium urllib3

USER jenkins