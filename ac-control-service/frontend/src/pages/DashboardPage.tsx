import { useEffect, useState } from "react";
import { AlertTriangle, RefreshCcw } from "lucide-react";

import { ActivityFeed } from "@/components/ActivityFeed";
import { ManualControlCard } from "@/components/ManualControlCard";
import { ProjectionChartCard } from "@/components/ProjectionChartCard";
import { SmartControlCard } from "@/components/SmartControlCard";
import { StatusHero } from "@/components/StatusHero";
import { useSmartAcStore } from "@/store/useSmartAcStore";

export default function DashboardPage() {
  const [controlFace, setControlFace] = useState<"manual" | "automation">("manual");
  const {
    dashboard,
    loading,
    saving,
    error,
    clearError,
    refreshAll,
    applyManual,
    setSmartControl,
    evaluateSmartControl,
    sendFeedback,
  } = useSmartAcStore();

  useEffect(() => {
    if (!dashboard) {
      void refreshAll();
    }
  }, [dashboard, refreshAll]);

  if (!dashboard && loading) {
    return <DashboardSkeleton />;
  }

  if (!dashboard) {
    return (
      <div className="rounded-[30px] border border-rose-300/20 bg-rose-400/10 p-6 text-rose-100">
        Dashboard data is not available yet. Try refreshing the service.
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {error ? (
        <div className="flex items-center justify-between rounded-[24px] border border-amber-300/20 bg-amber-300/10 px-4 py-3 text-sm text-amber-50">
          <div className="flex items-center gap-3">
            <AlertTriangle size={16} />
            <span>{error}</span>
          </div>
          <button type="button" className="text-xs uppercase tracking-[0.18em]" onClick={clearError}>
            Dismiss
          </button>
        </div>
      ) : null}

      <div className="flex justify-end">
        <button
          type="button"
          onClick={() => void refreshAll()}
          className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-4 py-2 text-sm text-slate-200 transition hover:border-white/20 hover:text-white"
        >
          <RefreshCcw size={16} />
          Refresh live status
        </button>
      </div>

      <StatusHero status={dashboard.status} smartControl={dashboard.smart_control} />

      <section className="space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="text-xs uppercase tracking-[0.24em] text-slate-400">Control deck</p>
            <h2 className="mt-2 font-display text-2xl text-white">
              Manual control and automation
            </h2>
            <p className="mt-2 max-w-2xl text-sm text-slate-300">
              Switch between direct AC commands and the smart engine. They use the same live
              device state and shape the same comfort history.
            </p>
          </div>
          <div className="inline-flex rounded-full border border-white/10 bg-black/20 p-1">
            <button
              type="button"
              onClick={() => setControlFace("manual")}
              className={`rounded-full px-4 py-2 text-sm transition ${
                controlFace === "manual"
                  ? "bg-cyan-400/15 text-white"
                  : "text-slate-300 hover:text-white"
              }`}
            >
              Manual
            </button>
            <button
              type="button"
              onClick={() => setControlFace("automation")}
              className={`rounded-full px-4 py-2 text-sm transition ${
                controlFace === "automation"
                  ? "bg-cyan-400/15 text-white"
                  : "text-slate-300 hover:text-white"
              }`}
            >
              Automation
            </button>
          </div>
        </div>

        {controlFace === "manual" ? (
          <ManualControlCard status={dashboard.status} saving={saving} onApply={applyManual} />
        ) : (
          <SmartControlCard
            smartControl={dashboard.smart_control}
            saving={saving}
            onToggle={setSmartControl}
            onEvaluate={evaluateSmartControl}
            onFeedback={(direction) => sendFeedback(direction)}
          />
        )}
      </section>

      <div className="grid gap-6 xl:grid-cols-[1.15fr_0.85fr]">
        <ProjectionChartCard
          projections={dashboard.projections}
          timezone={dashboard.smart_control.context.timezone}
          localTimeIso={dashboard.smart_control.context.local_time_iso}
        />
        <ActivityFeed items={dashboard.activity} />
      </div>
    </div>
  );
}

function DashboardSkeleton() {
  return (
    <div className="space-y-6">
      <div className="h-64 animate-pulse rounded-[30px] bg-white/5" />
      <div className="grid gap-6 xl:grid-cols-2">
        <div className="h-96 animate-pulse rounded-[30px] bg-white/5" />
        <div className="h-96 animate-pulse rounded-[30px] bg-white/5" />
      </div>
      <div className="grid gap-6 xl:grid-cols-[1.15fr_0.85fr]">
        <div className="h-96 animate-pulse rounded-[30px] bg-white/5" />
        <div className="h-96 animate-pulse rounded-[30px] bg-white/5" />
      </div>
    </div>
  );
}
