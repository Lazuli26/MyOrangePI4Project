from __future__ import annotations

import os
from typing import Literal, Optional, Protocol

from fastapi import Depends, FastAPI, Header, HTTPException, status
from pydantic import BaseModel, Field
from ac_config import Settings

try:
    import tinytuya
except ImportError:  # pragma: no cover - optional until real Tuya hookup exists
    tinytuya = None


Mode = Literal["off", "auto", "cool", "heat", "dry", "fan"]
# Conservative public API profile based on the Smart Life app behavior observed for
# this ADINA unit. These limits are intentionally narrower than the Tuya product
# schema and should be revisited if future testing proves additional modes exist.
ModeRequestValue = Literal["auto", "cool", "dry", "fan", "cold", "wet", "wind"]
FanSpeed = Literal["auto", "low", "medium", "middle", "high", "strong", "mute"]
VerticalSwing = Literal["fixed", "swing"]

# The mobile app only exposes 16-32 C even though the generic Tuya schema reports a
# much wider range. Keep the API conservative until the device is tested further.
APP_OBSERVED_MIN_TEMP_C = 16
APP_OBSERVED_MAX_TEMP_C = 32

MODE_TO_TUYA = {
    "auto": "auto",
    "cool": "cold",
    "heat": "hot",
    "dry": "wet",
    "fan": "wind",
    "cold": "cold",
    "hot": "hot",
    "wet": "wet",
    "wind": "wind",
}
TUYA_TO_MODE = {
    "auto": "auto",
    "cold": "cool",
    "hot": "heat",
    "wet": "dry",
    "wind": "fan",
    "cool": "cool",
    "heat": "heat",
    "dry": "dry",
    "fan": "fan",
}
VERTICAL_SWING_TO_TUYA = {
    # App-observed vertical positions for this unit. Broader Tuya vane positions are
    # intentionally hidden until they are verified to be useful and supported.
    "fixed": "off",
    "swing": "same",
}
TUYA_TO_VERTICAL_SWING = {
    "off": "fixed",
    "same": "swing",
}
FAN_TO_TUYA = {
    "auto": "auto",
    "low": "low",
    "medium": "middle",
    "middle": "middle",
    "high": "high",
    "strong": "strong",
    "mute": "mute",
}
TUYA_TO_FAN = {
    "auto": "auto",
    "low": "low",
    "middle": "middle",
    "medium": "middle",
    "high": "high",
    "strong": "strong",
    "mute": "mute",
}


class AcStatus(BaseModel):
    online: bool = True
    power: bool = False
    mode: Mode = "off"
    target_temp_c: int = Field(
        default=24, ge=APP_OBSERVED_MIN_TEMP_C, le=APP_OBSERVED_MAX_TEMP_C
    )
    current_temp_c: Optional[float] = None
    fan_speed: FanSpeed = "auto"
    sleep: bool = False
    uvc: bool = False
    display: bool = True
    horizontal_swing: bool = False
    vertical_swing: VerticalSwing = "fixed"
    vertical_swing_raw: Optional[str] = None
    fault_code: Optional[int] = None
    source: str


class PowerRequest(BaseModel):
    power: bool


class ModeRequest(BaseModel):
    mode: ModeRequestValue


class TemperatureRequest(BaseModel):
    target_temp_c: int = Field(ge=APP_OBSERVED_MIN_TEMP_C, le=APP_OBSERVED_MAX_TEMP_C)


class FanRequest(BaseModel):
    fan_speed: FanSpeed


class ToggleRequest(BaseModel):
    enabled: bool


class VerticalSwingRequest(BaseModel):
    # The app currently exposes only "fixed" and "swing" for vertical swing, so the
    # public API intentionally matches that narrower surface for now.
    mode: VerticalSwing


class ApplyRequest(BaseModel):
    power: Optional[bool] = None
    mode: Optional[ModeRequestValue] = None
    target_temp_c: Optional[int] = Field(
        default=None, ge=APP_OBSERVED_MIN_TEMP_C, le=APP_OBSERVED_MAX_TEMP_C
    )
    fan_speed: Optional[FanSpeed] = None
    sleep: Optional[bool] = None
    uvc: Optional[bool] = None
    display: Optional[bool] = None
    horizontal_swing: Optional[bool] = None
    vertical_swing: Optional[VerticalSwing] = None


class BackendNotReadyError(RuntimeError):
    pass


