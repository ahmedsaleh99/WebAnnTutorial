import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { expect, it, vi } from "vitest";

import { Dropdown } from "./Dropdown";

it("supports arrow keys, selection, and Escape without trapping focus", async () => {
  const onChange = vi.fn();
  render(<Dropdown label="Type" value="dipser" options={[
    { value: "dipser", label: "DIPSER" },
    { value: "cvip2026", label: "CVIP2026" },
  ]} onChange={onChange} />);
  const actor = userEvent.setup();
  const trigger = screen.getByRole("combobox", { name: "Type: DIPSER" });

  trigger.focus();
  await actor.keyboard("{ArrowDown}");
  expect(screen.getByRole("option", { name: "DIPSER" })).toHaveFocus();
  await actor.keyboard("{ArrowDown}{Enter}");
  expect(onChange).toHaveBeenCalledWith("cvip2026");
  expect(screen.queryByRole("listbox")).not.toBeInTheDocument();
  expect(trigger).toHaveFocus();

  await actor.keyboard("{ArrowDown}{Escape}");
  expect(screen.queryByRole("listbox")).not.toBeInTheDocument();
  expect(trigger).toHaveFocus();
});
