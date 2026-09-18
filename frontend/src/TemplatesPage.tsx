import { useEffect, useRef, useState, type SubmitEvent } from "react";

import { ApiError } from "./api";
import { Dropdown } from "./Dropdown";
import { deleteTemplate, listTemplates, saveTemplate,
  type ProjectTemplate, type ProjectType, type TemplateInput } from "./templatesApi";

const projectTypes: { value: ProjectType; label: string }[] = [
  { value: "dipser", label: "DIPSER" },
  { value: "cvip2020", label: "CVIP2020" },
  { value: "cvip2026", label: "CVIP2026" },
];
const slugify = (value: string) => value.toLowerCase().trim()
  .replace(/[^a-z0-9]+/g, "-").replace(/(^-|-$)/g, "");
const initialConfiguration = {
  dimensions: ["action", "affect", "engagement"].map((name) => ({
    name, key: name, labels: [
      { name: "Unavailable", color: "#555965" },
      { name: "Ambiguous", color: "#8b8e99" },
    ],
  })),
  bounding_boxes: true,
  multiple_video_views: true,
};

function message(error: unknown): string {
  return error instanceof Error ? error.message : "Could not save the template.";
}

function dimensionNames(configuration: Record<string, unknown>): string[] {
  if (!Array.isArray(configuration.dimensions)) return [];
  return configuration.dimensions.map((item: unknown) => {
    if (typeof item === "string") return item;
    return typeof item === "object" && item !== null && "name" in item && typeof item.name === "string"
      ? item.name : "Dimension";
  });
}

function TemplateDialog({ template, token, onClose, onSaved, onUnauthorized }: {
  template: ProjectTemplate | null;
  token: string;
  onClose: () => void;
  onSaved: (item: ProjectTemplate) => void;
  onUnauthorized: () => void;
}) {
  const [form, setForm] = useState<TemplateInput>({
    name: template?.name ?? "", key: template?.key ?? "",
    project_type: template?.project_type ?? "dipser",
    is_active: template?.is_active ?? true,
    description: template?.description ?? "",
    configuration: template?.configuration ?? initialConfiguration,
  });
  const [configuration, setConfiguration] = useState(JSON.stringify(form.configuration, null, 2));
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const dialogRef = useRef<HTMLDivElement>(null);
  const nameRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    nameRef.current?.focus();
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") { onClose(); return; }
      if (event.key !== "Tab" || !dialogRef.current) return;
      const controls = Array.from(dialogRef.current.querySelectorAll<HTMLElement>(
        "button:not(:disabled), input:not(:disabled), select:not(:disabled), textarea:not(:disabled)",
      ));
      if (event.shiftKey && document.activeElement === controls[0]) {
        event.preventDefault(); controls[controls.length - 1]?.focus();
      } else if (!event.shiftKey && document.activeElement === controls[controls.length - 1]) {
        event.preventDefault(); controls[0]?.focus();
      }
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [onClose]);

  async function submit(event: SubmitEvent<HTMLFormElement>) {
    event.preventDefault();
    let parsed: unknown;
    try { parsed = JSON.parse(configuration) as unknown; }
    catch { setError("Configuration must be a valid JSON object."); return; }
    if (typeof parsed !== "object" || parsed === null || Array.isArray(parsed)) {
      setError("Configuration must be a valid JSON object."); return;
    }
    setError(null);
    setSaving(true);
    try { onSaved(await saveTemplate({ ...form, configuration: parsed as Record<string, unknown> }, token, template?.id)); }
    catch (failure) {
      if (failure instanceof ApiError && failure.kind === "unauthorized") onUnauthorized();
      else setError(message(failure));
    } finally { setSaving(false); }
  }

  return <div className="modal-backdrop" onMouseDown={(event) => { if (event.target === event.currentTarget) onClose(); }}>
    <div ref={dialogRef} role="dialog" aria-modal="true" aria-label={template ? `Edit ${template.name}` : "Create project template"}>
      <form className="template-dialog" onSubmit={submit}>
        <header><div><small>{template ? "EDIT TEMPLATE" : "NEW TEMPLATE"}</small>
          <h2>{template?.name ?? "Create project template"}</h2></div>
          <button className="close-button" type="button" aria-label="Close dialog" onClick={onClose}>
            <svg viewBox="0 0 24 24" aria-hidden="true"><path d="m7 7 10 10M17 7 7 17" /></svg>
          </button></header>
        <div className="template-dialog-body">
          {error && <p role="alert">{error}</p>}
          <div className="form-grid">
            <label>Template name<input ref={nameRef} required value={form.name} onChange={(event) => {
              const name = event.currentTarget.value;
              setForm((current) => ({ ...current, name,
                key: !template && (!current.key || current.key === slugify(current.name)) ? slugify(name) : current.key }));
            }} /></label>
            <label>Unique key<input required pattern="[a-z0-9-]+" value={form.key} onChange={(event) => {
              const key = event.currentTarget.value;
              setForm((current) => ({ ...current, key }));
            }} /></label>
            <Dropdown label="Project type" value={form.project_type} options={projectTypes}
              onChange={(project_type) => setForm((current) => ({ ...current, project_type }))} />
            <label className="checkbox"><input type="checkbox" checked={form.is_active} onChange={(event) => {
              const is_active = event.currentTarget.checked;
              setForm((current) => ({ ...current, is_active }));
            }} />Active template</label>
            <label className="wide">Description<textarea rows={3} value={form.description} onChange={(event) => {
              const description = event.currentTarget.value;
              setForm((current) => ({ ...current, description }));
            }} /></label>
            <label className="wide">Configuration (JSON)<textarea className="code" rows={10} value={configuration} onChange={(event) => setConfiguration(event.currentTarget.value)} /></label>
          </div>
        </div>
        <footer><button type="button" onClick={onClose}>Cancel</button>
          <button className="primary" type="submit" disabled={saving}>{saving ? "Saving…" : template ? "Save new version" : "Create template"}</button></footer>
      </form>
    </div>
  </div>;
}

