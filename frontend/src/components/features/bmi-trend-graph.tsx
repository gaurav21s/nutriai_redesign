"use client";

import { useMemo, useState } from "react";
import { cn } from "@/lib/cn";

interface BMIGraphPoint {
  date: string;
  weightKg: number;
  heightCm: number;
  bmi: number;
}

type SeriesKey = "weightKg" | "heightCm" | "bmi";

const seriesConfig: Array<{ key: SeriesKey; title: string; color: string; unit: string }> = [
  { key: "weightKg", title: "Weight", color: "#da5d3e", unit: "kg" },
  { key: "heightCm", title: "Height", color: "#1f2937", unit: "cm" },
  { key: "bmi", title: "BMI", color: "#da5d3e", unit: "" },
];

function formatDateLabel(date: string): string {
  const row = new Date(`${date}T00:00:00`);
  return row.toLocaleDateString(undefined, { month: "short", day: "numeric" });
}

function getTickIndices(length: number): number[] {
  if (length <= 6) return [...Array(length).keys()];
  const step = Math.ceil(length / 6);
  const rows = [0];
  for (let i = step; i < length - 1; i += step) rows.push(i);
  rows.push(length - 1);
  return [...new Set(rows)];
}

function buildPlot(values: number[]) {
  const width = 540;
  const height = 180;
  const padX = 48;
  const padY = 26;
  const minY = Math.min(...values);
  const maxY = Math.max(...values);
  const span = Math.max(maxY - minY, 1);

  const points = values.map((value, index) => {
    const x = padX + (index * (width - padX * 2)) / Math.max(values.length - 1, 1);
    const y = height - padY - ((value - minY) / span) * (height - padY * 2);
    return { x, y, value: Number(value.toFixed(1)) };
  });

  return { width, height, padX, padY, points };
}

function SeriesChart({
  points,
  seriesKey,
  title,
  color,
  unit,
}: {
  points: BMIGraphPoint[];
  seriesKey: SeriesKey;
  title: string;
  color: string;
  unit: string;
}) {
  const [hoverIndex, setHoverIndex] = useState<number | null>(null);
  const values = points.map((item) => item[seriesKey]);

  const plot = useMemo(() => buildPlot(values), [values]);
  const polyline = plot.points.map((point) => `${point.x},${point.y}`).join(" ");
  const ticks = getTickIndices(points.length);

  const hoverPoint = hoverIndex != null ? plot.points[hoverIndex] : null;
  const hoverDate = hoverIndex != null ? formatDateLabel(points[hoverIndex].date) : "";

  return (
    <section className="rounded-editorial border border-black/[0.03] bg-white p-6 shadow-soft-glow group transition-all hover:bg-white/80">
      <div className="mb-6 flex items-center justify-between">
        <h4 className="text-[10px] font-bold uppercase tracking-widest text-foreground/40">{title}</h4>
        {hoverPoint ? (
          <p className="text-sm font-display font-semibold text-vibrant animate-reveal">
            {hoverPoint.value}
            {unit ? ` ${unit}` : ""} <span className="text-[10px] text-foreground/20 italic ml-2">• {hoverDate}</span>
          </p>
        ) : null}
      </div>

      <div className="overflow-x-auto overflow-y-hidden custom-scrollbar-minimal">
        <svg
          viewBox={`0 0 ${plot.width} ${plot.height}`}
          className="h-[180px] w-full min-w-[540px]"
          onMouseLeave={() => setHoverIndex(null)}
        >
          <line x1={plot.padX} y1={plot.height - plot.padY} x2={plot.width - plot.padX} y2={plot.height - plot.padY} stroke="currentColor" className="text-black/[0.03]" strokeWidth="1" />
          <line x1={plot.padX} y1={plot.padY} x2={plot.padX} y2={plot.height - plot.padY} stroke="currentColor" className="text-black/[0.03]" strokeWidth="1" />

          <polyline fill="none" stroke={color} strokeWidth="3" strokeLinejoin="round" strokeLinecap="round" points={polyline} className="opacity-80" />

          {plot.points.map((point, index) => (
            <circle
              key={`${title}-${points[index].date}`}
              cx={point.x}
              cy={point.y}
              r={hoverIndex === index ? 6 : 4}
              fill={color}
              className="transition-all duration-300 cursor-pointer"
              opacity={hoverIndex == null || hoverIndex === index ? 1 : 0.2}
              onMouseEnter={() => setHoverIndex(index)}
            />
          ))}

          {hoverPoint && (
            <g className="animate-reveal">
              <line x1={hoverPoint.x} y1={plot.padY} x2={hoverPoint.x} y2={plot.height - plot.padY} stroke={color} strokeWidth="1" strokeDasharray="4 4" opacity="0.4" />
              <circle cx={hoverPoint.x} cy={hoverPoint.y} r="10" fill={color} opacity="0.1" />
            </g>
          )}

          {ticks.map((index) => (
            <text
              key={`${title}-tick-${points[index].date}`}
              x={plot.points[index].x}
              y={plot.height - 6}
              textAnchor="middle"
              className="fill-foreground/20 text-[9px] font-bold uppercase tracking-widest"
            >
              {formatDateLabel(points[index].date)}
            </text>
          ))}
        </svg>
      </div>
    </section>
  );
}

export function BMITrendGraph({ points, onReset, className }: { points: BMIGraphPoint[]; onReset: () => void; className?: string }) {
  if (!points.length) {
    return (
      <section className={cn("rounded-editorial border border-black/[0.03] bg-white/40 p-12 text-center", className)}>
        <div className="opacity-20 italic">
          <p className="text-sm font-medium mb-4">No graph data yet</p>
          <button
            type="button"
            onClick={onReset}
            className="px-6 py-2 rounded-full border border-black/10 text-[10px] font-bold uppercase tracking-widest hover:bg-black/5 transition-all"
          >
            Clear Graph
          </button>
        </div>
      </section>
    );
  }

  return (
    <section className={cn("rounded-editorial border border-black/[0.03] bg-white/40 p-10 shadow-elegant", className)}>
      <div className="flex items-center justify-between gap-6 mb-10 border-b border-black/[0.02] pb-6">
        <div>
          <h3 className="text-[10px] font-bold uppercase tracking-[0.2em] text-vibrant mb-1">Daily Tracking</h3>
          <p className="text-xl font-display font-semibold text-foreground">Weight, Height, BMI</p>
        </div>
        <button
          type="button"
          onClick={onReset}
          className="rounded-full border border-black/[0.05] bg-white px-6 py-2 text-[10px] font-bold uppercase tracking-widest text-foreground/40 hover:text-foreground/60 shadow-soft-glow transition-all active:scale-95"
        >
          Reset Graph
        </button>
      </div>

      <div className="grid gap-6">
        {seriesConfig.map((series) => (
          <SeriesChart
            key={series.key}
            points={points}
            seriesKey={series.key}
            title={series.title}
            color={series.color}
            unit={series.unit}
          />
        ))}
      </div>
    </section>
  );
}
