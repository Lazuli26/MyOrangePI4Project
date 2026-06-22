import { useEffect } from "react";
import { BarChart3, ThermometerSun } from "lucide-react";

import { ActivityFeed } from "@/components/ActivityFeed";
import { ProjectionChartCard } from "@/components/ProjectionChartCard";
import { SleepProfileEditor } from "@/components/SleepProfileEditor";
import { useSmartAcStore } from "@/store/useSmartAcStore";

function formatObservedTime(iso: string, timezone: string) {
  try {
    return new Date(iso).toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
      timeZone: timezone,
    });
  } catch {
    return new Date(iso).toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
    });
  }
}

export default function InsightsPage() {
  const {
    dashboard,
    saving,
    refreshAll,
    saveSleepProfile,
    deleteSleepProfile,
  } = useSmartAcStore();

  useEffect(() => {
    if (!dashboard) {
      void refreshAll();
    }
  }, [dashboard, refreshAll]);

  if (!dashboard) {
    return <div className="h-64 animate-pulse rounded-[30px] bg-white/5" />;
  }

  const weather = dashboard.weather;
  const facts = [
    {
      label: "Outdoor high forecast",
      value:
        weather?.forecast_high_c != null ? `${weather.forecast_high_c.toFixed(1)}°C` : "—",
      icon: ThermometerSun,
    },
    {
      label: "Weather observations",
      value: weather?.observed_at
        ? formatObservedTime(
            weather.observed_at,
            dashboard.smart_control.context.timezone,
          )
        : "—",
      icon: BarChart3,
    },
  ];

  return (
    <div className="space-y-6">
      <section className="grid gap-4 lg:grid-cols-2">
        {facts.map(({ label, value, icon: Icon }) => (
          <div key={label} className="rounded-[28px] border border-white/10 bg-white/6 p-6">
            <div className="flex items-center justify-between text-slate-400">
              <span className="text-xs uppercase tracking-[0.2em]">{label}</span>
              <Icon size={18} />
            </div>
            <div className="mt-4 font-display text-4xl text-white">{value}</div>
          </div>
        ))}
      </section>

      <ProjectionChartCard
        projections={dashboard.projections}
        timezone={dashboard.smart_control.context.timezone}
        localTimeIso={dashboard.smart_control.context.local_time_iso}
      />
      <SleepProfileEditor
        profiles={dashboard.sleep_profiles}
        saving={saving}
        onSave={saveSleepProfile}
        onDelete={deleteSleepProfile}
      />
      <ActivityFeed items={dashboard.activity} />
    </div>
  );
}
