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
  const { visualization_type } = comparison;

  // Normalizar visualization_type (remover espaços, converter para string)
  const normalizedVizType = visualization_type?.toString().trim();
  
  switch (normalizedVizType) {
    case "table_with_line_chart":
      // Tools que compartilham table_with_line_chart
      const tool_name = comparison.tool_name?.toString().trim();
      if (tool_name === "CargaMensalTool" || tool_name === "CadicTool") {
        return <CargaMensalView comparison={comparison} />;
      }
      if (tool_name === "ClastValoresTool") {
        return <CVUView comparison={comparison} />;
      }
      // Fallback para outras tools com table_with_line_chart
      return (
        <div className="w-full space-y-6 mt-4">
          <p className="text-sm text-muted-foreground">
            Visualização não implementada para tool: {tool_name || "desconhecida"}
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

    default:
      // Fallback: retornar mensagem
      return (
        <div className="w-full space-y-6 mt-4">
          <p className="text-sm text-muted-foreground">
            Visualização não implementada para este tipo: {visualization_type || "desconhecido"}
          </p>
        </div>
      );
  }
}
