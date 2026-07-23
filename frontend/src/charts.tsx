import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  CartesianGrid,
  Legend,
} from "recharts";
import type { Breakdown, DrugTrendPoint, PrepGroup, TrendPoint } from "./api";
import { gbp, gbpCompact, gbpPrecise, numCompact } from "./format";

const AXIS = { stroke: "#3a4d73", fontSize: 11 };
const GRID = "#20304e";
const BAR_COLORS = [
  "#2f80ed", "#56ccf2", "#27c093", "#f2c14e", "#bb6bd9",
  "#ef6461", "#9b8cff", "#4dd0a7", "#f19066", "#5aa9e6",
];

export type TrendMetric = "nic" | "items" | "cost_per_item";

const METRIC_CFG: Record<
  TrendMetric,
  { label: string; color: string; axis: (v: number) => string; tip: (v: number) => string }
> = {
  nic: { label: "Net ingredient cost", color: "#2f80ed", axis: gbpCompact, tip: gbp },
  items: { label: "Prescription items", color: "#27c093", axis: numCompact, tip: numCompact },
  cost_per_item: {
    label: "Cost per item",
    color: "#f2c14e",
    axis: (v) => `£${v.toFixed(2)}`,
    tip: gbpPrecise,
  },
};

export function TrendChart({ data, metric }: { data: TrendPoint[]; metric: TrendMetric }) {
  const cfg = METRIC_CFG[metric];
  return (
    <ResponsiveContainer width="100%" height={280}>
      <AreaChart data={data} margin={{ top: 8, right: 8, left: 4, bottom: 0 }}>
        <defs>
          <linearGradient id="trendFill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={cfg.color} stopOpacity={0.45} />
            <stop offset="100%" stopColor={cfg.color} stopOpacity={0.02} />
          </linearGradient>
        </defs>
        <CartesianGrid stroke={GRID} vertical={false} />
        <XAxis dataKey="label" tick={AXIS} tickLine={false} axisLine={{ stroke: GRID }} />
        <YAxis tick={AXIS} tickLine={false} axisLine={false} tickFormatter={cfg.axis} width={64} />
        <Tooltip formatter={(v: number) => [cfg.tip(v), cfg.label]} />
        <Area
          type="monotone"
          dataKey={metric}
          name={cfg.label}
          stroke={cfg.color}
          strokeWidth={2}
          fill="url(#trendFill)"
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}

export function DrugTrendChart({ data }: { data: DrugTrendPoint[] }) {
  return (
    <ResponsiveContainer width="100%" height={260}>
      <AreaChart data={data} margin={{ top: 8, right: 8, left: 4, bottom: 0 }}>
        <defs>
          <linearGradient id="drugFill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#9b8cff" stopOpacity={0.45} />
            <stop offset="100%" stopColor="#9b8cff" stopOpacity={0.02} />
          </linearGradient>
        </defs>
        <CartesianGrid stroke={GRID} vertical={false} />
        <XAxis dataKey="label" tick={AXIS} tickLine={false} axisLine={{ stroke: GRID }} />
        <YAxis tick={AXIS} tickLine={false} axisLine={false} tickFormatter={gbpCompact} width={64} />
        <Tooltip formatter={(v: number) => [gbp(v), "Net ingredient cost"]} />
        <Area
          type="monotone"
          dataKey="nic"
          name="Net ingredient cost"
          stroke="#9b8cff"
          strokeWidth={2}
          fill="url(#drugFill)"
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}

export function BreakdownBars({ data }: { data: Breakdown[] }) {
  const rows = [...data].sort((a, b) => a.nic - b.nic); // ascending for horizontal bars
  const height = Math.max(240, rows.length * 26);
  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={rows} layout="vertical" margin={{ top: 4, right: 16, left: 8, bottom: 4 }}>
        <CartesianGrid stroke={GRID} horizontal={false} />
        <XAxis type="number" tick={AXIS} tickLine={false} axisLine={false} tickFormatter={(v) => gbpCompact(v)} />
        <YAxis
          type="category"
          dataKey="name"
          tick={{ ...AXIS, width: 190 }}
          width={200}
          tickLine={false}
          axisLine={false}
        />
        <Tooltip formatter={(v: number) => gbp(v)} cursor={{ fill: "rgba(47,128,237,0.08)" }} />
        <Bar dataKey="nic" radius={[0, 5, 5, 0]}>
          {rows.map((_, i) => (
            <Cell key={i} fill={BAR_COLORS[(rows.length - 1 - i) % BAR_COLORS.length]} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

export function PrepDonut({ data }: { data: PrepGroup[] }) {
  const colors: Record<string, string> = {
    Generic: "#27c093",
    Branded: "#2f80ed",
    "Appliances & devices": "#f2c14e",
    Other: "#8896b3",
  };
  const total = data.reduce((s, d) => s + d.nic, 0);
  return (
    <ResponsiveContainer width="100%" height={260}>
      <PieChart>
        <Pie
          data={data}
          dataKey="nic"
          nameKey="prep_group"
          innerRadius={62}
          outerRadius={100}
          paddingAngle={2}
          stroke="none"
        >
          {data.map((d, i) => (
            <Cell key={i} fill={colors[d.prep_group] || BAR_COLORS[i % BAR_COLORS.length]} />
          ))}
        </Pie>
        <Tooltip
          formatter={(v: number, n: string) => [`${gbp(v)} (${((v / total) * 100).toFixed(1)}%)`, n]}
        />
        <Legend wrapperStyle={{ fontSize: 12 }} />
      </PieChart>
    </ResponsiveContainer>
  );
}

export { numCompact };
