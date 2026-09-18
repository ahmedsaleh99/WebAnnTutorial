import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { App } from "./App";

const annotator = { id: 1, username: "amina", role: "annotator" as const, must_change_password: false };

describe("App", () => {
  it("renders semantic dashboard landmarks", () => {
    render(<App user={annotator} onLogout={() => undefined} />);

    const header = screen.getByRole("banner");
    const headerContent = within(header);

    expect(headerContent.getByText("Annotation Platform")).toBeInTheDocument();
    expect(headerContent.getByRole("navigation", { name: "Primary navigation" })).toBeInTheDocument();
    expect(screen.getByRole("main")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "My jobs", level: 1 })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Project templates" })).not.toBeInTheDocument();
    expect(headerContent.getByText("amina")).toBeInTheDocument();
    expect(headerContent.getByRole("button", { name: "Sign out" })).toBeEnabled();
  });

  it("starts keyboard focus at the Jobs navigation button", async () => {
    const user = userEvent.setup();
    render(<App user={annotator} onLogout={() => undefined} />);

    await user.tab();

    expect(screen.getByRole("button", { name: "My Jobs" })).toHaveFocus();
  });

  it("calls logout when the user activates the header button", async () => {
    const onLogout = vi.fn();
    render(<App user={annotator} onLogout={onLogout} />);

    await userEvent.setup().click(screen.getByRole("button", { name: "Sign out" }));

    expect(onLogout).toHaveBeenCalledOnce();
  });

  it("shows configuration only for the backend admin role", () => {
    const admin = { ...annotator, role: "admin" as const };
    render(<App user={admin} onLogout={() => undefined} />);

    expect(screen.getByRole("button", { name: "Project templates" })).toBeInTheDocument();
    expect(within(screen.getByRole("banner")).getByText("Admin")).toBeInTheDocument();
  });
});
