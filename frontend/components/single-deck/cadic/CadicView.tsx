"use client";

import React from "react";
import { motion } from "framer-motion";
import { CadicTable } from "./CadicTable";
import { CargaMensalChart } from "../carga-mensal/CargaMensalChart";
import type { SingleDeckVisualizationData } from "../shared/types";

interface CadicViewProps {
  visualizationData: SingleDeckVisualizationData;
}

export function CadicView({ visualizationData }: CadicViewProps) {
  const { table, chart_data, chart_config } = visualizationData;

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="w-full space-y-6 mt-4"
    >
      {table && table.length > 0 && <CadicTable data={table} />}
      {chart_data && chart_data.labels && chart_data.labels.length > 0 && (
        <CargaMensalChart data={chart_data} title={chart_config?.title} />
      )}
    </motion.div>
  );
}
