"use client";

import React from "react";
import { motion } from "framer-motion";
import { RestricaoVazaoHQTable } from "./RestricaoVazaoHQTable";
import type { SingleDeckVisualizationData } from "../shared/types";

interface RestricaoVazaoHQViewProps {
  visualizationData: SingleDeckVisualizationData;
}

export function RestricaoVazaoHQView({ visualizationData }: RestricaoVazaoHQViewProps) {
  const { table } = visualizationData;

  if (!table || table.length === 0) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full space-y-6 mt-4"
      >
        <p className="text-sm text-muted-foreground">
          Nenhuma restrição de vazão encontrada.
        </p>
      </motion.div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="w-full space-y-6 mt-4"
    >
      <RestricaoVazaoHQTable data={table} />
    </motion.div>
  );
}
