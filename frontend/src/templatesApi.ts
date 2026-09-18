import { ApiError, request } from "./api";

export type ProjectType = "dipser" | "cvip2020" | "cvip2026";

export interface ProjectTemplate {
  id: string;
  name: string;
  key: string;
  project_type: ProjectType;
  description: string;
  configuration: Record<string, unknown>;
  version: number;
  is_active: boolean;
  created_by_username: string | null;
  updated_at: string;
}

export type TemplateInput = Pick<ProjectTemplate,
  "name" | "key" | "project_type" | "description" | "configuration" | "is_active">;

function record(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function readTemplate(value: unknown): ProjectTemplate {
  if (!record(value) || typeof value.id !== "string" || typeof value.name !== "string"
    || typeof value.key !== "string" || !["dipser", "cvip2020", "cvip2026"].includes(String(value.project_type))
    || typeof value.description !== "string" || !record(value.configuration)
    || typeof value.version !== "number" || typeof value.is_active !== "boolean"
    || (value.created_by_username !== null && typeof value.created_by_username !== "string")
    || typeof value.updated_at !== "string") {
    throw new ApiError("The server returned invalid template data.", null, "server");
  }
  return value as unknown as ProjectTemplate;
}

export async function listTemplates(token: string): Promise<ProjectTemplate[]> {
  const templates: ProjectTemplate[] = [];
  let path: string | null = "/api/templates/";
  while (path) {
    const page: unknown = await request(path, "GET", undefined, token);
    if (!record(page) || !Array.isArray(page.results)
      || (page.next !== null && typeof page.next !== "string")) {
      throw new ApiError("The server returned an invalid template list.", null, "server");
    }
    templates.push(...page.results.map(readTemplate));
    if (page.next) {
      const next = new URL(page.next, window.location.origin);
      if (next.pathname !== "/api/templates/") {
        throw new ApiError("The server returned an invalid template page.", null, "server");
      }
      path = next.pathname + next.search;
    } else path = null;
  }
  return templates;
}

export async function saveTemplate(input: TemplateInput, token: string, id?: string): Promise<ProjectTemplate> {
  return readTemplate(await request(id ? `/api/templates/${id}/` : "/api/templates/", id ? "PATCH" : "POST", input, token));
}

export async function deleteTemplate(id: string, token: string): Promise<void> {
  await request(`/api/templates/${id}/`, "DELETE", undefined, token);
}
