// Typed client for the Prescription Cost Analysis API.

export interface MonthRef { year_month: number; label: string; }

export interface Meta {
  months: MonthRef[];
  latest_month: number | null;
  earliest_month: number | null;
  month_count: number;
  last_updated: string | null;
}

export interface Kpi { value: number; mom_pct: number | null; yoy_pct: number | null; }
export interface Overview {
  year_month: number;
  label: string;
  nic: Kpi;
  items: Kpi;
  cost_per_item: Kpi;
  quantity: Kpi;
}

export interface TrendPoint {
  year_month: number; label: string;
  nic: number; items: number; quantity: number; cost_per_item: number;
}

export interface Breakdown {
  code: string; name: string; parent: string | null;
  nic: number; items: number; quantity: number; cost_per_item?: number;
}

export interface Drug {
  code: string; name: string; chapter: string;
  nic: number; items: number; quantity: number; cost_per_item: number;
}

export interface PrepGroup { prep_group: string; nic: number; items: number; }
export interface PrepClass {
  prep_class: string; prep_class_label: string; prep_group: string;
  nic: number; items: number; quantity: number;
}
export interface PrepBreakdown { groups: PrepGroup[]; classes: PrepClass[]; }

const BASE = import.meta.env.VITE_API_BASE || "";

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) throw new Error(`${res.status} ${res.statusText} for ${path}`);
  return res.json() as Promise<T>;
}

export const api = {
  meta: () => get<Meta>("/api/meta"),
  overview: (month: string) => get<Overview>(`/api/overview?month=${month}`),
  trend: () => get<TrendPoint[]>("/api/trend"),
  therapeutic: (month: string, level: "chapter" | "section", limit = 15) =>
    get<Breakdown[]>(`/api/therapeutic?month=${month}&level=${level}&limit=${limit}`),
  geography: (month: string, level: "region" | "icb") =>
    get<Breakdown[]>(`/api/geography?month=${month}&level=${level}`),
  drugs: (month: string, limit = 15) => get<Drug[]>(`/api/drugs?month=${month}&limit=${limit}`),
  prepclass: (month: string) => get<PrepBreakdown>(`/api/prepclass?month=${month}`),
};
