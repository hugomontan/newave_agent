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

interface LimitesIntercambioChartProps {
  data: ChartData;
  par?: string;
  sentido?: string;
}

export function LimitesIntercambioChart({ data, par, sentido }: LimitesIntercambioChartProps) {
  // Validar dados
  if (!data || !data.labels || data.labels.length === 0 || !data.datasets || data.datasets.length === 0) {
    return (
      <div className="bg-card border border-border rounded-lg p-4 sm:p-6 w-full">
        <h3 className="text-base sm:text-lg font-semibold mb-4 text-card-foreground">
          {par && sentido ? `${par} - ${sentido}` : "Limites de Intercâmbio"}
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

  // Calcular domain do eixo Y com uma margem de 5%
  const yAxisDomain: [number | string, number | string] = 
    minValue !== null && maxValue !== null && minValue !== maxValue
      ? [
          Math.max(0, minValue - (maxValue - minValue) * 0.05), // Margem de 5% abaixo, mínimo 0
          maxValue + (maxValue - minValue) * 0.05 // Margem de 5% acima
        ]
      : minValue !== null && maxValue !== null && minValue === maxValue
      ? (() => {
          const singleValue = minValue;
          if (singleValue === 0) {
            return [0, 100];
          }
          return [Math.max(0, singleValue * 0.9), singleValue * 1.1];
        })()
      : ['auto', 'auto'];

  // Cores para as linhas
  const colors = ["#8884d8", "#82ca9d", "#ffc658", "#ff7300"];

  // Título dinâmico
  const chartTitle = par && sentido ? `${par} - ${sentido}` : "Limites de Intercâmbio";

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-card border border-border rounded-lg p-4 sm:p-6 w-full"
    >
      <h3 className="text-base sm:text-lg font-semibold mb-4 text-card-foreground">
        {chartTitle}
      </h3>
      <div className="w-full min-w-[600px] overflow-hidden">
        <ResponsiveContainer width="100%" height={400}>
          <LineChart
            data={chartData}
            margin={{
              top: 10,
              right: 110,
              left: 20,
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
              domain={yAxisDomain}
              tickFormatter={(value) => {
                // Formatar valores grandes com separador de milhar, sem decimais quando inteiro
                if (Number.isInteger(value)) {
                  return value.toLocaleString('pt-BR', { minimumFractionDigits: 0, maximumFractionDigits: 0 });
                }
                return value.toLocaleString('pt-BR');
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
                  return formatInteger(value);
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
