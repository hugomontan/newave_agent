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
import { motion } from "framer-motion";
import type { ChartData } from "../shared/types";
import { formatInteger } from "../shared/formatters";

interface CargaMensalChartProps {
  data: ChartData;
  title?: string;
}

export function CargaMensalChart({ data, title }: CargaMensalChartProps) {
  if (!data || !data.labels || data.labels.length === 0 || !data.datasets || data.datasets.length === 0) {
    return (
      <div className="bg-card border border-border rounded-lg p-4 sm:p-6 w-full">
        <h3 className="text-base sm:text-lg font-semibold mb-4 text-card-foreground">
          Carga Mensal por Submercado
        </h3>
        <p className="text-sm text-muted-foreground">Não foi possível gerar o gráfico.</p>
      </div>
    );
  }

  const chartData = data.labels.map((label, index) => {
    const point: Record<string, string | number | null> = { periodo: label };
    data.datasets.forEach((dataset) => {
      point[dataset.label] = dataset.data[index] ?? null;
    });
    return point;
  });

  // Calcular valores mínimo e máximo para ajustar o eixo Y
  const allValues: number[] = [];
  chartData.forEach((point) => {
    data.datasets.forEach((dataset) => {
      const value = point[dataset.label];
      if (typeof value === 'number' && !isNaN(value)) {
        allValues.push(value);
      }
    });
  });

  const minValue = allValues.length > 0 ? Math.min(...allValues) : 0;
  const maxValue = allValues.length > 0 ? Math.max(...allValues) : 100;
  
  // Ajustar o domínio do eixo Y com uma margem de 5%
  const margin = (maxValue - minValue) * 0.05;
  const yDomain: [number, number] = [
    Math.max(0, Math.floor(minValue - margin)),
    Math.ceil(maxValue + margin)
  ];

  const colors = ["#8884d8", "#82ca9d", "#ffc658", "#ff7300", "#00ff00", "#ff00ff"];

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-card border border-border rounded-lg p-4 sm:p-6 w-full"
    >
      <h3 className="text-base sm:text-lg font-semibold mb-4 text-card-foreground">
        {title || "Carga Mensal por Submercado"}
      </h3>
      <div className="w-full min-w-[600px] overflow-hidden">
        <ResponsiveContainer width="100%" height={400}>
          <LineChart data={chartData} margin={{ top: 10, right: 110, left: 20, bottom: 5 }}>
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
              width={80}
              domain={yDomain}
              tickFormatter={(value) => formatInteger(value)}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: "#1f2937",
                border: "1px solid #374151",
                borderRadius: "6px",
                color: "#f3f4f6",
                fontSize: "14px",
              }}
              formatter={(value: number | string) => formatInteger(value as number)}
            />
            <Legend wrapperStyle={{ color: "#9ca3af", fontSize: "14px" }} />
            {data.datasets.map((dataset, index) => (
              <Line
                key={dataset.label}
                type="linear"
                dataKey={dataset.label}
                stroke={colors[index % colors.length]}
                strokeWidth={2}
                dot={false}
                activeDot={false}
                connectNulls={false}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>
    </motion.div>
  );
}
