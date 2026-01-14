"use client";

import React from "react";
import { motion } from "framer-motion";
import { DsvaguaTable } from "./DsvaguaTable";
import { VazoesChart } from "../vazoes/VazoesChart";
import type { SingleDeckVisualizationData } from "../shared/types";

interface DsvaguaViewProps {
  visualizationData: SingleDeckVisualizationData;
}

export function DsvaguaView({ visualizationData }: DsvaguaViewProps) {
  const { table, chart_data, chart_config } = visualizationData;

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="w-full space-y-6 mt-4"
    >
      {table && table.length > 0 && <DsvaguaTable data={table} />}
      {chart_data && chart_data.labels && chart_data.labels.length > 0 && (
        <VazoesChart data={chart_data} chartConfig={chart_config} />
      )}
    </motion.div>
  );
}
