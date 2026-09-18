import { fireEvent, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, expect, it, vi } from "vitest";

import { TemplatesPage } from "./TemplatesPage";

const response = (status: number, data: unknown) => ({
  ok: status >= 200 && status < 300,
  status,
  text: async () => data === null ? "" : JSON.stringify(data),
});
const existing = {
  id: "template-1", name: "Conversation", key: "conversation", project_type: "dipser",
  description: "Speech annotations", configuration: { dimensions: [{ name: "Action" }] },
  version: 1, is_active: true, created_by_username: "admin",
  updated_at: "2026-01-01T12:00:00Z",
};

afterEach(() => vi.unstubAllGlobals());

it("matches the reference filters and card details", async () => {
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue(response(200, {
    results: [existing, { ...existing, id: "template-2", name: "Video", key: "video", project_type: "cvip2026", is_active: false }], next: null,
  })));
  render(<TemplatesPage token="secret" onUnauthorized={() => undefined} />);
  const heading = await screen.findByRole("heading", { name: "Conversation" });
  expect(heading.closest("article")?.querySelector(".template-card-badges")?.textContent).toBe("DIPSERv1Active");
  expect(heading.closest("article")?.querySelector(".status")?.getAttribute("data-tooltip")).toBe("Status");
  expect(screen.getAllByText("Action")).toHaveLength(2);
  expect(within(heading.closest("article") as HTMLElement).getByText("Dimensions")).toBeInTheDocument();
  expect(screen.getAllByText(/Created by/)).toHaveLength(2);
  const actor = userEvent.setup();
  await actor.click(screen.getByRole("combobox", { name: /^Type:/ }));
  await actor.click(screen.getByRole("option", { name: "CVIP2026" }));
  expect(screen.queryByRole("heading", { name: "Conversation" })).not.toBeInTheDocument();
  expect(screen.getByRole("heading", { name: "Video" })).toBeInTheDocument();
  await actor.click(screen.getByRole("combobox", { name: /^Status:/ }));
  await actor.click(screen.getByRole("option", { name: "Active" }));
  expect(screen.getByText("No matching templates")).toBeInTheDocument();
});

it("creates a typed template, then edits it as a new version", async () => {
  const records: Array<Record<string, unknown>> = [];
  const fetchMock = vi.fn(async (_path: string, options: RequestInit) => {
    if (options.method === "GET") return response(200, { results: records, next: null });
    const data = JSON.parse(options.body as string) as Record<string, unknown>;
    const item = { ...existing, ...data, version: options.method === "PATCH" ? 2 : 1 };
    if (options.method === "PATCH") records[0] = item;
    else records.push(item);
    return response(options.method === "PATCH" ? 200 : 201, item);
  });
  vi.stubGlobal("fetch", fetchMock);
  render(<TemplatesPage token="secret" onUnauthorized={() => undefined} />);
  await screen.findByText("No matching templates");
  const actor = userEvent.setup();
  await actor.click(screen.getByRole("button", { name: "New template" }));
  let dialog = within(screen.getByRole("dialog"));
  await actor.type(dialog.getByRole("textbox", { name: "Template name" }), "Conversation");
  expect(dialog.getByRole("textbox", { name: "Unique key" })).toHaveValue("conversation");
  await actor.click(dialog.getByRole("combobox", { name: /^Project type:/ }));
  await actor.click(dialog.getByRole("option", { name: "CVIP2026" }));
  await actor.click(dialog.getByRole("button", { name: "Create template" }));
  expect(await screen.findByRole("heading", { name: "Conversation" })).toBeInTheDocument();
  expect(fetchMock).toHaveBeenCalledWith("/api/templates/", expect.objectContaining({
    method: "POST", headers: expect.objectContaining({ Authorization: "Token secret" }),
    body: expect.stringContaining('"project_type":"cvip2026"'),
  }));
  await actor.click(screen.getByRole("button", { name: "Edit Conversation" }));
  dialog = within(screen.getByRole("dialog"));
  await actor.type(dialog.getByRole("textbox", { name: "Description" }), " updated");
  await actor.click(dialog.getByRole("button", { name: "Save new version" }));
  expect(await screen.findByText(/v2/)).toBeInTheDocument();
});

it("keeps the editor open when JSON or the server rejects a save", async () => {
  const fetchMock = vi.fn(async (_path: string, options: RequestInit) =>
    options.method === "GET" ? response(200, { results: [], next: null })
      : response(400, { key: ["This key is already used."] }));
  vi.stubGlobal("fetch", fetchMock);
  render(<TemplatesPage token="secret" onUnauthorized={() => undefined} />);
  await screen.findByText("No matching templates");
  const actor = userEvent.setup();
  await actor.click(screen.getByRole("button", { name: "New template" }));
  const dialog = within(screen.getByRole("dialog"));
  await actor.type(dialog.getByRole("textbox", { name: "Template name" }), "Conversation");
  await actor.clear(dialog.getByRole("textbox", { name: "Configuration (JSON)" }));
  await actor.type(dialog.getByRole("textbox", { name: "Configuration (JSON)" }), "bad-json");
  await actor.click(dialog.getByRole("button", { name: "Create template" }));
  expect(await dialog.findByRole("alert")).toHaveTextContent("valid JSON object");
  expect(fetchMock).toHaveBeenCalledTimes(1);
  await actor.clear(dialog.getByRole("textbox", { name: "Configuration (JSON)" }));
  fireEvent.change(dialog.getByRole("textbox", { name: "Configuration (JSON)" }), { target: { value: "{}" } });
  await actor.click(dialog.getByRole("button", { name: "Create template" }));
  expect(await dialog.findByRole("alert")).toHaveTextContent("key: This key is already used.");
  expect(dialog.getByRole("textbox", { name: "Template name" })).toHaveValue("Conversation");
});

it("keeps a template visible when the backend rejects deletion", async () => {
  const fetchMock = vi.fn(async (_path: string, options: RequestInit) =>
    options.method === "GET" ? response(200, { results: [existing], next: null })
      : response(409, { detail: "Templates used by projects cannot be deleted." }));
  vi.stubGlobal("fetch", fetchMock);
  vi.stubGlobal("confirm", vi.fn().mockReturnValue(true));
  render(<TemplatesPage token="secret" onUnauthorized={() => undefined} />);
  await screen.findByRole("heading", { name: "Conversation" });
  await userEvent.setup().click(screen.getByRole("button", { name: "Delete Conversation" }));
  expect(await screen.findByRole("alert")).toHaveTextContent("Templates used by projects cannot be deleted.");
  expect(screen.getByRole("heading", { name: "Conversation" })).toBeInTheDocument();
  expect(fetchMock).toHaveBeenCalledWith("/api/templates/template-1/", expect.objectContaining({ method: "DELETE" }));
});

it("restores focus after the template dialog closes", async () => {
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue(response(200, { results: [], next: null })));
  render(<TemplatesPage token="secret" onUnauthorized={() => undefined} />);
  await screen.findByText("No matching templates");
  const open = screen.getByRole("button", { name: "New template" });
  const actor = userEvent.setup();
  await actor.click(open);
  expect(within(screen.getByRole("dialog")).getByRole("textbox", { name: "Template name" })).toHaveFocus();
  await actor.keyboard("{Escape}");
  expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  expect(open).toHaveFocus();
});
