"use client";

import React from "react";
import { motion } from "framer-motion";
import { UHTable } from "./UHTable";
import { VolumeInicialView } from "../volume-inicial/VolumeInicialView";
import type { SingleDeckVisualizationData } from "../shared/types";

interface UHViewProps {
  visualizationData: SingleDeckVisualizationData;
}

export function UHView({ visualizationData }: UHViewProps) {
  const { table, filtros } = visualizationData;

  // Detectar se é volume inicial: verificar se a tabela tem apenas as 4 colunas específicas
  const isVolumeInicial = React.useMemo(() => {
    if (!table || table.length === 0) return false;
    
    const firstRow = table[0] as any;
    const columns = Object.keys(firstRow);
    
    // Volume inicial tem exatamente: usina, codigo, data, volume_inicial
    const expectedColumns = ['usina', 'codigo', 'data', 'volume_inicial'];
    const hasAllExpected = expectedColumns.every(col => columns.includes(col));
    const hasOnlyExpected = columns.length === expectedColumns.length;
    
    return hasAllExpected && hasOnlyExpected;
  }, [table]);

  // Se for volume inicial, usar componente específico
  if (isVolumeInicial) {
    return <VolumeInicialView visualizationData={visualizationData} />;
  }

  // Caso contrário, usar formatação genérica do bloco UH
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
