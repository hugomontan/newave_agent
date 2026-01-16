"use client";

import React from "react";
import { motion } from "framer-motion";
import { DPTable } from "./DPTable";
import type { SingleDeckVisualizationData } from "../shared/types";

interface DPViewProps {
  visualizationData: SingleDeckVisualizationData;
}

export function DPView({ visualizationData }: DPViewProps) {
  const { table, filtros } = visualizationData;

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="w-full mt-4 space-y-6"
    >
      {/* Informação de filtros (quando filtrado por submercado ou estágio) */}
      {(filtros?.submercado || filtros?.estagio) && (
        <div className="bg-card border border-border rounded-lg p-4 sm:p-6">
          <h3 className="text-base sm:text-lg font-semibold text-card-foreground mb-2">
            Filtros Aplicados
          </h3>
          <div className="text-sm text-muted-foreground space-y-1">
            {filtros.submercado && (
              <p>Submercado: {filtros.submercado}</p>
            )}
            {filtros.estagio && (
              <p>Estágio: {filtros.estagio}</p>
            )}
            {filtros.numero_patamares && (
              <p>Número de Patamares: {filtros.numero_patamares}</p>
            )}
          </div>
        </div>
      )}

      {/* Tabela de carga dos subsistemas */}
      {table && table.length > 0 && (
        <DPTable data={table as any} />
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
