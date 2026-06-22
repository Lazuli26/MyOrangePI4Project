import type {
  AppSettings,
  DashboardResponse,
  FeedbackDirection,
  ManualApplyRequest,
  SleepProfile,
  SleepProfileInput,
  SmartControlState,
  SmartSettingsUpdate,
} from "@/types";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, {
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
      ...(init?.headers ?? {}),
    },
    ...init,
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `Request failed with status ${response.status}`);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}

export const api = {
  getDashboard: () => request<DashboardResponse>("/api/dashboard"),
  getSettings: () => request<AppSettings>("/api/settings"),
  updateSettings: (payload: SmartSettingsUpdate) =>
    request<AppSettings>("/api/settings", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  clearLearningMemory: () =>
    request<{ deleted_training_samples: number }>("/api/settings/clear-learning-memory", {
      method: "POST",
    }),
  applyManual: (payload: ManualApplyRequest) =>
    request("/api/manual/apply", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  sendFeedback: (direction: FeedbackDirection, note?: string) =>
    request("/api/manual/feedback", {
      method: "POST",
      body: JSON.stringify({ direction, note }),
    }),
  getSmartControl: () => request<SmartControlState>("/api/smart-control"),
  updateSmartControl: (payload: {
    enabled?: boolean;
    min_cycle_minutes?: number;
    max_temp_step_c?: number;
    learning_rate?: number;
    quiet_hours_start?: string | null;
    quiet_hours_end?: string | null;
  }) =>
    request<SmartControlState>("/api/smart-control", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  evaluateSmartControl: () =>
    request<SmartControlState>("/api/smart-control/evaluate", {
      method: "POST",
    }),
  saveSleepProfile: (payload: SleepProfileInput) =>
    request<SleepProfile>("/api/sleep-profiles", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  deleteSleepProfile: (profileId: string) =>
    request(`/api/sleep-profiles/${profileId}`, {
      method: "DELETE",
    }),
};
