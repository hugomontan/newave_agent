"use client";

import React from "react";
import { motion } from "framer-motion";
import { UHTable } from "./UHTable";
import type { SingleDeckVisualizationData } from "../shared/types";

interface UHViewProps {
  visualizationData: SingleDeckVisualizationData;
}

export function UHView({ visualizationData }: UHViewProps) {
  const { table, filtros } = visualizationData;

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="w-full mt-4 space-y-6"
    >
      {/* Informação da usina (quando filtrado por usina específica) */}
      {filtros?.usina_especifica && filtros?.nome_usina && (
        <div className="bg-card border border-border rounded-lg p-4 sm:p-6">
          <h3 className="text-base sm:text-lg font-semibold text-card-foreground mb-2">
            {filtros.nome_usina}
          </h3>
          <p className="text-sm text-muted-foreground">
            Código: {filtros.usina_especifica}
          </p>
        </div>
      )}

      {/* Tabela de usinas */}
      {table && table.length > 0 && (
        <UHTable data={table as any} />
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
