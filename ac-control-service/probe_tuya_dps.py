from __future__ import annotations

import argparse
import json
from typing import Any

from ac_config import Settings

try:
    import tinytuya
except ImportError as exc:  # pragma: no cover - runtime-only helper
    raise SystemExit(
        "tinytuya is not installed. Run: pip install -r requirements.txt"
    ) from exc


def _json_default(value: Any) -> str:
    return str(value)


def _build_parser() -> argparse.ArgumentParser:
    settings = Settings()
    parser = argparse.ArgumentParser(
        description="Probe a specific Tuya device and print its available DPS/state."
    )
    parser.add_argument(
        "--device-id",
        default=settings.tuya_device_id,
        help="Tuya device id. Defaults to TUYA_DEVICE_ID from .env if present.",
    )
    parser.add_argument(
        "--ip",
        default=settings.tuya_device_ip,
        help="Device IP address. Defaults to TUYA_DEVICE_IP from .env if present.",
    )
    parser.add_argument(
        "--local-key",
        default=settings.tuya_local_key,
        help="Tuya local key. Defaults to TUYA_LOCAL_KEY from .env if present.",
    )
    parser.add_argument(
        "--version",
        default=settings.tuya_device_version,
        help="Protocol version, usually 3.3 or 3.4.",
    )
    parser.add_argument(
        "--raw",
        action="store_true",
        help="Only print the raw TinyTuya status response.",
    )
    return parser


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()

    missing = [
        label
        for label, value in (
            ("--device-id / TUYA_DEVICE_ID", args.device_id),
            ("--ip / TUYA_DEVICE_IP", args.ip),
            ("--local-key / TUYA_LOCAL_KEY", args.local_key),
        )
        if not value
    ]
    if missing:
        parser.error("Missing required values: " + ", ".join(missing))

    device = tinytuya.Device(
        dev_id=args.device_id,
        address=args.ip,
        local_key=args.local_key,
    )
    device.set_version(float(args.version))

    print(f"Probing device {args.device_id} at {args.ip} using version {args.version}...")

    try:
        available_dps = device.detect_available_dps()
    except Exception as exc:  # pragma: no cover - depends on device/network
        available_dps = {"error": str(exc)}

    try:
        status = device.status()
    except Exception as exc:  # pragma: no cover - depends on device/network
        status = {"error": str(exc)}

    if args.raw:
        print(json.dumps(status, indent=2, sort_keys=True, default=_json_default))
        return 0

    print()
    print("Detected DPS:")
    print(json.dumps(available_dps, indent=2, sort_keys=True, default=_json_default))
    print()
    print("Status payload:")
    print(json.dumps(status, indent=2, sort_keys=True, default=_json_default))
    print()
    print("Tip: toggle one setting in Smart Life, rerun this script, and compare the DPS values.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