class AcAdapter(Protocol):
    def get_status(self) -> AcStatus:
        ...

    def set_power(self, power: bool) -> AcStatus:
        ...

    def set_mode(self, mode: str) -> AcStatus:
        ...

    def set_target_temp(self, target_temp_c: int) -> AcStatus:
        ...

    def set_fan_speed(self, fan_speed: str) -> AcStatus:
        ...

    def set_sleep(self, enabled: bool) -> AcStatus:
        ...

    def set_uvc(self, enabled: bool) -> AcStatus:
        ...

    def set_display(self, enabled: bool) -> AcStatus:
        ...

    def set_horizontal_swing(self, enabled: bool) -> AcStatus:
        ...

    def set_vertical_swing(self, mode: str) -> AcStatus:
        ...


class MockAcAdapter:
    def __init__(self) -> None:
        self._status = AcStatus(
            source="mock",
            online=True,
            power=False,
            mode="off",
            target_temp_c=24,
            current_temp_c=26.5,
            fan_speed="auto",
        )

    def get_status(self) -> AcStatus:
        return self._status.model_copy(deep=True)

    def set_power(self, power: bool) -> AcStatus:
        self._status.power = power
        if not power:
            self._status.mode = "off"
        elif self._status.mode == "off":
            self._status.mode = "cool"
        return self.get_status()

    def set_mode(self, mode: str) -> AcStatus:
        self._status.mode = mode  # type: ignore[assignment]
        self._status.power = True
        return self.get_status()

    def set_target_temp(self, target_temp_c: int) -> AcStatus:
        self._status.target_temp_c = target_temp_c
        return self.get_status()

    def set_fan_speed(self, fan_speed: str) -> AcStatus:
        self._status.fan_speed = fan_speed  # type: ignore[assignment]
        return self.get_status()

    def set_sleep(self, enabled: bool) -> AcStatus:
        self._status.sleep = enabled
        return self.get_status()

    def set_uvc(self, enabled: bool) -> AcStatus:
        self._status.uvc = enabled
        return self.get_status()

    def set_display(self, enabled: bool) -> AcStatus:
        self._status.display = enabled
        return self.get_status()

    def set_horizontal_swing(self, enabled: bool) -> AcStatus:
        self._status.horizontal_swing = enabled
        return self.get_status()

    def set_vertical_swing(self, mode: str) -> AcStatus:
        self._status.vertical_swing = mode  # type: ignore[assignment]
        self._status.vertical_swing_raw = VERTICAL_SWING_TO_TUYA.get(mode, mode)
        return self.get_status()


