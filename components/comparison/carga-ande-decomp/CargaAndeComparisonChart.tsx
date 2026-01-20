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

interface CargaAndeComparisonChartProps {
  data: ChartData;
  config?: {
    type?: string;
    title?: string;
    x_axis?: string;
    y_axis?: string;
  };
}

export function CargaAndeComparisonChart({ 
  data, 
  config 
}: CargaAndeComparisonChartProps) {
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
  const maxTicks = 10;
  const step = Math.max(1, Math.ceil(chartData.length / maxTicks));

  return (
    <div className="bg-card border border-border rounded-lg p-4 sm:p-6">
      <h4 className="text-base sm:text-lg font-semibold text-card-foreground mb-4">
        {config?.title || "Evolução da Carga ANDE"}
      </h4>
      <div className="w-full h-[400px]">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 60 }}>
            <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
            <XAxis 
              dataKey="data" 
              angle={-45}
              textAnchor="end"
              height={80}
              interval={step - 1}
              tick={{ fill: 'currentColor', fontSize: 12 }}
              className="text-muted-foreground"
            />
            <YAxis 
              tick={{ fill: 'currentColor', fontSize: 12 }}
              className="text-muted-foreground"
              label={{ 
                value: config?.y_axis || "MWmed", 
                angle: -90, 
                position: 'insideLeft',
                style: { textAnchor: 'middle', fill: 'currentColor' }
              }}
            />
            <Tooltip 
              contentStyle={{ 
                backgroundColor: 'hsl(var(--card))',
                border: '1px solid hsl(var(--border))',
                borderRadius: '6px',
                color: 'hsl(var(--card-foreground))'
              }}
              formatter={(value: any) => {
                if (typeof value === 'number') {
                  return `${value.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} MW`;
                }
                return value;
              }}
            />
            <Legend 
              wrapperStyle={{ paddingTop: '20px' }}
              iconType="line"
            />
            {data.datasets.map((dataset, index) => (
              <Line
                key={index}
                type="monotone"
                dataKey={dataset.label}
                stroke={dataset.borderColor || "rgb(59, 130, 246)"}
                strokeWidth={2}
                dot={false}
                activeDot={false}
                fill={dataset.backgroundColor || "rgba(59, 130, 246, 0.1)"}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
