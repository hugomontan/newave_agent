"use client";

import React from "react";
import { CargaMensalView } from "./carga-mensal";
import { LimitesIntercambioView } from "./limites-intercambio";
import { GTMINView } from "./gtmin";
import { CVUView } from "./cvu";
import type { ComparisonData } from "./shared/types";

interface ComparisonRouterProps {
  comparison: ComparisonData;
}

export function ComparisonRouter({ comparison }: ComparisonRouterProps) {
  const { visualization_type, tool_name } = comparison;

  // Router baseado em visualization_type e tool_name
  switch (visualization_type) {
    case "table_with_line_chart":
      // Detectar tool específica
      if (tool_name === "CargaMensalTool" || tool_name === "CadicTool") {
        return <CargaMensalView comparison={comparison} />;
      }
      if (tool_name === "ClastValoresTool") {
        return <CVUView comparison={comparison} />;
      }
      // Para outras tools com table_with_line_chart, retornar fallback
      return (
        <div className="w-full space-y-6 mt-4">
          <p className="text-sm text-muted-foreground">
            Visualização não implementada para tool: {tool_name || "desconhecida"}
          </p>
        </div>
      );

    case "limites_intercambio":
      return <LimitesIntercambioView comparison={comparison} />;

    case "gtmin_changes_table":
      return <GTMINView comparison={comparison} />;

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
