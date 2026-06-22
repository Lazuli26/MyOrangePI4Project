import { useMemo, useState } from "react";
import { MoonStar, Pencil, Plus, RotateCcw, Trash2 } from "lucide-react";

import type { FanSpeed, SleepProfile, SleepProfileInput } from "@/types";

type SleepProfileEditorProps = {
  profiles: SleepProfile[];
  saving: boolean;
  onSave: (payload: SleepProfileInput) => Promise<void>;
  onDelete: (profileId: string) => Promise<void>;
};

const defaultDraft: SleepProfileInput = {
  label: "Night comfort",
  start_time: "22:30",
  end_time: "06:30",
  target_temp_c: 24,
  fan_speed: "low" as FanSpeed,
  enabled: true,
};

export function SleepProfileEditor({
  profiles,
  saving,
  onSave,
  onDelete,
}: SleepProfileEditorProps) {
  const [draft, setDraft] = useState<SleepProfileInput>(defaultDraft);
  const [editingProfileId, setEditingProfileId] = useState<string | null>(null);
  const activeCount = useMemo(() => profiles.filter((item) => item.enabled).length, [profiles]);

  function startEditing(profile: SleepProfile) {
    setDraft({
      id: profile.id,
      label: profile.label,
      start_time: profile.start_time,
      end_time: profile.end_time,
      target_temp_c: profile.target_temp_c,
      fan_speed: profile.fan_speed ?? "auto",
      enabled: profile.enabled,
    });
    setEditingProfileId(profile.id);
  }

  function resetDraft() {
    setDraft(defaultDraft);
    setEditingProfileId(null);
  }

  return (
    <section className="rounded-[30px] border border-white/10 bg-white/6 p-6">
      <div className="mb-6 flex items-center justify-between gap-4">
        <div>
          <p className="text-xs uppercase tracking-[0.24em] text-slate-400">Sleep profile</p>
          <h3 className="mt-2 font-display text-2xl text-white">Night-time automation</h3>
        </div>
        <div className="rounded-full border border-white/10 bg-black/20 px-4 py-2 text-xs uppercase tracking-[0.18em] text-slate-300">
          {activeCount} active
        </div>
      </div>

      <div className="grid gap-4 xl:grid-cols-[1.2fr_0.9fr]">
        <div className="space-y-3">
          {profiles.length === 0 ? (
            <div className="rounded-[24px] border border-dashed border-white/10 bg-black/20 px-4 py-6 text-sm text-slate-300">
              No sleep profiles yet. Add one to teach the controller how nights should feel.
            </div>
          ) : null}
          {profiles.map((profile) => (
            <article key={profile.id} className="rounded-[24px] border border-white/10 bg-black/20 p-4">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <div className="inline-flex items-center gap-2 rounded-full bg-indigo-400/10 px-3 py-1 text-[11px] uppercase tracking-[0.18em] text-indigo-100">
                    <MoonStar size={14} />
                    {profile.enabled ? "Active" : "Paused"}
                  </div>
                  <h4 className="mt-3 text-lg font-medium text-white">{profile.label}</h4>
                  <p className="mt-1 text-sm text-slate-300">
                    {profile.start_time} → {profile.end_time} at {profile.target_temp_c}°C
                    {profile.fan_speed ? ` • fan ${profile.fan_speed}` : ""}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => startEditing(profile)}
                    disabled={saving}
                    className="rounded-full border border-white/10 bg-white/5 p-2 text-slate-300 transition hover:border-cyan-300/40 hover:text-cyan-100"
                    aria-label={`Edit ${profile.label}`}
                  >
                    <Pencil size={16} />
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      if (editingProfileId === profile.id) {
                        resetDraft();
                      }
                      void onDelete(profile.id);
                    }}
                    disabled={saving}
                    className="rounded-full border border-white/10 bg-white/5 p-2 text-slate-300 transition hover:border-rose-300/40 hover:text-rose-100"
                    aria-label={`Delete ${profile.label}`}
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              </div>
            </article>
          ))}
        </div>

        <form
          className="rounded-[28px] border border-white/10 bg-black/20 p-5"
          onSubmit={async (event) => {
            event.preventDefault();
            await onSave(draft);
            resetDraft();
          }}
        >
          <div className="mb-4 flex items-center justify-between">
            <h4 className="text-sm uppercase tracking-[0.2em] text-slate-400">
              {editingProfileId ? "Edit selected profile" : "Create or revise"}
            </h4>
            <Plus size={16} className="text-slate-400" />
          </div>
          {editingProfileId ? (
            <div className="mb-4 flex items-center justify-between rounded-2xl border border-cyan-300/20 bg-cyan-400/10 px-4 py-3 text-sm text-cyan-50">
              <span>Editing an existing night profile.</span>
              <button
                type="button"
                onClick={resetDraft}
                className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-black/20 px-3 py-1.5 text-xs uppercase tracking-[0.18em] text-white"
              >
                <RotateCcw size={14} />
                New draft
              </button>
            </div>
          ) : null}
          <div className="grid gap-4">
            <label className="grid gap-2 text-sm text-slate-200">
              <span>Name</span>
              <input
                value={draft.label}
                onChange={(event) => setDraft((current) => ({ ...current, label: event.target.value }))}
                className="rounded-2xl border border-white/10 bg-slate-950/70 px-4 py-3 text-white outline-none"
              />
            </label>
            <div className="grid gap-4 sm:grid-cols-2">
              <label className="grid gap-2 text-sm text-slate-200">
                <span>Start</span>
                <input
                  type="time"
                  value={draft.start_time}
                  onChange={(event) =>
                    setDraft((current) => ({ ...current, start_time: event.target.value }))
                  }
                  className="rounded-2xl border border-white/10 bg-slate-950/70 px-4 py-3 text-white outline-none"
                />
              </label>
              <label className="grid gap-2 text-sm text-slate-200">
                <span>End</span>
                <input
                  type="time"
                  value={draft.end_time}
                  onChange={(event) =>
                    setDraft((current) => ({ ...current, end_time: event.target.value }))
                  }
                  className="rounded-2xl border border-white/10 bg-slate-950/70 px-4 py-3 text-white outline-none"
                />
              </label>
            </div>
            <div className="grid gap-4 sm:grid-cols-2">
              <label className="grid gap-2 text-sm text-slate-200">
                <span>Target °C</span>
                <input
                  type="number"
                  min={16}
                  max={32}
                  value={draft.target_temp_c}
                  onChange={(event) =>
                    setDraft((current) => ({
                      ...current,
                      target_temp_c: Number(event.target.value),
                    }))
                  }
                  className="rounded-2xl border border-white/10 bg-slate-950/70 px-4 py-3 text-white outline-none"
                />
              </label>
              <label className="grid gap-2 text-sm text-slate-200">
                <span>Fan speed</span>
                <select
                  value={draft.fan_speed}
                  onChange={(event) =>
                    setDraft((current) => ({
                      ...current,
                      fan_speed: event.target.value as FanSpeed,
                    }))
                  }
                  className="rounded-2xl border border-white/10 bg-slate-950/70 px-4 py-3 text-white outline-none"
                >
                  {["auto", "low", "middle", "high", "mute"].map((option) => (
                    <option key={option} value={option}>
                      {option}
                    </option>
                  ))}
                </select>
              </label>
            </div>
            <label className="flex items-center justify-between rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-white">
              <span>Enabled</span>
              <input
                type="checkbox"
                checked={draft.enabled}
                onChange={(event) => setDraft((current) => ({ ...current, enabled: event.target.checked }))}
                className="h-4 w-4 accent-cyan-400"
              />
            </label>
          </div>
          <button
            type="submit"
            disabled={saving}
            className="mt-5 inline-flex w-full items-center justify-center rounded-full border border-cyan-300/40 bg-cyan-400/15 px-4 py-3 text-sm font-medium text-white transition hover:bg-cyan-400/25 disabled:opacity-50"
          >
            {saving
              ? "Saving…"
              : editingProfileId
                ? "Update sleep profile"
                : "Save sleep profile"}
          </button>
        </form>
      </div>
    </section>
  );
}
