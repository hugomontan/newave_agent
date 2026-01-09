"use client";

import React from "react";
import { ComparisonChart } from "./ComparisonChart";
import { DifferencesTable } from "./DifferencesTable";
import { ExptHierarchicalView } from "./ExptHierarchicalView";
import { motion } from "framer-motion";

interface ComparisonViewProps {
  comparison: {
    deck_1: {
      name: string;
      success: boolean;
      data: Record<string, unknown>[];
      summary?: Record<string, unknown>;
      error?: string;
    };
    deck_2: {
      name: string;
      success: boolean;
      data: Record<string, unknown>[];
      summary?: Record<string, unknown>;
      error?: string;
    };
    chart_data?: {
      labels: string[];
      datasets: Array<{
        label: string;
        data: (number | null)[];
      }>;
    } | null;
    charts_by_par?: Record<string, {
      par: string;
      sentido: string;
      chart_data: {
        labels: string[];
        datasets: Array<{
          label: string;
          data: (number | null)[];
        }>;
      } | null;
      chart_config?: {
        type: string;
        title: string;
        x_axis: string;
        y_axis: string;
      };
    }>;
    differences?: Array<{
      field: string;
      period: string;
      deck_1_value: number;
      deck_2_value: number;
      difference: number;
      difference_percent: number;
    }>;
    comparison_table?: Array<{
      data?: string | number;
      classe?: string;
      ano?: string | number;
      mes?: string | number;
      deck_1?: number | null;
      deck_2?: number | null;
      deck_1_value?: number | null;
      deck_2_value?: number | null;
      diferenca?: number | null;
      difference?: number | null;
      diferenca_percent?: number | null;
      difference_percent?: number | null;
      par_key?: string;
      par?: string;
      sentido?: string;
    }>;
    visualization_type?: string;
    comparison_by_type?: Record<string, unknown>;
    comparison_by_usina?: Record<string, unknown>;
  };
}

