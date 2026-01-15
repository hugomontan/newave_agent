"use client";

import React from "react";
import { CargaMensalView } from "./carga-mensal";
import { LimitesIntercambioView } from "./limites-intercambio";
import { GTMINView } from "./gtmin";
import { VazaoMinimaView } from "./vazao-minima";
import { CVUView } from "./cvu";
import { ReservatorioInicialView } from "./reservatorio-inicial";
import { UsinasNaoSimuladasView } from "./usinas-nao-simuladas";
import { RestricaoEletricaView } from "./restricao-eletrica";
import type { ComparisonData } from "./shared/types";

interface ComparisonRouterProps {
  comparison: ComparisonData;
}

export function ComparisonRouter({ comparison }: ComparisonRouterProps) {
  const { visualization_type, tool_name, comparison_table, chart_data, chart_config } = comparison;

  // Normalizar visualization_type (remover espaços, converter para string)
  const normalizedVizType = visualization_type?.toString().trim();
  // Normalizar tool_name com múltiplas tentativas (case-insensitive, remover espaços)
  const normalizedToolName = tool_name 
    ? tool_name.toString().trim() 
    : (chart_config as any)?.tool_name?.toString().trim() || "";
  
  // DEBUG: Log para identificar problemas
  if (process.env.NODE_ENV === 'development') {
    console.log('[ComparisonRouter] Debug:', {
      tool_name,
      normalizedToolName,
      visualization_type: normalizedVizType,
      chart_config_tool_name: (chart_config as any)?.tool_name,
      hasTableData: comparison_table && comparison_table.length > 0,
      hasChartData: chart_data && chart_data.labels && chart_data.labels.length > 0
    });
  }
  
  // Verificar se há dados para renderizar mesmo sem visualization_type específico
  const hasTableData = comparison_table && comparison_table.length > 0;
  const hasChartData = chart_data && chart_data.labels && chart_data.labels.length > 0;
  
  // Verificar tool_name PRIMEIRO, antes do switch (prioridade máxima)
  // SEMPRE usar UsinasNaoSimuladasView para UsinasNaoSimuladasTool, SEM EXCEÇÃO
  // Verificação case-insensitive para garantir que funcione mesmo com variações
  if (normalizedToolName.toLowerCase() === "usinasnaosimuladastool") {
    if (process.env.NODE_ENV === 'development') {
      console.log('[ComparisonRouter] ✅ Usando UsinasNaoSimuladasView para UsinasNaoSimuladasTool');
    }
    return <UsinasNaoSimuladasView comparison={comparison} />;
  }
  
  // Verificação adicional: se chart_config indica UsinasNaoSimuladasTool mas tool_name não está presente
  const chartConfigToolName = (chart_config as any)?.tool_name?.toString().trim() || "";
  if (chartConfigToolName.toLowerCase() === "usinasnaosimuladastool") {
    if (process.env.NODE_ENV === 'development') {
      console.log('[ComparisonRouter] ✅ Usando UsinasNaoSimuladasView (detectado via chart_config)');
    }
    return <UsinasNaoSimuladasView comparison={comparison} />;
  }

  switch (normalizedVizType) {
    case "table_with_line_chart":
      // Tools que compartilham table_with_line_chart
      // IMPORTANTE: UsinasNaoSimuladasTool já foi tratado acima, não deve chegar aqui
      if (normalizedToolName === "CargaMensalTool" || normalizedToolName === "CadicTool") {
        return <CargaMensalView comparison={comparison} />;
      }
      if (normalizedToolName === "ClastValoresTool") {
        return <CVUView comparison={comparison} />;
      }
      // Fallback: tentar renderizar com CVUView se houver dados (mas não para UsinasNaoSimuladasTool)
      if (hasTableData || hasChartData) {
        return <CVUView comparison={comparison} />;
      }
      // Fallback para outras tools com table_with_line_chart
      return (
        <div className="w-full space-y-6 mt-4">
          <p className="text-sm text-muted-foreground">
            Visualização não implementada para tool: {normalizedToolName || "desconhecida"}
          </p>
        </div>
      );

    case "reservatorio_inicial_table":
      return <ReservatorioInicialView comparison={comparison} />;

    case "limites_intercambio":
      return <LimitesIntercambioView comparison={comparison} />;

    case "gtmin_changes_table":
    case "gtmin_matrix":
      return <GTMINView comparison={comparison} />;

    case "vazao_minima_changes_table":
      return <VazaoMinimaView comparison={comparison} />;

    case "restricao_eletrica":
      return <RestricaoEletricaView comparison={comparison} />;

    case "line_chart":
      // Tools que usam line_chart padrão
      // IMPORTANTE: UsinasNaoSimuladasTool já foi tratado acima, não deve chegar aqui
      if (normalizedToolName === "VazoesTool" || normalizedToolName === "DsvaguaTool") {
        // Usar componente genérico ou criar específico se necessário
        if (hasTableData || hasChartData) {
          return <UsinasNaoSimuladasView comparison={comparison} />;
        }
      }
      // Fallback para outras tools com line_chart (mas não UsinasNaoSimuladasTool)
      if (hasTableData || hasChartData) {
        return <UsinasNaoSimuladasView comparison={comparison} />;
      }
      break;

    case "llm_free":
    case "unknown":
    case "desconhecido":
      // Tentar renderizar com base no tool_name e dados disponíveis
      // IMPORTANTE: UsinasNaoSimuladasTool já foi tratado acima, não deve chegar aqui
      if (normalizedToolName === "ClastValoresTool" && (hasTableData || hasChartData)) {
        return <CVUView comparison={comparison} />;
      }
      if ((normalizedToolName === "CargaMensalTool" || normalizedToolName === "CadicTool") && (hasTableData || hasChartData)) {
        return <CargaMensalView comparison={comparison} />;
      }
      if ((normalizedToolName === "VazoesTool" || normalizedToolName === "DsvaguaTool") && (hasTableData || hasChartData)) {
        return <UsinasNaoSimuladasView comparison={comparison} />;
      }
      if (normalizedToolName === "RestricaoEletricaTool" && (hasTableData || comparison.charts_by_restricao)) {
        return <RestricaoEletricaView comparison={comparison} />;
      }
      // Se não há dados, mostrar mensagem
      if (!hasTableData && !hasChartData) {
        return (
          <div className="w-full space-y-6 mt-4">
            <p className="text-sm text-muted-foreground">
              Visualização não implementada para este tipo: {visualization_type || "desconhecido"}
            </p>
          </div>
        );
      }
      // Se há dados mas não há visualização específica, tentar renderizar genérico
      return <CVUView comparison={comparison} />;

    default:
      // Fallback: tentar renderizar com base em tool_name e dados disponíveis
      // IMPORTANTE: UsinasNaoSimuladasTool já foi tratado acima, não deve chegar aqui
      if (normalizedToolName === "ClastValoresTool" && (hasTableData || hasChartData)) {
        return <CVUView comparison={comparison} />;
      }
      if ((normalizedToolName === "CargaMensalTool" || normalizedToolName === "CadicTool") && (hasTableData || hasChartData)) {
        return <CargaMensalView comparison={comparison} />;
      }
      if ((normalizedToolName === "VazoesTool" || normalizedToolName === "DsvaguaTool") && (hasTableData || hasChartData)) {
        return <UsinasNaoSimuladasView comparison={comparison} />;
      }
      if (normalizedToolName === "RestricaoEletricaTool" && (hasTableData || comparison.charts_by_restricao)) {
        return <RestricaoEletricaView comparison={comparison} />;
      }
      // Se não há dados, mostrar mensagem
      if (!hasTableData && !hasChartData) {
        return (
          <div className="w-full space-y-6 mt-4">
            <p className="text-sm text-muted-foreground">
              Visualização não implementada para este tipo: {visualization_type || "desconhecido"}
            </p>
          </div>
        );
      }
      // Se há dados mas não há visualização específica, tentar renderizar genérico
      // Mas não usar CVUView como fallback genérico - usar UsinasNaoSimuladasView que é mais genérico
      if (hasTableData || hasChartData) {
        return <UsinasNaoSimuladasView comparison={comparison} />;
      }
      return (
        <div className="w-full space-y-6 mt-4">
          <p className="text-sm text-muted-foreground">
            Visualização não implementada para este tipo: {visualization_type || "desconhecido"}
          </p>
        </div>
      );
  }
}
