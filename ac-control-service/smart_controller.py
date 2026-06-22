from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time, timedelta, timezone
import platform
import re
import subprocess
from typing import Any, Protocol
from zoneinfo import ZoneInfo

from apscheduler.schedulers.background import BackgroundScheduler

from smart_predictor import ContextTemperaturePredictor, PredictionContext, PredictorResult
from smart_models import (
    AppSettingsModel,
    AppSettingsUpdate,
    DashboardResponse,
    FeedbackRequest,
    ManualApplyRequest,
    ProjectionPoint,
    SleepProfile,
    SleepProfileUpsert,
    SmartContext,
    SmartControlState,
    SmartControlUpdate,
    WeatherSnapshot,
)
from smart_store import SmartStore
from smart_weather import WeatherService

MIN_TEMP_C = 16
MAX_TEMP_C = 32
UTC = timezone.utc


class SmartGateway(Protocol):
    def get_status(self) -> Any:
        ...

    def apply_payload(self, payload: dict[str, object]) -> Any:
        ...


@dataclass
class Recommendation:
    payload: dict[str, object]
    mode: str
    target_temp_c: int
    explanation: list[str]
    confidence: float
    predicted_target_c: float
    sample_count: int
    baseline_target_c: float


@dataclass
class PresenceStatus:
    enabled: bool
    monitored_ips: list[str]
    reachable_ips: list[str]
    anyone_home: bool | None
    last_checked_at: str | None


