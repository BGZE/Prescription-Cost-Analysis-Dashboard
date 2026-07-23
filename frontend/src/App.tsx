import { useEffect, useState } from "react";
import {
  api,
  type Breakdown,
  type Drug,
  type Kpi,
  type Meta,
  type Overview,
  type PrepBreakdown,
  type TrendPoint,
} from "./api";
import { BreakdownBars, PrepDonut, TrendChart } from "./charts";
import { gbp, gbpCompact, gbpPrecise, monthName, numCompact, pct } from "./format";

export default function App() {
  const [meta, setMeta] = useState<Meta | null>(null);
  const [month, setMonth] = useState<string>("latest");
  const [error, setError] = useState<string | null>(null);

  const [overview, setOverview] = useState<Overview | null>(null);
  const [trend, setTrend] = useState<TrendPoint[]>([]);
  const [trendMonths, setTrendMonths] = useState<number>(0); // 0 = all months
  const [therapeutic, setTherapeutic] = useState<Breakdown[]>([]);
  const [thLevel, setThLevel] = useState<"chapter" | "section">("chapter");
  const [geo, setGeo] = useState<Breakdown[]>([]);
  const [geoLevel, setGeoLevel] = useState<"region" | "icb">("region");
  const [drugs, setDrugs] = useState<Drug[]>([]);
  const [prep, setPrep] = useState<PrepBreakdown | null>(null);

  // Load metadata once; default the selector to the latest month.
  useEffect(() => {
    api.meta().then((m) => {
      setMeta(m);
      if (m.latest_month) setMonth(String(m.latest_month));
    }).catch((e) => setError(String(e)));
    api.trend().then(setTrend).catch((e) => setError(String(e)));
  }, []);

  // Reload month-scoped data whenever the month changes.
  useEffect(() => {
    if (month === "latest" && !meta) return;
    const m = month;
    Promise.all([
      api.overview(m).then(setOverview),
      api.drugs(m, 15).then(setDrugs),
      api.prepclass(m).then(setPrep),
    ]).catch((e) => setError(String(e)));
  }, [month, meta]);

  useEffect(() => {
    if (!meta) return;
    api.therapeutic(month, thLevel, 15).then(setTherapeutic).catch((e) => setError(String(e)));
  }, [month, thLevel, meta]);

  useEffect(() => {
    if (!meta) return;
    api.geography(month, geoLevel).then(setGeo).catch((e) => setError(String(e)));
  }, [month, geoLevel, meta]);

  if (error) {
    return (
      <div className="center">
        <div className="error">
          <strong>Couldn't load data.</strong>
          <div className="muted" style={{ marginTop: 8 }}>{error}</div>
        </div>
      </div>
    );
  }
  if (!meta || !overview) {
    return <div className="center"><div className="spinner" /></div>;
  }

  const activeYm = overview.year_month;

  return (
    <div className="app">
      <header className="header">
        <div className="brand">
          <div className="logo">NHS</div>
          <div>
            <h1>Prescription Cost Analysis</h1>
            <p>England · community prescribing cost &amp; volume · NHSBSA open data</p>
          </div>
        </div>
        <div className="controls">
          <select
            className="month-select"
            value={month}
            onChange={(e) => setMonth(e.target.value)}
          >
            {[...meta.months].reverse().map((m) => (
              <option key={m.year_month} value={String(m.year_month)}>
                {monthName(m.year_month)}
              </option>
            ))}
          </select>
          <div className="updated">
            {meta.month_count} months loaded
            {meta.last_updated && (
              <><br />updated {new Date(meta.last_updated).toLocaleDateString("en-GB")}</>
            )}
          </div>
        </div>
      </header>

      <section className="kpi-grid">
        <KpiCard label="Net ingredient cost" kpi={overview.nic} fmt={gbpCompact} />
        <KpiCard label="Prescription items" kpi={overview.items} fmt={numCompact} />
        <KpiCard label="Cost per item" kpi={overview.cost_per_item} fmt={(v) => gbpPrecise(v)} invert />
        <KpiCard label="Quantity dispensed" kpi={overview.quantity} fmt={numCompact} />
      </section>

      <div className="grid">
        <div className="panel col-8">
          <div className="panel-head">
            <h2>Monthly spend &amp; cost per item</h2>
            <div className="toggle">
              <button className={trendMonths === 6 ? "active" : ""} onClick={() => setTrendMonths(6)}>6M</button>
              <button className={trendMonths === 12 ? "active" : ""} onClick={() => setTrendMonths(12)}>12M</button>
              <button className={trendMonths === 0 ? "active" : ""} onClick={() => setTrendMonths(0)}>All</button>
            </div>
          </div>
          <TrendChart data={trendMonths > 0 ? trend.slice(-trendMonths) : trend} />
        </div>

        <div className="panel col-4">
          <div className="panel-head">
            <h2>Generic vs branded</h2>
            <span className="sub">{monthName(activeYm)}</span>
          </div>
          {prep && <PrepDonut data={prep.groups} />}
          {prep && (
            <div className="muted" style={{ marginTop: 6 }}>
              Generic prescribing drives most items but a fraction of the cost.
            </div>
          )}
        </div>

        <div className="panel col-6">
          <div className="panel-head">
            <h2>Spend by therapeutic area</h2>
            <div className="toggle">
              <button className={thLevel === "chapter" ? "active" : ""} onClick={() => setThLevel("chapter")}>BNF chapter</button>
              <button className={thLevel === "section" ? "active" : ""} onClick={() => setThLevel("section")}>Section</button>
            </div>
          </div>
          <BreakdownBars data={therapeutic} />
        </div>

        <div className="panel col-6">
          <div className="panel-head">
            <h2>Spend by geography</h2>
            <div className="toggle">
              <button className={geoLevel === "region" ? "active" : ""} onClick={() => setGeoLevel("region")}>Region</button>
              <button className={geoLevel === "icb" ? "active" : ""} onClick={() => setGeoLevel("icb")}>ICB</button>
            </div>
          </div>
          <BreakdownBars data={geo.slice(0, 15)} />
        </div>

        <div className="panel col-12">
          <div className="panel-head">
            <h2>Top drugs by cost</h2>
            <span className="sub">BNF chemical substance · {monthName(activeYm)}</span>
          </div>
          <DrugsTable drugs={drugs} />
        </div>
      </div>

      <footer className="footer">
        Data source:{" "}
        <a href="https://opendata.nhsbsa.net/dataset/prescription-cost-analysis-pca-monthly-data" target="_blank" rel="noreferrer">
          NHSBSA Prescription Cost Analysis (monthly)
        </a>
        . NIC = Net Ingredient Cost (list price before discounts, excluding dispensing fees).
        Figures cover prescriptions dispensed in the community in England.
      </footer>
    </div>
  );
}

