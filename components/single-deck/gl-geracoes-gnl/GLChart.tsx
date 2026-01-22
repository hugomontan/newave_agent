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

interface GLChartProps {
  data: ChartData;
  title?: string;
  patamar?: string;
}

export function GLChart({ data, title, patamar }: GLChartProps) {
  if (!data || !data.labels || data.labels.length === 0 || !data.datasets || data.datasets.length === 0) {
    return (
      <div className="bg-card border border-border rounded-lg p-4 sm:p-6 w-full">
        <h3 className="text-base sm:text-lg font-semibold mb-4 text-card-foreground">
          {title || `Evolução da Geração - ${patamar || "Patamar"}`}
        </h3>
        <p className="text-sm text-muted-foreground">
          Não foi possível gerar o gráfico. Dados insuficientes.
        </p>
      </div>
    );
  }

  const chartData = data.labels.map((label, index) => {
    const point: Record<string, string | number | null> = {
      data: label,
    };
    
    data.datasets.forEach((dataset) => {
      point[dataset.label] = dataset.data[index] ?? null;
    });
    
    return point;
  });

  let minValue: number | null = null;
  let maxValue: number | null = null;
  
  data.datasets.forEach((dataset) => {
    dataset.data.forEach((value) => {
      if (value !== null && typeof value === 'number' && !isNaN(value) && isFinite(value)) {
        if (minValue === null || value < minValue) {
          minValue = value;
        }
        if (maxValue === null || value > maxValue) {
          maxValue = value;
        }
      }
    });
  });

  const yAxisDomain: [number | string, number | string] = 
    minValue !== null && maxValue !== null && minValue !== maxValue
      ? (() => {
          const range = maxValue - minValue;
          const margin = range * 0.05;
          const minDomain = Math.max(0, minValue - margin);
          const maxDomain = maxValue + margin;
          return [minDomain, maxDomain];
        })()
      : minValue !== null && maxValue !== null && minValue === maxValue
      ? (() => {
          const singleValue = minValue;
          if (singleValue === 0) {
            return [0, 100];
          }
          return [Math.max(0, singleValue * 0.9), singleValue * 1.1];
        })()
      : ['auto', 'auto'];

  // Cores por patamar
  const patamarColors: Record<string, string> = {
    "PESADA": "#ef4444",   // red-500
    "MÉDIA": "#eab308",    // yellow-500
    "LEVE": "#22c55e",     // green-500
  };

  const color = patamar ? patamarColors[patamar] || "#8884d8" : "#8884d8";

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-card border border-border rounded-lg p-4 sm:p-6 w-full"
    >
      <h3 className="text-base sm:text-lg font-semibold mb-4 text-card-foreground">
        {title || `Evolução da Geração - ${patamar || "Patamar"}`}
      </h3>
      <div className="w-full min-w-[600px] overflow-hidden">
        <ResponsiveContainer width="100%" height={400}>
          <LineChart
            data={chartData}
            margin={{
              top: 10,
              right: 110,
              left: -40,
              bottom: 5,
            }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
            <XAxis 
              dataKey="data" 
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
              domain={yAxisDomain}
              allowDataOverflow={false}
              label={{ value: "Geração (MW)", angle: -90, position: "insideLeft", style: { textAnchor: "middle", fill: "#9ca3af" } }}
              tickFormatter={(value) => {
                if (typeof value === 'number' && !isNaN(value) && isFinite(value)) {
                  return value.toLocaleString('pt-BR', { 
                    minimumFractionDigits: 2, 
                    maximumFractionDigits: 2 
                  });
                }
                return String(value);
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
              formatter={(value: number | string) => {
                if (typeof value === 'number' && !isNaN(value) && isFinite(value)) {
                  return `${value.toLocaleString('pt-BR', { 
                    minimumFractionDigits: 2, 
                    maximumFractionDigits: 2 
                  })} MW`;
                }
                return value === null || value === undefined ? "-" : String(value);
              }}
            />
            <Legend 
              wrapperStyle={{ color: "#9ca3af", fontSize: "14px" }}
            />
            {data.datasets.map((dataset, index) => (
              <Line
                key={dataset.label}
                type="linear"
                dataKey={dataset.label}
                stroke={color}
                strokeWidth={2}
                dot={false}
                activeDot={{ r: 4 }}
                connectNulls={false}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>
    </motion.div>
  );
}
