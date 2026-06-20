from __future__ import annotations

import argparse
import json
from typing import Any

try:
    import tinytuya
except ImportError as exc:  # pragma: no cover - runtime-only helper
    raise SystemExit(
        "tinytuya is not installed. Run: pip install -r requirements.txt"
    ) from exc


def _json_default(value: Any) -> str:
    return str(value)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Discover Tuya devices visible on the local network."
    )
    parser.add_argument(
        "--retries",
        type=int,
        default=8,
        help="Broadcast discovery retry count. Higher values help on noisy Wi-Fi.",
    )
    parser.add_argument(
        "--raw",
        action="store_true",
        help="Print the raw TinyTuya discovery object without extra summary text.",
    )
    args = parser.parse_args()

    print(f"Scanning local LAN for Tuya devices with {args.retries} retries...")
    results = tinytuya.deviceScan(maxretry=args.retries)

    if args.raw:
        print(json.dumps(results, indent=2, sort_keys=True, default=_json_default))
        return 0

    if not results:
        print("No Tuya devices discovered.")
        return 1

    print()
    print("Discovered devices:")
    for ip, details in sorted(results.items()):
        print(f"- {ip}")
        if isinstance(details, dict):
            for key in ("gwId", "version", "name", "productKey", "id"):
                value = details.get(key)
                if value:
                    print(f"  {key}: {value}")
            print("  raw:")
            print(
                json.dumps(details, indent=4, sort_keys=True, default=_json_default)
            )
        else:
            print(f"  raw: {details}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
