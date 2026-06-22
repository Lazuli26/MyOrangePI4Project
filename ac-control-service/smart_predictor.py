from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from math import cos, pi, sin

from smart_models import TrainingSample

UTC = timezone.utc


@dataclass
class PredictionContext:
    local_hour: float
    indoor_temp_c: float | None = None
    outside_temp_c: float | None = None
    apparent_temp_c: float | None = None
    humidity_pct: float | None = None
    wind_speed_kmh: float | None = None
    forecast_high_c: float | None = None
    forecast_low_c: float | None = None
    presence_anyone_home: bool | None = None


@dataclass
class PredictorResult:
    predicted_target_c: float
    sample_count: int
    confidence: float
    explanation: list[str]
    baseline_target_c: float


@dataclass
class TrainedPredictor:
    intercept: float
    weights: list[float]
    sample_count: int
    memory_lifetime_days: int
    baseline_target_c: float

    def predict(self, context: PredictionContext) -> PredictorResult:
        context_vector = _feature_vector(context)
        predicted_target = self.intercept + sum(
            weight * value for weight, value in zip(self.weights, context_vector)
        )
        grouped = _grouped_contributions(self.weights, context_vector)
        return PredictorResult(
            predicted_target_c=predicted_target,
            sample_count=self.sample_count,
            confidence=_confidence(self.sample_count, grouped),
            explanation=_explain(
                grouped,
                self.sample_count,
                self.memory_lifetime_days,
                predicted_target,
            ),
            baseline_target_c=self.baseline_target_c,
        )


class ContextTemperaturePredictor:
    def __init__(
        self,
        *,
        regularization: float = 0.025,
        epochs: int = 220,
        learning_rate: float = 0.03,
    ) -> None:
        self.regularization = regularization
        self.epochs = epochs
        self.learning_rate = learning_rate

    def fit(
        self,
        *,
        samples: list[TrainingSample],
        memory_lifetime_days: int,
    ) -> TrainedPredictor:
        if not samples:
            return TrainedPredictor(
                intercept=24.0,
                weights=[0.0] * len(_feature_names()),
                sample_count=0,
                memory_lifetime_days=memory_lifetime_days,
                baseline_target_c=24.0,
            )

        baseline_target = sum(sample.preferred_target_c for sample in samples) / len(samples)
        weights = [0.0] * len(_feature_names())
        intercept = baseline_target
        weighted_samples = [
            (
                _feature_vector(sample),
                sample.preferred_target_c,
                self._effective_weight(sample, memory_lifetime_days),
            )
            for sample in samples
        ]

        for _ in range(self.epochs):
            for feature_vector, target, sample_weight in weighted_samples:
                prediction = intercept + sum(
                    weight * value for weight, value in zip(weights, feature_vector)
                )
                error = prediction - target
                intercept -= self.learning_rate * sample_weight * error
                updated_weights: list[float] = []
                for weight, value in zip(weights, feature_vector):
                    gradient = (error * value) + (self.regularization * weight)
                    updated_weights.append(weight - (self.learning_rate * sample_weight * gradient))
                weights = updated_weights

        return TrainedPredictor(
            intercept=intercept,
            weights=weights,
            sample_count=len(samples),
            memory_lifetime_days=memory_lifetime_days,
            baseline_target_c=baseline_target,
        )

    def predict(
        self,
        *,
        samples: list[TrainingSample],
        context: PredictionContext,
        memory_lifetime_days: int,
    ) -> PredictorResult:
        return self.fit(samples=samples, memory_lifetime_days=memory_lifetime_days).predict(context)

    def _effective_weight(self, sample: TrainingSample, memory_lifetime_days: int) -> float:
        occurred_at = _parse_iso(sample.occurred_at)
        age_days = max(0.0, (datetime.now(UTC) - occurred_at).total_seconds() / 86400.0)
        recency_weight = max(0.25, 1.0 - (age_days / max(memory_lifetime_days, 1)) * 0.75)
        return max(0.1, sample.sample_weight * recency_weight)


def _feature_names() -> list[str]:
    return [
        "hour_sin",
        "hour_cos",
        "indoor_temp",
        "outside_temp",
        "apparent_temp",
        "humidity",
        "wind_speed",
        "forecast_high",
        "forecast_low",
        "presence",
    ]


