"use client";

import React from "react";
import { motion } from "framer-motion";
import { VolumeInicialTable } from "./VolumeInicialTable";
import type { SingleDeckVisualizationData } from "../shared/types";

interface VolumeInicialViewProps {
  visualizationData: SingleDeckVisualizationData;
}

export function VolumeInicialView({ visualizationData }: VolumeInicialViewProps) {
  const { table } = visualizationData;

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="w-full mt-4 space-y-6"
    >
      {/* Tabela de volume inicial */}
      {table && table.length > 0 && (
        <VolumeInicialTable data={table as any} />
      )}

      {(!table || table.length === 0) && (
        <div className="bg-card border border-border rounded-lg p-4 sm:p-6">
          <p className="text-sm text-muted-foreground">
            Nenhum dado disponível.
          </p>
        </div>
      )}
    </motion.div>
  );
}
