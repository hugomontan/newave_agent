"use client";

import React from "react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts";
import { motion } from "framer-motion";
import type { ChartData } from "../shared/types";

interface VolumeInicialComparisonChartProps {
  data: ChartData;
  config?: {
    type?: string;
    title?: string;
    x_axis?: string;
    y_axis?: string;
    tool_name?: string;
  };
}

export function VolumeInicialComparisonChart({ data, config }: VolumeInicialComparisonChartProps) {
  if (!data || !data.labels || data.labels.length === 0 || !data.datasets || data.datasets.length === 0) {
    return null;
  }

  // Converter dados para formato do Recharts
  const chartData = data.labels.map((label, index) => {
    const point: any = { periodo: label };
    data.datasets.forEach((dataset) => {
      point[dataset.label] = dataset.data[index];
    });
    return point;
  });

  const title = config?.title || "Evolução do Volume Inicial";

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-card border border-border rounded-lg p-4 sm:p-6 w-full"
    >
      <h3 className="text-base sm:text-lg font-semibold mb-4 text-card-foreground">
        {title}
      </h3>
      <div className="w-full overflow-hidden" style={{ minWidth: 0 }}>
        <ResponsiveContainer width="100%" height={400}>
          <LineChart
            data={chartData}
            margin={{
              top: 5,
              right: 10,
              left: -40,
              bottom: 5,
            }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
            <XAxis 
              dataKey="periodo" 
              stroke="#9ca3af"
              tick={{ fill: "#9ca3af", fontSize: 14 }}
              angle={-45}
              textAnchor="end"
              height={80}
            />
            <YAxis 
              stroke="#9ca3af"
              tick={{ fill: "#9ca3af", fontSize: 14 }}
              width={100}
              tickFormatter={(value) => {
                if (value === null || value === undefined) return "-";
                return `${value}%`;
              }}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: "#1f2937",
                border: "1px solid #374151",
                borderRadius: "6px",
                color: "#f3f4f6",
                fontSize: "14px",
              }}
              formatter={(value: any) => {
                if (value === null || value === undefined) return "-";
                return `${value}%`;
              }}
            />
            <Legend 
              wrapperStyle={{ color: "#9ca3af", fontSize: "14px" }}
            />
            {data.datasets.map((dataset, index) => {
              const datasetWithColor = dataset as any;
              return (
                <Line
                  key={dataset.label}
                  type="monotone"
                  dataKey={dataset.label}
                  stroke={datasetWithColor.borderColor || `rgb(${59 + index * 50}, 130, 246)`}
                  strokeWidth={2}
                  dot={false}
                  activeDot={false}
                  connectNulls={false}
                />
              );
            })}
          </LineChart>
        </ResponsiveContainer>
      </div>
    </motion.div>
  );
}
