import {
  Gauge,
  MoonStar,
  Sparkles,
  SunMedium,
  Thermometer,
  Wind,
} from "lucide-react";

import type { AcStatus, SmartControlState } from "@/types";

type StatusHeroProps = {
  status: AcStatus;
  smartControl: SmartControlState;
};

const modeLabels: Record<AcStatus["mode"], string> = {
  off: "Offline cooling",
  auto: "Adaptive auto",
  cool: "Cooling focus",
  dry: "Dry comfort",
  fan: "Air circulation",
};

export function StatusHero({ status, smartControl }: StatusHeroProps) {
  const statCards = [
    {
      label: "Current temperature",
      value: status.current_temp_c != null ? `${status.current_temp_c.toFixed(1)}°C` : "—",
      icon: Thermometer,
    },
    {
      label: "Target temperature",
      value: `${status.target_temp_c}°C`,
      icon: Gauge,
    },
    {
      label: "Fan profile",
      value: status.fan_speed,
      icon: Wind,
    },
    {
      label: "Automation confidence",
      value: `${Math.round(smartControl.confidence * 100)}%`,
      icon: Sparkles,
    },
  ];

  return (
    <section className="grid gap-4 xl:grid-cols-[1.4fr_1fr]">
      <div className="relative overflow-hidden rounded-[32px] border border-cyan-300/15 bg-white/6 p-6 shadow-[0_35px_120px_rgba(0,0,0,0.35)]">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_right,_rgba(86,214,255,0.24),_transparent_28%),radial-gradient(circle_at_bottom_left,_rgba(255,190,92,0.16),_transparent_26%)]" />
        <div className="relative flex h-full flex-col justify-between gap-8">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <div className="mb-3 flex items-center gap-2 text-xs uppercase tracking-[0.24em] text-cyan-100/70">
                <span
                  className={`inline-flex h-2.5 w-2.5 rounded-full ${
                    status.online ? "bg-emerald-400 shadow-[0_0_16px_rgba(52,211,153,0.6)]" : "bg-rose-400"
                  }`}
                />
                {status.online ? "Unit online" : "Unit offline"}
              </div>
              <h2 className="font-display text-5xl text-white sm:text-6xl">
                {status.power ? `${status.target_temp_c}°` : "Standby"}
              </h2>
              <p className="mt-3 max-w-md text-sm text-slate-300">
                {modeLabels[status.mode]} with {smartControl.enabled ? "smart control enabled" : "manual control active"}.
              </p>
            </div>
            <div className="rounded-[24px] border border-white/10 bg-black/20 px-4 py-3 text-right">
              <div className="text-[11px] uppercase tracking-[0.22em] text-slate-400">
                Model offset
              </div>
              <div className="mt-2 text-2xl font-semibold text-white">
                {smartControl.learned_bias_c > 0 ? "+" : ""}
                {smartControl.learned_bias_c.toFixed(1)}°C
              </div>
              <div className="mt-2 flex items-center justify-end gap-2 text-xs text-slate-300">
                {status.sleep ? <MoonStar size={14} /> : <SunMedium size={14} />}
                <span>{status.sleep ? "Sleep profile applied" : "Daytime comfort profile"}</span>
              </div>
            </div>
          </div>

          <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
            {statCards.map(({ label, value, icon: Icon }) => (
              <div
                key={label}
                className="rounded-[22px] border border-white/10 bg-black/20 p-4 backdrop-blur"
              >
                <div className="flex items-center justify-between text-slate-300">
                  <span className="text-xs uppercase tracking-[0.18em]">{label}</span>
                  <Icon size={16} />
                </div>
                <div className="mt-4 text-2xl font-semibold text-white">{value}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <aside className="rounded-[32px] border border-white/10 bg-white/6 p-6">
        <div className="flex items-center justify-between">
          <h3 className="font-display text-2xl text-white">Automation pulse</h3>
          <span
            className={`rounded-full px-3 py-1 text-xs uppercase tracking-[0.18em] ${
              smartControl.enabled
                ? "bg-emerald-400/15 text-emerald-200"
                : "bg-slate-500/20 text-slate-300"
            }`}
          >
            {smartControl.enabled ? "Enabled" : "Paused"}
          </span>
        </div>
        <ul className="mt-5 space-y-3 text-sm text-slate-300">
          {smartControl.explanation.map((item) => (
            <li key={item} className="rounded-2xl border border-white/8 bg-black/20 px-4 py-3">
              {item}
            </li>
          ))}
          {smartControl.explanation.length === 0 ? (
            <li className="rounded-2xl border border-white/8 bg-black/20 px-4 py-3">
              Smart control is waiting for enough context to make a recommendation.
            </li>
          ) : null}
        </ul>
      </aside>
    </section>
  );
}
