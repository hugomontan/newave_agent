"use client";

import React from "react";
import { motion } from "framer-motion";
import { CadastroHidrTable } from "../cadastro-hidr/CadastroHidrTable";
import type { SingleDeckVisualizationData } from "../shared/types";

interface ConfhdViewProps {
  visualizationData: SingleDeckVisualizationData;
}

export function ConfhdView({ visualizationData }: ConfhdViewProps) {
  const { table } = visualizationData;

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="w-full mt-4"
    >
      {table && table.length > 0 && <CadastroHidrTable data={table} />}
    </motion.div>
  );
}