export function ComparisonView({ comparison }: ComparisonViewProps) {
  const { deck_1, deck_2, chart_data, charts_by_par, differences, comparison_table, visualization_type, comparison_by_type, comparison_by_usina } = comparison;
  
  // Verificar se é formato hierárquico do EXPT
  const isExptHierarchical = visualization_type === "expt_hierarchical" && 
                             (comparison_by_type || comparison_by_usina);
  
  // Se for formato hierárquico, usar componente específico
  if (isExptHierarchical) {
    return <ExptHierarchicalView comparison={comparison} />;
  }
  
  // Debug: verificar chart_data
  React.useEffect(() => {
    console.log("[ComparisonView] comparison completo:", comparison);
    if (chart_data) {
      console.log("[ComparisonView] chart_data recebido:", chart_data);
      console.log("[ComparisonView] labels:", chart_data.labels);
      console.log("[ComparisonView] datasets:", chart_data.datasets);
      console.log("[ComparisonView] labels.length:", chart_data.labels?.length);
      console.log("[ComparisonView] datasets.length:", chart_data.datasets?.length);
    } else {
      console.log("[ComparisonView] chart_data é null ou undefined");
    }
  }, [chart_data, comparison]);

  // Converter comparison_table para formato de differences se necessário
  const tableData = comparison_table || differences || [];
  
  // Debug: verificar comparison_table
  React.useEffect(() => {
    console.log("[ComparisonView] comparison_table:", comparison_table);
    console.log("[ComparisonView] comparison_table length:", comparison_table?.length);
    if (comparison_table && comparison_table.length > 0) {
      console.log("[ComparisonView] primeiro item comparison_table:", comparison_table[0]);
    }
  }, [comparison_table]);
  
  // Função para mapear row para formato de differences
  const mapRowToDifference = (row: typeof comparison_table[0]) => {
    // Priorizar "period" se disponível (contém nome da usina + período para GTMIN)
    // Depois "ano" (para Carga Mensal), depois "data" ou "classe"
    const periodValue = row.period !== undefined ? String(row.period) :
                       (row.ano !== undefined ? String(row.ano) : 
                       (row.data !== undefined ? String(row.data) : 
                       (row.classe !== undefined ? String(row.classe) : "")));
    
    // Determinar o tipo baseado no formato do período
    const isCargaMensal = periodValue.includes("/") || periodValue.match(/\d{4}-\d{2}/); // Formato "Dez/2025" ou "2025-12"
    // Para Carga Adicional, usar label apropriado
    const isCargaAdicional = periodValue.includes("/") && comparison_table && comparison_table.length > 0;
    const fieldLabel = isCargaMensal || isCargaAdicional ? (isCargaAdicional ? "Carga Adicional" : "Carga Mensal") : (row.classe ? String(row.classe) : "CVU");
    
    const deck1Value = row.deck_1 ?? row.deck_1_value ?? null;
    const deck2Value = row.deck_2 ?? row.deck_2_value ?? null;
    
    return {
      field: fieldLabel,
      period: periodValue,
      periodo_coluna: row.periodo_coluna ? String(row.periodo_coluna) : undefined,
      deck_1_value: deck1Value !== null && deck1Value !== undefined ? Number(deck1Value) : 0,
      deck_2_value: deck2Value !== null && deck2Value !== undefined ? Number(deck2Value) : 0,
      difference: row.diferenca ?? row.difference ?? null,
      difference_percent: row.diferenca_percent ?? row.difference_percent ?? null,
      is_inclusao_ou_exclusao: row.is_inclusao_ou_exclusao ?? false,
    };
  };

  // Agrupar por tipo_mudanca_key se existir (para MudancasGeracoesTermicasTool)
  const groupedByTipoMudanca = React.useMemo(() => {
    if (!comparison_table || comparison_table.length === 0) return null;
    if (!comparison_table[0]?.tipo_mudanca_key) return null;
    
    const grouped: Record<string, { tipo: string; label: string; rows: typeof comparison_table }> = {};
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

  // Agrupar por par_key se existir (para LimitesIntercambioTool)
  const groupedByPar = React.useMemo(() => {
    if (!comparison_table || comparison_table.length === 0) return null;
    if (!comparison_table[0]?.par_key) return null;
    
    const grouped: Record<string, { par: string; sentido: string; rows: typeof comparison_table }> = {};
    comparison_table.forEach((row) => {
      const key = row.par_key!;
      if (!grouped[key]) {
        grouped[key] = {
          par: row.par || "",
          sentido: row.sentido || "",
          rows: []
        };
      }
      grouped[key].rows.push(row);
    });
    return grouped;
  }, [comparison_table]);

  // Mapear comparison_table para formato de differences (se não agrupado)
  const mappedDifferences = (groupedByPar || groupedByTipoMudanca)
    ? null  // Se agrupado, não usar mappedDifferences
    : (comparison_table 
        ? comparison_table.map(mapRowToDifference)
        : differences || []);
  
  // Determinar label da primeira coluna (Ano ou Usina)
  // Exceção: volumes iniciais sempre usa "Usina"
  // Se houver campo "ano" na comparison_table, usar "Ano"
  const firstColumnLabel = React.useMemo(() => {
    // Verificar se é tool de volumes iniciais
    if (visualization_type === "volume_inicial_changes_table") {
      return "Usina";
    }
    
    // Verificar se é CVU (ClastValoresTool) ou Carga Mensal - ambos usam visualization_type "table_with_line_chart"
    // Carga Mensal tem campos "ano" e "mes", CVU só tem "ano"
    if (visualization_type === "table_with_line_chart") {
      if (comparison_table && comparison_table.length > 0) {
        const firstRow = comparison_table[0];
        
        // Verificar se tem campo "mes" - indica Carga Mensal (usa "Período" ou "Ano" dependendo do contexto)
        const hasMesField = comparison_table.some(row => {
          const mesValue = row.mes;
          return mesValue !== undefined && mesValue !== null && mesValue !== '';
        });
        
        if (hasMesField) {
          // Carga Mensal: usar "Ano" (a primeira coluna mostra o período/ano)
          console.log("[ComparisonView] Detectado Carga Mensal - usando label 'Ano'");
          return "Ano";
        }
        
        // Se não tem "mes", verificar se tem campo "ano" - indica CVU
        const hasAnoField = comparison_table.some(row => {
          const anoValue = row.ano;
          return anoValue !== undefined && anoValue !== null && anoValue !== '';
        });
        if (hasAnoField) {
          console.log("[ComparisonView] Detectado CVU com campo 'ano' - usando label 'Ano'");
          return "Ano";
        }
        
        // Se não encontrou campo "ano" mas é table_with_line_chart, 
        // verificar se o periodValue parece ser um ano (números)
        if (firstRow) {
          // Se period existe e parece ser um número ou "Ano X", é CVU
          const periodValue = firstRow.period;
          if (periodValue && typeof periodValue === 'string' && /^Ano\s+\d+/.test(periodValue)) {
            console.log("[ComparisonView] Detectado CVU por formato de period - usando label 'Ano'");
            return "Ano";
          }
        }
      }
    }
    
    if (comparison_table && comparison_table.length > 0) {
      const firstRow = comparison_table[0];
      
      // Verificar se tem campo "classe" === "VOLUME_INICIAL"
      if (firstRow.classe === "VOLUME_INICIAL") {
        return "Usina";
      }
      
      // Verificar se tem campo "ano" (para ClastValoresTool e outras tools que usam ano)
      // Verificar na primeira linha e também em outras linhas para garantir
      // O campo "ano" pode ser number ou string, então verificamos se existe e não é null/undefined
      const hasAnoField = comparison_table.some(row => {
        const anoValue = row.ano;
        return anoValue !== undefined && anoValue !== null && anoValue !== '';
      });
      
      if (hasAnoField) {
        console.log("[ComparisonView] Campo 'ano' detectado - usando label 'Ano'");
        return "Ano";
      }
      
      // Verificação adicional: se o periodValue parece ser um número (ano)
      // Isso ajuda quando o campo "ano" não está presente mas o period é um número
      const firstMapped = mapRowToDifference(firstRow);
      if (firstMapped.period && /^\d+$/.test(String(firstMapped.period).trim())) {
        // Se period é apenas um número, provavelmente é um ano
        console.log("[ComparisonView] Period é um número - usando label 'Ano'");
        return "Ano";
      }
      
      console.log("[ComparisonView] Nenhum campo 'ano' detectado - usando label padrão 'Usina'");
      console.log("[ComparisonView] Primeira linha:", firstRow);
      console.log("[ComparisonView] Campos disponíveis na primeira linha:", Object.keys(firstRow));
    }
    
    // Padrão: Usina
    return "Usina";
  }, [comparison_table, visualization_type]);
  
  // Debug: verificar mappedDifferences
  React.useEffect(() => {
    console.log("[ComparisonView] mappedDifferences length:", mappedDifferences?.length);
    if (mappedDifferences && mappedDifferences.length > 0) {
      console.log("[ComparisonView] primeiro mappedDifference:", mappedDifferences[0]);
    }
    if (groupedByPar) {
      console.log("[ComparisonView] groupedByPar:", Object.keys(groupedByPar).length, "pares");
    }
    if (groupedByTipoMudanca) {
      console.log("[ComparisonView] groupedByTipoMudanca:", Object.keys(groupedByTipoMudanca).length, "tipos");
    }
  }, [mappedDifferences, groupedByPar, groupedByTipoMudanca]);

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="w-full space-y-6 mt-4"
    >
      {/* Tabelas e Gráficos de Comparação */}
      {groupedByTipoMudanca ? (
        // Renderizar tabelas agrupadas por tipo de mudança (para GTMIN)
        Object.entries(groupedByTipoMudanca).map(([key, group]) => {
          const mappedRows = group.rows.map(mapRowToDifference);
          return (
            <div key={key} className="space-y-2">
              <h4 className="text-lg font-semibold text-card-foreground">
                {group.label}
              </h4>
              <DifferencesTable 
                differences={mappedRows}
                deck1Name={deck_1.name}
                deck2Name={deck_2.name}
                firstColumnLabel={firstColumnLabel}
              />
            </div>
          );
        })
      ) : groupedByPar && charts_by_par ? (
        // Renderizar tabela e gráfico juntos para cada par (intercalados)
        Object.entries(groupedByPar).map(([key, group]) => {
          const mappedRows = group.rows.map(mapRowToDifference);
          const parChart = charts_by_par[key];
          const hasChartData = parChart && parChart.chart_data && parChart.chart_data.labels && parChart.chart_data.labels.length > 0;
          
          return (
            <div key={key} className="space-y-4">
              <div className="space-y-2">
                <h4 className="text-lg font-semibold text-card-foreground">
                  {group.par} - {group.sentido}
                </h4>
                <DifferencesTable 
                  differences={mappedRows}
                  deck1Name={deck_1.name}
                  deck2Name={deck_2.name}
                />
              </div>
              {hasChartData && (
                <ComparisonChart data={parChart.chart_data} />
              )}
            </div>
          );
        })
      ) : groupedByPar ? (
        // Renderizar apenas tabelas agrupadas por par (sem gráficos por par)
        Object.entries(groupedByPar).map(([key, group]) => {
          const mappedRows = group.rows.map(mapRowToDifference);
          return (
            <div key={key} className="space-y-2">
              <h4 className="text-lg font-semibold text-card-foreground">
                {group.par} - {group.sentido}
              </h4>
              <DifferencesTable 
                differences={mappedRows}
                deck1Name={deck_1.name}
                deck2Name={deck_2.name}
                firstColumnLabel={firstColumnLabel}
              />
            </div>
          );
        })
      ) : (
        // Renderizar tabela única (comportamento padrão)
        mappedDifferences && mappedDifferences.length > 0 && (
          <DifferencesTable 
            differences={mappedDifferences}
            deck1Name={deck_1.name}
            deck2Name={deck_2.name}
            firstColumnLabel={firstColumnLabel}
          />
        )
      )}

      {/* Gráfico único (apenas se não houver charts_by_par) */}
      {!charts_by_par && (() => {
        const hasChartData = chart_data && chart_data.labels && chart_data.labels.length > 0 && chart_data.datasets && chart_data.datasets.length > 0;
        console.log("[ComparisonView] Renderizando gráfico - hasChartData:", hasChartData);
        console.log("[ComparisonView] chart_data:", chart_data);
        if (hasChartData) {
          return (
            <div className="w-full">
              <ComparisonChart data={chart_data} />
            </div>
          );
        }
        return null;
      })()}

      {/* Mensagem de erro se algum deck falhou */}
      {(!deck_1.success || !deck_2.success) && (
        <div className="bg-destructive/10 border border-destructive/30 rounded-lg p-4">
          <h3 className="text-sm font-semibold text-destructive mb-2">
            Erros na comparação:
          </h3>
          {!deck_1.success && (
            <p className="text-xs text-destructive/80">
              {deck_1.name}: {deck_1.error || "Erro desconhecido"}
            </p>
          )}
          {!deck_2.success && (
            <p className="text-xs text-destructive/80">
              {deck_2.name}: {deck_2.error || "Erro desconhecido"}
            </p>
          )}
        </div>
      )}
    </motion.div>
  );
}
