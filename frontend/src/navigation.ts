import type { UserRole } from "./api";

export interface NavigationItem {
  href: string;
  label: string;
}

const commonItems: NavigationItem[] = [{ href: "#jobs", label: "Jobs" }];

export function navigationFor(role: UserRole): NavigationItem[] {
  const items = [...commonItems];
  if (role === "manager" || role === "admin") {
    items.push({ href: "#tasks", label: "Tasks" });
    items.push({ href: "#videos", label: "Videos" });
    items.push({ href: "#projects", label: "Projects" });
  }
  if (role === "admin") {
    items.push({ href: "#templates", label: "Project templates" });
    items.push({ href: "#users", label: "Users" });
    items.push({ href: "#analytics", label: "Analytics" });
    items.push({ href: "#agreement", label: "Agreement" });
    items.push({ href: "#logs", label: "Logs" });
  }
  return items;
}
