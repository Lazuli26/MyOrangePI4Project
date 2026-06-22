import { NavLink } from "react-router-dom";
import { Home, LineChart, Settings2, Wind } from "lucide-react";

import type { ReactNode } from "react";

type AppShellProps = {
  children: ReactNode;
};

const links = [
  { to: "/", label: "Dashboard", icon: Home },
  { to: "/insights", label: "Insights", icon: LineChart },
  { to: "/settings", label: "Settings", icon: Settings2 },
];

export function AppShell({ children }: AppShellProps) {
  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_top,_rgba(86,214,255,0.14),_transparent_22%),linear-gradient(180deg,_#07111f_0%,_#050910_48%,_#02050a_100%)] text-slate-100">
      <div className="mx-auto flex min-h-screen max-w-7xl flex-col px-4 pb-10 pt-6 sm:px-6 lg:px-8">
        <header className="mb-6 rounded-[28px] border border-white/10 bg-white/5 p-4 shadow-[0_30px_80px_rgba(0,0,0,0.35)] backdrop-blur-xl">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <div className="mb-2 flex items-center gap-3 text-cyan-200/80">
                <span className="rounded-full border border-cyan-400/30 bg-cyan-400/10 px-3 py-1 text-[11px] uppercase tracking-[0.24em]">
                  OrangePi LAN Climate
                </span>
                <Wind size={16} />
              </div>
              <h1 className="font-display text-3xl text-white sm:text-4xl">
                Smart AC Controller
              </h1>
              <p className="mt-2 max-w-2xl text-sm text-slate-300">
                A local-first comfort dashboard that blends live control, weather-aware
                automation, and learnable feedback into one polished control surface.
              </p>
            </div>
            <nav className="flex flex-wrap gap-2">
              {links.map(({ to, label, icon: Icon }) => (
                <NavLink
                  key={to}
                  to={to}
                  className={({ isActive }) =>
                    [
                      "group flex items-center gap-2 rounded-full border px-4 py-2 text-sm transition",
                      isActive
                        ? "border-cyan-300/50 bg-cyan-400/15 text-white shadow-[0_0_24px_rgba(86,214,255,0.18)]"
                        : "border-white/10 bg-white/5 text-slate-300 hover:border-white/20 hover:bg-white/10 hover:text-white",
                    ].join(" ")
                  }
                >
                  <Icon size={16} className="opacity-80 transition group-hover:opacity-100" />
                  <span>{label}</span>
                </NavLink>
              ))}
            </nav>
          </div>
        </header>
        <main className="flex-1">{children}</main>
      </div>
    </div>
  );
}
