"use client";

import React from "react";
import { motion } from "framer-motion";

interface MatrixCell {
  value: number | null;
  difference: number | null;
}

interface MatrixRow {
  nome_usina: string;
  codigo_usina?: number;
  periodo?: string;  // Mês individual (ex: "2025-12")
  periodo_inicio?: string;  // Período original início
  periodo_fim?: string;  // Período original fim
  gtmin_values: Record<string, number | null>;
  matrix?: Record<string, number | null>;  // Opcional - matriz de diferenças
  value_groups?: Record<string | number, string[]>;  // Grupos de valores iguais para coloração (chave pode ser string do JSON)
}

interface GTMINMatrixTableProps {
  matrixData: MatrixRow[];
  deckNames: string[];
}

export function GTMINMatrixTable({ matrixData, deckNames }: GTMINMatrixTableProps) {
  console.log("[GTMIN_MATRIX_TABLE] Recebido:", {
    matrixData_length: matrixData?.length,
    matrixData_sample: matrixData?.[0],
    deckNames,
  });
  
  // Debug detalhado: verificar correspondência entre deckNames e chaves em gtmin_values
  if (matrixData && matrixData.length > 0 && deckNames && deckNames.length > 0) {
    const firstRow = matrixData[0];
    const gtminValuesKeys = Object.keys(firstRow.gtmin_values || {});
    console.log("[GTMIN_MATRIX_TABLE] [DEBUG] Verificação de correspondência:", {
      deckNames,
      gtminValuesKeys,
      correspondencia: deckNames.every(dn => gtminValuesKeys.includes(dn)),
      chaves_em_deckNames: gtminValuesKeys.every(k => deckNames.includes(k)),
      primeira_linha_valores: firstRow.gtmin_values,
    });
  }
  
  if (!matrixData || matrixData.length === 0) {
    console.log("[GTMIN_MATRIX_TABLE] ⚠️ matrixData vazio ou inválido");
    return (
      <div className="text-center py-8 text-muted-foreground">
        Nenhum dado disponível para exibição.
      </div>
    );
  }
  
  if (!deckNames || deckNames.length === 0) {
    console.log("[GTMIN_MATRIX_TABLE] ⚠️ deckNames vazio ou inválido");
    return (
      <div className="text-center py-8 text-muted-foreground">
        Nenhum deck disponível para exibição.
      </div>
    );
  }

  // Função para formatar valor
  const formatValue = (value: number | null | undefined): string => {
    if (value === null || value === undefined) return "-";
    return value.toFixed(2);
  };

  // Função para obter cor da célula baseada no valor (para colorir valores iguais)
  // valueGroups pode ter chaves como string (JSON) ou number (TypeScript)
  const getCellColor = (value: number | null | undefined, valueGroups?: Record<string | number, string[]>, deckName?: string): string => {
    if (value === null || value === undefined) return "bg-muted/30";
    
    // Se temos grupos de valores iguais, usar cores diferentes para cada grupo
    if (valueGroups && deckName) {
      const roundedValue = Math.round(value * 100) / 100;  // Arredondar para 2 casas
      const groupEntries = Object.entries(valueGroups);
      
      for (let i = 0; i < groupEntries.length; i++) {
        const [groupValueStr, decks] = groupEntries[i];
        // Converter para número (pode vir como string do JSON)
        const groupValue = typeof groupValueStr === 'string' ? parseFloat(groupValueStr) : groupValueStr;
        
        if (Math.abs(groupValue - roundedValue) < 0.01 && decks.includes(deckName)) {
          // Usar índice do grupo para gerar cor consistente
          const colors = [
            "bg-blue-100/30 border-blue-300/50",
            "bg-green-100/30 border-green-300/50",
            "bg-yellow-100/30 border-yellow-300/50",
            "bg-purple-100/30 border-purple-300/50",
            "bg-pink-100/30 border-pink-300/50",
            "bg-indigo-100/30 border-indigo-300/50",
          ];
          return colors[i % colors.length];
        }
      }
    }
    
    return "bg-muted/30";
  };

  // Função para obter cor do texto baseada no valor
  const getTextColor = (value: number | null | undefined): string => {
    if (value === null || value === undefined) return "text-muted-foreground";
    return "text-foreground";
  };
  
  // Agrupar linhas por usina para melhor organização
  const groupedByUsina = React.useMemo(() => {
    const grouped: Record<string, MatrixRow[]> = {};
    matrixData.forEach((row) => {
      const usinaKey = `${row.nome_usina}-${row.codigo_usina || ''}`;
      if (!grouped[usinaKey]) {
        grouped[usinaKey] = [];
      }
      grouped[usinaKey].push(row);
    });
    // Ordenar linhas dentro de cada grupo por período
    Object.keys(grouped).forEach((key) => {
      grouped[key].sort((a, b) => {
        const periodoA = a.periodo || a.periodo_inicio || '';
        const periodoB = b.periodo || b.periodo_inicio || '';
        return periodoA.localeCompare(periodoB);
      });
    });
    return grouped;
  }, [matrixData]);

  // Debug: verificar se groupedByUsina está vazio
  const usinaEntries = Object.entries(groupedByUsina);
  console.log("[GTMIN_MATRIX_TABLE] [DEBUG] Renderização:", {
    groupedByUsina_count: usinaEntries.length,
    usinaKeys: Object.keys(groupedByUsina),
    firstUsinaRows: usinaEntries[0] ? usinaEntries[0][1].length : 0,
  });
  
  if (usinaEntries.length === 0) {
    console.log("[GTMIN_MATRIX_TABLE] ⚠️ Nenhuma usina encontrada para renderizar");
    return (
      <div className="text-center py-8 text-muted-foreground">
        Nenhuma usina encontrada nos dados.
      </div>
    );
  }

  return (
    <div className="w-full space-y-6 overflow-x-auto">
      {usinaEntries.map(([usinaKey, rows], usinaIndex) => {
        const firstRow = rows[0];
        const usinaName = firstRow.nome_usina;
        const usinaCodigo = firstRow.codigo_usina;

        return (
          <motion.div
            key={usinaKey}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: usinaIndex * 0.1 }}
            className="bg-card rounded-lg border border-border p-4 space-y-3"
          >
            {/* Cabeçalho da usina */}
            <div className="flex items-center justify-between border-b border-border pb-2">
              <div>
                <h3 className="text-lg font-semibold text-card-foreground">
                  {usinaName}
                </h3>
                {usinaCodigo && (
                  <p className="text-sm text-muted-foreground">
                    Código: {usinaCodigo}
                  </p>
                )}
              </div>
            </div>

            {/* Tabela: Linhas = meses, Colunas = decks */}
            <div className="w-full overflow-x-auto">
              <table className="w-full border-collapse" style={{ minWidth: 'max-content' }}>
                <thead>
                  <tr>
                    <th className="border border-border bg-muted/50 px-3 py-2 text-left text-sm font-semibold text-card-foreground sticky left-0 z-10">
                      Período
                    </th>
                    {deckNames.map((deckName) => (
                      <th
                        key={deckName}
                        className="border border-border bg-muted/50 px-3 py-2 text-center text-sm font-semibold text-card-foreground min-w-[100px]"
                      >
                        {deckName}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {rows.map((row, rowIndex) => {
                    const periodo = row.periodo || row.periodo_inicio || 'N/A';
                    return (
                      <tr key={`${usinaKey}-${periodo}-${rowIndex}`}>
                        <td className="border border-border bg-muted/30 px-3 py-2 text-sm font-medium text-card-foreground sticky left-0 z-10">
                          {periodo}
                        </td>
                        {deckNames.map((deckName) => {
                          const value = row.gtmin_values?.[deckName];
                          const cellColor = getCellColor(value, row.value_groups, deckName);
                          const textColor = getTextColor(value);
                          
                          // Debug para primeira célula da primeira linha
                          if (rowIndex === 0 && deckNames.indexOf(deckName) === 0) {
                            console.log("[GTMIN_MATRIX_TABLE] [DEBUG] Primeira célula:", {
                              deckName,
                              value,
                              gtmin_values: row.gtmin_values,
                              hasValue: value !== null && value !== undefined,
                            });
                          }
                          
                          return (
                            <td
                              key={deckName}
                              className={`border border-border px-3 py-2 text-center text-sm ${cellColor} ${textColor}`}
                            >
                              {value !== null && value !== undefined ? (
                                <span className="font-medium">{formatValue(value)}</span>
                              ) : (
                                <span className="text-muted-foreground">-</span>
                              )}
                            </td>
                          );
                        })}
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </motion.div>
        );
      })}
    </div>
  );
}
