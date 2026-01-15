"use client";

import React from "react";
import { motion } from "framer-motion";
import { GTMINGroupedTable } from "./GTMINGroupedTable";
import { GTMINMatrixTable } from "./GTMINMatrixTable";
import type { ComparisonData, TableRow, Difference } from "../shared/types";
import { getDeckNames } from "../shared/types";

// Configuração de tamanhos das mensagens (pode ser ajustado para testar)
const MESSAGE_SIZES = {
  errorTitle: "text-base",      // Tamanho do título da mensagem de erro (text-xs, text-sm, text-base, text-lg, text-xl)
  errorText: "text-sm",          // Tamanho do texto da mensagem de erro (text-xs, text-sm, text-base, text-lg)
  emptyMessage: "text-base",     // Tamanho da mensagem quando não há dados (text-xs, text-sm, text-base, text-lg)
} as const;

interface GTMINViewProps {
  comparison: ComparisonData;
}

export function GTMINView({ comparison }: GTMINViewProps) {
  const { deck_1, deck_2, comparison_table, matrix_data, deck_displays, deck_count, visualization_type, deck_names } = comparison;
  
  // Obter nomes de todos os decks (suporte N decks)
  const allDeckNames = getDeckNames(comparison);
  
  // Usar primeiro e último deck para exibição (compatibilidade com formato atual)
  const deck1Name = deck_displays?.[0] || allDeckNames[0] || deck_1?.name || "Deck 1";
  const deck2Name = deck_displays?.[deck_displays.length - 1] || allDeckNames[allDeckNames.length - 1] || deck_2?.name || "Deck 2";
  
  // Verificar se deve usar matriz de comparação (mais de 2 decks ou visualization_type = "gtmin_matrix")
  const useMatrix = visualization_type === "gtmin_matrix" || 
                    (deck_count && deck_count > 2) || 
                    (deck_names && deck_names.length > 2) ||
                    (matrix_data && matrix_data.length > 0);

  // Função para mapear row para formato de differences
  const mapRowToDifference = (row: TableRow): Difference => {
    const periodValue = row.period !== undefined ? String(row.period) :
                       (row.data !== undefined ? String(row.data) : "");
    
    const deck1Value = row.deck_1 ?? row.deck_1_value ?? null;
    const deck2Value = row.deck_2 ?? row.deck_2_value ?? null;
    
    return {
      field: "GTMIN",
      period: periodValue,
      periodo_coluna: row.periodo_coluna ? String(row.periodo_coluna) : undefined,
      deck_1_value: deck1Value !== null && deck1Value !== undefined ? Number(deck1Value) : 0,
      deck_2_value: deck2Value !== null && deck2Value !== undefined ? Number(deck2Value) : 0,
      difference: row.diferenca ?? row.difference ?? null,
      difference_percent: row.diferenca_percent ?? row.difference_percent ?? null,
      is_inclusao_ou_exclusao: row.is_inclusao_ou_exclusao ?? false,
    };
  };

  // Agrupar por tipo_mudanca_key se existir
  const groupedByTipoMudanca = React.useMemo(() => {
    if (!comparison_table || comparison_table.length === 0) return null;
    if (!comparison_table[0]?.tipo_mudanca_key) return null;
    
    const grouped: Record<string, { tipo: string; label: string; rows: TableRow[] }> = {};
    comparison_table.forEach((row) => {
      const key = row.tipo_mudanca_key!;
      if (!grouped[key]) {
        grouped[key] = {
          tipo: row.tipo_mudanca || "",
          label: row.tipo_mudanca_label || row.tipo_mudanca || "",
          rows: []
        };
      }
      grouped[key].rows.push(row);
    });
    return grouped;
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

  // Se deve usar matriz, renderizar componente de matriz
  if (useMatrix && matrix_data && matrix_data.length > 0) {
    const matrixDeckNames = deck_names || deck_displays || allDeckNames;
    return (
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full space-y-6 mt-4"
      >
        <GTMINMatrixTable 
          matrixData={matrix_data} 
          deckNames={matrixDeckNames}
        />
      </motion.div>
    );
  }

  // Caso contrário, usar visualização tradicional (2 decks)
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="w-full space-y-6 mt-4"
    >
      {groupedByTipoMudanca ? (
        // Renderizar tabelas agrupadas por tipo de mudança
        Object.entries(groupedByTipoMudanca).map(([key, group]) => {
          const mappedRows = group.rows.map(mapRowToDifference);
          return (
            <div key={key} className="space-y-2">
              <h4 className="text-lg font-semibold text-card-foreground">
                {group.label}
              </h4>
              <GTMINGroupedTable 
                differences={mappedRows}
                deck1Name={deck1Name}
                deck2Name={deck2Name}
                firstColumnLabel={firstColumnLabel}
              />
            </div>
          );
        })
      ) : comparison_table && comparison_table.length > 0 ? (
        // Fallback: renderizar tabela única se não houver agrupamento
        <GTMINGroupedTable 
          differences={comparison_table.map(mapRowToDifference)}
          deck1Name={deck1Name}
          deck2Name={deck2Name}
          firstColumnLabel={firstColumnLabel}
        />
      ) : null}

      {/* Mensagem de erro se algum deck falhou */}
      {deck_1 && deck_2 && (!deck_1.success || !deck_2.success) && (
        <div className="bg-destructive/10 border border-destructive/30 rounded-lg p-4">
          <h3 className={`${MESSAGE_SIZES.errorTitle} font-semibold text-destructive mb-2`}>
            Erros na comparação:
          </h3>
          {deck_1 && !deck_1.success && (
            <p className={`${MESSAGE_SIZES.errorText} text-destructive/80`}>
              {deck_1.name}: {deck_1.error || "Erro desconhecido"}
            </p>
          )}
          {deck_2 && !deck_2.success && (
            <p className={`${MESSAGE_SIZES.errorText} text-destructive/80`}>
              {deck_2.name}: {deck_2.error || "Erro desconhecido"}
            </p>
          )}
        </div>
      )}
    </motion.div>
  );
}
