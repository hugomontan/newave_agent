"use client";

import React, { useState, useMemo } from "react";
import { Download } from "lucide-react";
import { formatNumber } from "../shared/formatters";
import { exportToCSV } from "../shared/csvExport";
import type { TableRow, Difference } from "../shared/types";

// Configuração de tamanhos das mensagens (pode ser ajustado para testar)
const MESSAGE_SIZES = {
  emptyMessage: "text-base"
} as const;

// Cores para as colunas de decks (expandido para suportar até 12 decks)
const DECK_COLORS = [
  "text-blue-400",
  "text-purple-400",
  "text-green-400",
  "text-orange-400",
  "text-cyan-400",
  "text-pink-400",
  "text-emerald-400",
  "text-sky-400",
  "text-violet-400",
  "text-red-400",
  "text-slate-400",
  "text-amber-400",
];

const INITIAL_ROWS = 10;

interface VazaoMinimaGroupedTableProps {
  differences: Difference[];
  deck1Name: string;
  deck2Name: string;
  deckNames?: string[]; // Novos: nomes de todos os decks para N-deck support
  firstColumnLabel?: string;
  mesesOrdenados?: string[]; // Meses no formato YYYY-MM para matriz transposta (apenas VAZMINT)
  tipoVazao?: "VAZMIN" | "VAZMINT"; // Tipo de vazão para filtrar/identificar
}

