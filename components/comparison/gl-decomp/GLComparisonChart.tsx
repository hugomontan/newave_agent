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

interface GLComparisonChartProps {
  data: ChartData;
  config?: {
    type?: string;
    title?: string;
    x_axis?: string;
    y_axis?: string;
    tool_name?: string;
  };
  patamar?: string;
  patamarNumero?: number;
}

export function GLComparisonChart({ 
  data, 
  config,
  patamar,
  patamarNumero
}: GLComparisonChartProps) {
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

  // Definir espaçamento dinâmico entre ticks do eixo X
  const maxTicks = 10; // número máximo aproximado de labels visíveis
  const step = Math.max(1, Math.ceil(chartData.length / maxTicks));

  // Título do gráfico
  const chartTitle = config?.title || 
    (patamarNumero ? `Evolução da Geração - Patamar ${patamarNumero} (${patamar || ""})` : 
     "Evolução da Geração GNL");

  return (
    <div className="bg-card border border-border rounded-lg p-4 sm:p-6">
      <h4 className="text-base sm:text-lg font-semibold text-card-foreground mb-4">
        {chartTitle}
      </h4>
      <div className="w-full h-[400px]">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 60 }}>
            <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
            <XAxis 
              dataKey="data" 
              className="text-xs"
              tick={{ fill: "currentColor", fontSize: 11 }}
              angle={-45}
              textAnchor="end"
              height={80}
              tickMargin={10}
              // Mostrar apenas algumas labels para evitar poluição visual
              tickFormatter={(value: string, index: number) =>
                index % step === 0 ? value : ""
              }
            />
            <YAxis 
              className="text-xs"
              tick={{ fill: "currentColor" }}
              label={{ 
                value: config?.y_axis || "Geração Total (MW)", 
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
            {data.datasets.map((dataset, index) => {
              // Extrair cor do dataset se disponível
              const strokeColor = (dataset as any).borderColor || 
                `hsl(${index * 60}, 70%, 50%)`;
              
              return (
                <Line
                  key={dataset.label}
                  type="monotone"
                  dataKey={dataset.label}
                  stroke={strokeColor}
                  strokeWidth={2}
                  dot={{ r: 4 }}
                  activeDot={{ r: 6 }}
                  connectNulls={false}
                />
              );
            })}
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