export function TemplatesPage({ token, onUnauthorized }: { token: string; onUnauthorized: () => void }) {
  const [templates, setTemplates] = useState<ProjectTemplate[]>([]);
  const [loading, setLoading] = useState(Boolean(token));
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [activity, setActivity] = useState("all");
  const [type, setType] = useState("all");
  const [editing, setEditing] = useState<ProjectTemplate | "new" | null>(null);
  const returnFocus = useRef<HTMLElement | null>(null);

  useEffect(() => {
    if (!token) return;
    let active = true;
    listTemplates(token).then((items) => { if (active) setTemplates(items); })
      .catch((failure: unknown) => {
        if (!active) return;
        if (failure instanceof ApiError && failure.kind === "unauthorized") onUnauthorized();
        else setError(message(failure));
      }).finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [token, onUnauthorized]);

  function open(template: ProjectTemplate | "new") {
    returnFocus.current = document.activeElement instanceof HTMLElement ? document.activeElement : null;
    setEditing(template);
  }
  function close() { setEditing(null); queueMicrotask(() => returnFocus.current?.focus()); }
  async function remove(template: ProjectTemplate) {
    if (!window.confirm(`Delete ${template.name}?`)) return;
    setError(null);
    try {
      await deleteTemplate(template.id, token);
      setTemplates((current) => current.filter((item) => item.id !== template.id));
    } catch (failure) {
      if (failure instanceof ApiError && failure.kind === "unauthorized") onUnauthorized();
      else setError(message(failure));
    }
  }

  const types = Array.from(new Set(templates.map((template) => template.project_type)));
  const query = search.trim().toLowerCase();
  const filtered = templates.filter((template) =>
    (activity === "all" || (activity === "active") === template.is_active)
    && (type === "all" || template.project_type === type)
    && (!query || `${template.name} ${template.key} ${template.description}`.toLowerCase().includes(query)));

  return <section aria-labelledby="templates-heading">
    <div className="page-heading"><div><small>ADMINISTRATION</small><h1 id="templates-heading">Project templates</h1>
      <p>Define reusable annotation schemas and behavior.</p></div>
      <button className="primary add-button" type="button" aria-label="New template" onClick={() => open("new")}><b aria-hidden="true">+</b><span>New template</span></button></div>
    {error && <p role="alert">{error}</p>}
    <div className="card-filters template-filters">
      <label>Search<input type="search" placeholder="Name, key, description..." value={search} onChange={(event) => setSearch(event.currentTarget.value)} /></label>
      <Dropdown label="Status" value={activity} options={[
        { value: "all", label: "All statuses" }, { value: "active", label: "Active" }, { value: "inactive", label: "Inactive" },
      ]} onChange={setActivity} />
      <Dropdown label="Type" value={type} options={[
        { value: "all", label: "All types" },
        ...types.map((item) => ({ value: item, label: projectTypes.find((choice) => choice.value === item)?.label ?? item })),
      ]} onChange={setType} />
      <span>{filtered.length} of {templates.length} templates</span>
    </div>
    {loading ? <p role="status">Loading templates…</p> : <div className="template-grid">
      {filtered.map((template) => <article className="template-card" key={template.id}>
        <header><div className="template-icon">T</div>
          <div className="template-card-badges">
            <span className="template-type-badge" data-tooltip="Project type">{projectTypes.find((choice) => choice.value === template.project_type)?.label}</span>
            <span className="version-badge" data-tooltip="Version">v{template.version}</span>
            <span className={`status ${template.is_active ? "active" : ""}`} data-tooltip="Status">{template.is_active ? "Active" : "Inactive"}</span>
          </div>
        </header>
        <h2>{template.name}</h2><p>{template.description || "No description"}</p>
        <div className="template-dimensions"><small>Dimensions</small>
          <div className="chips">{dimensionNames(template.configuration).map((name, index) => <span key={`${name}-${index}`}>{name}</span>)}</div>
        </div>
        <footer><div className="card-footer-meta"><span>Created by <strong>{template.created_by_username ?? "Unknown"}</strong></span>
          <span>Updated {new Date(template.updated_at).toLocaleDateString()}</span></div>
          <div className="card-actions"><button className="icon-button" type="button" aria-label={`Edit ${template.name}`} title={`Edit ${template.name}`} onClick={() => open(template)}>
            <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 20h4l11-11-4-4L4 16v4Zm12-16 4 4 1-1a2 2 0 0 0 0-3l-1-1a2 2 0 0 0-3 0l-1 1Z" /></svg>
          </button>
            <button className="icon-button danger" type="button" aria-label={`Delete ${template.name}`} title={`Delete ${template.name}`} onClick={() => void remove(template)}>
              <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 7h14M9 7V4h6v3m-8 0 1 13h8l1-13M10 11v5m4-5v5" /></svg>
            </button></div>
        </footer>
      </article>)}
      {filtered.length === 0 && <div className="empty"><strong>No matching templates</strong><p>{templates.length ? "Change or clear the filters." : "Create the first CVIP Engagement template."}</p></div>}
    </div>}
    {editing && <TemplateDialog key={editing === "new" ? "new" : editing.id} template={editing === "new" ? null : editing}
      token={token} onUnauthorized={onUnauthorized} onClose={close} onSaved={(item) => {
        setTemplates((current) => editing === "new" ? [...current, item] : current.map((value) => value.id === item.id ? item : value));
        close();
      }} />}
  </section>;
}