function KpiCard({
  label, kpi, fmt, invert,
}: { label: string; kpi: Kpi; fmt: (v: number) => string; invert?: boolean }) {
  return (
    <div className="kpi">
      <div className="label">{label}</div>
      <div className="value">{fmt(kpi.value)}</div>
      <div className="deltas">
        <Delta label="MoM" value={kpi.mom_pct} invert={invert} />
        <Delta label="YoY" value={kpi.yoy_pct} invert={invert} />
      </div>
    </div>
  );
}

function Delta({ label, value, invert }: { label: string; value: number | null; invert?: boolean }) {
  let cls = "flat";
  if (value !== null && value !== 0) {
    const good = invert ? value < 0 : value > 0;
    cls = good ? "up" : "down";
  }
  const arrow = value === null ? "" : value > 0 ? "▲" : value < 0 ? "▼" : "■";
  return (
    <span className={`delta ${cls}`}>
      {arrow} {pct(value)} <span className="tag">{label}</span>
    </span>
  );
}

function DrugsTable({ drugs }: { drugs: Drug[] }) {
  return (
    <div style={{ overflowX: "auto" }}>
      <table className="table">
        <thead>
          <tr>
            <th className="rank">#</th>
            <th>Chemical substance</th>
            <th>Therapeutic area</th>
            <th className="num">Cost (NIC)</th>
            <th className="num">Items</th>
            <th className="num">Cost / item</th>
          </tr>
        </thead>
        <tbody>
          {drugs.map((d, i) => (
            <tr key={d.code}>
              <td className="rank">{i + 1}</td>
              <td>{d.name}</td>
              <td><span className="chip">{d.chapter}</span></td>
              <td className="num">{gbp(d.nic)}</td>
              <td className="num">{numCompact(d.items)}</td>
              <td className="num">{gbpPrecise(d.cost_per_item)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
