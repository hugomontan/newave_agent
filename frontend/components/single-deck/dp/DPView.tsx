"use client";

import React from "react";
import { motion } from "framer-motion";
import { DPTable } from "./DPTable";
import { formatNumber } from "../shared/formatters";
import type { SingleDeckVisualizationData } from "../shared/types";

interface DPViewProps {
  visualizationData: SingleDeckVisualizationData;
}

export function DPView({ visualizationData }: DPViewProps) {
  const { table, filtros, mw_medios } = visualizationData;

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

      {/* MW Médio Total (quando houver cálculo de carga média ponderada) */}
      {mw_medios && mw_medios.length > 0 && (
        <div className="bg-card border border-border rounded-lg p-4 sm:p-6">
          <div>
            <p className="text-sm text-muted-foreground mb-1">MW Médio Total</p>
            {mw_medios.map((mw: any, index: number) => (
              <div key={index} className="mb-2 last:mb-0">
                {mw_medios.length > 1 ? (
                  <p className="text-lg sm:text-xl font-semibold text-card-foreground">
                    Estágio {mw.estagio}, Submercado {mw.codigo_submercado}:{" "}
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
