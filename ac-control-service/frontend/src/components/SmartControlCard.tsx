import { BrainCircuit, CloudSun, Gauge, ThermometerSun } from "lucide-react";

import type { SmartControlState } from "@/types";

type SmartControlCardProps = {
  smartControl: SmartControlState;
  saving: boolean;
  onToggle: (enabled: boolean) => Promise<void>;
  onEvaluate: () => Promise<void>;
  onFeedback: (direction: "too_cold" | "too_hot") => Promise<void>;
};

export function SmartControlCard({
  smartControl,
  saving,
  onToggle,
  onEvaluate,
  onFeedback,
}: SmartControlCardProps) {
  const localClock = smartControl.context.local_time_iso.slice(11, 16);
  const contextItems = [
    {
      label: "Indoor",
      value:
        smartControl.context.indoor_temp_c != null
          ? `${smartControl.context.indoor_temp_c.toFixed(1)}°C`
          : "—",
      icon: Gauge,
    },
    {
      label: "Outdoor",
      value:
        smartControl.context.outside_temp_c != null
          ? `${smartControl.context.outside_temp_c.toFixed(1)}°C`
          : "—",
      icon: CloudSun,
    },
    {
      label: "Feels like",
      value:
        smartControl.context.apparent_temp_c != null
          ? `${smartControl.context.apparent_temp_c.toFixed(1)}°C`
          : "—",
      icon: ThermometerSun,
    },
    {
      label: "Humidity",
      value:
        smartControl.context.humidity_pct != null
          ? `${Math.round(smartControl.context.humidity_pct)}%`
          : "—",
      icon: BrainCircuit,
    },
    {
      label: "Predicted target",
      value: `${smartControl.predicted_target_c.toFixed(1)}°C`,
      icon: ThermometerSun,
    },
    {
      label: "Memory samples",
      value: `${smartControl.predictor_sample_count} / ${smartControl.memory_window_days}d`,
      icon: BrainCircuit,
    },
    {
      label: "Presence",
      value: !smartControl.context.presence_detection_enabled
        ? "Disabled"
        : smartControl.context.presence_anyone_home === true
          ? "Home"
          : smartControl.context.presence_anyone_home === false
            ? "Away"
            : "Unknown",
      icon: Gauge,
    },
    {
      label: "Power policy",
      value: smartControl.context.allow_automation_power_on ? "Auto-on allowed" : "Manual only",
      icon: BrainCircuit,
    },
  ];

  return (
    <section className="rounded-[30px] border border-white/10 bg-white/6 p-6">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.24em] text-slate-400">Smart control</p>
          <h3 className="mt-2 font-display text-2xl text-white">Comfort automation</h3>
          <p className="mt-2 max-w-2xl text-sm text-slate-300">
            This engine watches time of day, weather, and indoor conditions, then uses your
            manual behavior and feedback to tune future targets.
          </p>
          <p className="mt-2 text-xs uppercase tracking-[0.18em] text-slate-500">
            Predictor {smartControl.predictor_name}
          </p>
          <p className="mt-3 text-xs uppercase tracking-[0.18em] text-slate-500">
            Local automation clock {localClock} • {smartControl.context.timezone}
          </p>
          {smartControl.context.presence_detection_enabled ? (
            <p className="mt-2 text-xs text-slate-400">
              Presence check watches {smartControl.context.monitored_presence_ips.length} device
              {smartControl.context.monitored_presence_ips.length === 1 ? "" : "s"} on the LAN.
            </p>
          ) : null}
        </div>
        <button
          type="button"
          onClick={() => void onToggle(!smartControl.enabled)}
          disabled={saving}
          className={`inline-flex min-w-44 items-center justify-center rounded-full border px-5 py-3 text-sm font-medium transition ${
            smartControl.enabled
              ? "border-emerald-300/40 bg-emerald-400/15 text-emerald-100"
              : "border-white/10 bg-black/20 text-slate-200"
          }`}
        >
          {smartControl.enabled ? "Disable automation" : "Enable automation"}
        </button>
      </div>

      <div className="mt-6 grid gap-4 lg:grid-cols-[1.05fr_0.95fr]">
        <div className="rounded-[26px] border border-white/10 bg-black/20 p-5">
          <div className="mb-3 flex items-center justify-between">
            <h4 className="text-sm uppercase tracking-[0.2em] text-slate-400">Current reasoning</h4>
            <button
              type="button"
              onClick={() => void onEvaluate()}
              disabled={saving}
              className="rounded-full border border-white/10 bg-white/5 px-3 py-1.5 text-xs text-white transition hover:border-cyan-300/40 hover:bg-cyan-400/10"
            >
              Evaluate now
            </button>
          </div>
          <div className="space-y-3">
            {smartControl.explanation.map((item) => (
              <div key={item} className="rounded-2xl border border-white/8 bg-white/5 px-4 py-3 text-sm text-slate-200">
                {item}
              </div>
            ))}
          </div>

          <div className="mt-5 grid gap-3 sm:grid-cols-2">
            <button
              type="button"
              onClick={() => void onFeedback("too_cold")}
              disabled={saving}
              className="rounded-2xl border border-sky-300/20 bg-sky-400/10 px-4 py-4 text-left transition hover:bg-sky-400/20"
            >
              <div className="text-[11px] uppercase tracking-[0.22em] text-sky-100/70">Feedback</div>
              <div className="mt-2 text-lg font-semibold text-white">Too cold</div>
              <p className="mt-1 text-sm text-sky-100/80">Raise comfort immediately and learn warmer preferences for similar conditions.</p>
            </button>
            <button
              type="button"
              onClick={() => void onFeedback("too_hot")}
              disabled={saving}
              className="rounded-2xl border border-amber-300/20 bg-amber-300/10 px-4 py-4 text-left transition hover:bg-amber-300/20"
            >
              <div className="text-[11px] uppercase tracking-[0.22em] text-amber-100/70">Feedback</div>
              <div className="mt-2 text-lg font-semibold text-white">Too hot</div>
              <p className="mt-1 text-sm text-amber-100/80">Cool faster now and teach the model to aim colder in matching weather and time windows.</p>
            </button>
          </div>
        </div>

        <div className="grid gap-3 sm:grid-cols-2">
          {contextItems.map(({ label, value, icon: Icon }) => (
            <div key={label} className="rounded-[24px] border border-white/10 bg-black/20 p-4">
              <div className="flex items-center justify-between text-slate-400">
                <span className="text-xs uppercase tracking-[0.2em]">{label}</span>
                <Icon size={16} />
              </div>
              <div className="mt-4 text-2xl font-semibold text-white">{value}</div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
