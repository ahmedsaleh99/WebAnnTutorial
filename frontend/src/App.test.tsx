import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import { App } from "./App";

describe("App", () => {
  it("renders semantic dashboard landmarks", () => {
    render(<App role="annotator" />);

    const header = screen.getByRole("banner");
    const headerContent = within(header);

    expect(headerContent.getByRole("link", { name: "WebAnn home" })).toBeInTheDocument();
    expect(headerContent.getByRole("navigation", { name: "Primary navigation" })).toBeInTheDocument();
    expect(screen.getByRole("main")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Dashboard", level: 1 })).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "Configuration" })).not.toBeInTheDocument();
    expect(headerContent.getByRole("button", { name: "User: annotator" })).toBeDisabled();
    expect(headerContent.getByRole("button", { name: "Log out" })).toBeDisabled();
  });

  it("starts keyboard focus at the brand link", async () => {
    const user = userEvent.setup();
    render(<App />);

    await user.tab();

    expect(screen.getByRole("link", { name: "WebAnn home" })).toHaveFocus();
  });
});
