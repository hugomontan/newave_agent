"use client";

import React from "react";
import { motion } from "framer-motion";
import { GTMINGroupedTable } from "./GTMINGroupedTable";
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
  const { deck_1, deck_2, comparison_table, matrix_data, deck_displays, deck_count, visualization_type, deck_names, meses_ordenados } = comparison as any;
  
  // Obter nomes de todos os decks (suporte N decks)
  const allDeckNames = getDeckNames(comparison);
  
  // Usar primeiro e último deck para exibição (compatibilidade com formato atual)
  const deck1Name = deck_displays?.[0] || allDeckNames[0] || deck_1?.name || "Deck 1";
  const deck2Name = deck_displays?.[deck_displays.length - 1] || allDeckNames[allDeckNames.length - 1] || deck_2?.name || "Deck 2";

  // Converter matrix_data para comparison_table se necessário
  const convertedComparisonTable = React.useMemo(() => {
    // Se já temos comparison_table, usar diretamente
    if (comparison_table && comparison_table.length > 0) {
      return comparison_table;
    }
    
    // Se temos matrix_data mas não comparison_table, converter
    if (matrix_data && matrix_data.length > 0 && deck_names && deck_names.length > 0) {
      return matrix_data.map((matrixRow: any) => {
        const nome_usina = matrixRow.nome_usina || "N/A";
        const periodo_inicio = matrixRow.periodo_inicio || "N/A";
        const periodo_fim = matrixRow.periodo_fim || periodo_inicio;
        const periodo = matrixRow.periodo || periodo_inicio;
        const gtmin_values = matrixRow.gtmin_values || {};
        
        // Formatar período para coluna (formato "MM-YYYY até MM-YYYY")
        const formatPeriodoColuna = (inicio: string, fim: string): string => {
          if (!inicio || inicio === "N/A") return "";
          try {
            const convertToMMYYYY = (dateStr: string): string => {
              if (!dateStr || dateStr === "N/A") return "";
              if (dateStr.includes("-")) {
                const parts = dateStr.split("-");
                if (parts.length === 2) {
                  return `${parts[1]}-${parts[0]}`;
                }
              }
              return dateStr;
            };
            
            const inicioFormatado = convertToMMYYYY(inicio);
            const fimFormatado = convertToMMYYYY(fim);
            
            if (inicioFormatado && fimFormatado && inicioFormatado !== fimFormatado) {
              return `${inicioFormatado} até ${fimFormatado}`;
            } else if (inicioFormatado) {
              return inicioFormatado;
            }
            return "";
          } catch {
            return "";
          }
        };
        
        const periodo_coluna = formatPeriodoColuna(periodo_inicio, periodo_fim);
        
        // Criar linha da tabela comparativa
        const tableRow: any = {
          field: nome_usina,
          nome_usina: nome_usina,
          codigo_usina: matrixRow.codigo_usina,
          period: nome_usina,
          periodo_coluna: periodo_coluna,
          periodo: periodo,
          periodo_inicio: periodo_inicio,
          periodo_fim: periodo_fim,
          classe: "GTMIN",
        };
        
        // Mapear gtmin_values[deck_name] para deck_1, deck_2, etc. na ordem de deck_names
        deck_names.forEach((deckName: string, idx: number) => {
          const deckKey = `deck_${idx + 1}` as keyof TableRow;
          const deckValueKey = `deck_${idx + 1}_value` as keyof TableRow;
          const value = gtmin_values[deckName];
          tableRow[deckKey] = value !== null && value !== undefined ? value : null;
          tableRow[deckValueKey] = value !== null && value !== undefined ? value : null;
        });
        
        return tableRow;
      });
    }
    
    return comparison_table || [];
  }, [comparison_table, matrix_data, deck_names]);

  // Função para mapear row para formato de differences
  // Para matriz transposta, preservar todos os campos originais do TableRow
  const mapRowToDifference = (row: TableRow): Difference & Partial<TableRow> => {
    // Verificar se é matriz transposta (tem campos month_YYYY-MM)
    const isTransposed = Object.keys(row).some(key => key.startsWith('month_'));
    
    // Preservar period como está vindo do backend
    const periodValue = row.period !== undefined ? String(row.period) :
                       (row.data !== undefined ? String(row.data) : "");
    
    // Preservar field (nome da usina)
    const fieldValue = (row as any).field || (row as any).nome_usina || "GTMIN";
    
    const deck1Value = row.deck_1 ?? row.deck_1_value ?? null;
    const deck2Value = row.deck_2 ?? row.deck_2_value ?? null;
    
    const difference: Difference & Partial<TableRow> = {
      field: fieldValue,
      period: periodValue,
      periodo_coluna: row.periodo_coluna ? String(row.periodo_coluna) : undefined,
      deck_1_value: deck1Value !== null && deck1Value !== undefined ? Number(deck1Value) : 0,
      deck_2_value: deck2Value !== null && deck2Value !== undefined ? Number(deck2Value) : 0,
      difference: row.diferenca ?? row.difference ?? null,
      difference_percent: row.diferenca_percent ?? row.difference_percent ?? null,
      is_inclusao_ou_exclusao: row.is_inclusao_ou_exclusao ?? false,
    };
    
    // Se for matriz transposta, preservar TODOS os campos originais do TableRow
    if (isTransposed) {
      // Copiar TODOS os campos do TableRow para preservar month_YYYY-MM e outros campos
      Object.keys(row).forEach(key => {
        // Preservar todos os campos, especialmente month_*, deck_name, nome_usina, etc.
        (difference as any)[key] = row[key as keyof TableRow];
      });
      // Campos preservados (sem log para produção)
    }
    
    return difference;
  };

  // Agrupar por tipo_mudanca_key se existir
  const groupedByTipoMudanca = React.useMemo(() => {
    if (!convertedComparisonTable || convertedComparisonTable.length === 0) return null;
    if (!convertedComparisonTable[0]?.tipo_mudanca_key) return null;
    
    const grouped: Record<string, { tipo: string; label: string; rows: TableRow[] }> = {};
    convertedComparisonTable.forEach((row: TableRow) => {
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
  }, [convertedComparisonTable]);

  // Determinar label da primeira coluna
  const firstColumnLabel = React.useMemo(() => {
    if (convertedComparisonTable && convertedComparisonTable.length > 0) {
      const firstRow = convertedComparisonTable[0];
      if (firstRow.classe === "VOLUME_INICIAL") {
        return "Usina";
      }
      const hasAnoField = convertedComparisonTable.some((row: TableRow) => {
        const anoValue = row.ano;
        return anoValue !== undefined && anoValue !== null && anoValue !== '';
      });
      if (hasAnoField) {
        return "Ano";
      }
    }
    return "Usina";
  }, [convertedComparisonTable]);

  // Verificar se é matriz transposta antes de mapear
  const isTransposedMatrix = React.useMemo(() => {
    if (!convertedComparisonTable || convertedComparisonTable.length === 0) return false;
    const firstRow = convertedComparisonTable[0];
    return Object.keys(firstRow).some(key => key.startsWith('month_'));
  }, [convertedComparisonTable]);

  // Sempre usar GTMINGroupedTable (não usar matriz)
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="w-full space-y-6 mt-4"
    >
      {groupedByTipoMudanca ? (
        // Renderizar tabelas agrupadas por tipo de mudança
        Object.entries(groupedByTipoMudanca).map(([key, group]) => {
          // Se for matriz transposta, passar TableRows diretamente (preservando campos month_)
          // Caso contrário, mapear para Difference
          const rowsToPass = isTransposedMatrix 
            ? group.rows.map((row: TableRow) => mapRowToDifference(row)) as any
            : group.rows.map(mapRowToDifference);
          
          return (
            <div key={key} className="space-y-2">
              <h4 className="text-lg font-semibold text-card-foreground">
                {group.label}
              </h4>
              <GTMINGroupedTable 
                differences={rowsToPass}
                deck1Name={deck1Name}
                deck2Name={deck2Name}
                deckNames={deck_names || deck_displays || allDeckNames}
                firstColumnLabel={firstColumnLabel}
                mesesOrdenados={meses_ordenados as string[] | undefined}
              />
            </div>
          );
        })
      ) : convertedComparisonTable && convertedComparisonTable.length > 0 ? (
        // Fallback: renderizar tabela única se não houver agrupamento
        // Se for matriz transposta, passar TableRows diretamente (preservando campos month_)
        (() => {
          const rowsToPass = isTransposedMatrix
            ? convertedComparisonTable.map((row: TableRow) => mapRowToDifference(row)) as any
            : convertedComparisonTable.map(mapRowToDifference);
          
          return (
            <GTMINGroupedTable 
              differences={rowsToPass}
              deck1Name={deck1Name}
              deck2Name={deck2Name}
              deckNames={deck_names || deck_displays || allDeckNames}
              firstColumnLabel={firstColumnLabel}
              mesesOrdenados={meses_ordenados as string[] | undefined}
            />
          );
        })()
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
