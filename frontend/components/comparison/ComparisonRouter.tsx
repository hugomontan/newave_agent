"use client";

import React from "react";
import { CargaMensalView } from "./carga-mensal";
import { LimitesIntercambioView } from "./limites-intercambio";
import { GTMINView } from "./gtmin";
import { VazaoMinimaView } from "./vazao-minima";
import { CVUView } from "./cvu";
import { ReservatorioInicialView } from "./reservatorio-inicial";
import type { ComparisonData } from "./shared/types";

interface ComparisonRouterProps {
  comparison: ComparisonData;
}

export function ComparisonRouter({ comparison }: ComparisonRouterProps) {
  const { visualization_type, tool_name, comparison_table, chart_data } = comparison;

  // Normalizar visualization_type (remover espaços, converter para string)
  const normalizedVizType = visualization_type?.toString().trim();
  const normalizedToolName = tool_name?.toString().trim();
  
  // Verificar se há dados para renderizar mesmo sem visualization_type específico
  const hasTableData = comparison_table && comparison_table.length > 0;
  const hasChartData = chart_data && chart_data.labels && chart_data.labels.length > 0;
  
  switch (normalizedVizType) {
    case "table_with_line_chart":
      // Tools que compartilham table_with_line_chart
      if (normalizedToolName === "CargaMensalTool" || normalizedToolName === "CadicTool") {
        return <CargaMensalView comparison={comparison} />;
      }
      if (normalizedToolName === "ClastValoresTool") {
        return <CVUView comparison={comparison} />;
      }
      // Fallback: tentar renderizar com CVUView se houver dados
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
      return <GTMINView comparison={comparison} />;

    case "vazao_minima_changes_table":
      return <VazaoMinimaView comparison={comparison} />;

    case "llm_free":
    case "unknown":
    case "desconhecido":
      // Tentar renderizar com base no tool_name e dados disponíveis
      if (normalizedToolName === "ClastValoresTool" && (hasTableData || hasChartData)) {
        return <CVUView comparison={comparison} />;
      }
      if ((normalizedToolName === "CargaMensalTool" || normalizedToolName === "CadicTool") && (hasTableData || hasChartData)) {
        return <CargaMensalView comparison={comparison} />;
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
      if (normalizedToolName === "ClastValoresTool" && (hasTableData || hasChartData)) {
        return <CVUView comparison={comparison} />;
      }
      if ((normalizedToolName === "CargaMensalTool" || normalizedToolName === "CadicTool") && (hasTableData || hasChartData)) {
        return <CargaMensalView comparison={comparison} />;
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
  }
}
