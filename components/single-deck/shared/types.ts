/**
 * Tipos TypeScript para visualizações single deck.
 */

export interface TableRow {
  [key: string]: string | number | null | undefined;
}

export interface ChartData {
  labels: string[];
  datasets: Array<{
    label: string;
    data: Array<number | null>;
    [key: string]: any;
  }>;
}

export interface ChartConfig {
  type: string;
  title: string;
  x_axis: string;
  y_axis: string;
  [key: string]: any;
}

export interface SingleDeckVisualizationData {
  table?: TableRow[];
  chart_data?: ChartData | null;
  charts_by_par?: Record<string, {
    par: string;
    sentido: string;
    chart_data: ChartData;
    chart_config?: ChartConfig;
  }>;
  charts_by_restricao?: Record<string, {
    labels: string[];
    datasets: Array<{
      label: string;
      data: Array<number | null>;
    }>;
  }>;
  tables_by_fonte?: Record<string, TableRow[]>;
  tables_by_tipo?: Record<string, TableRow[]>;
  filtros?: {
    usina?: {
      codigo: number;
      nome: string;
    };
    tipo_modificacao?: string;
    usina_especifica?: number;
    nome_usina?: string;
    ree?: number;
  };
  todas_usinas?: Array<{
    codigo: number;
    nome: string;
  }>;
  stats_geral?: {
    total_tipos?: number;
    total_registros?: number;
    tipos_encontrados?: string[];
  };
  visualization_type?: string;
  chart_config?: ChartConfig;
  tool_name?: string;
}
