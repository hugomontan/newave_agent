"use client";

import React from "react";
import { ExptHierarchicalView } from "./comparison/expt-hierarchical";
import { ComparisonRouter } from "./comparison";
import type { ComparisonData } from "./comparison/shared/types";

interface ComparisonViewProps {
  comparison: ComparisonData;
}

export function ComparisonView({ comparison }: ComparisonViewProps) {
  const { visualization_type, comparison_by_type, comparison_by_usina } = comparison;
  
  // Verificar se é formato hierárquico do EXPT
  const isExptHierarchical = visualization_type === "expt_hierarchical" && 
                             (comparison_by_type || comparison_by_usina);
  
  // Se for formato hierárquico, usar componente específico
  if (isExptHierarchical) {
    return <ExptHierarchicalView comparison={comparison as any} />;
  }
  
  // Usar o router modularizado
  return <ComparisonRouter comparison={comparison} />;
}