class TinyTuyaAcAdapter:
    def __init__(self, settings: Settings) -> None:
        missing = [
            name
            for name, value in (
                ("TUYA_DEVICE_ID", settings.tuya_device_id),
                ("TUYA_DEVICE_IP", settings.tuya_device_ip),
                ("TUYA_LOCAL_KEY", settings.tuya_local_key),
            )
            if not value
        ]
        if missing:
            raise BackendNotReadyError(
                f"tinytuya backend selected but missing: {', '.join(missing)}"
            )
        if tinytuya is None:
            raise BackendNotReadyError(
                "tinytuya is not installed. Run: pip install -r requirements.txt"
            )
        self.settings = settings
        self._device = tinytuya.Device(
            dev_id=settings.tuya_device_id,
            address=settings.tuya_device_ip,
            local_key=settings.tuya_local_key,
        )
        self._device.set_version(float(settings.tuya_device_version))

    def _dps_key(self, dpid: int) -> str:
        return str(dpid)

    def _read_status(self) -> dict:
        response = self._device.status()
        dps = response.get("dps")
        if not isinstance(dps, dict):
            raise BackendNotReadyError(f"Unexpected TinyTuya status payload: {response!r}")
        return dps

    def _parse_status(self, dps: dict) -> AcStatus:
        power = bool(dps.get(self._dps_key(self.settings.tuya_power_dpid), False))
        mode_value = str(dps.get(self._dps_key(self.settings.tuya_mode_dpid), "off"))
        target_temp = dps.get(self._dps_key(self.settings.tuya_target_temp_dpid), 24)
        current_temp = dps.get(self._dps_key(self.settings.tuya_current_temp_dpid))
        fan_speed = str(dps.get(self._dps_key(self.settings.tuya_fan_speed_dpid), "auto"))
        sleep = bool(dps.get(self._dps_key(self.settings.tuya_sleep_dpid), False))
        uvc = bool(dps.get(self._dps_key(self.settings.tuya_uvc_dpid), False))
        display = bool(dps.get(self._dps_key(self.settings.tuya_display_dpid), True))
        horizontal_swing = bool(
            dps.get(self._dps_key(self.settings.tuya_horizontal_swing_dpid), False)
        )
        vertical_swing_raw_value = dps.get(
            self._dps_key(self.settings.tuya_vertical_swing_dpid)
        )
        fault_code = dps.get(self._dps_key(self.settings.tuya_fault_dpid))

        if not power:
            normalized_mode: Mode = "off"
        elif mode_value in TUYA_TO_MODE:
            normalized_mode = TUYA_TO_MODE[mode_value]  # type: ignore[assignment]
        else:
            normalized_mode = "auto"

        normalized_fan: FanSpeed
        if fan_speed in TUYA_TO_FAN:
            normalized_fan = TUYA_TO_FAN[fan_speed]  # type: ignore[assignment]
        else:
            normalized_fan = "auto"

        try:
            normalized_target = int(target_temp)
        except (TypeError, ValueError):
            normalized_target = 24

        normalized_current: Optional[float]
        try:
            normalized_current = float(current_temp) if current_temp is not None else None
        except (TypeError, ValueError):
            normalized_current = None

        try:
            normalized_fault = int(fault_code) if fault_code is not None else None
        except (TypeError, ValueError):
            normalized_fault = None

        raw_vertical_swing = (
            str(vertical_swing_raw_value) if vertical_swing_raw_value is not None else None
        )
        normalized_vertical_swing: VerticalSwing = TUYA_TO_VERTICAL_SWING.get(
            raw_vertical_swing or "off", "fixed"
        )  # type: ignore[assignment]

        return AcStatus(
            source="tinytuya",
            online=True,
            power=power,
            mode=normalized_mode,
            target_temp_c=normalized_target,
            current_temp_c=normalized_current,
            fan_speed=normalized_fan,
            sleep=sleep,
            uvc=uvc,
            display=display,
            horizontal_swing=horizontal_swing,
            vertical_swing=normalized_vertical_swing,
            vertical_swing_raw=raw_vertical_swing,
            fault_code=normalized_fault,
        )

    def get_status(self) -> AcStatus:
        return self._parse_status(self._read_status())

    def set_power(self, power: bool) -> AcStatus:
        self._device.set_status(power, switch=self.settings.tuya_power_dpid)
        return self.get_status()

    def set_mode(self, mode: str) -> AcStatus:
        if mode == "off":
            self._device.set_status(False, switch=self.settings.tuya_power_dpid)
            return self.get_status()

        tuya_mode = MODE_TO_TUYA.get(mode, mode)
        self._device.set_value(self.settings.tuya_mode_dpid, tuya_mode)
        if tuya_mode != "off":
            self._device.set_status(True, switch=self.settings.tuya_power_dpid)
        return self.get_status()

    def set_target_temp(self, target_temp_c: int) -> AcStatus:
        self._device.set_value(self.settings.tuya_target_temp_dpid, target_temp_c)
        return self.get_status()

    def set_fan_speed(self, fan_speed: str) -> AcStatus:
        tuya_fan_speed = FAN_TO_TUYA.get(fan_speed, fan_speed)
        self._device.set_value(self.settings.tuya_fan_speed_dpid, tuya_fan_speed)
        return self.get_status()

    def set_sleep(self, enabled: bool) -> AcStatus:
        self._device.set_value(self.settings.tuya_sleep_dpid, enabled)
        return self.get_status()

    def set_uvc(self, enabled: bool) -> AcStatus:
        self._device.set_value(self.settings.tuya_uvc_dpid, enabled)
        return self.get_status()

    def set_display(self, enabled: bool) -> AcStatus:
        self._device.set_value(self.settings.tuya_display_dpid, enabled)
        return self.get_status()

    def set_horizontal_swing(self, enabled: bool) -> AcStatus:
        self._device.set_value(self.settings.tuya_horizontal_swing_dpid, enabled)
        return self.get_status()

    def set_vertical_swing(self, mode: str) -> AcStatus:
        tuya_vertical_swing = VERTICAL_SWING_TO_TUYA.get(mode, mode)
        self._device.set_value(self.settings.tuya_vertical_swing_dpid, tuya_vertical_swing)
        return self.get_status()


settings = Settings()


def _build_adapter() -> AcAdapter:
    if settings.backend == "mock":
        return MockAcAdapter()
    if settings.backend == "tinytuya":
        return TinyTuyaAcAdapter(settings)
    raise BackendNotReadyError(
        f"Unsupported AC_BACKEND '{settings.backend}'. Use 'mock' or 'tinytuya'."
    )


