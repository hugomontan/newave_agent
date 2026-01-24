"use client";

import React from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import type { ChartData } from "../shared/types";

interface CVUComparisonChartProps {
  data: ChartData;
  config?: {
    type?: string;
    title?: string;
    x_axis?: string;
    y_axis?: string;
  };
}

export function CVUComparisonChart({ 
  data, 
  config 
}: CVUComparisonChartProps) {
  if (!data || !data.labels || data.labels.length === 0 || !data.datasets || data.datasets.length === 0) {
    return null;
  }

  // Transformar dados para formato Recharts
  const chartData = data.labels.map((label, index) => {
    const point: Record<string, any> = {
      data: label,
    };
    
    data.datasets.forEach((dataset) => {
      point[dataset.label] = dataset.data[index];
    });
    
    return point;
  });

  // Cores das séries (definidas no formatter)
  // CVU Pesada: rgb(239, 68, 68) - red-500
  // CVU Média: rgb(234, 179, 8) - yellow-500
  // CVU Leve: rgb(34, 197, 94) - green-500
  const colors = [
    "rgb(239, 68, 68)",  // red-500 - Pesada
    "rgb(234, 179, 8)",  // yellow-500 - Média
    "rgb(34, 197, 94)",  // green-500 - Leve
  ];

  return (
    <div className="bg-card border border-border rounded-lg p-4 sm:p-6">
      <h4 className="text-base sm:text-lg font-semibold text-card-foreground mb-4">
        {config?.title || "Evolução do CVU"}
      </h4>
      <div className="w-full h-[400px]">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
            <XAxis 
              dataKey="data" 
              className="text-xs"
              tick={{ fill: "currentColor" }}
            />
            <YAxis 
              className="text-xs"
              tick={{ fill: "currentColor" }}
              label={{ 
                value: config?.y_axis || "CVU (R$/MWh)", 
                angle: -90, 
                position: "insideLeft",
                style: { textAnchor: "middle", fill: "currentColor" }
              }}
            />
            <Tooltip 
              contentStyle={{ 
                backgroundColor: "hsl(var(--card))",
                border: "1px solid hsl(var(--border))",
                borderRadius: "0.5rem"
              }}
            />
            <Legend />
            {data.datasets.map((dataset, index) => (
              <Line
                key={dataset.label}
                type="monotone"
                dataKey={dataset.label}
                stroke={(dataset as any).borderColor || colors[index % colors.length]}
                strokeWidth={2}
                dot={false}
                activeDot={false}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
