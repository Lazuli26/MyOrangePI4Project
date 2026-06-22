from __future__ import annotations

import json
import urllib.parse
import urllib.request
from typing import Any

from smart_models import WeatherSnapshot, utc_now_iso


class WeatherService:
    forecast_base_url = "https://api.open-meteo.com/v1/forecast"

    def fetch_weather(
        self, *, latitude: float, longitude: float, timezone: str | None = None
    ) -> WeatherSnapshot:
        query = urllib.parse.urlencode(
            {
                "latitude": latitude,
                "longitude": longitude,
                "current": ",".join(
                    [
                        "temperature_2m",
                        "apparent_temperature",
                        "relative_humidity_2m",
                        "wind_speed_10m",
                        "weather_code",
                        "is_day",
                    ]
                ),
                "daily": ",".join(
                    [
                        "temperature_2m_max",
                        "temperature_2m_min",
                    ]
                ),
                "timezone": timezone or "auto",
                "forecast_days": 1,
            }
        )
        with urllib.request.urlopen(f"{self.forecast_base_url}?{query}", timeout=10) as response:
            payload = json.loads(response.read().decode("utf-8"))
        return self._parse_payload(payload)

    def _parse_payload(self, payload: dict[str, Any]) -> WeatherSnapshot:
        current = payload.get("current", {})
        daily = payload.get("daily", {})
        forecast_high = self._first_value(daily.get("temperature_2m_max"))
        forecast_low = self._first_value(daily.get("temperature_2m_min"))

        return WeatherSnapshot(
            observed_at=utc_now_iso(),
            timezone=str(payload.get("timezone", "UTC")),
            outside_temp_c=self._as_float(current.get("temperature_2m")),
            apparent_temp_c=self._as_float(current.get("apparent_temperature")),
            humidity_pct=self._as_float(current.get("relative_humidity_2m")),
            wind_speed_kmh=self._as_float(current.get("wind_speed_10m")),
            weather_code=self._as_int(current.get("weather_code")),
            is_day=self._as_bool(current.get("is_day")),
            forecast_high_c=self._as_float(forecast_high),
            forecast_low_c=self._as_float(forecast_low),
        )

    def _first_value(self, value: Any) -> Any:
        if isinstance(value, list) and value:
            return value[0]
        return value

    def _as_float(self, value: Any) -> float | None:
        try:
            return None if value is None else float(value)
        except (TypeError, ValueError):
            return None

    def _as_int(self, value: Any) -> int | None:
        try:
            return None if value is None else int(value)
        except (TypeError, ValueError):
            return None

    def _as_bool(self, value: Any) -> bool | None:
        if value is None:
            return None
        return bool(value)
