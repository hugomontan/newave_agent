const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// Funções NEWAVE (mantidas para compatibilidade, agora usam /api/newave)
const NEWAVE_API_URL = `${API_URL}/api/newave`;

// Funções DECOMP
const DECOMP_API_URL = `${API_URL}/api/decomp`;

export interface QueryResponse {
  session_id: string;
  query: string;
  response: string;
  generated_code: string;
  execution_success: boolean;
  execution_output: string | null;
  raw_data: Record<string, unknown>[] | null;
  retry_count: number;
  error: string | null;
  comparison_data?: {
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
    decks_raw?: Array<{
      deck_name: string;
      display_name: string;
      data: Record<string, unknown>;
    }>;
    // Dados formatados
    chart_data?: {
      labels: string[];
      datasets: Array<{
        label: string;
        data: (number | null)[];
      }>;
    } | null;
    differences?: Array<{
      field: string;
      period: string;
      deck_1_value: number;
      deck_2_value: number;
      difference: number;
      difference_percent: number;
    }>;
  } | null;
}

export interface UploadResponse {
  session_id: string;
  message: string;
  files_count: number;
}

export interface SessionInfo {
  session_id: string;
  path: string;
  files: string[];
  files_count: number;
}

// Tipos para eventos de streaming
export interface StreamEvent {
  type: 
    | 'start' 
    | 'node_start' 
    | 'node_detail' 
    | 'node_complete' 
    | 'code_start' 
    | 'code_line' 
    | 'code_complete'
    | 'execution_result'
    | 'response_start'
    | 'response_chunk'
    | 'response_complete'
    | 'retry'
    | 'disambiguation'
    | 'complete'
    | 'error';
  message?: string;
  node?: string;
  info?: {
    name: string;
    icon: string;
    description: string;
  };
  detail?: string;
  line?: string;
  line_number?: number;
  code?: string;
  success?: boolean;
  stdout?: string;
  stderr?: string;
  chunk?: string;
  response?: string;
  requires_user_choice?: boolean;
  alternative_type?: string;
  visualization_data?: {
    table?: Array<Record<string, unknown>>;
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
      };
      chart_config?: {
        type: string;
        title: string;
        x_axis: string;
        y_axis: string;
      };
    }>;
    visualization_type?: string;
    chart_config?: {
      type: string;
      title: string;
      x_axis: string;
      y_axis: string;
    };
    tool_name?: string;
  };
  plant_correction_followup?: {
    type: "plant_correction";
    message: string;
    selected_plant: {
      type: "hydraulic" | "thermal";
      codigo: number;
      nome: string;
      nome_completo: string;
      tool_name: string;
    };
    all_plants: Array<{codigo: number; nome: string; nome_completo: string}>;
    original_query: string;
  };
  comparison_data?: {
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
    comparison_table?: Array<any>;
    matrix_data?: Array<{
      nome_usina: string;
      codigo_usina?: number;
      periodo?: string;
      periodo_inicio?: string;
      periodo_fim?: string;
      gtmin_values: Record<string, number | null>;
      matrix?: Record<string, number | null>;
      value_groups?: Record<number, string[]>;
    }>;
    deck_names?: string[];
    deck_displays?: string[];
    deck_count?: number;
    visualization_type?: string;
    tool_name?: string;
    comparison_by_type?: Record<string, any>;
    comparison_by_usina?: Record<string, any>;
    comparison_by_ree?: Record<string, any>;
    stats?: Record<string, any>;
  } | null;
  retry_count?: number;
  max_retries?: number;
  retry?: number;
  total_retries?: number;
  data?: {
    type: string;
    question: string;
    options: Array<{
      label: string;
      query: string;
      tool_name: string;
    }>;
    original_query: string;
  };
}