def _feature_vector(sample: TrainingSample | PredictionContext) -> list[float]:
    hour_sin, hour_cos = _hour_cycle(sample.local_hour)
    return [
        hour_sin,
        hour_cos,
        _scale_temperature(sample.indoor_temp_c, center=25.0, span=8.0),
        _scale_temperature(sample.outside_temp_c, center=29.0, span=12.0),
        _scale_temperature(sample.apparent_temp_c, center=31.0, span=12.0),
        _scale_value(sample.humidity_pct, center=60.0, span=30.0),
        _scale_value(sample.wind_speed_kmh, center=10.0, span=25.0),
        _scale_temperature(sample.forecast_high_c, center=30.0, span=12.0),
        _scale_temperature(sample.forecast_low_c, center=22.0, span=12.0),
        _scale_presence(sample.presence_anyone_home),
    ]


def _grouped_contributions(weights: list[float], context_vector: list[float]) -> dict[str, float]:
    return {
        "time": (weights[0] * context_vector[0]) + (weights[1] * context_vector[1]),
        "indoor": weights[2] * context_vector[2],
        "outdoor": (weights[3] * context_vector[3])
        + (weights[4] * context_vector[4])
        + (weights[7] * context_vector[7])
        + (weights[8] * context_vector[8]),
        "humidity_wind": (weights[5] * context_vector[5]) + (weights[6] * context_vector[6]),
        "presence": weights[9] * context_vector[9],
    }


def _explain(
    grouped_contributions: dict[str, float],
    sample_count: int,
    memory_lifetime_days: int,
    predicted_target_c: float,
) -> list[str]:
    if sample_count == 0:
        return [
            "The context predictor does not have enough saved comfort examples yet.",
            "It is falling back to a neutral 24.0C target until you build more history.",
        ]
    explanation = [
        f"Context regression used {sample_count} comfort samples from the last {memory_lifetime_days} days.",
        f"Predicted preferred target is {predicted_target_c:.1f}C before mode selection.",
    ]
    ordered = sorted(
        grouped_contributions.items(),
        key=lambda item: abs(item[1]),
        reverse=True,
    )
    for name, contribution in ordered:
        if abs(contribution) < 0.12:
            continue
        direction = "warmer" if contribution > 0 else "cooler"
        if name == "time":
            explanation.append(f"Time of day is nudging the preferred target {direction}.")
        elif name == "indoor":
            explanation.append(f"The indoor AC reading is nudging the preferred target {direction}.")
        elif name == "outdoor":
            explanation.append(f"Current and forecast weather are nudging the preferred target {direction}.")
        elif name == "humidity_wind":
            explanation.append(f"Humidity and airflow conditions are nudging the preferred target {direction}.")
        elif name == "presence":
            explanation.append(f"Home presence context is nudging the preferred target {direction}.")
        if len(explanation) >= 4:
            break
    if len(explanation) == 2:
        explanation.append("The model is currently relying on a broad average because the saved contexts are still sparse.")
    return explanation


def _confidence(sample_count: int, grouped_contributions: dict[str, float]) -> float:
    if sample_count == 0:
        return 0.12
    sample_factor = min(0.55, sample_count / 60.0)
    signal_factor = min(
        0.25,
        sum(1 for value in grouped_contributions.values() if abs(value) >= 0.12) * 0.06,
    )
    return min(0.96, 0.18 + sample_factor + signal_factor)


def _hour_cycle(local_hour: float) -> tuple[float, float]:
    radians = 2 * pi * (local_hour / 24.0)
    return sin(radians), cos(radians)


def _scale_temperature(value: float | None, *, center: float, span: float) -> float:
    if value is None:
        return 0.0
    return (float(value) - center) / span


def _scale_value(value: float | None, *, center: float, span: float) -> float:
    if value is None:
        return 0.0
    return (float(value) - center) / span


def _scale_presence(value: bool | None) -> float:
    if value is None:
        return 0.0
    return 1.0 if value else -1.0


def _parse_iso(value: str) -> datetime:
    text = value[:-1] + "+00:00" if value.endswith("Z") else value
    parsed = datetime.fromisoformat(text)
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)
