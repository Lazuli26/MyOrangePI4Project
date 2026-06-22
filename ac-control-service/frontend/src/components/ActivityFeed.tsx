import { Clock3 } from "lucide-react";

import type { ActivityItem } from "@/types";

type ActivityFeedProps = {
  items: ActivityItem[];
};

const kinds: Record<ActivityItem["kind"], string> = {
  manual: "Manual",
  feedback: "Feedback",
  smart: "Smart",
};

export function ActivityFeed({ items }: ActivityFeedProps) {
  return (
    <section className="rounded-[30px] border border-white/10 bg-white/6 p-6">
      <div className="mb-5 flex items-center justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.24em] text-slate-400">Recent actions</p>
          <h3 className="mt-2 font-display text-2xl text-white">Automation diary</h3>
        </div>
        <Clock3 size={18} className="text-slate-400" />
      </div>
      <div className="space-y-3">
        {items.length === 0 ? (
          <div className="rounded-[24px] border border-dashed border-white/10 bg-black/20 px-4 py-6 text-sm text-slate-300">
            The controller has not logged any manual or automated actions yet.
          </div>
        ) : null}
        {items.map((item) => (
          <article key={item.id} className="rounded-[24px] border border-white/10 bg-black/20 p-4">
            <div className="flex items-center justify-between gap-4">
              <div>
                <div className="text-[11px] uppercase tracking-[0.2em] text-slate-400">
                  {kinds[item.kind]}
                </div>
                <h4 className="mt-2 text-lg font-medium text-white">{item.title}</h4>
              </div>
              <div className="text-right text-xs text-slate-400">
                <div>{new Date(item.occurred_at).toLocaleDateString()}</div>
                <div>{new Date(item.occurred_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</div>
              </div>
            </div>
            <p className="mt-3 text-sm text-slate-300">{item.detail}</p>
            {item.command_sent != null ? (
              <div className="mt-3 text-xs uppercase tracking-[0.18em] text-slate-400">
                {item.command_sent ? "Command sent to AC" : "Decision logged without sending a command"}
              </div>
            ) : null}
          </article>
        ))}
      </div>
    </section>
  );
}