adapter = _build_adapter()
app = FastAPI(
    title="AC Control Service",
    version="0.1.0",
    description=(
        "Lightweight AC control API for testing on a PC now and moving to the OrangePi later."
    ),
)


def require_token(x_api_token: Optional[str] = Header(default=None)) -> None:
    if not settings.api_token:
        return
    if x_api_token != settings.api_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing X-API-Token header.",
        )


def with_backend_error(action):
    try:
        return action()
    except BackendNotReadyError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "backend": settings.backend}


@app.get("/ac/status", response_model=AcStatus, dependencies=[Depends(require_token)])
def get_ac_status() -> AcStatus:
    return with_backend_error(adapter.get_status)


@app.post("/ac/power", response_model=AcStatus, dependencies=[Depends(require_token)])
def set_power(request: PowerRequest) -> AcStatus:
    return with_backend_error(lambda: adapter.set_power(request.power))


@app.post("/ac/mode", response_model=AcStatus, dependencies=[Depends(require_token)])
def set_mode(request: ModeRequest) -> AcStatus:
    return with_backend_error(lambda: adapter.set_mode(request.mode))


@app.post(
    "/ac/temperature",
    response_model=AcStatus,
    dependencies=[Depends(require_token)],
)
def set_temperature(request: TemperatureRequest) -> AcStatus:
    return with_backend_error(lambda: adapter.set_target_temp(request.target_temp_c))


@app.post("/ac/fan", response_model=AcStatus, dependencies=[Depends(require_token)])
def set_fan(request: FanRequest) -> AcStatus:
    return with_backend_error(lambda: adapter.set_fan_speed(request.fan_speed))


@app.post("/ac/sleep", response_model=AcStatus, dependencies=[Depends(require_token)])
def set_sleep(request: ToggleRequest) -> AcStatus:
    return with_backend_error(lambda: adapter.set_sleep(request.enabled))


@app.post("/ac/uvc", response_model=AcStatus, dependencies=[Depends(require_token)])
def set_uvc(request: ToggleRequest) -> AcStatus:
    return with_backend_error(lambda: adapter.set_uvc(request.enabled))


@app.post("/ac/display", response_model=AcStatus, dependencies=[Depends(require_token)])
def set_display(request: ToggleRequest) -> AcStatus:
    return with_backend_error(lambda: adapter.set_display(request.enabled))


@app.post(
    "/ac/swing/horizontal",
    response_model=AcStatus,
    dependencies=[Depends(require_token)],
)
def set_horizontal_swing(request: ToggleRequest) -> AcStatus:
    return with_backend_error(lambda: adapter.set_horizontal_swing(request.enabled))


@app.post(
    "/ac/swing/vertical",
    response_model=AcStatus,
    dependencies=[Depends(require_token)],
)
def set_vertical_swing(request: VerticalSwingRequest) -> AcStatus:
    return with_backend_error(lambda: adapter.set_vertical_swing(request.mode))


@app.post("/ac/apply", response_model=AcStatus, dependencies=[Depends(require_token)])
def apply_state(request: ApplyRequest) -> AcStatus:
    status_snapshot = with_backend_error(adapter.get_status)
    if request.power is not None:
        status_snapshot = with_backend_error(lambda: adapter.set_power(request.power))
    if request.mode is not None:
        status_snapshot = with_backend_error(lambda: adapter.set_mode(request.mode))
    if request.target_temp_c is not None:
        status_snapshot = with_backend_error(
            lambda: adapter.set_target_temp(request.target_temp_c)
        )
    if request.fan_speed is not None:
        status_snapshot = with_backend_error(
            lambda: adapter.set_fan_speed(request.fan_speed)
        )
    if request.sleep is not None:
        status_snapshot = with_backend_error(lambda: adapter.set_sleep(request.sleep))
    if request.uvc is not None:
        status_snapshot = with_backend_error(lambda: adapter.set_uvc(request.uvc))
    if request.display is not None:
        status_snapshot = with_backend_error(lambda: adapter.set_display(request.display))
    if request.horizontal_swing is not None:
        status_snapshot = with_backend_error(
            lambda: adapter.set_horizontal_swing(request.horizontal_swing)
        )
    if request.vertical_swing is not None:
        status_snapshot = with_backend_error(
            lambda: adapter.set_vertical_swing(request.vertical_swing)
        )
    return status_snapshot
