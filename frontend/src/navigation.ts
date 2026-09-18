import type { UserRole } from "./api";

export interface NavigationItem {
  href: string;
  label: string;
}

const commonItems: NavigationItem[] = [
  { href: "#dashboard", label: "Dashboard" },
  { href: "#assigned-work", label: "Assigned work" },
];

export function navigationFor(role: UserRole): NavigationItem[] {
  const items = [...commonItems];
  if (role === "manager" || role === "admin") {
    items.push({ href: "#workflow", label: "Workflow" });
  }
  if (role === "admin") {
    items.push({ href: "#configuration", label: "Configuration" });
  }
  return items;
}
