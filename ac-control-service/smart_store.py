from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from smart_models import (
    ActivityItem,
    AppSettingsModel,
    AppSettingsUpdate,
    SleepProfile,
    SleepProfileUpsert,
    TrainingSample,
    WeatherSnapshot,
    utc_now_iso,
)


UTC = timezone.utc


class SmartStore:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                create table if not exists app_settings (
                  id text primary key,
                  location_label text not null,
                  latitude real not null,
                  longitude real not null,
                  timezone text not null,
                  smart_enabled integer not null default 0,
                  allow_automation_power_on integer not null default 0,
                  min_cycle_minutes integer not null default 15,
                  max_temp_step_c integer not null default 2,
                  learning_rate real not null default 0.25,
                  quiet_hours_start text,
                  quiet_hours_end text,
                  weather_enabled integer not null default 1,
                  presence_detection_enabled integer not null default 0,
                  presence_check_interval_minutes integer not null default 5,
                  presence_device_ips text not null default '[]',
                  updated_at text not null
                );

                create table if not exists sleep_profile (
                  id text primary key,
                  label text not null,
                  start_time text not null,
                  end_time text not null,
                  target_temp_c integer not null,
                  fan_speed text,
                  enabled integer not null default 1,
                  updated_at text not null
                );

                create table if not exists weather_snapshot (
                  id text primary key,
                  observed_at text not null,
                  timezone text not null,
                  outside_temp_c real,
                  apparent_temp_c real,
                  humidity_pct real,
                  wind_speed_kmh real,
                  weather_code integer,
                  is_day integer,
                  forecast_high_c real,
                  forecast_low_c real
                );

                create table if not exists usage_event (
                  id text primary key,
                  occurred_at text not null,
                  source text not null,
                  action_type text not null,
                  mode text,
                  target_temp_c integer,
                  fan_speed text,
                  indoor_temp_c real,
                  outside_temp_c real
                );

                create table if not exists feedback_event (
                  id text primary key,
                  occurred_at text not null,
                  direction text not null,
                  indoor_temp_c real,
                  outside_temp_c real,
                  active_mode text,
                  active_target_temp_c integer,
                  note text
                );

                create table if not exists smart_decision_event (
                  id text primary key,
                  occurred_at text not null,
                  decision_type text not null,
                  recommended_mode text,
                  recommended_target_temp_c integer,
                  explanation_json text not null,
                  command_sent integer not null default 0
                );

                create table if not exists training_event (
                  id text primary key,
                  occurred_at text not null,
                  source text not null,
                  preferred_target_c real not null,
                  local_hour real not null,
                  indoor_temp_c real,
                  outside_temp_c real,
                  apparent_temp_c real,
                  humidity_pct real,
                  wind_speed_kmh real,
                  forecast_high_c real,
                  forecast_low_c real,
                  presence_anyone_home integer,
                  sample_weight real not null default 1.0
                );

                create index if not exists idx_usage_event_occurred_at on usage_event (occurred_at);
                create index if not exists idx_feedback_event_occurred_at on feedback_event (occurred_at);
                create index if not exists idx_smart_decision_event_occurred_at on smart_decision_event (occurred_at);
                create index if not exists idx_weather_snapshot_observed_at on weather_snapshot (observed_at);
                create index if not exists idx_training_event_occurred_at on training_event (occurred_at);
                """
            )
            self._ensure_app_settings_columns(connection)
            existing = connection.execute("select count(*) from app_settings").fetchone()[0]
            if existing == 0:
                now = utc_now_iso()
                connection.execute(
                    """
                    insert into app_settings (
                      id, location_label, latitude, longitude, timezone, smart_enabled,
                      allow_automation_power_on, min_cycle_minutes, max_temp_step_c,
                      learning_rate, memory_lifetime_days, quiet_hours_start, quiet_hours_end, weather_enabled,
                      presence_detection_enabled, presence_check_interval_minutes,
                      presence_device_ips, updated_at
                    ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        "default",
                        "Home",
                        0.0,
                        0.0,
                        "UTC",
                        0,
                        0,
                        15,
                        2,
                        0.25,
                        45,
                        None,
                        None,
                        1,
                        0,
                        5,
                        "[]",
                        now,
                    ),
                )
            connection.commit()

    def _ensure_app_settings_columns(self, connection: sqlite3.Connection) -> None:
        columns = {
            row["name"] for row in connection.execute("pragma table_info(app_settings)").fetchall()
        }
        required_columns = {
            "allow_automation_power_on": "integer not null default 0",
            "presence_detection_enabled": "integer not null default 0",
            "presence_check_interval_minutes": "integer not null default 5",
            "presence_device_ips": "text not null default '[]'",
            "memory_lifetime_days": "integer not null default 45",
        }
        for name, definition in required_columns.items():
            if name not in columns:
                connection.execute(f"alter table app_settings add column {name} {definition}")

    def get_settings(self) -> AppSettingsModel:
        with self._connect() as connection:
            row = connection.execute("select * from app_settings where id = 'default'").fetchone()
        return AppSettingsModel(
            location_label=row["location_label"],
            latitude=row["latitude"],
            longitude=row["longitude"],
            timezone=row["timezone"],
            smart_enabled=bool(row["smart_enabled"]),
            allow_automation_power_on=bool(row["allow_automation_power_on"]),
            min_cycle_minutes=row["min_cycle_minutes"],
            max_temp_step_c=row["max_temp_step_c"],
            learning_rate=row["learning_rate"],
            memory_lifetime_days=row["memory_lifetime_days"],
            quiet_hours_start=row["quiet_hours_start"],
            quiet_hours_end=row["quiet_hours_end"],
            weather_enabled=bool(row["weather_enabled"]),
            presence_detection_enabled=bool(row["presence_detection_enabled"]),
            presence_check_interval_minutes=row["presence_check_interval_minutes"],
            presence_device_ips=self._parse_presence_device_ips(row["presence_device_ips"]),
            updated_at=row["updated_at"],
        )

    def update_settings(self, update: AppSettingsUpdate) -> AppSettingsModel:
        current = self.get_settings()
        merged = current.model_copy(update=update.model_dump(exclude_unset=True))
        merged.presence_device_ips = self._normalize_presence_device_ips(merged.presence_device_ips)
        merged.updated_at = utc_now_iso()
        with self._connect() as connection:
            connection.execute(
                """
                update app_settings
                set location_label = ?, latitude = ?, longitude = ?, timezone = ?,
                    smart_enabled = ?, allow_automation_power_on = ?,
                    min_cycle_minutes = ?, max_temp_step_c = ?, learning_rate = ?,
                    memory_lifetime_days = ?, quiet_hours_start = ?, quiet_hours_end = ?, weather_enabled = ?,
                    presence_detection_enabled = ?, presence_check_interval_minutes = ?,
                    presence_device_ips = ?, updated_at = ?
                where id = 'default'
                """,
                (
                    merged.location_label,
                    merged.latitude,
                    merged.longitude,
                    merged.timezone,
                    int(merged.smart_enabled),
                    int(merged.allow_automation_power_on),
                    merged.min_cycle_minutes,
                    merged.max_temp_step_c,
                    merged.learning_rate,
                    merged.memory_lifetime_days,
                    merged.quiet_hours_start,
                    merged.quiet_hours_end,
                    int(merged.weather_enabled),
                    int(merged.presence_detection_enabled),
                    merged.presence_check_interval_minutes,
                    json.dumps(merged.presence_device_ips),
                    merged.updated_at,
                ),
            )
            connection.commit()
        return merged

    def _parse_presence_device_ips(self, raw: str | None) -> list[str]:
        if not raw:
            return []
        try:
            value = json.loads(raw)
        except json.JSONDecodeError:
            value = raw.splitlines()
        if not isinstance(value, list):
            return []
        return self._normalize_presence_device_ips(value)

    def _normalize_presence_device_ips(self, values: list[str] | None) -> list[str]:
        if not values:
            return []
        normalized: list[str] = []
        for value in values:
            text = str(value).strip()
            if text and text not in normalized:
                normalized.append(text)
        return normalized

    def list_sleep_profiles(self) -> list[SleepProfile]:
        with self._connect() as connection:
            rows = connection.execute(
                "select * from sleep_profile order by start_time, label"
            ).fetchall()
        return [
            SleepProfile(
                id=row["id"],
                label=row["label"],
                start_time=row["start_time"],
                end_time=row["end_time"],
                target_temp_c=row["target_temp_c"],
                fan_speed=row["fan_speed"],
                enabled=bool(row["enabled"]),
                updated_at=row["updated_at"],
            )
            for row in rows
        ]

    def upsert_sleep_profile(self, payload: SleepProfileUpsert) -> SleepProfile:
        profile_id = payload.id or str(uuid.uuid4())
        now = utc_now_iso()
        with self._connect() as connection:
            connection.execute(
                """
                insert into sleep_profile (
                  id, label, start_time, end_time, target_temp_c, fan_speed, enabled, updated_at
                ) values (?, ?, ?, ?, ?, ?, ?, ?)
                on conflict(id) do update set
                  label = excluded.label,
                  start_time = excluded.start_time,
                  end_time = excluded.end_time,
                  target_temp_c = excluded.target_temp_c,
                  fan_speed = excluded.fan_speed,
                  enabled = excluded.enabled,
                  updated_at = excluded.updated_at
                """,
                (
                    profile_id,
                    payload.label,
                    payload.start_time,
                    payload.end_time,
                    payload.target_temp_c,
                    payload.fan_speed,
                    int(payload.enabled),
                    now,
                ),
            )
            connection.commit()
        return SleepProfile(
            id=profile_id,
            label=payload.label,
            start_time=payload.start_time,
            end_time=payload.end_time,
            target_temp_c=payload.target_temp_c,
            fan_speed=payload.fan_speed,
            enabled=payload.enabled,
            updated_at=now,
        )

    def delete_sleep_profile(self, profile_id: str) -> None:
        with self._connect() as connection:
            connection.execute("delete from sleep_profile where id = ?", (profile_id,))
            connection.commit()

    def save_weather_snapshot(self, snapshot: WeatherSnapshot) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                insert into weather_snapshot (
                  id, observed_at, timezone, outside_temp_c, apparent_temp_c,
                  humidity_pct, wind_speed_kmh, weather_code, is_day,
                  forecast_high_c, forecast_low_c
                ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(uuid.uuid4()),
                    snapshot.observed_at,
                    snapshot.timezone,
                    snapshot.outside_temp_c,
                    snapshot.apparent_temp_c,
                    snapshot.humidity_pct,
                    snapshot.wind_speed_kmh,
                    snapshot.weather_code,
                    None if snapshot.is_day is None else int(snapshot.is_day),
                    snapshot.forecast_high_c,
                    snapshot.forecast_low_c,
                ),
            )
            connection.commit()

    def get_latest_weather_snapshot(self) -> WeatherSnapshot | None:
        with self._connect() as connection:
            row = connection.execute(
                "select * from weather_snapshot order by observed_at desc limit 1"
            ).fetchone()
        if row is None:
            return None
        return WeatherSnapshot(
            observed_at=row["observed_at"],
            timezone=row["timezone"],
            outside_temp_c=row["outside_temp_c"],
            apparent_temp_c=row["apparent_temp_c"],
            humidity_pct=row["humidity_pct"],
            wind_speed_kmh=row["wind_speed_kmh"],
            weather_code=row["weather_code"],
            is_day=None if row["is_day"] is None else bool(row["is_day"]),
            forecast_high_c=row["forecast_high_c"],
            forecast_low_c=row["forecast_low_c"],
        )

    def add_usage_event(
        self,
        *,
        source: str,
        action_type: str,
        mode: str | None,
        target_temp_c: int | None,
        fan_speed: str | None,
        indoor_temp_c: float | None,
        outside_temp_c: float | None,
    ) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                insert into usage_event (
                  id, occurred_at, source, action_type, mode, target_temp_c,
                  fan_speed, indoor_temp_c, outside_temp_c
                ) values (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(uuid.uuid4()),
                    utc_now_iso(),
                    source,
                    action_type,
                    mode,
                    target_temp_c,
                    fan_speed,
                    indoor_temp_c,
                    outside_temp_c,
                ),
            )
            connection.commit()

    def add_feedback_event(
        self,
        *,
        direction: str,
        indoor_temp_c: float | None,
        outside_temp_c: float | None,
        active_mode: str | None,
        active_target_temp_c: int | None,
        note: str | None,
    ) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                insert into feedback_event (
                  id, occurred_at, direction, indoor_temp_c, outside_temp_c,
                  active_mode, active_target_temp_c, note
                ) values (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(uuid.uuid4()),
                    utc_now_iso(),
                    direction,
                    indoor_temp_c,
                    outside_temp_c,
                    active_mode,
                    active_target_temp_c,
                    note,
                ),
            )
            connection.commit()

    def add_smart_decision_event(
        self,
        *,
        decision_type: str,
        recommended_mode: str | None,
        recommended_target_temp_c: int | None,
        explanation: list[str],
        command_sent: bool,
    ) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                insert into smart_decision_event (
                  id, occurred_at, decision_type, recommended_mode,
                  recommended_target_temp_c, explanation_json, command_sent
                ) values (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(uuid.uuid4()),
                    utc_now_iso(),
                    decision_type,
                    recommended_mode,
                    recommended_target_temp_c,
                    json.dumps(explanation),
                    int(command_sent),
                ),
            )
            connection.commit()

    def add_training_event(
        self,
        *,
        occurred_at: str | None = None,
        source: str,
        preferred_target_c: float,
        local_hour: float,
        indoor_temp_c: float | None,
        outside_temp_c: float | None,
        apparent_temp_c: float | None,
        humidity_pct: float | None,
        wind_speed_kmh: float | None,
        forecast_high_c: float | None,
        forecast_low_c: float | None,
        presence_anyone_home: bool | None,
        sample_weight: float,
    ) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                insert into training_event (
                  id, occurred_at, source, preferred_target_c, local_hour, indoor_temp_c,
                  outside_temp_c, apparent_temp_c, humidity_pct, wind_speed_kmh,
                  forecast_high_c, forecast_low_c, presence_anyone_home, sample_weight
                ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(uuid.uuid4()),
                    occurred_at or utc_now_iso(),
                    source,
                    preferred_target_c,
                    local_hour,
                    indoor_temp_c,
                    outside_temp_c,
                    apparent_temp_c,
                    humidity_pct,
                    wind_speed_kmh,
                    forecast_high_c,
                    forecast_low_c,
                    None if presence_anyone_home is None else int(presence_anyone_home),
                    sample_weight,
                ),
            )
            connection.commit()

    def count_training_events(self) -> int:
        with self._connect() as connection:
            row = connection.execute("select count(*) as count from training_event").fetchone()
        return int(row["count"])

    def get_training_events(self, lifetime_days: int, limit: int = 1000) -> list[TrainingSample]:
        cutoff = (datetime.now(UTC) - timedelta(days=lifetime_days)).replace(microsecond=0)
        cutoff_iso = cutoff.isoformat().replace("+00:00", "Z")
        with self._connect() as connection:
            rows = connection.execute(
                """
                select *
                from training_event
                where occurred_at >= ?
                order by occurred_at desc
                limit ?
                """,
                (cutoff_iso, limit),
            ).fetchall()
        return [
            TrainingSample(
                occurred_at=row["occurred_at"],
                source=row["source"],
                preferred_target_c=float(row["preferred_target_c"]),
                local_hour=float(row["local_hour"]),
                indoor_temp_c=row["indoor_temp_c"],
                outside_temp_c=row["outside_temp_c"],
                apparent_temp_c=row["apparent_temp_c"],
                humidity_pct=row["humidity_pct"],
                wind_speed_kmh=row["wind_speed_kmh"],
                forecast_high_c=row["forecast_high_c"],
                forecast_low_c=row["forecast_low_c"],
                presence_anyone_home=None
                if row["presence_anyone_home"] is None
                else bool(row["presence_anyone_home"]),
                sample_weight=float(row["sample_weight"]),
            )
            for row in rows
        ]

    def clear_training_events(self) -> int:
        with self._connect() as connection:
            cursor = connection.execute("delete from training_event")
            connection.commit()
        return cursor.rowcount

    def get_usage_events(self, limit: int = 240) -> list[sqlite3.Row]:
        with self._connect() as connection:
            return connection.execute(
                "select * from usage_event order by occurred_at desc limit ?", (limit,)
            ).fetchall()

    def get_feedback_events(self, limit: int = 240) -> list[sqlite3.Row]:
        with self._connect() as connection:
            return connection.execute(
                "select * from feedback_event order by occurred_at desc limit ?", (limit,)
            ).fetchall()

    def get_recent_activity(self, limit: int = 16) -> list[ActivityItem]:
        items: list[ActivityItem] = []
        with self._connect() as connection:
            usage_rows = connection.execute(
                "select * from usage_event order by occurred_at desc limit ?",
                (limit,),
            ).fetchall()
            feedback_rows = connection.execute(
                "select * from feedback_event order by occurred_at desc limit ?",
                (limit,),
            ).fetchall()
            smart_rows = connection.execute(
                "select * from smart_decision_event order by occurred_at desc limit ?",
                (limit,),
            ).fetchall()

        for row in usage_rows:
            detail = f"{row['action_type']} -> {row['mode'] or 'off'} at {row['target_temp_c'] or '-'}C"
            items.append(
                ActivityItem(
                    id=row["id"],
                    occurred_at=row["occurred_at"],
                    kind="manual",
                    title="Manual change",
                    detail=detail,
                )
            )
        for row in feedback_rows:
            items.append(
                ActivityItem(
                    id=row["id"],
                    occurred_at=row["occurred_at"],
                    kind="feedback",
                    title="Comfort feedback",
                    detail=f"{row['direction']} at {row['active_target_temp_c'] or '-'}C",
                )
            )
        for row in smart_rows:
            explanation = json.loads(row["explanation_json"])
            items.append(
                ActivityItem(
                    id=row["id"],
                    occurred_at=row["occurred_at"],
                    kind="smart",
                    title="Smart decision",
                    detail="; ".join(explanation[:2]) or row["decision_type"],
                    command_sent=bool(row["command_sent"]),
                )
            )

        items.sort(key=lambda item: item.occurred_at, reverse=True)
        return items[:limit]

    def get_hourly_average_targets(self, lifetime_days: int) -> dict[int, float]:
        rows = self.get_training_events(lifetime_days=lifetime_days, limit=2000)
        accumulator: dict[int, list[int]] = {}
        for row in rows:
            accumulator.setdefault(int(row.local_hour) % 24, []).append(
                int(round(row.preferred_target_c))
            )
        return {
            hour: sum(values) / len(values)
            for hour, values in accumulator.items()
            if values
        }

    def get_hourly_feedback_bias(self, timezone_name: str, lifetime_days: int) -> dict[int, float]:
        rows = self.get_feedback_events(limit=1000)
        cutoff = (datetime.now(UTC) - timedelta(days=lifetime_days)).replace(microsecond=0)
        accumulator: dict[int, list[int]] = {}
        for row in rows:
            if self._parse_iso_datetime(row["occurred_at"]) < cutoff:
                continue
            hour = self._local_hour(row["occurred_at"], timezone_name)
            score = -1 if row["direction"] == "too_hot" else 1
            accumulator.setdefault(hour, []).append(score)
        return {
            hour: max(-4.0, min(4.0, float(sum(values))))
            for hour, values in accumulator.items()
            if values
        }

    def _local_hour(self, occurred_at: str, timezone_name: str) -> int:
        dt = self._parse_iso_datetime(occurred_at)
        return dt.astimezone(self._resolve_timezone(timezone_name)).hour

    def _parse_iso_datetime(self, value: str) -> datetime:
        if value.endswith("Z"):
            value = value[:-1] + "+00:00"
        return datetime.fromisoformat(value)

    def _resolve_timezone(self, timezone_name: str):
        try:
            return ZoneInfo(timezone_name)
        except Exception:
            return UTC
