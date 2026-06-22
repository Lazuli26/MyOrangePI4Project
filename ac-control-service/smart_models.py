from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


Mode = Literal["off", "auto", "cool", "dry", "fan"]
FanSpeed = Literal["auto", "low", "middle", "high", "strong", "mute"]
VerticalSwing = Literal["fixed", "swing"]
ProjectionSegment = Literal["past", "current", "future"]
FeedbackDirection = Literal["too_cold", "too_hot"]


class AppSettingsModel(BaseModel):
    location_label: str = "Home"
    latitude: float = 0.0
    longitude: float = 0.0
    timezone: str = "UTC"
    smart_enabled: bool = False
    allow_automation_power_on: bool = False
    min_cycle_minutes: int = Field(default=15, ge=5, le=120)
    max_temp_step_c: int = Field(default=2, ge=1, le=4)
    learning_rate: float = Field(default=0.25, ge=0.0, le=1.0)
    memory_lifetime_days: int = Field(default=45, ge=7, le=365)
    quiet_hours_start: Optional[str] = None
    quiet_hours_end: Optional[str] = None
    weather_enabled: bool = True
    presence_detection_enabled: bool = False
    presence_check_interval_minutes: int = Field(default=5, ge=1, le=120)
    presence_device_ips: list[str] = Field(default_factory=list)
    updated_at: Optional[str] = None


class AppSettingsUpdate(BaseModel):
    location_label: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    timezone: Optional[str] = None
    smart_enabled: Optional[bool] = None
    allow_automation_power_on: Optional[bool] = None
    min_cycle_minutes: Optional[int] = Field(default=None, ge=5, le=120)
    max_temp_step_c: Optional[int] = Field(default=None, ge=1, le=4)
    learning_rate: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    memory_lifetime_days: Optional[int] = Field(default=None, ge=7, le=365)
    quiet_hours_start: Optional[str] = None
    quiet_hours_end: Optional[str] = None
    weather_enabled: Optional[bool] = None
    presence_detection_enabled: Optional[bool] = None
    presence_check_interval_minutes: Optional[int] = Field(default=None, ge=1, le=120)
    presence_device_ips: Optional[list[str]] = None


class SleepProfile(BaseModel):
    id: str
    label: str
    start_time: str
    end_time: str
    target_temp_c: int = Field(ge=16, le=32)
    fan_speed: Optional[FanSpeed] = None
    enabled: bool = True
    updated_at: Optional[str] = None


class SleepProfileUpsert(BaseModel):
    id: Optional[str] = None
    label: str
    start_time: str
    end_time: str
    target_temp_c: int = Field(ge=16, le=32)
    fan_speed: Optional[FanSpeed] = None
    enabled: bool = True


class WeatherSnapshot(BaseModel):
    observed_at: str
    timezone: str
    outside_temp_c: Optional[float] = None
    apparent_temp_c: Optional[float] = None
    humidity_pct: Optional[float] = None
    wind_speed_kmh: Optional[float] = None
    weather_code: Optional[int] = None
    is_day: Optional[bool] = None
    forecast_high_c: Optional[float] = None
    forecast_low_c: Optional[float] = None


class SmartContext(BaseModel):
    local_time_iso: str
    timezone: str
    allow_automation_power_on: bool = False
    presence_detection_enabled: bool = False
    presence_anyone_home: Optional[bool] = None
    monitored_presence_ips: list[str] = Field(default_factory=list)
    reachable_presence_ips: list[str] = Field(default_factory=list)
    last_presence_check_at: Optional[str] = None
    outside_temp_c: Optional[float] = None
    apparent_temp_c: Optional[float] = None
    humidity_pct: Optional[float] = None
    wind_speed_kmh: Optional[float] = None
    weather_code: Optional[int] = None
    forecast_high_c: Optional[float] = None
    forecast_low_c: Optional[float] = None
    indoor_temp_c: Optional[float] = None


class SmartControlState(BaseModel):
    enabled: bool
    next_evaluation_at: Optional[str] = None
    last_evaluation_at: Optional[str] = None
    predictor_name: str = "context-regression-v1"
    predicted_target_c: float = 24.0
    predictor_sample_count: int = 0
    memory_window_days: int = 45
    learned_bias_c: float = 0.0
    confidence: float = 0.0
    explanation: list[str] = Field(default_factory=list)
    context: SmartContext


@dataclass
class TrainingSample:
    occurred_at: str
    source: str
    preferred_target_c: float
    local_hour: float
    indoor_temp_c: float | None = None
    outside_temp_c: float | None = None
    apparent_temp_c: float | None = None
    humidity_pct: float | None = None
    wind_speed_kmh: float | None = None
    forecast_high_c: float | None = None
    forecast_low_c: float | None = None
    presence_anyone_home: bool | None = None
    sample_weight: float = 1.0


class ProjectionPoint(BaseModel):
    hour_label: str
    minutes_from_midnight: int
    segment: ProjectionSegment
    mode: Mode
    target_temp_c: int


class ActivityItem(BaseModel):
    id: str
    occurred_at: str
    kind: Literal["manual", "feedback", "smart"]
    title: str
    detail: str
    command_sent: Optional[bool] = None


class DashboardResponse(BaseModel):
    status: dict
    smart_control: SmartControlState
    weather: Optional[WeatherSnapshot] = None
    projections: list[ProjectionPoint]
    activity: list[ActivityItem]
    sleep_profiles: list[SleepProfile]
    hourly_average_targets: list[ProjectionPoint]


class ManualApplyRequest(BaseModel):
    power: Optional[bool] = None
    mode: Optional[Literal["auto", "cool", "dry", "fan"]] = None
    target_temp_c: Optional[int] = Field(default=None, ge=16, le=32)
    fan_speed: Optional[FanSpeed] = None
    sleep: Optional[bool] = None
    uvc: Optional[bool] = None
    display: Optional[bool] = None
    horizontal_swing: Optional[bool] = None
    vertical_swing: Optional[VerticalSwing] = None


class FeedbackRequest(BaseModel):
    direction: FeedbackDirection
    note: Optional[str] = None


class SmartControlUpdate(BaseModel):
    enabled: Optional[bool] = None
    min_cycle_minutes: Optional[int] = Field(default=None, ge=5, le=120)
    max_temp_step_c: Optional[int] = Field(default=None, ge=1, le=4)
    learning_rate: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    quiet_hours_start: Optional[str] = None
    quiet_hours_end: Optional[str] = None


def utc_now_iso() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
