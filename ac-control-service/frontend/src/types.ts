export type AcMode = "off" | "auto" | "cool" | "dry" | "fan";
export type FanSpeed = "auto" | "low" | "middle" | "high" | "strong" | "mute";
export type VerticalSwing = "fixed" | "swing";
export type FeedbackDirection = "too_cold" | "too_hot";

export type AcStatus = {
  online: boolean;
  power: boolean;
  mode: AcMode;
  target_temp_c: number;
  current_temp_c: number | null;
  fan_speed: FanSpeed;
  sleep: boolean;
  uvc: boolean;
  display: boolean;
  horizontal_swing: boolean;
  vertical_swing: VerticalSwing;
  vertical_swing_raw?: string | null;
  fault_code?: number | null;
  source: string;
};

export type SmartContext = {
  local_time_iso: string;
  timezone: string;
  allow_automation_power_on: boolean;
  presence_detection_enabled: boolean;
  presence_anyone_home?: boolean | null;
  monitored_presence_ips: string[];
  reachable_presence_ips: string[];
  last_presence_check_at?: string | null;
  outside_temp_c?: number | null;
  apparent_temp_c?: number | null;
  humidity_pct?: number | null;
  wind_speed_kmh?: number | null;
  weather_code?: number | null;
  forecast_high_c?: number | null;
  forecast_low_c?: number | null;
  indoor_temp_c?: number | null;
};

export type SmartControlState = {
  enabled: boolean;
  predictor_name: string;
  predicted_target_c: number;
  predictor_sample_count: number;
  memory_window_days: number;
  next_evaluation_at?: string | null;
  last_evaluation_at?: string | null;
  learned_bias_c: number;
  confidence: number;
  explanation: string[];
  context: SmartContext;
};

export type ProjectionPoint = {
  hour_label: string;
  minutes_from_midnight: number;
  segment: "past" | "current" | "future";
  mode: AcMode;
  target_temp_c: number;
};

export type ActivityItem = {
  id: string;
  occurred_at: string;
  kind: "manual" | "feedback" | "smart";
  title: string;
  detail: string;
  command_sent?: boolean | null;
};

export type SleepProfile = {
  id: string;
  label: string;
  start_time: string;
  end_time: string;
  target_temp_c: number;
  fan_speed?: FanSpeed | null;
  enabled: boolean;
  updated_at?: string | null;
};

export type SleepProfileInput = {
  id?: string;
  label: string;
  start_time: string;
  end_time: string;
  target_temp_c: number;
  fan_speed?: FanSpeed | null;
  enabled: boolean;
};

export type AppSettings = {
  location_label: string;
  latitude: number;
  longitude: number;
  timezone: string;
  smart_enabled: boolean;
  allow_automation_power_on: boolean;
  min_cycle_minutes: number;
  max_temp_step_c: number;
  learning_rate: number;
  memory_lifetime_days: number;
  quiet_hours_start?: string | null;
  quiet_hours_end?: string | null;
  weather_enabled: boolean;
  presence_detection_enabled: boolean;
  presence_check_interval_minutes: number;
  presence_device_ips: string[];
  updated_at?: string | null;
};

export type DashboardResponse = {
  status: AcStatus;
  smart_control: SmartControlState;
  weather?: {
    observed_at: string;
    timezone: string;
    outside_temp_c?: number | null;
    apparent_temp_c?: number | null;
    humidity_pct?: number | null;
    wind_speed_kmh?: number | null;
    weather_code?: number | null;
    is_day?: boolean | null;
    forecast_high_c?: number | null;
    forecast_low_c?: number | null;
  } | null;
  projections: ProjectionPoint[];
  activity: ActivityItem[];
  sleep_profiles: SleepProfile[];
  hourly_average_targets: ProjectionPoint[];
};

export type ManualApplyRequest = {
  power?: boolean;
  mode?: "auto" | "cool" | "dry" | "fan";
  target_temp_c?: number;
  fan_speed?: FanSpeed;
  sleep?: boolean;
  uvc?: boolean;
  display?: boolean;
  horizontal_swing?: boolean;
  vertical_swing?: VerticalSwing;
};

export type SmartSettingsUpdate = Partial<
  Pick<
    AppSettings,
    | "location_label"
    | "latitude"
    | "longitude"
    | "timezone"
    | "smart_enabled"
    | "allow_automation_power_on"
    | "min_cycle_minutes"
    | "max_temp_step_c"
    | "learning_rate"
    | "memory_lifetime_days"
    | "quiet_hours_start"
    | "quiet_hours_end"
    | "weather_enabled"
    | "presence_detection_enabled"
    | "presence_check_interval_minutes"
    | "presence_device_ips"
  >
>;
