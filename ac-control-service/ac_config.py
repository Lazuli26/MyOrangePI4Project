from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def load_dotenv() -> None:
    env_path = Path(__file__).with_name(".env")
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


load_dotenv()


@dataclass
class Settings:
    backend: str = os.getenv("AC_BACKEND", "mock").strip().lower()
    bind_host: str = os.getenv("AC_BIND_HOST", "127.0.0.1").strip()
    bind_port: int = int(os.getenv("AC_BIND_PORT", "8008"))
    api_token: str = os.getenv("AC_API_TOKEN", "").strip()
    smart_db_path: str = os.getenv(
        "SMART_DB_PATH", str(Path(__file__).with_name("smart_controller.db"))
    ).strip()
    frontend_dist_path: str = os.getenv(
        "FRONTEND_DIST_PATH", str(Path(__file__).with_name("frontend").joinpath("dist"))
    ).strip()
    tuya_device_id: str = os.getenv("TUYA_DEVICE_ID", "").strip()
    tuya_device_ip: str = os.getenv("TUYA_DEVICE_IP", "").strip()
    tuya_local_key: str = os.getenv("TUYA_LOCAL_KEY", "").strip()
    tuya_device_version: str = os.getenv("TUYA_DEVICE_VERSION", "3.3").strip()
    tuya_power_dpid: int = int(os.getenv("TUYA_POWER_DPID", "1"))
    tuya_target_temp_dpid: int = int(os.getenv("TUYA_TARGET_TEMP_DPID", "2"))
    tuya_current_temp_dpid: int = int(os.getenv("TUYA_CURRENT_TEMP_DPID", "3"))
    tuya_mode_dpid: int = int(os.getenv("TUYA_MODE_DPID", "4"))
    tuya_fan_speed_dpid: int = int(os.getenv("TUYA_FAN_SPEED_DPID", "5"))
    tuya_uvc_dpid: int = int(os.getenv("TUYA_UVC_DPID", "11"))
    tuya_sleep_dpid: int = int(os.getenv("TUYA_SLEEP_DPID", "25"))
    tuya_vertical_swing_dpid: int = int(os.getenv("TUYA_VERTICAL_SWING_DPID", "31"))
    tuya_horizontal_swing_dpid: int = int(os.getenv("TUYA_HORIZONTAL_SWING_DPID", "33"))
    tuya_display_dpid: int = int(os.getenv("TUYA_DISPLAY_DPID", "36"))
    tuya_fault_dpid: int = int(os.getenv("TUYA_FAULT_DPID", "108"))
