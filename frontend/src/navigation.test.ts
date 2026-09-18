import { describe, expect, it } from "vitest";

import { navigationFor } from "./navigation";

describe("navigationFor", () => {
  it("gives annotators only their work navigation", () => {
    expect(navigationFor("annotator").map((item) => item.label)).toEqual([
      "Jobs",
    ]);
  });

  it("shows tasks and projects to managers", () => {
    expect(navigationFor("manager").map((item) => item.label)).toEqual([
      "Jobs", "Tasks", "Videos", "Projects",
    ]);
  });

  it("adds configuration navigation only for administrators", () => {
    expect(navigationFor("admin").map((item) => item.label)).toEqual([
      "Jobs", "Tasks", "Videos", "Projects", "Project templates",
      "Users", "Analytics", "Agreement", "Logs",
    ]);
    expect(navigationFor("manager").map((item) => item.label)).not.toContain(
      "Project templates",
    );
  });
});
