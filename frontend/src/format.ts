// Number / currency formatting helpers used across the dashboard.

export function gbpCompact(n: number): string {
  const abs = Math.abs(n);
  if (abs >= 1e9) return `£${(n / 1e9).toFixed(2)}bn`;
  if (abs >= 1e6) return `£${(n / 1e6).toFixed(1)}m`;
  if (abs >= 1e3) return `£${(n / 1e3).toFixed(1)}k`;
  return `£${n.toFixed(0)}`;
}

export function gbp(n: number): string {
  return new Intl.NumberFormat("en-GB", {
    style: "currency",
    currency: "GBP",
    maximumFractionDigits: 0,
  }).format(n);
}

export function gbpPrecise(n: number): string {
  return new Intl.NumberFormat("en-GB", {
    style: "currency",
    currency: "GBP",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(n);
}

export function numCompact(n: number): string {
  const abs = Math.abs(n);
  if (abs >= 1e9) return `${(n / 1e9).toFixed(2)}bn`;
  if (abs >= 1e6) return `${(n / 1e6).toFixed(1)}m`;
  if (abs >= 1e3) return `${(n / 1e3).toFixed(1)}k`;
  return n.toLocaleString("en-GB");
}

export function pct(n: number | null): string {
  if (n === null || n === undefined) return "–";
  const sign = n > 0 ? "+" : "";
  return `${sign}${n.toFixed(1)}%`;
}

// Convert 202605 -> "May 2026".
export function monthName(ym: number): string {
  const s = String(ym);
  const year = Number(s.slice(0, 4));
  const month = Number(s.slice(4)) - 1;
  return new Date(year, month, 1).toLocaleDateString("en-GB", {
    month: "long",
    year: "numeric",
  });
}
