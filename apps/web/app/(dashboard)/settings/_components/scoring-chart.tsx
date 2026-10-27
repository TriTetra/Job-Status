"use client";

import { PieChart, Pie, Cell, ResponsiveContainer, Legend } from "recharts";

interface ScoringChartProps {
  chartData: Array<{
    name: string;
    value: number;
    color: string;
  }>;
}

export default function ScoringChart({ chartData }: ScoringChartProps) {
  return (
    <ResponsiveContainer width="100%" height="100%">
      <PieChart>
        <Pie
          data={chartData}
          cx="50%"
          cy="50%"
          innerRadius={60}
          outerRadius={100}
          paddingAngle={2}
          dataKey="value"
          animationDuration={400}
        >
          {chartData.map((entry, index) => (
            <Cell 
              key={`cell-${index}`} 
              fill={entry.color} 
              stroke="var(--surface)"
              strokeWidth={2}
              className="focus:outline-none"
            />
          ))}
        </Pie>
        <Legend
          verticalAlign="bottom"
          height={36}
          formatter={(value) => (
            <span className="text-xs pl-1" style={{ color: "var(--text-secondary)" }}>
              {value}
            </span>
          )}
        />
      </PieChart>
    </ResponsiveContainer>
  );
}
