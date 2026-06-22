import { create } from "zustand";

import { api } from "@/utils/api";
import type {
  AppSettings,
  DashboardResponse,
  FeedbackDirection,
  ManualApplyRequest,
  SleepProfileInput,
  SmartSettingsUpdate,
} from "@/types";

type SmartAcStore = {
  dashboard: DashboardResponse | null;
  settings: AppSettings | null;
  loading: boolean;
  saving: boolean;
  error: string | null;
  loadDashboard: () => Promise<void>;
  loadSettings: () => Promise<void>;
  refreshAll: () => Promise<void>;
  applyManual: (payload: ManualApplyRequest) => Promise<void>;
  sendFeedback: (direction: FeedbackDirection, note?: string) => Promise<void>;
  setSmartControl: (enabled: boolean) => Promise<void>;
  evaluateSmartControl: () => Promise<void>;
  saveSettings: (payload: SmartSettingsUpdate) => Promise<void>;
  clearLearningMemory: () => Promise<void>;
  saveSleepProfile: (payload: SleepProfileInput) => Promise<void>;
  deleteSleepProfile: (profileId: string) => Promise<void>;
  clearError: () => void;
};

async function withErrorHandling(
  set: (partial: Partial<SmartAcStore>) => void,
  work: () => Promise<void>,
) {
  try {
    await work();
  } catch (error) {
    const message = error instanceof Error ? error.message : "Unexpected error";
    set({ error: message });
    throw error;
  }
}

export const useSmartAcStore = create<SmartAcStore>((set, get) => ({
  dashboard: null,
  settings: null,
  loading: false,
  saving: false,
  error: null,
  clearError: () => set({ error: null }),
  loadDashboard: async () => {
    set({ loading: true, error: null });
    await withErrorHandling(set, async () => {
      const dashboard = await api.getDashboard();
      set({ dashboard, loading: false });
    }).finally(() => set({ loading: false }));
  },
  loadSettings: async () => {
    await withErrorHandling(set, async () => {
      const settings = await api.getSettings();
      set({ settings });
    });
  },
  refreshAll: async () => {
    set({ loading: true, error: null });
    await withErrorHandling(set, async () => {
      const [dashboard, settings] = await Promise.all([
        api.getDashboard(),
        api.getSettings(),
      ]);
      set({ dashboard, settings });
    }).finally(() => set({ loading: false }));
  },
  applyManual: async (payload) => {
    set({ saving: true, error: null });
    await withErrorHandling(set, async () => {
      await api.applyManual(payload);
      await get().loadDashboard();
    }).finally(() => set({ saving: false }));
  },
  sendFeedback: async (direction, note) => {
    set({ saving: true, error: null });
    await withErrorHandling(set, async () => {
      await api.sendFeedback(direction, note);
      await get().loadDashboard();
    }).finally(() => set({ saving: false }));
  },
  setSmartControl: async (enabled) => {
    set({ saving: true, error: null });
    await withErrorHandling(set, async () => {
      await api.updateSmartControl({ enabled });
      await get().refreshAll();
    }).finally(() => set({ saving: false }));
  },
  evaluateSmartControl: async () => {
    set({ saving: true, error: null });
    await withErrorHandling(set, async () => {
      await api.evaluateSmartControl();
      await get().loadDashboard();
    }).finally(() => set({ saving: false }));
  },
  saveSettings: async (payload) => {
    set({ saving: true, error: null });
    await withErrorHandling(set, async () => {
      const settings = await api.updateSettings(payload);
      set({ settings });
      await get().loadDashboard();
    }).finally(() => set({ saving: false }));
  },
  clearLearningMemory: async () => {
    set({ saving: true, error: null });
    await withErrorHandling(set, async () => {
      await api.clearLearningMemory();
      await get().refreshAll();
    }).finally(() => set({ saving: false }));
  },
  saveSleepProfile: async (payload) => {
    set({ saving: true, error: null });
    await withErrorHandling(set, async () => {
      await api.saveSleepProfile(payload);
      await get().loadDashboard();
    }).finally(() => set({ saving: false }));
  },
  deleteSleepProfile: async (profileId) => {
    set({ saving: true, error: null });
    await withErrorHandling(set, async () => {
      await api.deleteSleepProfile(profileId);
      await get().loadDashboard();
    }).finally(() => set({ saving: false }));
  },
}));
