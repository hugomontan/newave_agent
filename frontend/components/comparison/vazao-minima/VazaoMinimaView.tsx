"use client";

import React from "react";
import { motion } from "framer-motion";
import { VazaoMinimaGroupedTable } from "./VazaoMinimaGroupedTable";
import type { ComparisonData, TableRow, Difference } from "../shared/types";

// Configuração de tamanhos das mensagens (pode ser ajustado para testar)
const MESSAGE_SIZES = {
  errorTitle: "text-base",      // Tamanho do título da mensagem de erro (text-xs, text-sm, text-base, text-lg, text-xl)
  errorText: "text-sm",          // Tamanho do texto da mensagem de erro (text-xs, text-sm, text-base, text-lg)
  emptyMessage: "text-base",     // Tamanho da mensagem quando não há dados (text-xs, text-sm, text-base, text-lg)
} as const;

interface VazaoMinimaViewProps {
  comparison: ComparisonData;
}

export function VazaoMinimaView({ comparison }: VazaoMinimaViewProps) {
  const { deck_1, deck_2, comparison_table } = comparison;

  // Função para mapear row para formato de differences
  const mapRowToDifference = (row: TableRow): Difference => {
    const periodValue = row.period !== undefined ? String(row.period) :
                       (row.data !== undefined ? String(row.data) : "");
    
    const deck1Value = row.deck_1 ?? row.deck_1_value ?? null;
    const deck2Value = row.deck_2 ?? row.deck_2_value ?? null;
    
    // Usar tipo_vazao do row se disponível, senão usar classe, senão fallback para VAZMIN
    const tipoVazao = (row.tipo_vazao as string) || (row.classe as string) || "VAZMIN";
    
    return {
      field: tipoVazao,
      period: periodValue,
      periodo_coluna: row.periodo_coluna ? String(row.periodo_coluna) : undefined,
      deck_1_value: deck1Value !== null && deck1Value !== undefined ? Number(deck1Value) : 0,
      deck_2_value: deck2Value !== null && deck2Value !== undefined ? Number(deck2Value) : 0,
      difference: row.diferenca ?? row.difference ?? null,
      difference_percent: row.diferenca_percent ?? row.difference_percent ?? null,
      is_inclusao_ou_exclusao: row.is_inclusao_ou_exclusao ?? false,
    };
  };

  // Agrupar por tipo_vazao primeiro, depois por tipo_mudanca
  const groupedByTipoVazao = React.useMemo(() => {
    if (!comparison_table || comparison_table.length === 0) return null;
    if (!comparison_table[0]?.tipo_mudanca_key) return null;
    
    // Estrutura: {tipo_vazao: {tipo_mudanca: {label, rows}}}
    const grouped: Record<string, Record<string, { tipo: string; label: string; rows: TableRow[] }>> = {
      VAZMIN: {},
      VAZMINT: {}
    };
    
    comparison_table.forEach((row) => {
      const tipoVazao = (row.tipo_vazao as string) || (row.classe as string) || "VAZMIN";
      const key = row.tipo_mudanca_key as string;
      
      // Extrair tipo_mudanca da chave composta (formato: "VAZMIN-aumento" ou "VAZMINT-queda")
      let tipoMudanca = "";
      if (key && key.includes("-")) {
        tipoMudanca = key.split("-")[1] || "";
      } else {
        tipoMudanca = (row.tipo_mudanca as string) || "";
      }
      
      // Garantir que tipoVazao seja VAZMIN ou VAZMINT
      const tipoVazaoNormalized = tipoVazao === "VAZMINT" ? "VAZMINT" : "VAZMIN";
      
      if (!grouped[tipoVazaoNormalized][tipoMudanca]) {
        grouped[tipoVazaoNormalized][tipoMudanca] = {
          tipo: tipoMudanca,
          label: (row.tipo_mudanca_label as string) || tipoMudanca || "",
          rows: []
        };
      }
      grouped[tipoVazaoNormalized][tipoMudanca].rows.push(row);
    });
    
    // Remover tipos vazios
    Object.keys(grouped).forEach(tipoVazao => {
      if (Object.keys(grouped[tipoVazao]).length === 0) {
        delete grouped[tipoVazao];
      }
    });
    
    return Object.keys(grouped).length > 0 ? grouped : null;
  }, [comparison_table]);

  // Determinar label da primeira coluna
  const firstColumnLabel = React.useMemo(() => {
    if (comparison_table && comparison_table.length > 0) {
      const firstRow = comparison_table[0];
      if (firstRow.classe === "VOLUME_INICIAL") {
        return "Usina";
      }
      const hasAnoField = comparison_table.some(row => {
        const anoValue = row.ano;
        return anoValue !== undefined && anoValue !== null && anoValue !== '';
      });
      if (hasAnoField) {
        return "Ano";
      }
    }
    return "Usina";
  }, [comparison_table]);

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="w-full space-y-6 mt-4"
    >
      {groupedByTipoVazao ? (
        // Renderizar seções separadas por tipo_vazao (VAZMIN e VAZMINT)
        (["VAZMIN", "VAZMINT"] as const).map((tipoVazao) => {
          const gruposPorTipoVazao = groupedByTipoVazao[tipoVazao];
          if (!gruposPorTipoVazao || Object.keys(gruposPorTipoVazao).length === 0) {
            return null;
          }
          
          return (
            <div key={tipoVazao} className="space-y-4">
              {/* Título principal da seção (VAZMIN ou VAZMINT) */}
              <h3 className="text-xl font-bold text-card-foreground border-b border-border pb-2">
                {tipoVazao === "VAZMINT" ? "VAZMINT (Vazão Mínima com Período)" : "VAZMIN (Vazão Mínima sem Período)"}
              </h3>
              
              {/* Renderizar subseções por tipo de mudança dentro deste tipo_vazao */}
              {Object.entries(gruposPorTipoVazao).map(([tipoMudanca, group]) => {
                const mappedRows = group.rows.map(mapRowToDifference);
                return (
                  <div key={`${tipoVazao}-${tipoMudanca}`} className="space-y-2 ml-4">
                    <h4 className="text-lg font-semibold text-card-foreground">
                      {group.label}
                    </h4>
                    <VazaoMinimaGroupedTable 
                      differences={mappedRows}
                      deck1Name={deck_1.name}
                      deck2Name={deck_2.name}
                      firstColumnLabel={firstColumnLabel}
                    />
                  </div>
                );
              })}
            </div>
          );
        })
      ) : comparison_table && comparison_table.length > 0 ? (
        // Fallback: renderizar tabela única se não houver agrupamento
        <VazaoMinimaGroupedTable 
          differences={comparison_table.map(mapRowToDifference)}
          deck1Name={deck_1.name}
          deck2Name={deck_2.name}
          firstColumnLabel={firstColumnLabel}
        />
      ) : null}

      {/* Mensagem de erro se algum deck falhou */}
      {(!deck_1.success || !deck_2.success) && (
        <div className="bg-destructive/10 border border-destructive/30 rounded-lg p-4">
          <h3 className={`${MESSAGE_SIZES.errorTitle} font-semibold text-destructive mb-2`}>
            Erros na comparação:
          </h3>
          {!deck_1.success && (
            <p className={`${MESSAGE_SIZES.errorText} text-destructive/80`}>
              {deck_1.name}: {deck_1.error || "Erro desconhecido"}
            </p>
          )}
          {!deck_2.success && (
            <p className={`${MESSAGE_SIZES.errorText} text-destructive/80`}>
              {deck_2.name}: {deck_2.error || "Erro desconhecido"}
            </p>
          )}
        </div>
      )}
    </motion.div>
  );
}