class SmartController:
    def __init__(
        self,
        *,
        store: SmartStore,
        weather_service: WeatherService,
        gateway: SmartGateway,
    ) -> None:
        self.store = store
        self.weather_service = weather_service
        self.gateway = gateway
        self.scheduler = BackgroundScheduler(timezone=UTC)
        self.last_evaluation_at: datetime | None = None
        self.last_command_at: datetime | None = None
        self.next_evaluation_at: datetime | None = None
        self.presence_last_checked_at: datetime | None = None
        self.presence_last_reachable_ips: list[str] = []
        self.presence_last_anyone_home: bool | None = None
        self.predictor = ContextTemperaturePredictor()
        self._started = False

    def start(self) -> None:
        if self._started:
            return
        self.scheduler.add_job(
            self._scheduled_tick,
            "interval",
            minutes=1,
            id="smart-controller-tick",
            replace_existing=True,
        )
        self.scheduler.start()
        self._started = True

    def shutdown(self) -> None:
        if not self._started:
            return
        self.scheduler.shutdown(wait=False)
        self._started = False

    def _scheduled_tick(self) -> None:
        try:
            self.evaluate_and_apply(trigger="scheduled")
        except Exception:
            # Keep background automation resilient; request handlers surface errors.
            return

    def get_dashboard(self) -> DashboardResponse:
        status = self.gateway.get_status()
        settings = self.store.get_settings()
        weather = self._get_weather(settings)
        smart_state = self._build_smart_state(status, settings, weather)
        projections = self._build_projection_points(status, settings, weather)
        hourly_averages = self._build_hourly_average_points(settings)
        activity = self.store.get_recent_activity()
        return DashboardResponse(
            status=status.model_dump(),
            smart_control=smart_state,
            weather=weather,
            projections=projections,
            activity=activity,
            sleep_profiles=self.store.list_sleep_profiles(),
            hourly_average_targets=hourly_averages,
        )

    def get_settings(self) -> AppSettingsModel:
        return self.store.get_settings()

    def update_settings(self, update: AppSettingsUpdate) -> AppSettingsModel:
        settings = self.store.update_settings(update)
        if settings.weather_enabled and settings.latitude and settings.longitude:
            try:
                weather = self.weather_service.fetch_weather(
                    latitude=settings.latitude,
                    longitude=settings.longitude,
                    timezone=self._weather_timezone(settings),
                )
                if self._should_infer_timezone(settings.timezone) and weather.timezone:
                    settings = self.store.update_settings(
                        AppSettingsUpdate(timezone=weather.timezone)
                    )
                self.store.save_weather_snapshot(weather)
            except Exception:
                pass
        return settings

    def clear_learning_memory(self) -> dict[str, int]:
        deleted_samples = self.store.clear_training_events()
        return {"deleted_training_samples": deleted_samples}

    def list_sleep_profiles(self) -> list[SleepProfile]:
        return self.store.list_sleep_profiles()

    def upsert_sleep_profile(self, payload: SleepProfileUpsert) -> SleepProfile:
        return self.store.upsert_sleep_profile(payload)

    def delete_sleep_profile(self, profile_id: str) -> None:
        self.store.delete_sleep_profile(profile_id)

    def update_smart_control(self, update: SmartControlUpdate) -> SmartControlState:
        payload_data = update.model_dump(exclude_unset=True)
        if "enabled" in payload_data:
            payload_data["smart_enabled"] = payload_data.pop("enabled")
        payload = AppSettingsUpdate(**payload_data)
        settings = self.store.update_settings(payload)
        status = self.gateway.get_status()
        weather = self._get_weather(settings)
        return self._build_smart_state(status, settings, weather)

    def get_smart_control(self) -> SmartControlState:
        settings = self.store.get_settings()
        status = self.gateway.get_status()
        weather = self._get_weather(settings)
        return self._build_smart_state(status, settings, weather)

    def apply_manual(self, request: ManualApplyRequest) -> dict[str, Any]:
        settings = self.store.get_settings()
        status = self.gateway.apply_payload(
            request.model_dump(exclude_none=True, exclude_unset=True)
        )
        weather = self._get_weather(settings)
        presence = self._get_presence_status(settings)
        self.store.add_usage_event(
            source="manual-ui",
            action_type="manual_apply",
            mode=status.mode,
            target_temp_c=status.target_temp_c,
            fan_speed=status.fan_speed,
            indoor_temp_c=status.current_temp_c,
            outside_temp_c=weather.outside_temp_c if weather else None,
        )
        self._record_training_sample(
            settings=settings,
            weather=weather,
            presence=presence,
            preferred_target_c=float(status.target_temp_c),
            source="manual-ui",
            indoor_temp_c=status.current_temp_c,
            sample_weight=1.0,
        )
        return status.model_dump()

    def apply_feedback(self, request: FeedbackRequest) -> dict[str, Any]:
        settings = self.store.get_settings()
        status = self.gateway.get_status()
        weather = self._get_weather(settings)
        presence = self._get_presence_status(settings)
        current_target = status.target_temp_c or 24
        target_delta = -1 if request.direction == "too_hot" else 1
        new_target = self._clamp_temperature(current_target + target_delta)
        new_mode = status.mode
        payload: dict[str, object] = {"target_temp_c": new_target}
        if (
            request.direction == "too_hot"
            and status.mode in {"off", "fan"}
            and settings.allow_automation_power_on
        ):
            payload["power"] = True
            payload["mode"] = "cool"
            new_mode = "cool"
        elif request.direction == "too_cold" and status.mode == "off":
            payload["power"] = False
            new_mode = "off"
        elif not status.power and not settings.allow_automation_power_on:
            payload = {}
            new_mode = "off"

        updated = self.gateway.apply_payload(payload) if payload else status
        self.store.add_feedback_event(
            direction=request.direction,
            indoor_temp_c=status.current_temp_c,
            outside_temp_c=weather.outside_temp_c if weather else None,
            active_mode=status.mode,
            active_target_temp_c=status.target_temp_c,
            note=request.note,
        )
        self.store.add_usage_event(
            source="comfort-feedback",
            action_type=request.direction if payload else f"{request.direction}_recorded_only",
            mode=new_mode,
            target_temp_c=updated.target_temp_c,
            fan_speed=updated.fan_speed,
            indoor_temp_c=updated.current_temp_c,
            outside_temp_c=weather.outside_temp_c if weather else None,
        )
        self._record_training_sample(
            settings=settings,
            weather=weather,
            presence=presence,
            preferred_target_c=float(new_target),
            source="comfort-feedback",
            indoor_temp_c=status.current_temp_c,
            sample_weight=0.5 + settings.learning_rate,
        )
        return updated.model_dump()

    def evaluate_and_apply(self, *, trigger: str) -> SmartControlState:
        settings = self.store.get_settings()
        status = self.gateway.get_status()
        weather = self._get_weather(settings)
        presence = self._get_presence_status(settings)
        recommendation = self._recommend_for_now(status, settings, weather, presence)

        now = datetime.now(UTC)
        self.last_evaluation_at = now
        self.next_evaluation_at = now + timedelta(minutes=settings.min_cycle_minutes)
        command_sent = False

        if settings.smart_enabled:
            if self._can_send_command(settings, now, recommendation, status):
                updated = self.gateway.apply_payload(recommendation.payload)
                weather = self._get_weather(settings)
                self.last_command_at = now
                command_sent = True
                self.store.add_usage_event(
                    source="smart-control",
                    action_type=f"{trigger}_auto_adjust",
                    mode=updated.mode,
                    target_temp_c=updated.target_temp_c,
                    fan_speed=updated.fan_speed,
                    indoor_temp_c=updated.current_temp_c,
                    outside_temp_c=weather.outside_temp_c if weather else None,
                )

        self.store.add_smart_decision_event(
            decision_type=trigger,
            recommended_mode=recommendation.mode,
            recommended_target_temp_c=recommendation.target_temp_c,
            explanation=recommendation.explanation,
            command_sent=command_sent,
        )

        return self._build_smart_state(
            self.gateway.get_status(),
            settings,
            weather,
            presence=presence,
            recommendation=recommendation,
        )

    def _can_send_command(
        self,
        settings: AppSettingsModel,
        now: datetime,
        recommendation: Recommendation,
        status: Any,
    ) -> bool:
        if not recommendation.payload:
            return False
        if self.last_command_at is not None:
            elapsed = now - self.last_command_at
            if elapsed < timedelta(minutes=settings.min_cycle_minutes):
                return False
        if self._payload_matches_status(recommendation.payload, status):
            return False
        if self._in_quiet_hours(settings, self._local_now(settings.timezone).time()):
            # Quiet hours still allow bigger comfort corrections but skip tiny changes.
            target = recommendation.payload.get("target_temp_c")
            if isinstance(target, int) and abs(target - int(status.target_temp_c)) <= 1:
                return False
        return True

    def _payload_matches_status(self, payload: dict[str, object], status: Any) -> bool:
        for key, value in payload.items():
            if key == "power" and bool(status.power) != bool(value):
                return False
            if key == "mode" and status.mode != value:
                return False
            if key == "target_temp_c" and int(status.target_temp_c) != int(value):
                return False
            if key == "fan_speed" and status.fan_speed != value:
                return False
            if key == "sleep" and bool(status.sleep) != bool(value):
                return False
        return True

    def _build_smart_state(
        self,
        status: Any,
        settings: AppSettingsModel,
        weather: WeatherSnapshot | None,
        presence: PresenceStatus | None = None,
        recommendation: Recommendation | None = None,
    ) -> SmartControlState:
        presence = presence or self._get_presence_status(settings)
        recommendation = recommendation or self._recommend_for_now(status, settings, weather, presence)
        timezone_name = self._effective_timezone_name(settings, weather)
        context = SmartContext(
            local_time_iso=self._local_now(timezone_name).isoformat(),
            timezone=timezone_name,
            allow_automation_power_on=settings.allow_automation_power_on,
            presence_detection_enabled=presence.enabled,
            presence_anyone_home=presence.anyone_home,
            monitored_presence_ips=presence.monitored_ips,
            reachable_presence_ips=presence.reachable_ips,
            last_presence_check_at=presence.last_checked_at,
            outside_temp_c=weather.outside_temp_c if weather else None,
            apparent_temp_c=weather.apparent_temp_c if weather else None,
            humidity_pct=weather.humidity_pct if weather else None,
            wind_speed_kmh=weather.wind_speed_kmh if weather else None,
            weather_code=weather.weather_code if weather else None,
            forecast_high_c=weather.forecast_high_c if weather else None,
            forecast_low_c=weather.forecast_low_c if weather else None,
            indoor_temp_c=status.current_temp_c,
        )
        return SmartControlState(
            enabled=settings.smart_enabled,
            predictor_name="context-regression-v1",
            next_evaluation_at=self.next_evaluation_at.isoformat()
            if self.next_evaluation_at
            else None,
            last_evaluation_at=self.last_evaluation_at.isoformat()
            if self.last_evaluation_at
            else None,
            predicted_target_c=round(recommendation.predicted_target_c, 1),
            predictor_sample_count=recommendation.sample_count,
            memory_window_days=settings.memory_lifetime_days,
            learned_bias_c=round(
                recommendation.predicted_target_c - recommendation.baseline_target_c,
                2,
            ),
            confidence=round(recommendation.confidence, 2),
            explanation=recommendation.explanation,
            context=context,
        )

    def _recommend_for_now(
        self,
        status: Any,
        settings: AppSettingsModel,
        weather: WeatherSnapshot | None,
        presence: PresenceStatus,
    ) -> Recommendation:
        timezone_name = self._effective_timezone_name(settings, weather)
        local_now = self._local_now(timezone_name)
        profiles = self.store.list_sleep_profiles()
        sleep_profile = self._matching_sleep_profile(local_now.time(), profiles)
        self._bootstrap_training_samples_if_needed(settings, timezone_name)
        training_samples = self.store.get_training_events(settings.memory_lifetime_days, limit=2000)
        predictor = self.predictor.fit(
            samples=training_samples,
            memory_lifetime_days=settings.memory_lifetime_days,
        )
        predictor_result = predictor.predict(
            self._build_prediction_context(
                local_hour=local_now.hour + (local_now.minute / 60.0),
                indoor_temp_c=status.current_temp_c,
                weather=weather,
                presence=presence,
            )
        )

        if presence.enabled and presence.anyone_home is False:
            explanation = [
                "Presence detection did not find any monitored devices on the LAN.",
                "Automation keeps the AC off while nobody is home.",
            ]
            return Recommendation(
                payload={"power": False} if status.power else {},
                mode="off",
                target_temp_c=int(status.target_temp_c or 24),
                explanation=explanation,
                confidence=max(0.9, predictor_result.confidence),
                predicted_target_c=predictor_result.predicted_target_c,
                sample_count=predictor_result.sample_count,
                baseline_target_c=predictor_result.baseline_target_c,
            )

        predicted_target = predictor_result.predicted_target_c
        explanation = list(predictor_result.explanation)
        if sleep_profile:
            predicted_target = float(sleep_profile.target_temp_c)
            explanation.append(f"Sleep profile '{sleep_profile.label}' overrides the learned target.")

        target = self._clamp_temperature(round(predicted_target))
        mode = self._predict_mode(
            current_temp_c=status.current_temp_c,
            target_temp_c=target,
            active_sleep_profile=sleep_profile,
        )
        explanation.append(self._mode_explanation(mode, status.current_temp_c, target))
        payload: dict[str, object] = {}
        if mode == "off":
            payload["power"] = False
        else:
            payload.update(
                {
                    "power": True,
                    "mode": mode,
                    "target_temp_c": target,
                }
            )
            if sleep_profile and sleep_profile.fan_speed:
                payload["fan_speed"] = sleep_profile.fan_speed
                payload["sleep"] = True
            elif status.fan_speed in {"auto", "low", "middle", "high", "mute"}:
                payload["fan_speed"] = status.fan_speed

        confidence = predictor_result.confidence
        if not settings.allow_automation_power_on and not status.power:
            explanation.append(
                "Manual power-only is enabled, so automation waits until you turn the AC on."
            )
            payload = {}
            mode = "off"
        return Recommendation(
            payload=payload,
            mode=mode,
            target_temp_c=target,
            explanation=explanation[:4],
            confidence=confidence,
            predicted_target_c=predicted_target,
            sample_count=predictor_result.sample_count,
            baseline_target_c=predictor_result.baseline_target_c,
        )

    def _predict_mode(
        self,
        *,
        current_temp_c: float | None,
        target_temp_c: int,
        active_sleep_profile: SleepProfile | None,
    ) -> str:
        if current_temp_c is None:
            return "auto"
        delta = current_temp_c - target_temp_c
        if active_sleep_profile and delta >= 0.5:
            return "cool"
        if delta >= 2.0:
            return "cool"
        if delta >= 0.75:
            return "auto"
        if delta <= -4.0:
            return "off"
        return "fan"

    def _build_projection_points(
        self,
        status: Any,
        settings: AppSettingsModel,
        weather: WeatherSnapshot | None,
    ) -> list[ProjectionPoint]:
        presence = self._get_presence_status(settings)
        timezone_name = self._effective_timezone_name(settings, weather)
        now = self._local_now(timezone_name)
        hourly_avg = self.store.get_hourly_average_targets(settings.memory_lifetime_days)
        predictor = self.predictor.fit(
            samples=self.store.get_training_events(settings.memory_lifetime_days, limit=2000),
            memory_lifetime_days=settings.memory_lifetime_days,
        )
        profiles = self.store.list_sleep_profiles()
        points: list[ProjectionPoint] = []

        for hour in range(24):
            hour_time = now.replace(hour=hour, minute=0, second=0, microsecond=0)
            minutes = hour * 60
            if hour < now.hour:
                target = self._baseline_target_for_hour(hourly_avg, hour)
                mode = "off" if target <= 0 else status.mode if status.power else "off"
                segment = "past"
            elif hour == now.hour:
                target = int(status.target_temp_c)
                mode = status.mode if status.power else "off"
                segment = "current"
            else:
                profile = self._matching_sleep_profile(hour_time.time(), profiles)
                prediction = predictor.predict(
                    self._build_prediction_context(
                        local_hour=float(hour),
                        indoor_temp_c=status.current_temp_c,
                        weather=weather,
                        presence=presence,
                    )
                )
                target = self._clamp_temperature(
                    round(profile.target_temp_c if profile else prediction.predicted_target_c)
                )
                mode = self._predict_mode(
                    current_temp_c=status.current_temp_c,
                    target_temp_c=target,
                    active_sleep_profile=profile,
                )
                segment = "future"
            if presence.enabled and presence.anyone_home is False:
                mode = "off"
            elif not settings.allow_automation_power_on and not status.power and segment in {
                "current",
                "future",
            }:
                mode = "off"
            points.append(
                ProjectionPoint(
                    hour_label=f"{hour:02d}:00",
                    minutes_from_midnight=minutes,
                    segment=segment,
                    mode=mode,  # type: ignore[arg-type]
                    target_temp_c=self._clamp_temperature(target),
                )
            )
        return points

    def _build_hourly_average_points(self, settings: AppSettingsModel) -> list[ProjectionPoint]:
        hourly_avg = self.store.get_hourly_average_targets(settings.memory_lifetime_days)
        points: list[ProjectionPoint] = []
        for hour in range(24):
            if hour not in hourly_avg:
                continue
            points.append(
                ProjectionPoint(
                    hour_label=f"{hour:02d}:00",
                    minutes_from_midnight=hour * 60,
                    segment="past",
                    mode="auto",
                    target_temp_c=self._clamp_temperature(round(hourly_avg[hour])),
                )
            )
        return points

    def _get_weather(self, settings: AppSettingsModel) -> WeatherSnapshot | None:
        if not settings.weather_enabled or not settings.latitude or not settings.longitude:
            return self.store.get_latest_weather_snapshot()

        cached = self.store.get_latest_weather_snapshot()
        if cached is not None:
            observed_at = self._parse_iso(cached.observed_at)
            if observed_at and datetime.now(UTC) - observed_at < timedelta(minutes=20):
                return cached

        try:
            weather = self.weather_service.fetch_weather(
                latitude=settings.latitude,
                longitude=settings.longitude,
                timezone=self._weather_timezone(settings),
            )
            if settings.timezone != weather.timezone:
                self.store.update_settings(AppSettingsUpdate(timezone=weather.timezone))
            self.store.save_weather_snapshot(weather)
            return weather
        except Exception:
            return cached

    def _record_training_sample(
        self,
        *,
        settings: AppSettingsModel,
        weather: WeatherSnapshot | None,
        presence: PresenceStatus,
        preferred_target_c: float,
        source: str,
        indoor_temp_c: float | None,
        sample_weight: float,
    ) -> None:
        timezone_name = self._effective_timezone_name(settings, weather)
        local_now = self._local_now(timezone_name)
        self.store.add_training_event(
            source=source,
            preferred_target_c=preferred_target_c,
            local_hour=local_now.hour + (local_now.minute / 60.0),
            indoor_temp_c=indoor_temp_c,
            outside_temp_c=weather.outside_temp_c if weather else None,
            apparent_temp_c=weather.apparent_temp_c if weather else None,
            humidity_pct=weather.humidity_pct if weather else None,
            wind_speed_kmh=weather.wind_speed_kmh if weather else None,
            forecast_high_c=weather.forecast_high_c if weather else None,
            forecast_low_c=weather.forecast_low_c if weather else None,
            presence_anyone_home=presence.anyone_home,
            sample_weight=sample_weight,
        )

    def _bootstrap_training_samples_if_needed(
        self,
        settings: AppSettingsModel,
        timezone_name: str,
    ) -> None:
        if self.store.count_training_events() > 0:
            return
        for row in self.store.get_usage_events(limit=2000):
            if row["source"] not in {"manual-ui", "comfort-feedback"}:
                continue
            if row["target_temp_c"] is None:
                continue
            sample_weight = 1.0 if row["source"] == "manual-ui" else 0.5 + settings.learning_rate
            self.store.add_training_event(
                occurred_at=row["occurred_at"],
                source=row["source"],
                preferred_target_c=float(row["target_temp_c"]),
                local_hour=float(self.store._local_hour(row["occurred_at"], timezone_name)),
                indoor_temp_c=row["indoor_temp_c"],
                outside_temp_c=row["outside_temp_c"],
                apparent_temp_c=None,
                humidity_pct=None,
                wind_speed_kmh=None,
                forecast_high_c=None,
                forecast_low_c=None,
                presence_anyone_home=None,
                sample_weight=sample_weight,
            )

    def _build_prediction_context(
        self,
        *,
        local_hour: float,
        indoor_temp_c: float | None,
        weather: WeatherSnapshot | None,
        presence: PresenceStatus,
    ) -> PredictionContext:
        return PredictionContext(
            local_hour=local_hour,
            indoor_temp_c=indoor_temp_c,
            outside_temp_c=weather.outside_temp_c if weather else None,
            apparent_temp_c=weather.apparent_temp_c if weather else None,
            humidity_pct=weather.humidity_pct if weather else None,
            wind_speed_kmh=weather.wind_speed_kmh if weather else None,
            forecast_high_c=weather.forecast_high_c if weather else None,
            forecast_low_c=weather.forecast_low_c if weather else None,
            presence_anyone_home=presence.anyone_home,
        )

    def _baseline_target_for_hour(self, hourly_avg: dict[int, float], hour: int) -> float:
        if hour in hourly_avg:
            return hourly_avg[hour]
        nearest_distance = 25
        nearest_value = 24.0
        for candidate_hour, candidate_value in hourly_avg.items():
            distance = min(abs(candidate_hour - hour), 24 - abs(candidate_hour - hour))
            if distance < nearest_distance:
                nearest_distance = distance
                nearest_value = candidate_value
        return nearest_value

    def _mode_explanation(
        self,
        mode: str,
        current_temp_c: float | None,
        target_temp_c: int,
    ) -> str:
        if current_temp_c is None:
            return f"The controller uses {mode} because the indoor reading is unavailable."
        delta = current_temp_c - target_temp_c
        if mode == "cool":
            return f"The room is {delta:.1f}C above the preferred target, so cooling is the strongest match."
        if mode == "auto":
            return f"The room is slightly above the preferred target, so auto can trim comfort without overreacting."
        if mode == "fan":
            return "The room is already near or below the preferred target, so fan mode focuses on circulation."
        return "The room is well below the preferred target, so the controller backs off completely."

    def _weather_timezone(self, settings: AppSettingsModel) -> str:
        timezone_name = (settings.timezone or "").strip()
        if self._should_infer_timezone(timezone_name):
            return "auto"
        return "auto" if self._parse_fixed_offset_timezone(timezone_name) else timezone_name

    def _should_infer_timezone(self, timezone_name: str | None) -> bool:
        return (timezone_name or "").strip() in {"", "UTC"}

    def _effective_timezone_name(
        self, settings: AppSettingsModel, weather: WeatherSnapshot | None
    ) -> str:
        if weather and weather.timezone:
            return weather.timezone
        return settings.timezone

    def _local_now(self, timezone_name: str) -> datetime:
        fixed_offset_timezone = self._parse_fixed_offset_timezone(timezone_name)
        if fixed_offset_timezone is not None:
            return datetime.now(fixed_offset_timezone)
        try:
            tz = ZoneInfo(timezone_name)
        except Exception:
            tz = UTC
        return datetime.now(tz)

    def _parse_fixed_offset_timezone(self, timezone_name: str):
        text = (timezone_name or "").strip().upper()
        match = re.fullmatch(
            r"(?:UTC|GMT)([+-])(\d{1,2})(?::?(\d{2}))?",
            text,
        )
        if not match:
            return None
        sign_text, hours_text, minutes_text = match.groups()
        hours = int(hours_text)
        minutes = int(minutes_text or "0")
        delta = timedelta(hours=hours, minutes=minutes)
        if sign_text == "-":
            delta = -delta
        return timezone(delta)

    def _get_presence_status(self, settings: AppSettingsModel) -> PresenceStatus:
        monitored_ips = [ip.strip() for ip in settings.presence_device_ips if ip.strip()]
        if not settings.presence_detection_enabled or not monitored_ips:
            return PresenceStatus(
                enabled=settings.presence_detection_enabled,
                monitored_ips=monitored_ips,
                reachable_ips=[],
                anyone_home=None,
                last_checked_at=None,
            )

        now = datetime.now(UTC)
        if (
            self.presence_last_checked_at is not None
            and now - self.presence_last_checked_at
            < timedelta(minutes=settings.presence_check_interval_minutes)
        ):
            return PresenceStatus(
                enabled=True,
                monitored_ips=monitored_ips,
                reachable_ips=list(self.presence_last_reachable_ips),
                anyone_home=self.presence_last_anyone_home,
                last_checked_at=self.presence_last_checked_at.isoformat(),
            )

        reachable_ips: list[str] = []
        try:
            for ip_address in monitored_ips:
                if self._ping_host(ip_address):
                    reachable_ips.append(ip_address)
            self.presence_last_checked_at = now
            self.presence_last_reachable_ips = reachable_ips
            self.presence_last_anyone_home = bool(reachable_ips)
        except Exception:
            pass

        return PresenceStatus(
            enabled=True,
            monitored_ips=monitored_ips,
            reachable_ips=list(self.presence_last_reachable_ips),
            anyone_home=self.presence_last_anyone_home,
            last_checked_at=self.presence_last_checked_at.isoformat()
            if self.presence_last_checked_at
            else None,
        )

    def _ping_host(self, ip_address: str) -> bool:
        system = platform.system().lower()
        if system == "windows":
            command = ["ping", "-n", "1", "-w", "1000", ip_address]
        else:
            command = ["ping", "-c", "1", "-W", "1", ip_address]
        result = subprocess.run(
            command,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
            timeout=3,
        )
        return result.returncode == 0

    def _matching_sleep_profile(
        self, current_time: time, profiles: list[SleepProfile]
    ) -> SleepProfile | None:
        for profile in profiles:
            if not profile.enabled:
                continue
            start = self._parse_time(profile.start_time)
            end = self._parse_time(profile.end_time)
            if start is None or end is None:
                continue
            if self._time_in_window(current_time, start, end):
                return profile
        return None

    def _time_in_window(self, current: time, start: time, end: time) -> bool:
        if start <= end:
            return start <= current <= end
        return current >= start or current <= end

    def _parse_time(self, raw: str | None) -> time | None:
        if not raw:
            return None
        try:
            hour_text, minute_text = raw.split(":", 1)
            return time(hour=int(hour_text), minute=int(minute_text))
        except ValueError:
            return None

    def _parse_iso(self, raw: str | None) -> datetime | None:
        if not raw:
            return None
        text = raw[:-1] + "+00:00" if raw.endswith("Z") else raw
        try:
            parsed = datetime.fromisoformat(text)
            return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)
        except ValueError:
            return None

    def _in_quiet_hours(self, settings: AppSettingsModel, current_time: time) -> bool:
        start = self._parse_time(settings.quiet_hours_start)
        end = self._parse_time(settings.quiet_hours_end)
        if start is None or end is None:
            return False
        return self._time_in_window(current_time, start, end)

    def _clamp_temperature(self, value: int) -> int:
        return max(MIN_TEMP_C, min(MAX_TEMP_C, int(value)))
