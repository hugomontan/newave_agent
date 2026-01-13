// Tipos compartilhados para componentes de comparação

export interface ComparisonData {
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
  differences?: Difference[];
  comparison_table?: TableRow[];
  visualization_type?: string;
  comparison_by_type?: Record<string, any>;
  comparison_by_usina?: Record<string, any>;
  tool_name?: string;
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
  tipo_mudanca_key?: string;
  tipo_mudanca?: string;
  tipo_mudanca_label?: string;
  periodo_coluna?: string;
  period?: string;
  is_inclusao_ou_exclusao?: boolean;
}
