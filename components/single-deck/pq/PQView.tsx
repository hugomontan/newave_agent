"use client";

import React from "react";
import { motion } from "framer-motion";
import { PQTable } from "./PQTable";
import { formatNumber } from "../shared/formatters";
import type { SingleDeckVisualizationData } from "../shared/types";

interface PQViewProps {
  visualizationData: SingleDeckVisualizationData;
}

export function PQView({ visualizationData }: PQViewProps) {
  const { table, filtros, mw_medios } = visualizationData;

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="w-full mt-4 space-y-6"
    >
      {/* Informação de filtros (quando filtrado por tipo ou região) */}
      {(filtros?.tipo || filtros?.regiao) && (
        <div className="bg-card border border-border rounded-lg p-4 sm:p-6">
          <h3 className="text-base sm:text-lg font-semibold text-card-foreground mb-2">
            Filtros Aplicados
          </h3>
          <div className="text-sm text-muted-foreground space-y-1">
            {filtros.tipo && (
              <p>Tipo: {filtros.tipo}</p>
            )}
            {filtros.regiao && (
              <p>Região: {filtros.regiao}</p>
            )}
            {filtros.estagio && (
              <p>Estágio: {filtros.estagio}</p>
            )}
          </div>
        </div>
      )}

      {/* Tabela de gerações das pequenas usinas */}
      {table && table.length > 0 && (
        <PQTable data={table as any} />
      )}

      {/* MW Médio Total (quando houver cálculo de média ponderada) */}
      {mw_medios && mw_medios.length > 0 && (
        <div className="bg-card border border-border rounded-lg p-4 sm:p-6">
          <div>
            <p className="text-sm text-muted-foreground mb-1">MW Médio Total</p>
            {mw_medios.map((mw: any, index: number) => (
              <div key={index} className="mb-2 last:mb-0">
                {mw_medios.length > 1 ? (
                  <p className="text-lg sm:text-xl font-semibold text-card-foreground">
                    {mw.nome || `${mw.tipo} - ${mw.regiao}`}:{" "}
                    <span className="text-2xl sm:text-3xl font-bold">
                      {formatNumber(mw.mw_medio)}
                    </span>{" "}
                    <span className="text-base font-normal text-muted-foreground">MWmed</span>
                  </p>
                ) : (
                  <p className="text-3xl sm:text-4xl font-bold text-card-foreground">
                    {formatNumber(mw.mw_medio)}{" "}
                    <span className="text-lg font-normal text-muted-foreground">MWmed</span>
                  </p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {(!table || table.length === 0) && (!mw_medios || mw_medios.length === 0) && (
        <div className="bg-card border border-border rounded-lg p-4 sm:p-6">
          <p className="text-sm text-muted-foreground">
            Nenhum dado disponível.
          </p>
        </div>
      )}
    </motion.div>
  );
}
