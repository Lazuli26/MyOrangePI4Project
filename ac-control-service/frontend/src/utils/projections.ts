import type { AcMode, ProjectionPoint } from "@/types";

export type ProjectionChartRow = {
  hourLabel: string;
  minutesFromMidnight: number;
  target: number;
  segment: ProjectionPoint["segment"];
  mode: AcMode;
  auto: number | null;
  cool: number | null;
  dry: number | null;
  fan: number | null;
  off: number | null;
};

export function buildProjectionRows(points: ProjectionPoint[]): ProjectionChartRow[] {
  return points.map((point) => ({
    hourLabel: point.hour_label,
    minutesFromMidnight: point.minutes_from_midnight,
    target: point.target_temp_c,
    segment: point.segment,
    mode: point.mode,
    auto: point.mode === "auto" ? point.target_temp_c : null,
    cool: point.mode === "cool" ? point.target_temp_c : null,
    dry: point.mode === "dry" ? point.target_temp_c : null,
    fan: point.mode === "fan" ? point.target_temp_c : null,
    off: point.mode === "off" ? point.target_temp_c : null,
  }));
}

export function modeColor(mode: AcMode): string {
  switch (mode) {
    case "cool":
      return "#56d6ff";
    case "dry":
      return "#8c84ff";
    case "fan":
      return "#8ee0a1";
    case "off":
      return "#6c7389";
    case "auto":
    default:
      return "#ffbe5c";
  }
}
