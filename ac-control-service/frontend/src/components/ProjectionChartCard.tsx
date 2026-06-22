import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ReferenceArea,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type { ProjectionPoint } from "@/types";
import { buildProjectionRows, modeColor } from "@/utils/projections";

type ProjectionChartCardProps = {
  projections: ProjectionPoint[];
  timezone?: string;
  localTimeIso?: string;
};

export function ProjectionChartCard({
  projections,
  timezone,
  localTimeIso,
}: ProjectionChartCardProps) {
  const rows = buildProjectionRows(projections);
  const currentPoint = rows.find((row) => row.segment === "current");
  const localClock = localTimeIso?.slice(11, 16);

  return (
    <section className="rounded-[30px] border border-white/10 bg-white/6 p-6">
      <div className="mb-6 flex flex-col gap-2 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.24em] text-slate-400">Prediction curve</p>
          <h3 className="mt-2 font-display text-2xl text-white">Daily comfort line</h3>
          <p className="mt-2 max-w-3xl text-sm text-slate-300">
            Past values show the average target temperature by hour. The current point is live,
            and the shaded future region projects where the controller is likely to steer next.
          </p>
        </div>
        <div className="text-right text-xs uppercase tracking-[0.18em] text-slate-400">
          <div>Color represents the active AC mode across the day</div>
          {timezone ? (
            <div className="mt-2 tracking-[0.12em] text-slate-500">
              Hours shown in {timezone}
              {localClock ? ` • local now ${localClock}` : ""}
            </div>
          ) : null}
        </div>
      </div>
      <div className="h-[360px] rounded-[24px] border border-white/10 bg-black/20 p-3">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={rows} margin={{ left: 8, right: 8, top: 24, bottom: 12 }}>
            <CartesianGrid stroke="rgba(255,255,255,0.07)" vertical={false} />
            {currentPoint ? (
              <ReferenceArea
                x1={currentPoint.hourLabel}
                x2="23:00"
                fill="rgba(86,214,255,0.08)"
                strokeOpacity={0}
              />
            ) : null}
            <XAxis
              dataKey="hourLabel"
              stroke="#8b93a7"
              tickLine={false}
              axisLine={false}
              tickMargin={12}
              minTickGap={18}
            />
            <YAxis
              domain={[16, 32]}
              stroke="#8b93a7"
              tickLine={false}
              axisLine={false}
              width={40}
            />
            <Tooltip
              contentStyle={{
                background: "rgba(10, 14, 24, 0.92)",
                borderRadius: "18px",
                border: "1px solid rgba(255,255,255,0.08)",
                color: "#fff",
              }}
            />
            <Legend />
            <Line type="monotone" dataKey="off" name="Off" stroke={modeColor("off")} strokeWidth={3} dot={false} connectNulls={false} />
            <Line type="monotone" dataKey="auto" name="Auto" stroke={modeColor("auto")} strokeWidth={3} dot={false} connectNulls={false} />
            <Line type="monotone" dataKey="cool" name="Cool" stroke={modeColor("cool")} strokeWidth={3} dot={false} connectNulls={false} />
            <Line type="monotone" dataKey="dry" name="Dry" stroke={modeColor("dry")} strokeWidth={3} dot={false} connectNulls={false} />
            <Line type="monotone" dataKey="fan" name="Fan" stroke={modeColor("fan")} strokeWidth={3} dot={false} connectNulls={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}
