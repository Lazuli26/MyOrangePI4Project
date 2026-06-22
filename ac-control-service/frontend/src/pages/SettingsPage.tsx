import { useEffect, useMemo, useState } from "react";
import { LocateFixed, MapPinned, RotateCcw, Save } from "lucide-react";

import { useSmartAcStore } from "@/store/useSmartAcStore";

export default function SettingsPage() {
  const { settings, saving, refreshAll, saveSettings, clearLearningMemory } = useSmartAcStore();
  const [form, setForm] = useState({
    location_label: "Home",
    latitude: 0,
    longitude: 0,
    timezone: "UTC",
    smart_enabled: false,
    allow_automation_power_on: false,
    min_cycle_minutes: 15,
    max_temp_step_c: 2,
    learning_rate: 0.25,
    memory_lifetime_days: 45,
    quiet_hours_start: "",
    quiet_hours_end: "",
    weather_enabled: true,
    presence_detection_enabled: false,
    presence_check_interval_minutes: 5,
    presence_device_ips_text: "",
  });

  useEffect(() => {
    if (!settings) {
      void refreshAll();
    }
  }, [settings, refreshAll]);

  useEffect(() => {
    if (!settings) {
      return;
    }
    setForm({
      location_label: settings.location_label,
      latitude: settings.latitude,
      longitude: settings.longitude,
      timezone: settings.timezone,
      smart_enabled: settings.smart_enabled,
      allow_automation_power_on: settings.allow_automation_power_on,
      min_cycle_minutes: settings.min_cycle_minutes,
      max_temp_step_c: settings.max_temp_step_c,
      learning_rate: settings.learning_rate,
      memory_lifetime_days: settings.memory_lifetime_days,
      quiet_hours_start: settings.quiet_hours_start ?? "",
      quiet_hours_end: settings.quiet_hours_end ?? "",
      weather_enabled: settings.weather_enabled,
      presence_detection_enabled: settings.presence_detection_enabled,
      presence_check_interval_minutes: settings.presence_check_interval_minutes,
      presence_device_ips_text: settings.presence_device_ips.join("\n"),
    });
  }, [settings]);

  const coordinatesValid = useMemo(
    () => Number.isFinite(form.latitude) && Number.isFinite(form.longitude),
    [form.latitude, form.longitude],
  );

  return (
    <div className="grid gap-6 xl:grid-cols-[1.05fr_0.95fr]">
      <section className="rounded-[30px] border border-white/10 bg-white/6 p-6">
        <div className="mb-6">
          <p className="text-xs uppercase tracking-[0.24em] text-slate-400">Location and weather</p>
          <h2 className="mt-2 font-display text-3xl text-white">Environmental inputs</h2>
          <p className="mt-2 text-sm text-slate-300">
            These settings tell the controller where you are so it can combine weather
            forecasts, time zone, and AC feedback more intelligently.
          </p>
        </div>

        <div className="grid gap-4">
          <label className="grid gap-2 text-sm text-slate-200">
            <span>Location label</span>
            <input
              value={form.location_label}
              onChange={(event) => setForm((current) => ({ ...current, location_label: event.target.value }))}
              className="rounded-2xl border border-white/10 bg-slate-950/70 px-4 py-3 text-white outline-none"
            />
          </label>
          <div className="grid gap-4 sm:grid-cols-2">
            <label className="grid gap-2 text-sm text-slate-200">
              <span>Latitude</span>
              <input
                type="number"
                value={form.latitude}
                onChange={(event) =>
                  setForm((current) => ({ ...current, latitude: Number(event.target.value) }))
                }
                className="rounded-2xl border border-white/10 bg-slate-950/70 px-4 py-3 text-white outline-none"
              />
            </label>
            <label className="grid gap-2 text-sm text-slate-200">
              <span>Longitude</span>
              <input
                type="number"
                value={form.longitude}
                onChange={(event) =>
                  setForm((current) => ({ ...current, longitude: Number(event.target.value) }))
                }
                className="rounded-2xl border border-white/10 bg-slate-950/70 px-4 py-3 text-white outline-none"
              />
            </label>
          </div>
          <div className="flex flex-wrap gap-3">
            <button
              type="button"
              onClick={() => {
                if (!navigator.geolocation) {
                  return;
                }
                navigator.geolocation.getCurrentPosition((position) => {
                  const browserTimezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
                  setForm((current) => ({
                    ...current,
                    latitude: Number(position.coords.latitude.toFixed(6)),
                    longitude: Number(position.coords.longitude.toFixed(6)),
                    timezone:
                      current.timezone.trim() && current.timezone !== "UTC"
                        ? current.timezone
                        : browserTimezone || current.timezone,
                  }));
                });
              }}
              className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-4 py-2 text-sm text-white transition hover:border-cyan-300/40 hover:bg-cyan-400/10"
            >
              <LocateFixed size={16} />
              Use browser location
            </button>
            <div className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-black/20 px-4 py-2 text-sm text-slate-300">
              <MapPinned size={16} />
              {coordinatesValid ? "Coordinates ready" : "Enter valid coordinates"}
            </div>
          </div>
          <label className="grid gap-2 text-sm text-slate-200">
            <span>Timezone</span>
            <input
              value={form.timezone}
              onChange={(event) => setForm((current) => ({ ...current, timezone: event.target.value }))}
              className="rounded-2xl border border-white/10 bg-slate-950/70 px-4 py-3 text-white outline-none"
            />
            <span className="text-xs text-slate-400">
              Leave this as `UTC` or clear it and the backend will infer an IANA timezone such as
              `America/Costa_Rica` from the saved coordinates on the next weather refresh.
            </span>
          </label>
          <label className="flex items-center justify-between rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-white">
            <span>Use weather service</span>
            <input
              type="checkbox"
              checked={form.weather_enabled}
              onChange={(event) =>
                setForm((current) => ({ ...current, weather_enabled: event.target.checked }))
              }
              className="h-4 w-4 accent-cyan-400"
            />
          </label>
        </div>
      </section>

      <section className="rounded-[30px] border border-white/10 bg-white/6 p-6">
        <div className="mb-6">
          <p className="text-xs uppercase tracking-[0.24em] text-slate-400">Automation safeguards</p>
          <h2 className="mt-2 font-display text-3xl text-white">Controller tuning</h2>
          <p className="mt-2 text-sm text-slate-300">
            Quiet hours reduce unnecessary adjustments while you are resting. During that window
            the controller still reacts to larger comfort gaps, but it skips tiny one-degree nudges
            that would otherwise create extra beeps, fan changes, or short cycling.
          </p>
        </div>

        <div className="grid gap-4">
          <label className="flex items-center justify-between rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-white">
            <span>Smart control enabled</span>
            <input
              type="checkbox"
              checked={form.smart_enabled}
              onChange={(event) =>
                setForm((current) => ({ ...current, smart_enabled: event.target.checked }))
              }
              className="h-4 w-4 accent-cyan-400"
            />
          </label>

          <label className="flex items-center justify-between rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-white">
            <div>
              <div>Allow automation to power the AC on</div>
              <div className="mt-1 text-xs text-slate-400">
                Leave this off if only manual power-on should wake the AC.
              </div>
            </div>
            <input
              type="checkbox"
              checked={form.allow_automation_power_on}
              onChange={(event) =>
                setForm((current) => ({
                  ...current,
                  allow_automation_power_on: event.target.checked,
                }))
              }
              className="h-4 w-4 accent-cyan-400"
            />
          </label>

          <RangeRow
            label="Minimum cycle interval"
            value={form.min_cycle_minutes}
            unit="min"
            min={5}
            max={120}
            onChange={(value) => setForm((current) => ({ ...current, min_cycle_minutes: value }))}
          />

          <RangeRow
            label="Maximum temperature step"
            value={form.max_temp_step_c}
            unit="°C"
            min={1}
            max={4}
            onChange={(value) => setForm((current) => ({ ...current, max_temp_step_c: value }))}
          />

          <RangeRow
            label="Learning rate"
            value={Number(form.learning_rate.toFixed(2))}
            unit=""
            min={0}
            max={1}
            step={0.05}
            onChange={(value) => setForm((current) => ({ ...current, learning_rate: value }))}
          />

          <RangeRow
            label="Learning memory lifetime"
            value={form.memory_lifetime_days}
            unit="days"
            min={7}
            max={180}
            onChange={(value) => setForm((current) => ({ ...current, memory_lifetime_days: value }))}
          />

          <div className="rounded-[26px] border border-white/10 bg-black/20 p-5">
            <div className="mb-4">
              <p className="text-xs uppercase tracking-[0.24em] text-slate-400">Predictor memory</p>
              <h3 className="mt-2 font-display text-xl text-white">Context regression memory</h3>
              <p className="mt-2 text-sm text-slate-300">
                The predictor learns from saved comfort samples built from your manual target
                changes and `Too cold` or `Too hot` feedback. Older samples outside the selected
                lifetime are ignored during training.
              </p>
              <p className="mt-2 text-xs text-slate-400">
                Season and day-of-week tracking are intentionally not part of this predictor yet.
                Weather and time-of-day are the main signals for now, with those extra dimensions
                left as future work if they prove useful.
              </p>
            </div>

            <button
              type="button"
              onClick={() => {
                if (!window.confirm("Clear the saved learning memory used by the predictor?")) {
                  return;
                }
                void clearLearningMemory();
              }}
              disabled={saving}
              className="inline-flex items-center gap-2 rounded-full border border-rose-300/30 bg-rose-400/10 px-4 py-2 text-sm text-rose-100 transition hover:bg-rose-400/20 disabled:opacity-50"
            >
              <RotateCcw size={16} />
              Clear predictor memory
            </button>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <label className="grid gap-2 text-sm text-slate-200">
              <span>Quiet hours start</span>
              <input
                type="time"
                value={form.quiet_hours_start}
                onChange={(event) =>
                  setForm((current) => ({ ...current, quiet_hours_start: event.target.value }))
                }
                className="rounded-2xl border border-white/10 bg-slate-950/70 px-4 py-3 text-white outline-none"
              />
            </label>
            <label className="grid gap-2 text-sm text-slate-200">
              <span>Quiet hours end</span>
              <input
                type="time"
                value={form.quiet_hours_end}
                onChange={(event) =>
                  setForm((current) => ({ ...current, quiet_hours_end: event.target.value }))
                }
                className="rounded-2xl border border-white/10 bg-slate-950/70 px-4 py-3 text-white outline-none"
              />
            </label>
          </div>

          <div className="rounded-[26px] border border-white/10 bg-black/20 p-5">
            <div className="mb-4">
              <p className="text-xs uppercase tracking-[0.24em] text-slate-400">
                Presence detection
              </p>
              <h3 className="mt-2 font-display text-xl text-white">LAN home detection</h3>
              <p className="mt-2 text-sm text-slate-300">
                Monitor one or more LAN IP addresses, like your phone. If none of them respond,
                automation assumes nobody is home and turns the AC off.
              </p>
            </div>

            <div className="grid gap-4">
              <label className="flex items-center justify-between rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-white">
                <div>
                  <div>Enable presence detection</div>
                  <div className="mt-1 text-xs text-slate-400">
                    This check is optional and only affects automation behavior.
                  </div>
                </div>
                <input
                  type="checkbox"
                  checked={form.presence_detection_enabled}
                  onChange={(event) =>
                    setForm((current) => ({
                      ...current,
                      presence_detection_enabled: event.target.checked,
                    }))
                  }
                  className="h-4 w-4 accent-cyan-400"
                />
              </label>

              <RangeRow
                label="Presence check interval"
                value={form.presence_check_interval_minutes}
                unit="min"
                min={1}
                max={120}
                onChange={(value) =>
                  setForm((current) => ({
                    ...current,
                    presence_check_interval_minutes: value,
                  }))
                }
              />

              <label className="grid gap-2 text-sm text-slate-200">
                <span>Monitored LAN IP addresses</span>
                <textarea
                  value={form.presence_device_ips_text}
                  onChange={(event) =>
                    setForm((current) => ({
                      ...current,
                      presence_device_ips_text: event.target.value,
                    }))
                  }
                  rows={5}
                  placeholder={"192.168.50.100\n192.168.50.101"}
                  className="rounded-2xl border border-white/10 bg-slate-950/70 px-4 py-3 text-white outline-none"
                />
                <span className="text-xs text-slate-400">
                  Enter one IP per line. If every monitored device is unreachable, automation
                  treats the home as empty and keeps the AC off.
                </span>
              </label>
            </div>
          </div>
        </div>

        <button
          type="button"
          onClick={() =>
            void saveSettings({
              ...form,
              memory_lifetime_days: form.memory_lifetime_days,
              quiet_hours_start: form.quiet_hours_start || null,
              quiet_hours_end: form.quiet_hours_end || null,
              presence_device_ips: form.presence_device_ips_text
                .split(/\r?\n/)
                .map((item) => item.trim())
                .filter(Boolean),
            })
          }
          disabled={saving}
          className="mt-6 inline-flex w-full items-center justify-center gap-2 rounded-full border border-cyan-300/40 bg-cyan-400/15 px-4 py-3 text-sm font-medium text-white transition hover:bg-cyan-400/25 disabled:opacity-50"
        >
          <Save size={16} />
          {saving ? "Saving…" : "Save settings"}
        </button>
      </section>
    </div>
  );
}

type RangeRowProps = {
  label: string;
  value: number;
  min: number;
  max: number;
  unit: string;
  step?: number;
  onChange: (value: number) => void;
};

function RangeRow({ label, value, min, max, unit, step = 1, onChange }: RangeRowProps) {
  return (
    <label className="grid gap-2 rounded-2xl border border-white/10 bg-white/5 px-4 py-4 text-sm text-slate-200">
      <div className="flex items-center justify-between">
        <span>{label}</span>
        <span className="font-medium text-white">
          {value}
          {unit}
        </span>
      </div>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(event) => onChange(Number(event.target.value))}
        className="accent-cyan-400"
      />
    </label>
  );
}
