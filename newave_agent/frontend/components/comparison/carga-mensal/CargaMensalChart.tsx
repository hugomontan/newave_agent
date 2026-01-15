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

interface CargaMensalChartProps {
  data: ChartData;
}

export function CargaMensalChart({ data }: CargaMensalChartProps) {
  // Validar dados
  if (!data || !data.labels || data.labels.length === 0 || !data.datasets || data.datasets.length === 0) {
    return (
      <div className="bg-card border border-border rounded-lg p-4 sm:p-6 w-full">
        <h3 className="text-base sm:text-lg font-semibold mb-4 text-card-foreground">
          Evolução da Carga
        </h3>
        <p className="text-sm text-muted-foreground">
          Não foi possível gerar o gráfico. Dados insuficientes.
        </p>
      </div>
    );
  }

  // Transformar dados para formato do Recharts
  const chartData = data.labels.map((label, index) => {
    const point: Record<string, string | number | null> = {
      periodo: label,
    };
    
    data.datasets.forEach((dataset) => {
      point[dataset.label] = dataset.data[index] ?? null;
    });
    
    return point;
  });

  // Calcular min e max dos dados para ajustar o eixo Y automaticamente
  let minValue: number | null = null;
  let maxValue: number | null = null;
  
  data.datasets.forEach((dataset) => {
    dataset.data.forEach((value) => {
      if (value !== null && typeof value === 'number') {
        if (minValue === null || value < minValue) {
          minValue = value;
        }
        if (maxValue === null || value > maxValue) {
          maxValue = value;
        }
      }
    });
  });

  // Calcular domain do eixo Y com uma margem de 5%
  const yAxisDomain: [number | string, number | string] = 
    minValue !== null && maxValue !== null
      ? [
          Math.max(0, minValue - (maxValue - minValue) * 0.05), // Margem de 5% abaixo, mínimo 0
          maxValue + (maxValue - minValue) * 0.05 // Margem de 5% acima
        ]
      : ['auto', 'auto'];

  // Cores para as linhas
  const colors = ["#8884d8", "#82ca9d", "#ffc658", "#ff7300"];

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-card border border-border rounded-lg p-4 sm:p-6 w-full"
    >
      <h3 className="text-base sm:text-lg font-semibold mb-4 text-card-foreground">
        Evolução da Carga
      </h3>
      <div className="w-full min-w-[600px] overflow-hidden">
        <ResponsiveContainer width="100%" height={400}>
          <LineChart
            data={chartData}
            margin={{
              top: 5,
              right: 100,
              left: -70,
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
              width={120}
              domain={yAxisDomain}
              tickFormatter={(value) => {
                // Formatar valores de carga sempre como inteiros (sem decimais)
                const intValue = Math.round(Number(value));
                return intValue.toLocaleString('pt-BR', { 
                  minimumFractionDigits: 0, 
                  maximumFractionDigits: 0 
                });
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
                // Formatar valores no tooltip como inteiros
                if (value === null || value === undefined) return "-";
                const numValue = typeof value === 'string' ? parseFloat(value) : value;
                if (isNaN(numValue)) return "-";
                const intValue = Math.round(numValue);
                return intValue.toLocaleString('pt-BR', { 
                  minimumFractionDigits: 0, 
                  maximumFractionDigits: 0 
                });
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