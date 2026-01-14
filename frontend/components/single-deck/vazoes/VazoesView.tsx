"use client";

import React from "react";
import { motion } from "framer-motion";
import { VazoesTable } from "./VazoesTable";
import { VazoesChart } from "./VazoesChart";
import type { SingleDeckVisualizationData } from "../shared/types";

interface VazoesViewProps {
  visualizationData: SingleDeckVisualizationData;
}

export function VazoesView({ visualizationData }: VazoesViewProps) {
  const { table, chart_data, chart_config } = visualizationData;

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="w-full space-y-6 mt-4"
    >
      {table && table.length > 0 && <VazoesTable data={table} />}
      {chart_data && chart_data.labels && chart_data.labels.length > 0 && (
        <VazoesChart data={chart_data} chartConfig={chart_config} />
      )}
    </motion.div>
  );
}
