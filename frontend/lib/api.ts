const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

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
    differences?: Array<{
      field: string;
      period: string;
      deck_1_value: number;
      deck_2_value: number;
      difference: number;
      difference_percent: number;
    }>;
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

  const response = await fetch(`${API_URL}/upload`, {
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
  const response = await fetch(`${API_URL}/query`, {
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
  analysisMode?: "single" | "comparison" | "llm"
): AsyncGenerator<StreamEvent> {
  const response = await fetch(`${API_URL}/query/stream`, {
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

export async function getSession(sessionId: string): Promise<SessionInfo> {
  const response = await fetch(`${API_URL}/sessions/${sessionId}`);

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Sessão não encontrada");
  }

  return response.json();
}

export async function deleteSession(sessionId: string): Promise<void> {
  const response = await fetch(`${API_URL}/sessions/${sessionId}`, {
    method: "DELETE",
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Erro ao deletar sessão");
  }
}

export async function reindexDocs(): Promise<{ documents_count: number; message: string }> {
  const response = await fetch(`${API_URL}/index`, {
    method: "POST",
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Erro ao reindexar");
  }

  return response.json();
}