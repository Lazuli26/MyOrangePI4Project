from __future__ import annotations

import json
import os
import threading
import urllib.error
import urllib.request
from typing import Any

import tkinter as tk
from tkinter import ttk

from ac_config import load_dotenv


load_dotenv()

DEFAULT_BASE_URL = os.getenv("AC_GUI_BASE_URL", "http://127.0.0.1:8008").rstrip("/")
DEFAULT_API_TOKEN = os.getenv("AC_API_TOKEN", "")


def api_request(
    base_url: str,
    api_token: str,
    method: str,
    path: str,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    url = f"{base_url}{path}"
    body = None
    headers = {"Accept": "application/json"}
    if api_token:
        headers["X-API-Token"] = api_token
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    request = urllib.request.Request(url=url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            raw = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code}: {raw}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Network error: {exc.reason}") from exc

    if not raw.strip():
        return {}
    return json.loads(raw)


class AcControlGui(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("AC Control Panel")
        self.geometry("920x760")
        self.minsize(880, 680)

        self.base_url_var = tk.StringVar(value=DEFAULT_BASE_URL)
        self.api_token_var = tk.StringVar(value=DEFAULT_API_TOKEN)

        self.mode_var = tk.StringVar(value="cool")
        self.temp_var = tk.IntVar(value=24)
        self.fan_var = tk.StringVar(value="auto")
        self.sleep_var = tk.BooleanVar(value=False)
        self.uvc_var = tk.BooleanVar(value=False)
        self.display_var = tk.BooleanVar(value=True)
        self.horizontal_swing_var = tk.BooleanVar(value=False)
        self.vertical_swing_var = tk.StringVar(value="fixed")

        self.status_source_var = tk.StringVar(value="-")
        self.status_power_var = tk.StringVar(value="-")
        self.status_mode_var = tk.StringVar(value="-")
        self.status_target_temp_var = tk.StringVar(value="-")
        self.status_current_temp_var = tk.StringVar(value="-")
        self.status_fan_var = tk.StringVar(value="-")
        self.status_sleep_var = tk.StringVar(value="-")
        self.status_uvc_var = tk.StringVar(value="-")
        self.status_display_var = tk.StringVar(value="-")
        self.status_horizontal_swing_var = tk.StringVar(value="-")
        self.status_vertical_swing_var = tk.StringVar(value="-")
        self.status_fault_var = tk.StringVar(value="-")

        self._busy = False

        self.columnconfigure(0, weight=1)
        self.rowconfigure(3, weight=1)

        self._build_connection_frame()
        self._build_controls_frame()
        self._build_status_frame()
        self._build_log_frame()

        self.after(150, self.refresh_status)

    def _build_connection_frame(self) -> None:
        frame = ttk.LabelFrame(self, text="Connection")
        frame.grid(row=0, column=0, sticky="ew", padx=12, pady=(12, 6))
        frame.columnconfigure(1, weight=1)

        ttk.Label(frame, text="Base URL").grid(row=0, column=0, sticky="w", padx=8, pady=8)
        ttk.Entry(frame, textvariable=self.base_url_var).grid(
            row=0, column=1, sticky="ew", padx=8, pady=8
        )

        ttk.Label(frame, text="API token").grid(row=0, column=2, sticky="w", padx=8, pady=8)
        ttk.Entry(frame, textvariable=self.api_token_var, show="*").grid(
            row=0, column=3, sticky="ew", padx=8, pady=8
        )

        ttk.Button(frame, text="Refresh Status", command=self.refresh_status).grid(
            row=0, column=4, sticky="ew", padx=8, pady=8
        )

    def _build_controls_frame(self) -> None:
        frame = ttk.LabelFrame(self, text="Controls")
        frame.grid(row=1, column=0, sticky="ew", padx=12, pady=6)
        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=1)

        power_frame = ttk.Frame(frame)
        power_frame.grid(row=0, column=0, sticky="w", padx=8, pady=8)
        ttk.Button(power_frame, text="Power On", command=lambda: self.set_power(True)).grid(
            row=0, column=0, padx=(0, 8)
        )
        ttk.Button(power_frame, text="Power Off", command=lambda: self.set_power(False)).grid(
            row=0, column=1
        )

        core_frame = ttk.Frame(frame)
        core_frame.grid(row=1, column=0, sticky="ew", padx=8, pady=8)
        for index in range(6):
            core_frame.columnconfigure(index, weight=1 if index % 2 else 0)

        ttk.Label(core_frame, text="Mode").grid(row=0, column=0, sticky="w")
        ttk.Combobox(
            core_frame,
            textvariable=self.mode_var,
            values=["auto", "cool", "dry", "fan"],
            state="readonly",
        ).grid(row=0, column=1, sticky="ew", padx=(6, 12))

        ttk.Label(core_frame, text="Target C").grid(row=0, column=2, sticky="w")
        ttk.Spinbox(
            core_frame,
            from_=16,
            to=32,
            textvariable=self.temp_var,
            width=6,
        ).grid(row=0, column=3, sticky="w", padx=(6, 12))

        ttk.Label(core_frame, text="Fan").grid(row=0, column=4, sticky="w")
        ttk.Combobox(
            core_frame,
            textvariable=self.fan_var,
            values=["auto", "low", "middle", "high", "strong", "mute"],
            state="readonly",
        ).grid(row=0, column=5, sticky="ew", padx=(6, 0))

        ttk.Button(frame, text="Apply Core", command=self.apply_core).grid(
            row=2, column=0, sticky="w", padx=8, pady=(0, 8)
        )

        extras_frame = ttk.LabelFrame(frame, text="Extras")
        extras_frame.grid(row=0, column=1, rowspan=3, sticky="nsew", padx=8, pady=8)
        extras_frame.columnconfigure(0, weight=1)
        extras_frame.columnconfigure(1, weight=1)

        ttk.Checkbutton(extras_frame, text="Sleep", variable=self.sleep_var).grid(
            row=0, column=0, sticky="w", padx=8, pady=4
        )
        ttk.Checkbutton(extras_frame, text="UVC", variable=self.uvc_var).grid(
            row=0, column=1, sticky="w", padx=8, pady=4
        )
        ttk.Checkbutton(extras_frame, text="Display", variable=self.display_var).grid(
            row=1, column=0, sticky="w", padx=8, pady=4
        )
        ttk.Checkbutton(
            extras_frame, text="Horizontal Swing", variable=self.horizontal_swing_var
        ).grid(row=1, column=1, sticky="w", padx=8, pady=4)

        ttk.Label(extras_frame, text="Vertical Swing").grid(
            row=2, column=0, sticky="w", padx=8, pady=4
        )
        ttk.Combobox(
            extras_frame,
            textvariable=self.vertical_swing_var,
            values=["fixed", "swing"],
            state="readonly",
        ).grid(row=2, column=1, sticky="ew", padx=8, pady=4)

        button_row = ttk.Frame(extras_frame)
        button_row.grid(row=3, column=0, columnspan=2, sticky="w", padx=8, pady=(8, 4))
        ttk.Button(button_row, text="Apply Extras", command=self.apply_extras).grid(
            row=0, column=0, padx=(0, 8)
        )
        ttk.Button(button_row, text="Apply All", command=self.apply_all).grid(
            row=0, column=1
        )

        note = (
            "The control surface intentionally matches current Smart Life app behavior "
            "for this unit and can be widened later after more fan-speed testing."
        )
        ttk.Label(frame, text=note, wraplength=860, foreground="#555555").grid(
            row=3, column=0, columnspan=2, sticky="w", padx=8, pady=(0, 8)
        )

    def _build_status_frame(self) -> None:
        frame = ttk.LabelFrame(self, text="Latest Status")
        frame.grid(row=2, column=0, sticky="ew", padx=12, pady=6)

        rows = [
            ("Source", self.status_source_var),
            ("Power", self.status_power_var),
            ("Mode", self.status_mode_var),
            ("Target C", self.status_target_temp_var),
            ("Current C", self.status_current_temp_var),
            ("Fan", self.status_fan_var),
            ("Sleep", self.status_sleep_var),
            ("UVC", self.status_uvc_var),
            ("Display", self.status_display_var),
            ("Horizontal Swing", self.status_horizontal_swing_var),
            ("Vertical Swing", self.status_vertical_swing_var),
            ("Fault", self.status_fault_var),
        ]
        for index, (label, variable) in enumerate(rows):
            column = (index // 6) * 2
            row = index % 6
            ttk.Label(frame, text=label).grid(row=row, column=column, sticky="w", padx=8, pady=4)
            ttk.Label(frame, textvariable=variable).grid(
                row=row, column=column + 1, sticky="w", padx=(0, 24), pady=4
            )

    def _build_log_frame(self) -> None:
        frame = ttk.LabelFrame(self, text="Activity Log")
        frame.grid(row=3, column=0, sticky="nsew", padx=12, pady=(6, 12))
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)

        self.log_text = tk.Text(frame, wrap="word", height=14, state="disabled")
        self.log_text.grid(row=0, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.log_text.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.log_text.configure(yscrollcommand=scrollbar.set)

    def _append_log(self, message: str) -> None:
        self.log_text.configure(state="normal")
        self.log_text.insert("end", f"{message}\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def _set_busy(self, busy: bool) -> None:
        self._busy = busy
        self.configure(cursor="watch" if busy else "")

    def _run_request(
        self,
        description: str,
        method: str,
        path: str,
        payload: dict[str, Any] | None = None,
        sync_controls: bool = True,
    ) -> None:
        if self._busy:
            self._append_log("Busy: wait for the current request to finish.")
            return

        base_url = self.base_url_var.get().strip().rstrip("/")
        api_token = self.api_token_var.get().strip()
        self._set_busy(True)
        self._append_log(f"{description} -> {method} {path}")

        def worker() -> None:
            try:
                result = api_request(base_url, api_token, method, path, payload)
            except Exception as exc:  # pragma: no cover - UI-level failure path
                message = str(exc)
                self.after(0, lambda: self._handle_error(description, message))
                return
            self.after(0, lambda: self._handle_success(description, result, sync_controls))

        threading.Thread(target=worker, daemon=True).start()

    def _handle_error(self, description: str, message: str) -> None:
        self._set_busy(False)
        self._append_log(f"{description} failed: {message}")

    def _handle_success(
        self, description: str, result: dict[str, Any], sync_controls: bool
    ) -> None:
        self._set_busy(False)
        if "status" in result and "backend" in result:
            self._append_log(f"{description} ok: {json.dumps(result)}")
            return

        self._append_log(f"{description} ok")
        self._update_status(result, sync_controls=sync_controls)

    def _update_status(self, status_payload: dict[str, Any], sync_controls: bool) -> None:
        self.status_source_var.set(str(status_payload.get("source", "-")))
        self.status_power_var.set("on" if status_payload.get("power") else "off")
        self.status_mode_var.set(str(status_payload.get("mode", "-")))
        self.status_target_temp_var.set(str(status_payload.get("target_temp_c", "-")))
        self.status_current_temp_var.set(str(status_payload.get("current_temp_c", "-")))
        self.status_fan_var.set(str(status_payload.get("fan_speed", "-")))
        self.status_sleep_var.set(str(status_payload.get("sleep", "-")))
        self.status_uvc_var.set(str(status_payload.get("uvc", "-")))
        self.status_display_var.set(str(status_payload.get("display", "-")))
        self.status_horizontal_swing_var.set(str(status_payload.get("horizontal_swing", "-")))
        vertical_swing = status_payload.get("vertical_swing", "-")
        vertical_swing_raw = status_payload.get("vertical_swing_raw")
        if vertical_swing_raw:
            self.status_vertical_swing_var.set(f"{vertical_swing} ({vertical_swing_raw})")
        else:
            self.status_vertical_swing_var.set(str(vertical_swing))
        self.status_fault_var.set(str(status_payload.get("fault_code", "-")))

        if sync_controls:
            if "mode" in status_payload and status_payload["mode"] in {"auto", "cool", "dry", "fan"}:
                self.mode_var.set(str(status_payload["mode"]))
            if "target_temp_c" in status_payload:
                try:
                    self.temp_var.set(int(status_payload["target_temp_c"]))
                except (TypeError, ValueError):
                    pass
            if "fan_speed" in status_payload and status_payload["fan_speed"] in {
                "auto",
                "low",
                "middle",
                "high",
                "strong",
                "mute",
            }:
                self.fan_var.set(str(status_payload["fan_speed"]))
            self.sleep_var.set(bool(status_payload.get("sleep", False)))
            self.uvc_var.set(bool(status_payload.get("uvc", False)))
            self.display_var.set(bool(status_payload.get("display", True)))
            self.horizontal_swing_var.set(bool(status_payload.get("horizontal_swing", False)))
            if status_payload.get("vertical_swing") in {"fixed", "swing"}:
                self.vertical_swing_var.set(str(status_payload["vertical_swing"]))

    def refresh_status(self) -> None:
        self._run_request("Refresh status", "GET", "/ac/status")

    def set_power(self, enabled: bool) -> None:
        self._run_request("Set power", "POST", "/ac/power", {"power": enabled})

    def apply_core(self) -> None:
        payload = {
            "mode": self.mode_var.get(),
            "target_temp_c": int(self.temp_var.get()),
            "fan_speed": self.fan_var.get(),
        }
        self._run_request("Apply core controls", "POST", "/ac/apply-batch", payload)

    def apply_extras(self) -> None:
        payload = {
            "sleep": self.sleep_var.get(),
            "uvc": self.uvc_var.get(),
            "display": self.display_var.get(),
            "horizontal_swing": self.horizontal_swing_var.get(),
            "vertical_swing": self.vertical_swing_var.get(),
        }
        self._run_request("Apply extra controls", "POST", "/ac/apply-batch", payload)

    def apply_all(self) -> None:
        payload = {
            "mode": self.mode_var.get(),
            "target_temp_c": int(self.temp_var.get()),
            "fan_speed": self.fan_var.get(),
            "sleep": self.sleep_var.get(),
            "uvc": self.uvc_var.get(),
            "display": self.display_var.get(),
            "horizontal_swing": self.horizontal_swing_var.get(),
            "vertical_swing": self.vertical_swing_var.get(),
        }
        self._run_request("Apply full state", "POST", "/ac/apply-batch", payload)


def main() -> None:
    app = AcControlGui()
    app.mainloop()


if __name__ == "__main__":
    main()
