import {
  Area,
  Bar,
  BarChart,
  Cell,
  Line,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  CartesianGrid,
  Legend,
  ComposedChart,
} from "recharts";
import type { Breakdown, PrepGroup, TrendPoint } from "./api";
import { gbp, gbpCompact, gbpPrecise, numCompact } from "./format";

const AXIS = { stroke: "#3a4d73", fontSize: 11 };
const GRID = "#20304e";
const BAR_COLORS = [
  "#2f80ed", "#56ccf2", "#27c093", "#f2c14e", "#bb6bd9",
  "#ef6461", "#9b8cff", "#4dd0a7", "#f19066", "#5aa9e6",
];

export function TrendChart({ data }: { data: TrendPoint[] }) {
  return (
    <ResponsiveContainer width="100%" height={280}>
      <ComposedChart data={data} margin={{ top: 8, right: 8, left: 4, bottom: 0 }}>
        <defs>
          <linearGradient id="nicFill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#2f80ed" stopOpacity={0.45} />
            <stop offset="100%" stopColor="#2f80ed" stopOpacity={0.02} />
          </linearGradient>
        </defs>
        <CartesianGrid stroke={GRID} vertical={false} />
        <XAxis dataKey="label" tick={AXIS} tickLine={false} axisLine={{ stroke: GRID }} />
        <YAxis
          yAxisId="l"
          tick={AXIS}
          tickLine={false}
          axisLine={false}
          tickFormatter={(v) => gbpCompact(v)}
        />
        <YAxis
          yAxisId="r"
          orientation="right"
          tick={AXIS}
          tickLine={false}
          axisLine={false}
          tickFormatter={(v) => `£${v.toFixed(1)}`}
        />
        <Tooltip
          formatter={(v: number, name: string) =>
            name === "Cost / item" ? gbpPrecise(v) : gbp(v)
          }
        />
        <Legend wrapperStyle={{ fontSize: 12 }} />
        <Area
          yAxisId="l"
          type="monotone"
          dataKey="nic"
          name="Net ingredient cost"
          stroke="#2f80ed"
          strokeWidth={2}
          fill="url(#nicFill)"
        />
        <Line
          yAxisId="r"
          type="monotone"
          dataKey="cost_per_item"
          name="Cost / item"
          stroke="#f2c14e"
          strokeWidth={2}
          dot={false}
        />
      </ComposedChart>
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
