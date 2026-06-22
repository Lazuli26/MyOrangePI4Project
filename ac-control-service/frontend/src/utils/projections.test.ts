import { describe, expect, it } from "vitest";

import { buildProjectionRows, modeColor } from "@/utils/projections";

describe("buildProjectionRows", () => {
  it("maps each point into a mode-specific series row", () => {
    const rows = buildProjectionRows([
      {
        hour_label: "08:00",
        minutes_from_midnight: 480,
        segment: "past",
        mode: "cool",
        target_temp_c: 23,
      },
      {
        hour_label: "09:00",
        minutes_from_midnight: 540,
        segment: "future",
        mode: "fan",
        target_temp_c: 25,
      },
    ]);

    expect(rows[0].cool).toBe(23);
    expect(rows[0].fan).toBeNull();
    expect(rows[1].fan).toBe(25);
    expect(rows[1].cool).toBeNull();
  });
});

describe("modeColor", () => {
  it("returns stable palette values for chart styling", () => {
    expect(modeColor("cool")).toBe("#56d6ff");
    expect(modeColor("off")).toBe("#6c7389");
  });
});
