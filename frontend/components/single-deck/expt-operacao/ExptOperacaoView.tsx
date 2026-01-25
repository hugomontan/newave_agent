"use client";

import React from "react";
import { motion } from "framer-motion";
import { ExptOperacaoTable } from "./ExptOperacaoTable";
import type { SingleDeckVisualizationData } from "../shared/types";

interface ExptOperacaoViewProps {
  visualizationData: SingleDeckVisualizationData;
}

export function ExptOperacaoView({ visualizationData }: ExptOperacaoViewProps) {
  const { table, tables_by_tipo, filtros, tipos_info, ordem_tipos } = visualizationData;

  if (!table || table.length === 0) {
    return (
      <div className="bg-card border border-border rounded-lg p-4 sm:p-6 mt-4">
        <h3 className="text-base sm:text-lg font-semibold text-card-foreground mb-2">
          Dados de Operação Térmica
        </h3>
        <p className="text-sm text-muted-foreground">Nenhum dado disponível.</p>
      </div>
    );
  }

  // Se houver múltiplos tipos, renderizar tabelas separadas
  const hasMultipleTipos = tables_by_tipo && Object.keys(tables_by_tipo).length > 1;

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="w-full mt-4 space-y-6"
    >
      {/* Tabelas por tipo */}
      {hasMultipleTipos && tables_by_tipo && ordem_tipos ? (
        // Renderizar tabela separada para cada tipo na ordem especificada
        ordem_tipos
          .filter(tipo => tables_by_tipo[tipo] && tables_by_tipo[tipo].length > 0)
          .map((tipo) => {
            const tipoInfo = tipos_info?.[tipo] || { nome: tipo, unidade: '' };
            return (
              <ExptOperacaoTable
                key={tipo}
                data={tables_by_tipo[tipo] as Array<Record<string, any>>}
                tipo={tipo}
                tipoInfo={tipoInfo}
              />
            );
          })
      ) : (
        // Renderizar tabela única
        tables_by_tipo && Object.keys(tables_by_tipo).length === 1 ? (
          Object.entries(tables_by_tipo).map(([tipo, tableData]) => {
            const tipoInfo = tipos_info?.[tipo] || { nome: tipo, unidade: '' };
            return (
              <ExptOperacaoTable
                key={tipo}
                data={tableData as Array<Record<string, any>>}
                tipo={tipo}
                tipoInfo={tipoInfo}
              />
            );
          })
        ) : (
          <div className="bg-card border border-border rounded-lg p-4 sm:p-6">
            <p className="text-sm text-muted-foreground">Dados não disponíveis em formato tabular.</p>
          </div>
        )
      )}
    </motion.div>
  );
}
