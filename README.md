# my-nas-proj

## updateglobalip.service

PATH: /etc/systemd/system/updateglobalip.service

```
[Unit]
Description=Update Global IP via Firebase
After=network-online.target openmediavault-engined.service
Wants=network-online.target

[Service]
Type=simple
User=fus
WorkingDirectory=/home/fus/UserApplications/UpdateInfo
ExecStart=/bin/bash /home/fus/UserApplications/UpdateInfo/run.sh
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target

```

## fancontrol.service

PATH: /etc/systemd/system/fancontrol.service

```
[Unit]
Description=Fan Control via PWM on GPIO12 (Raspberry Pi 4)
After=network-online.target openmediavault-engined.service
Wants=network-online.target

[Service]
Type=simple
User=fus
WorkingDirectory=/home/fus/UserApplications/FanControl
ExecStart=/home/fus/miniforge3/envs/py3.8/bin/python /home/fus/UserApplications/FanControl/fan_control.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target

```

## DEMO


<img width="1070" height="722" alt="image" src="https://github.com/user-attachments/assets/08f0f77e-8cd2-4019-9ee0-09ed8340db28" />