export async function uploadDeck(file: File): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${NEWAVE_API_URL}/upload`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Erro ao fazer upload");
  }

  return response.json();
}

export async function sendQuery(
  sessionId: string,
  query: string
): Promise<QueryResponse> {
  const response = await fetch(`${NEWAVE_API_URL}/query`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      session_id: sessionId,
      query: query,
    }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Erro ao processar query");
  }

  return response.json();
}

export async function* sendQueryStream(
  sessionId: string,
  query: string,
  analysisMode?: "single" | "comparison" | "llm" | "llm_only"
): AsyncGenerator<StreamEvent> {
  const response = await fetch(`${NEWAVE_API_URL}/query/stream`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      session_id: sessionId,
      query: query,
      analysis_mode: analysisMode || "single",
    }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Erro ao processar query");
  }

  const reader = response.body?.getReader();
  if (!reader) {
    throw new Error("Streaming não suportado");
  }

  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    
    // Mantém a última linha incompleta no buffer
    buffer = lines.pop() || "";

    for (const line of lines) {
      if (line.startsWith("data: ")) {
        try {
          const data = JSON.parse(line.slice(6));
          yield data as StreamEvent;
        } catch (e) {
          console.error("[SSE] Erro ao parsear evento:", e);
        }
      }
    }
  }
}

export async function getSession(sessionId: string, model: "newave" | "decomp" = "newave"): Promise<SessionInfo> {
  const apiUrl = model === "decomp" ? `${DECOMP_API_URL}` : NEWAVE_API_URL;
  const response = await fetch(`${apiUrl}/sessions/${sessionId}`);

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Sessão não encontrada");
  }

  return response.json();
}

export async function deleteSession(sessionId: string, model: "newave" | "decomp" = "newave"): Promise<void> {
  const apiUrl = model === "decomp" ? `${DECOMP_API_URL}` : NEWAVE_API_URL;
  const response = await fetch(`${apiUrl}/sessions/${sessionId}`, {
    method: "DELETE",
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Erro ao deletar sessão");
  }
}

export async function reindexDocs(): Promise<{ documents_count: number; message: string }> {
  const response = await fetch(`${NEWAVE_API_URL}/index`, {
    method: "POST",
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Erro ao reindexar");
  }

  return response.json();
}

// =====================
// APIs para N-Decks
// =====================

export interface DeckInfo {
  name: string;
  display_name: string;
  year: number;
  month: number;
  week?: number | null;
}

export interface DecksListResponse {
  decks: DeckInfo[];
  total: number;
}

export interface ComparisonInitResponse {
  session_id: string;
  message: string;
  selected_decks: DeckInfo[];
  files_count: number;
}

/**
 * Lista todos os decks disponíveis no repositório.
 * Retorna ordenados cronologicamente (mais antigo primeiro).
 */
export async function listAvailableDecks(): Promise<DecksListResponse> {
  const url = `${NEWAVE_API_URL}/decks/list`;
  const response = await fetch(url);

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Erro ao listar decks");
  }

  return response.json();
}

/**
 * Inicializa o modo comparação com os decks selecionados.
 * @param selectedDecks Lista de nomes dos decks a comparar (opcional)
 */
export async function initComparison(selectedDecks?: string[]): Promise<ComparisonInitResponse> {
  const response = await fetch(`${NEWAVE_API_URL}/init-comparison`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      selected_decks: selectedDecks,
    }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Erro ao inicializar comparação");
  }

  return response.json();
}

/**
 * Carrega um deck específico do repositório.
 * @param deckName Nome do deck (ex: "NW202512")
 */
export async function loadDeckFromRepo(deckName: string): Promise<UploadResponse> {
  const response = await fetch(`${NEWAVE_API_URL}/load-deck`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      deck_name: deckName,
    }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Erro ao carregar deck");
  }

  return response.json();
}

// =====================
// APIs para DECOMP
// =====================

/**
 * Faz upload de um deck DECOMP (arquivo .zip).
 */
export async function uploadDecompDeck(file: File): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${DECOMP_API_URL}/upload`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Erro ao fazer upload");
  }

  return response.json();
}

/**
 * Envia uma pergunta sobre o deck DECOMP com streaming.
 */
export async function* queryDecompStream(
  sessionId: string,
  query: string,
  analysisMode?: "single" | "comparison"
): AsyncGenerator<StreamEvent> {
  const response = await fetch(`${DECOMP_API_URL}/query/stream`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      session_id: sessionId,
      query: query,
      analysis_mode: analysisMode || "single",
    }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Erro ao processar query");
  }

  const reader = response.body?.getReader();
  if (!reader) {
    throw new Error("Streaming não suportado");
  }

  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    
    // Mantém a última linha incompleta no buffer
    buffer = lines.pop() || "";

    for (const line of lines) {
      if (line.startsWith("data: ")) {
        try {
          const data = JSON.parse(line.slice(6));
          yield data as StreamEvent;
        } catch (e) {
          console.error("[SSE] Erro ao parsear evento:", e);
        }
      }
    }
  }
}

/**
 * Reindexa a documentação do DECOMP.
 */
export async function reindexDecompDocs(): Promise<{ documents_count: number; message: string }> {
  const response = await fetch(`${DECOMP_API_URL}/index`, {
    method: "POST",
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Erro ao reindexar");
  }

  return response.json();
}

/**
 * Lista todos os decks DECOMP disponíveis no repositório.
 * Retorna ordenados cronologicamente (mais antigo primeiro).
 */
export async function listAvailableDecompDecks(): Promise<DecksListResponse> {
  const url = `${DECOMP_API_URL}/decks`;
  const response = await fetch(url);

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Erro ao listar decks");
  }

  return response.json();
}

/**
 * Carrega um deck DECOMP específico do repositório.
 * @param deckName Nome do deck (ex: "DC202512-sem1" ou "DC202512")
 */
export async function loadDecompDeckFromRepo(deckName: string): Promise<UploadResponse> {
  const response = await fetch(`${DECOMP_API_URL}/load-deck`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      deck_name: deckName,
    }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Erro ao carregar deck");
  }

  return response.json();
}

/**
 * Inicializa o modo comparação DECOMP com os decks selecionados.
 * @param selectedDecks Lista de nomes dos decks a comparar (opcional)
 */
export async function initDecompComparison(selectedDecks?: string[]): Promise<ComparisonInitResponse> {
  const response = await fetch(`${DECOMP_API_URL}/init-comparison`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      selected_decks: selectedDecks,
    }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Erro ao inicializar comparação");
  }

  return response.json();
}