export function VazaoMinimaGroupedTable({ 
  differences, 
  deck1Name, 
  deck2Name, 
  deckNames,
  firstColumnLabel = "Usina",
  mesesOrdenados,
  tipoVazao
}: VazaoMinimaGroupedTableProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  
  // Obter lista de nomes dos decks (suporte N decks)
  const allDeckNames = useMemo(() => {
    if (deckNames && deckNames.length > 0) {
      return deckNames;
    }
    return [deck1Name, deck2Name];
  }, [deckNames, deck1Name, deck2Name]);

  // Detectar se estamos usando matriz transposta (campos month_YYYY-MM) - apenas para VAZMINT
  const differencesAsTableRows = differences as unknown as TableRow[];
  const isTransposed = useMemo(() => {
    if (!differences || differences.length === 0) return false;
    if (tipoVazao === "VAZMIN") return false; // VAZMIN não usa matriz transposta
    
    // Verificar no primeiro difference (pode ter campos preservados)
    const firstDiff = differences[0] as any;
    if (firstDiff && Object.keys(firstDiff).some((key: string) => key.startsWith('month_'))) {
      return true;
    }
    
    // Verificar no primeiro TableRow
    if (differencesAsTableRows && differencesAsTableRows.length > 0) {
      const firstRow = differencesAsTableRows[0];
      if (firstRow && Object.keys(firstRow).some(key => key.startsWith('month_'))) {
        return true;
      }
    }
    
    return false;
  }, [differences, differencesAsTableRows, tipoVazao]);

  // Extrair meses ordenados dos dados ou usar prop (apenas para VAZMINT)
  const meses = useMemo(() => {
    // Prioridade 1: usar mesesOrdenados da prop (vem do backend)
    if (mesesOrdenados && mesesOrdenados.length > 0) {
      return mesesOrdenados;
    }
    
    // Prioridade 2: extrair de todos os differences (coletar todos os meses únicos)
    if (isTransposed && differences.length > 0) {
      const allMonthKeys = new Set<string>();
      
      // Coletar de todos os differences
      differences.forEach((diff: any) => {
        Object.keys(diff).forEach((key: string) => {
          if (key.startsWith('month_')) {
            allMonthKeys.add(key.replace('month_', ''));
          }
        });
      });
      
      // Coletar de todos os TableRows também
      if (differencesAsTableRows && differencesAsTableRows.length > 0) {
        differencesAsTableRows.forEach((row: any) => {
          if (row) {
            Object.keys(row).forEach((key: string) => {
              if (key.startsWith('month_')) {
                allMonthKeys.add(key.replace('month_', ''));
              }
            });
          }
        });
      }
      
      if (allMonthKeys.size > 0) {
        return Array.from(allMonthKeys).sort();
      }
    }
    
    return [];
  }, [mesesOrdenados, isTransposed, differences, differencesAsTableRows]);
  
  if (!differences || differences.length === 0) {
    return (
      <div className="bg-card border border-border rounded-lg p-4 sm:p-6">
        <h3 className="text-base sm:text-lg font-semibold text-card-foreground mb-2">
          Mudanças de Vazão Mínima{tipoVazao ? ` (${tipoVazao})` : ""}
        </h3>
        <p className={`${MESSAGE_SIZES.emptyMessage} text-muted-foreground`}>
          Não houveram mudanças registradas{tipoVazao ? ` para ${tipoVazao}` : ""}.
        </p>
      </div>
    );
  }

  const hasMoreRows = differences.length > INITIAL_ROWS;
  const displayedData = isExpanded ? differences : differences.slice(0, INITIAL_ROWS);
  
  // Verificar se alguma linha tem periodo_coluna para mostrar a coluna consistentemente (apenas VAZMINT)
  const showPeriodoColumn = tipoVazao === "VAZMINT" && differences.some(d => d.periodo_coluna);

  // Função helper para obter o tipo de mudança do backend (apenas para VAZMINT com matriz transposta)
  const getChangeType = (diff: any, mes: string): 'stable' | 'increased' | 'decreased' | 'implemented' => {
    if (!isTransposed) return 'stable';
    
    const changeTypeKey = `change_type_${mes}`;
    const changeType = diff[changeTypeKey];
    
    if (!changeType || typeof changeType !== 'string') {
      return 'stable';
    }
    
    const validTypes: ('stable' | 'increased' | 'decreased' | 'implemented')[] = 
      ['stable', 'increased', 'decreased', 'implemented'];
    
    if (validTypes.includes(changeType as any)) {
      return changeType as 'stable' | 'increased' | 'decreased' | 'implemented';
    }
    
    return 'stable';
  };

  // Extrair informações da linha
  const extractRowInfo = (diff: Difference, tableRow: TableRow) => {
    if (isTransposed) {
      // Matriz transposta: field = usina, period = deck_name (display_name)
      const deckName = (diff as any)?.deck_name || diff.period || (tableRow as any)?.deck_name || "N/A";
      
      return {
        usina: diff.field || "N/A",
        deck: deckName
      };
    } else {
      // Formato tradicional: extrair usina e período
      const periodStr = String(diff.period || "");
      const fieldStr = String(diff.field || "");
      
      return { usina: fieldStr || periodStr, periodo: periodStr || diff.periodo_coluna || "" };
    }
  };

  const handleDownloadCSV = () => {
    const csvData = differences.map((diff, index) => {
      const tableRow = differencesAsTableRows[index];
      const rowInfo = extractRowInfo(diff, tableRow);
      const row: Record<string, string | number | null> = {
        [isTransposed ? "Usina" : firstColumnLabel]: rowInfo.usina,
      };
      
      if (isTransposed) {
        row.Deck = (rowInfo as any).deck || null;
        // Adicionar colunas para todos os meses
        meses.forEach((mes) => {
          const monthKey = `month_${mes}`;
          const value = ((diff as any)?.[monthKey] ?? tableRow?.[monthKey as keyof TableRow]) as number | null | undefined;
          row[mes] = value ?? null;
        });
      } else {
        // Formato tradicional
        if (showPeriodoColumn && (rowInfo as any).periodo) {
          row.Período = (rowInfo as any).periodo;
        }
        // Adicionar colunas para todos os decks
        for (let i = 0; i < allDeckNames.length; i++) {
          const deckKey = `deck_${i + 1}` as keyof TableRow;
          const deckValueKey = `deck_${i + 1}_value` as keyof TableRow;
          
          const value = (tableRow?.[deckKey] ?? tableRow?.[deckValueKey] ?? 
                        (i === 0 ? diff.deck_1_value : i === 1 ? diff.deck_2_value : null)) as number | null;
          
          row[allDeckNames[i]] = value ?? null;
        }
      }
      
      return row;
    });
    exportToCSV(csvData, `vazao_minima_${tipoVazao || 'all'}`);
  };

  return (
    <div className="bg-card border border-border rounded-lg p-4 sm:p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-base sm:text-lg font-semibold text-card-foreground">
          Mudanças de Vazão Mínima
        </h3>
        <div className="flex items-center gap-3">
          <span className="text-sm text-muted-foreground">
            {differences.length} registros
          </span>
          <button
            onClick={handleDownloadCSV}
            className="flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-card-foreground bg-background/50 hover:bg-background/70 border border-border rounded-lg transition-colors"
            title="Baixar como CSV"
          >
            <Download className="w-4 h-4" />
            CSV
          </button>
        </div>
      </div>

      <div className="overflow-x-auto -mx-4 sm:mx-0">
        <div className="inline-block min-w-full align-middle px-4 sm:px-0">
          <table className="min-w-full border-collapse">
            <thead>
              <tr className="border-b border-border bg-background/50">
                <th className="px-3 sm:px-4 py-3 text-left text-xs font-semibold text-card-foreground uppercase tracking-wider whitespace-nowrap">
                  {isTransposed ? "Usina" : firstColumnLabel}
                </th>
                {isTransposed && (
                  <th className="px-3 sm:px-4 py-3 text-left text-xs font-semibold text-card-foreground uppercase tracking-wider whitespace-nowrap">
                    Deck
                  </th>
                )}
                {!isTransposed && showPeriodoColumn && (
                  <th className="px-3 sm:px-4 py-3 text-left text-xs font-semibold text-card-foreground uppercase tracking-wider whitespace-nowrap">
                    Período
                  </th>
                )}
                {isTransposed ? (
                  // Matriz transposta: colunas = meses (apenas VAZMINT)
                  meses.map((mes) => (
                    <th 
                      key={mes}
                      className="px-3 sm:px-4 py-3 text-right text-xs font-semibold text-card-foreground uppercase tracking-wider whitespace-nowrap"
                    >
                      {mes}
                    </th>
                  ))
                ) : (
                  // Formato tradicional: colunas = decks
                  allDeckNames.map((name, index) => (
                    <th 
                      key={name}
                      className={`px-3 sm:px-4 py-3 text-right text-xs font-semibold uppercase tracking-wider whitespace-nowrap ${DECK_COLORS[index % DECK_COLORS.length]}`}
                    >
                      {name}
                    </th>
                  ))
                )}
              </tr>
            </thead>
            <tbody>
              {displayedData.map((diff, index) => {
                const tableRow = differencesAsTableRows[index];
                const rowInfo = extractRowInfo(diff, tableRow);
                
                return (
                  <tr
                    key={`${diff.period}-${index}`}
                    className="border-b border-border/50 hover:bg-background/30 transition-colors"
                  >
                    <td className="px-3 sm:px-4 py-2.5 text-sm text-card-foreground font-medium truncate" title={rowInfo.usina}>
                      {rowInfo.usina}
                    </td>
                    {isTransposed && (
                      <td className="px-3 sm:px-4 py-2.5 text-sm text-muted-foreground truncate" title={(rowInfo as any).deck || "-"}>
                        {(rowInfo as any).deck || "-"}
                      </td>
                    )}
                    {!isTransposed && showPeriodoColumn && (
                      <td className="px-3 sm:px-4 py-2.5 text-sm text-muted-foreground font-medium truncate" title={diff.periodo_coluna || "-"}>
                        {diff.periodo_coluna || "-"}
                      </td>
                    )}
                    {isTransposed ? (
                      // Matriz transposta: valores por mês
                      meses.length > 0 ? meses.map((mes) => {
                        const monthKey = `month_${mes}`;
                        const value = ((diff as any)?.[monthKey] ?? tableRow?.[monthKey as keyof TableRow]) as number | null | undefined;
                        
                        // Obter tipo de mudança do backend (já calculado)
                        const changeType = getChangeType(diff, mes);
                        
                        // Aplicar cor baseada no tipo de mudança
                        let cellClassName = "px-3 sm:px-4 py-2.5 text-sm text-right font-mono whitespace-nowrap";
                        let titleText = "";
                        
                        switch (changeType) {
                          case 'stable':
                            cellClassName += " text-blue-600 dark:text-blue-400";
                            titleText = "Valor estável entre decks";
                            break;
                          case 'increased':
                            cellClassName += " text-green-600 dark:text-green-400 font-semibold";
                            titleText = "Valor aumentou em relação ao deck anterior";
                            break;
                          case 'decreased':
                            cellClassName += " text-red-600 dark:text-red-400 font-semibold";
                            titleText = "Valor diminuiu em relação ao deck anterior";
                            break;
                          case 'implemented':
                            cellClassName += " text-purple-600 dark:text-purple-400 font-semibold";
                            titleText = "Valor implementado (não existia no deck anterior)";
                            break;
                        }
                        
                        return (
                          <td 
                            key={mes}
                            className={cellClassName}
                            title={titleText || undefined}
                          >
                            {value !== null && value !== undefined ? (
                              <>
                                {formatNumber(value)} <span className="text-xs text-muted-foreground ml-1">m³/s</span>
                              </>
                            ) : (
                              <span className="text-muted-foreground">-</span>
                            )}
                          </td>
                        );
                      }) : (
                        <td colSpan={allDeckNames.length} className="px-3 sm:px-4 py-2.5 text-sm text-center text-muted-foreground">
                          Nenhum mês disponível
                        </td>
                      )
                    ) : (
                      // Formato tradicional: valores por deck
                      allDeckNames.map((name, deckIndex) => {
                        const deckKey = `deck_${deckIndex + 1}` as keyof TableRow;
                        const deckValueKey = `deck_${deckIndex + 1}_value` as keyof TableRow;
                        
                        const value = (tableRow?.[deckKey] ?? tableRow?.[deckValueKey] ?? 
                                      (deckIndex === 0 ? diff.deck_1_value : deckIndex === 1 ? diff.deck_2_value : null)) as number | null;
                        
                        return (
                          <td 
                            key={name}
                            className={`px-3 sm:px-4 py-2.5 text-sm text-right font-mono whitespace-nowrap ${DECK_COLORS[deckIndex % DECK_COLORS.length]}`}
                          >
                            {value !== null && value !== undefined ? (
                              <>
                                {formatNumber(value)} <span className="text-xs text-muted-foreground ml-1">m³/s</span>
                              </>
                            ) : (
                              <span className="text-muted-foreground">-</span>
                            )}
                          </td>
                        );
                      })
                    )}
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {hasMoreRows && (
        <div className="mt-4 flex justify-center">
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="px-4 py-2 text-sm font-medium text-card-foreground bg-background/50 hover:bg-background/70 border border-border rounded-lg transition-colors"
          >
            {isExpanded 
              ? `Mostrar menos (${INITIAL_ROWS} primeiros)` 
              : `Mostrar todos (${differences.length - INITIAL_ROWS} restantes)`}
          </button>
        </div>
      )}
    </div>
  );
}
