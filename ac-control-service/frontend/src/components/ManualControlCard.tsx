import { useEffect, useState } from "react";
import { Gauge, Power, Send, SlidersHorizontal } from "lucide-react";

import type { AcStatus, FanSpeed, ManualApplyRequest, VerticalSwing } from "@/types";

type ManualControlCardProps = {
  status: AcStatus;
  saving: boolean;
  onApply: (payload: ManualApplyRequest) => Promise<void>;
};

const modes: Array<{ value: "auto" | "cool" | "dry" | "fan"; label: string }> = [
  { value: "auto", label: "Auto" },
  { value: "cool", label: "Cool" },
  { value: "dry", label: "Dry" },
  { value: "fan", label: "Fan" },
];

const fanSpeeds: FanSpeed[] = ["auto", "low", "middle", "high", "strong", "mute"];

export function ManualControlCard({ status, saving, onApply }: ManualControlCardProps) {
  const [power, setPower] = useState(status.power);
  const [mode, setMode] = useState<"auto" | "cool" | "dry" | "fan">("cool");
  const [targetTemp, setTargetTemp] = useState(status.target_temp_c);
  const [fanSpeed, setFanSpeed] = useState<FanSpeed>(status.fan_speed);
  const [sleep, setSleep] = useState(status.sleep);
  const [uvc, setUvc] = useState(status.uvc);
  const [display, setDisplay] = useState(status.display);
  const [horizontalSwing, setHorizontalSwing] = useState(status.horizontal_swing);
  const [verticalSwing, setVerticalSwing] = useState<VerticalSwing>(status.vertical_swing);

  useEffect(() => {
    setPower(status.power);
    if (status.mode !== "off") {
      setMode(status.mode as "auto" | "cool" | "dry" | "fan");
    }
    setTargetTemp(status.target_temp_c);
    setFanSpeed(status.fan_speed);
    setSleep(status.sleep);
    setUvc(status.uvc);
    setDisplay(status.display);
    setHorizontalSwing(status.horizontal_swing);
    setVerticalSwing(status.vertical_swing);
  }, [status]);

  return (
    <section className="rounded-[30px] border border-white/10 bg-white/6 p-6">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.24em] text-slate-400">Manual control</p>
          <h3 className="mt-2 font-display text-2xl text-white">Basic AC interface</h3>
        </div>
        <div className="rounded-full border border-white/10 bg-black/20 p-3 text-cyan-200">
          <SlidersHorizontal size={18} />
        </div>
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.2fr_0.9fr]">
        <div className="space-y-5">
          <div className="flex flex-wrap gap-3">
            <button
              type="button"
              onClick={() => void onApply({ power: !status.power })}
              className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-black/25 px-4 py-2 text-sm text-white transition hover:border-cyan-300/40 hover:bg-cyan-400/10"
            >
              <Power size={16} />
              {status.power ? "Power off" : "Power on"}
            </button>
            <div className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-black/20 px-4 py-2 text-sm text-slate-300">
              <Gauge size={16} />
              Current source: {status.source}
            </div>
          </div>

          <div>
            <label className="mb-3 block text-xs uppercase tracking-[0.2em] text-slate-400">
              Mode
            </label>
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
              {modes.map((entry) => (
                <button
                  key={entry.value}
                  type="button"
                  onClick={() => setMode(entry.value)}
                  className={`rounded-2xl border px-4 py-3 text-sm transition ${
                    mode === entry.value
                      ? "border-cyan-300/60 bg-cyan-400/15 text-white"
                      : "border-white/10 bg-black/20 text-slate-300 hover:border-white/20 hover:text-white"
                  }`}
                >
                  {entry.label}
                </button>
              ))}
            </div>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <div className="rounded-[24px] border border-white/10 bg-black/20 p-4">
              <div className="text-xs uppercase tracking-[0.2em] text-slate-400">Target temperature</div>
              <div className="mt-3 flex items-center justify-between">
                <button
                  type="button"
                  onClick={() => setTargetTemp((current) => Math.max(16, current - 1))}
                  className="h-12 w-12 rounded-full border border-white/10 bg-white/5 text-xl text-white"
                >
                  –
                </button>
                <div className="font-display text-4xl text-white">{targetTemp}°</div>
                <button
                  type="button"
                  onClick={() => setTargetTemp((current) => Math.min(32, current + 1))}
                  className="h-12 w-12 rounded-full border border-white/10 bg-white/5 text-xl text-white"
                >
                  +
                </button>
              </div>
            </div>

            <div className="rounded-[24px] border border-white/10 bg-black/20 p-4">
              <label className="text-xs uppercase tracking-[0.2em] text-slate-400">Fan speed</label>
              <select
                value={fanSpeed}
                onChange={(event) => setFanSpeed(event.target.value as FanSpeed)}
                className="mt-4 w-full rounded-2xl border border-white/10 bg-slate-950/70 px-4 py-3 text-sm text-white outline-none"
              >
                {fanSpeeds.map((entry) => (
                  <option key={entry} value={entry}>
                    {entry}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>

        <div className="rounded-[28px] border border-white/10 bg-black/20 p-5">
          <div className="mb-4 text-xs uppercase tracking-[0.2em] text-slate-400">Comfort toggles</div>
          <div className="grid gap-3">
            <ToggleRow label="Sleep" checked={sleep} onChange={setSleep} />
            <ToggleRow label="UVC" checked={uvc} onChange={setUvc} />
            <ToggleRow label="Display" checked={display} onChange={setDisplay} />
            <ToggleRow
              label="Horizontal swing"
              checked={horizontalSwing}
              onChange={setHorizontalSwing}
            />
            <label className="text-xs uppercase tracking-[0.2em] text-slate-400">Vertical swing</label>
            <select
              value={verticalSwing}
              onChange={(event) => setVerticalSwing(event.target.value as VerticalSwing)}
              className="rounded-2xl border border-white/10 bg-slate-950/70 px-4 py-3 text-sm text-white outline-none"
            >
              <option value="fixed">Fixed</option>
              <option value="swing">Swing</option>
            </select>
          </div>

          <button
            type="button"
            onClick={() =>
              void onApply({
                power,
                mode,
                target_temp_c: targetTemp,
                fan_speed: fanSpeed,
                sleep,
                uvc,
                display,
                horizontal_swing: horizontalSwing,
                vertical_swing: verticalSwing,
              })
            }
            disabled={saving}
            className="mt-6 inline-flex w-full items-center justify-center gap-2 rounded-full border border-cyan-300/40 bg-cyan-400/15 px-4 py-3 text-sm font-medium text-white transition hover:bg-cyan-400/25 disabled:cursor-not-allowed disabled:opacity-50"
          >
            <Send size={16} />
            {saving ? "Applying…" : "Apply grouped update"}
          </button>
        </div>
      </div>
    </section>
  );
}

type ToggleRowProps = {
  label: string;
  checked: boolean;
  onChange: (next: boolean) => void;
};

function ToggleRow({ label, checked, onChange }: ToggleRowProps) {
  return (
    <button
      type="button"
      onClick={() => onChange(!checked)}
      className="flex items-center justify-between rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-left text-sm text-white transition hover:border-white/20"
    >
      <span>{label}</span>
      <span
        className={`inline-flex rounded-full px-3 py-1 text-[11px] uppercase tracking-[0.18em] ${
          checked ? "bg-cyan-400/20 text-cyan-100" : "bg-slate-700/50 text-slate-300"
        }`}
      >
        {checked ? "On" : "Off"}
      </span>
    </button>
  );
}
