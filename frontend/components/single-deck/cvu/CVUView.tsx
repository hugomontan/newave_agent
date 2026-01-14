"use client";

import React from "react";
import { motion } from "framer-motion";
import { CVUTable } from "./CVUTable";
import { CVUChart } from "./CVUChart";
import type { SingleDeckVisualizationData } from "../shared/types";

interface CVUViewProps {
  visualizationData: SingleDeckVisualizationData;
}

export function CVUView({ visualizationData }: CVUViewProps) {
  const { table, chart_data, chart_config } = visualizationData;

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="w-full space-y-6 mt-4"
    >
      {table && table.length > 0 && (
        <CVUTable data={table} />
      )}

      {chart_data && chart_data.labels && chart_data.labels.length > 0 && (
        <CVUChart data={chart_data} title={chart_config?.title} />
      )}
    </motion.div>
  );
}
