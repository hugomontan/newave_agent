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
  // Campos específicos para DisponibilidadeUsinaTool
  disponibilidade_total?: number;
  // Campos específicos para InflexibilidadeUsinaTool
  inflexibilidade_total?: number;
  detalhes_patamares?: Array<{
    patamar: string;
    patamar_numero: number;
    inflexibilidade: number | null;
    duracao: number | null;
  }>;
  usina?: {
    codigo: number;
    nome: string;
    submercado: number;
  };
  calculo?: {
    numerador: number;
    denominador: number;
    resultado: number;
  };
  // Campos específicos para CargaMediaPonderadaTool
  mw_medios?: Array<{
    estagio?: number;
    codigo_submercado?: number;
    mw_medio: number;
  }>;
  // Campos específicos para PQPequenasUsinasTool
  tables_by_regiao?: Record<string, TableRow[]>;
  tables_by_tipo?: Record<string, TableRow[]>;
  stats_geral?: {
    total_registros?: number;
    regioes_encontradas?: string[];
    tipos_encontrados?: string[];
    total_mw_medio_geral?: number;
  };
  mw_medios_por_regiao?: Array<{
    regiao: string;
    mw_medio: number;
  }>;
  mw_medios_por_tipo?: Array<{
    tipo: string;
    mw_medio: number;
  }>;
}
