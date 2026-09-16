import { describe, expect, it } from "vitest";

import { navigationFor } from "./navigation";

describe("navigationFor", () => {
  it("gives annotators only their work navigation", () => {
    expect(navigationFor("annotator").map((item) => item.label)).toEqual([
      "Dashboard",
      "Assigned work",
    ]);
  });

  it("adds workflow navigation for managers", () => {
    expect(navigationFor("manager").map((item) => item.label)).toContain(
      "Workflow",
    );
  });

  it("adds configuration navigation only for administrators", () => {
    expect(navigationFor("administrator").map((item) => item.label)).toContain(
      "Configuration",
    );
    expect(navigationFor("manager").map((item) => item.label)).not.toContain(
      "Configuration",
    );
  });
});
