// Tipos compartilhados para componentes de comparação
// Suporta N decks para comparação dinâmica

// Tipo para informações de um deck individual
export interface DeckRawData {
  deck_name: string;
  display_name: string;
  data: Record<string, unknown>;
}

export interface ComparisonData {
  // Campos legados para compatibilidade com 2 decks
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
  deck_1_name?: string;
  deck_2_name?: string;
  
  // Novos campos para N decks
  deck_names?: string[];
  deck_displays?: string[];
  deck_count?: number;
  decks_raw?: DeckRawData[];
  
  // Dados formatados
  chart_data?: ChartData | null;
  charts_by_par?: Record<string, {
    par: string;
    sentido: string;
    chart_data: ChartData | null;
    chart_config?: {
      type: string;
      title: string;
      x_axis: string;
      y_axis: string;
    };
  }>;
  charts_by_restricao?: Record<string, Record<string, ChartData>>;
  differences?: Difference[];
  comparison_table?: TableRow[];
  matrix_data?: MatrixRow[];
  visualization_type?: string;
  comparison_by_type?: Record<string, any>;
  comparison_by_usina?: Record<string, any>;
  comparison_by_ree?: Record<string, any>;
  stats?: Record<string, any>;
  tool_name?: string;
}

export interface MatrixRow {
  nome_usina: string;
  codigo_usina: number;
  periodo_inicio: string;
  periodo_fim: string;
  gtmin_values: Record<string, number | null>;
  matrix: Record<string, number | null>;
}

// Helper para verificar se é análise histórica (mais de 2 decks)
export function isHistoricalAnalysis(comparison: ComparisonData): boolean {
  return (comparison.deck_count ?? 2) > 2;
}

// Helper para obter lista de nomes de decks
export function getDeckNames(comparison: ComparisonData): string[] {
  if (comparison.deck_displays && comparison.deck_displays.length > 0) {
    return comparison.deck_displays;
  }
  return [
    comparison.deck_1?.name || "Deck 1",
    comparison.deck_2?.name || "Deck 2"
  ];
}

export interface ChartData {
  labels: string[];
  datasets: Array<{
    label: string;
    data: (number | null)[];
  }>;
}

export interface Difference {
  field: string;
  period: string;
  periodo_coluna?: string;
  mes?: number | string;
  deck_1_value: number;
  deck_2_value: number;
  difference?: number | null;
  difference_percent?: number | null;
  is_inclusao_ou_exclusao?: boolean;
}

export interface TableRow {
  data?: string | number;
  classe?: string;
  classe_info?: string; // Campo de validação: "Custos de Classe - Nome da usina"
  ano?: string | number;
  mes?: string | number;
  
  // Campos legados para 2 decks
  deck_1?: number | null;
  deck_2?: number | null;
  deck_1_value?: number | null;
  deck_2_value?: number | null;
  diferenca?: number | null;
  difference?: number | null;
  diferenca_percent?: number | null;
  difference_percent?: number | null;
  
  // Campos dinâmicos para N decks (deck_3, deck_4, etc.)
  [key: `deck_${number}`]: number | null | undefined;
  
  // Outros campos
  par_key?: string;
  par?: string;
  sentido?: string;
  tipo_mudanca_key?: string;
  tipo_mudanca?: string;
  tipo_mudanca_label?: string;
  periodo_coluna?: string;
  period?: string;
  is_inclusao_ou_exclusao?: boolean;
  
  // Campos para análise histórica
  trend?: "up" | "down" | "stable";
  min_value?: number;
  max_value?: number;
  avg_value?: number;
}
