"use client";

import React, { useState, useRef, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { ChatMessage } from "@/components/ChatMessage";
import { AgentProgress, AgentStep } from "@/components/AgentProgress";
import {
  sendQueryStream,
  deleteSession,
  reindexDocs,
  StreamEvent,
} from "@/lib/api";
import { motion } from "framer-motion";
import { Send, MoreVertical, RefreshCw, Trash2, ArrowLeft, GitCompare } from "lucide-react";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  code?: string;
  executionSuccess?: boolean;
  executionOutput?: string | null;
  rawData?: Record<string, unknown>[] | null;
  retryCount?: number;
  error?: string | null;
  timestamp: Date;
  disambiguationData?: {
    type: string;
    question: string;
    options: Array<{label: string; query: string; tool_name: string}>;
    original_query: string;
  };
  comparisonData?: {
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
    comparison_table?: Array<{
      data?: string | number;
      classe?: string;
      ano?: string | number;
      deck_1?: number | null;
      deck_2?: number | null;
      deck_1_value?: number | null;
      deck_2_value?: number | null;
      diferenca?: number | null;
      difference?: number | null;
      diferenca_percent?: number | null;
      difference_percent?: number | null;
    }>;
    visualization_type?: string;
    comparison_by_type?: Record<string, unknown>;
    comparison_by_usina?: Record<string, unknown>;
  };
}

export default function ComparisonPage() {
  const router = useRouter();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [isReindexing, setIsReindexing] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Streaming state
  const [agentSteps, setAgentSteps] = useState<AgentStep[]>([]);
  const [streamingCode, setStreamingCode] = useState("");
  const [streamingResponse, setStreamingResponse] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [executionSuccess, setExecutionSuccess] = useState<boolean | null>(null);
  const [executionError, setExecutionError] = useState<string | null>(null);
  const [executionOutput, setExecutionOutput] = useState<string | null>(null);
  const [retryCount, setRetryCount] = useState(0);
  const [maxRetries, setMaxRetries] = useState(3);
  const [comparisonData, setComparisonData] = useState<Message["comparisonData"]>(null);
  const [disambiguationData, setDisambiguationData] = useState<{
    type: string;
    question: string;
    options: Array<{label: string; query: string; tool_name: string}>;
    original_query: string;
  } | null>(null);

  // Refs para capturar estado durante streaming
  const streamingCodeRef = useRef("");
  const streamingResponseRef = useRef("");
  const executionSuccessRef = useRef<boolean | null>(null);
  const executionErrorRef = useRef<string | null>(null);
  const executionOutputRef = useRef<string | null>(null);
  const retryCountRef = useRef(0);
  const comparisonDataRef = useRef<Message["comparisonData"]>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, agentSteps, streamingCode, streamingResponse]);

  // Carregar sessão de comparação ao montar
  useEffect(() => {
    const initializeComparison = async () => {
      try {
        // Chamar API para inicializar modo comparação
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/init-comparison`, {
          method: "POST",
        });

        if (!response.ok) {
          throw new Error("Erro ao inicializar modo comparação");
        }

        const data = await response.json();
        setSessionId(data.session_id);

        setMessages([
          {
            id: Date.now().toString(),
            role: "assistant",
            content: `Modo Comparação ativado! Todas as consultas compararão automaticamente os dados entre **Dezembro 2025** e **Janeiro 2026**.\n\nFaça sua primeira consulta para ver os resultados lado a lado com gráficos comparativos.`,
            timestamp: new Date(),
          },
        ]);
      } catch (err) {
        console.error("Error initializing comparison:", err);
        setMessages([
          {
            id: Date.now().toString(),
            role: "assistant",
            content: `❌ **Erro ao inicializar modo comparação:**\n\n${
              err instanceof Error ? err.message : "Erro desconhecido"
            }`,
            timestamp: new Date(),
          },
        ]);
      }
    };

    initializeComparison();
  }, []);

  const processStreamEvent = useCallback((event: StreamEvent) => {
    switch (event.type) {
      case "start":
        setAgentSteps([]);
        setStreamingCode("");
        setStreamingResponse("");
        setIsStreaming(true);
        setExecutionSuccess(null);
        setExecutionError(null);
        setExecutionOutput(null);
        setRetryCount(0);
        setComparisonData(null);
        streamingCodeRef.current = "";
        streamingResponseRef.current = "";
        executionSuccessRef.current = null;
        executionErrorRef.current = null;
        executionOutputRef.current = null;
        retryCountRef.current = 0;
        comparisonDataRef.current = null;
        break;

      case "node_start":
        if (event.node && event.info) {
          setAgentSteps((prev) => {
            const existing = prev.find((s) => s.node === event.node);
            if (existing) {
              return prev.map((s) =>
                s.node === event.node ? { ...s, status: "running" as const } : s
              );
            }
            return [
              ...prev,
              {
                node: event.node!,
                name: event.info!.name,
                icon: event.info!.icon,
                description: event.info!.description,
                status: "running" as const,
              },
            ];
          });
        }
        break;

      case "node_detail":
        if (event.node && event.detail) {
          setAgentSteps((prev) =>
            prev.map((s) =>
              s.node === event.node ? { ...s, detail: event.detail } : s
            )
          );
        }
        break;

      case "node_complete":
        if (event.node) {
          setAgentSteps((prev) =>
            prev.map((s) =>
              s.node === event.node ? { ...s, status: "completed" as const } : s
            )
          );
        }
        break;

      case "code_line":
        if (event.line !== undefined) {
          setStreamingCode((prev) => {
            const newCode = prev ? prev + "\n" + event.line : event.line!;
            streamingCodeRef.current = newCode;
            return newCode;
          });
        }
        break;

      case "code_complete":
        if (event.code) {
          setStreamingCode(event.code);
          streamingCodeRef.current = event.code;
        }
        break;

      case "execution_result":
        setExecutionSuccess(event.success ?? false);
        executionSuccessRef.current = event.success ?? false;
        if (event.stdout) {
          setExecutionOutput(event.stdout);
          executionOutputRef.current = event.stdout;
        }
        if (event.stderr) {
          setExecutionError(event.stderr);
          executionErrorRef.current = event.stderr;
        }
        break;

      case "retry":
        if (event.retry_count !== undefined) {
          setRetryCount(event.retry_count);
          retryCountRef.current = event.retry_count;
          if (event.max_retries) {
            setMaxRetries(event.max_retries);
          }
          setAgentSteps((prev) => [
            ...prev,
            {
              node: `retry_${event.retry_count}`,
              name: `Tentativa ${event.retry_count + 1}/${event.max_retries || 3}`,
              icon: "🔄",
              description: event.message || "Corrigindo código com base no erro...",
              status: "running" as const,
            },
          ]);
        }
        break;

      case "response_start":
        setStreamingResponse("");
        streamingResponseRef.current = "";
        break;

      case "response_chunk":
        if (event.chunk) {
          setStreamingResponse((prev) => {
            const newResponse = prev + event.chunk;
            streamingResponseRef.current = newResponse;
            return newResponse;
          });
        }
        break;

      case "response_complete":
        if (event.response) {
          setStreamingResponse(event.response);
          streamingResponseRef.current = event.response;
        }
        if (event.comparison_data) {
          console.log("[FRONTEND] comparison_data recebido no response_complete:", event.comparison_data);
          console.log("[FRONTEND] comparison_table presente:", event.comparison_data.comparison_table !== undefined);
          console.log("[FRONTEND] comparison_table length:", event.comparison_data.comparison_table?.length);
          if (event.comparison_data.comparison_table && event.comparison_data.comparison_table.length > 0) {
            console.log("[FRONTEND] primeiro item comparison_table:", event.comparison_data.comparison_table[0]);
          }
          console.log("[FRONTEND] chart_data presente:", event.comparison_data.chart_data !== undefined);
          if (event.comparison_data.chart_data) {
            console.log("[FRONTEND] chart_data labels:", event.comparison_data.chart_data.labels);
            console.log("[FRONTEND] chart_data datasets:", event.comparison_data.chart_data.datasets);
          }
          setComparisonData(event.comparison_data);
          comparisonDataRef.current = event.comparison_data;
        }
        break;

      case "disambiguation":
        if (event.data) {
          setDisambiguationData(event.data);
          setMessages((prev) => [
            ...prev,
            {
              id: Date.now().toString(),
              role: "assistant",
              content: "",
              disambiguationData: event.data,
              timestamp: new Date(),
            },
          ]);
        }
        break;

      case "complete":
        setIsStreaming(false);
        break;

      case "error":
        setIsStreaming(false);
        setExecutionError(event.message || "Erro desconhecido");
        executionErrorRef.current = event.message || "Erro desconhecido";
        break;
    }
  }, []);

  const handleSendMessage = async () => {
    if (!input.trim() || !sessionId || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: input.trim(),
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);
    setAgentSteps([]);
    setStreamingCode("");
    setStreamingResponse("");
    setExecutionSuccess(null);
    setExecutionError(null);
    setExecutionOutput(null);
    setRetryCount(0);
    setComparisonData(null);
    comparisonDataRef.current = null;

    try {
      // Enviar query com modo comparação
      for await (const event of sendQueryStream(sessionId, userMessage.content, "comparison")) {
        processStreamEvent(event);
      }

      await new Promise(resolve => setTimeout(resolve, 100));

      let rawData: Record<string, unknown>[] | null = null;
      if (executionOutputRef.current) {
        try {
          const jsonMatch = executionOutputRef.current.match(/---JSON_DATA_START---([\s\S]*?)---JSON_DATA_END---/);
          if (jsonMatch) {
            rawData = JSON.parse(jsonMatch[1].trim());
          }
        } catch {
          // Ignora erro de parsing
        }
      }

      const hasContent = streamingResponseRef.current && streamingResponseRef.current.trim();
      const hasData = rawData && rawData.length > 0;
      const hasCode = streamingCodeRef.current && streamingCodeRef.current.trim();
      
      if (hasContent || hasData || hasCode || comparisonDataRef.current) {
        const assistantMessage: Message = {
          id: (Date.now() + 1).toString(),
          role: "assistant",
          content: streamingResponseRef.current || "",
          code: streamingCodeRef.current || undefined,
          executionSuccess: executionSuccessRef.current ?? false,
          executionOutput: executionOutputRef.current,
          rawData: rawData,
          retryCount: retryCountRef.current,
          error: executionErrorRef.current,
          comparisonData: comparisonDataRef.current || undefined,
          timestamp: new Date(),
        };

        setMessages((prev) => [...prev, assistantMessage]);
      }
      
      setAgentSteps([]);
      setStreamingCode("");
      setStreamingResponse("");

    } catch (err) {
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: `❌ **Erro ao processar sua pergunta:**\n\n${
          err instanceof Error ? err.message : "Erro desconhecido"
        }`,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, errorMessage]);
      setAgentSteps([]);
      setStreamingCode("");
      setStreamingResponse("");
    } finally {
      setIsLoading(false);
    }
  };

  const onClearSession = async () => {
    if (sessionId) {
      try {
        await deleteSession(sessionId);
      } catch (err) {
        console.error("Error deleting session:", err);
      }
    }

    setSessionId(null);
    setMessages([]);
    setAgentSteps([]);
    setStreamingCode("");
    setStreamingResponse("");
  };

  const handleReindex = async () => {
    setIsReindexing(true);
    try {
      const result = await reindexDocs();
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now().toString(),
          role: "assistant",
          content: `✅ **Documentação reindexada!**\n\n${result.documents_count} documentos foram processados.`,
          timestamp: new Date(),
        },
      ]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now().toString(),
          role: "assistant",
          content: `❌ **Erro ao reindexar:**\n\n${
            err instanceof Error ? err.message : "Erro desconhecido"
          }`,
          timestamp: new Date(),
        },
      ]);
    } finally {
      setIsReindexing(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleDisambiguationOptionClick = async (query: string) => {
    if (!sessionId) return;
    
    setDisambiguationData(null);
    
    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: query,
      timestamp: new Date(),
    };
    
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);
    setAgentSteps([]);
    setStreamingCode("");
    setStreamingResponse("");
    setExecutionSuccess(null);
    setExecutionError(null);
    setExecutionOutput(null);
    setRetryCount(0);
    setComparisonData(null);
    comparisonDataRef.current = null;

    try {
      for await (const event of sendQueryStream(sessionId, query, "comparison")) {
        processStreamEvent(event);
      }

      await new Promise(resolve => setTimeout(resolve, 100));

      let rawData: Record<string, unknown>[] | null = null;
      if (executionOutputRef.current) {
        try {
          const jsonMatch = executionOutputRef.current.match(/---JSON_DATA_START---([\s\S]*?)---JSON_DATA_END---/);
          if (jsonMatch) {
            rawData = JSON.parse(jsonMatch[1].trim());
          }
        } catch {
          // Ignora erro de parsing
        }
      }

      const hasContent = streamingResponseRef.current && streamingResponseRef.current.trim();
      const hasData = rawData && rawData.length > 0;
      const hasCode = streamingCodeRef.current && streamingCodeRef.current.trim();
      
      if (hasContent || hasData || hasCode || comparisonDataRef.current) {
        const assistantMessage: Message = {
          id: (Date.now() + 1).toString(),
          role: "assistant",
          content: streamingResponseRef.current || "",
          code: streamingCodeRef.current || undefined,
          executionSuccess: executionSuccessRef.current ?? false,
          executionOutput: executionOutputRef.current,
          rawData: rawData,
          retryCount: retryCountRef.current,
          error: executionErrorRef.current,
          comparisonData: comparisonDataRef.current || undefined,
          timestamp: new Date(),
        };

        setMessages((prev) => [...prev, assistantMessage]);
      }
      
      setAgentSteps([]);
      setStreamingCode("");
      setStreamingResponse("");

    } catch (err) {
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: `❌ **Erro ao processar sua pergunta:**\n\n${
          err instanceof Error ? err.message : "Erro desconhecido"
        }`,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, errorMessage]);
      setAgentSteps([]);
      setStreamingCode("");
      setStreamingResponse("");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <main className="flex flex-col h-screen bg-background overflow-hidden">
      {/* Header */}
      <header className="border-b border-border bg-background">
        <div className="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => router.push("/")}
              className="h-8 w-8 text-muted-foreground hover:text-foreground hover:bg-muted"
            >
              <ArrowLeft className="w-4 h-4" />
            </Button>
            <div className="flex items-center gap-2">
              <GitCompare className="w-4 h-4 text-primary" />
              <h1 className="text-sm font-medium text-foreground">Análise Comparativa</h1>
            </div>
          </div>
          <div className="flex items-center gap-1">
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-8 w-8 text-muted-foreground hover:text-foreground hover:bg-muted"
                >
                  <MoreVertical className="w-4 h-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-72 bg-card border-border">
                <DropdownMenuLabel className="text-card-foreground">Configurações</DropdownMenuLabel>
                <DropdownMenuSeparator />
                
                <div className="px-2 py-1.5">
                  <p className="text-xs text-muted-foreground font-medium mb-1">Modo Ativo</p>
                  <p className="text-xs text-foreground">Comparação Multi-Deck</p>
                  <p className="text-xs text-muted-foreground mt-1">
                    Comparando: Dezembro 2025 vs Janeiro 2026
                  </p>
                </div>
                
                {sessionId && (
                  <>
                    <div className="px-2 py-1.5">
                      <p className="text-xs text-muted-foreground font-medium mb-1">Session ID</p>
                      <code className="text-xs bg-background text-foreground px-2 py-1 rounded block overflow-hidden text-ellipsis border border-border font-mono break-all">
                        {sessionId}
                      </code>
                    </div>
                    
                    <DropdownMenuSeparator />
                    
                    <DropdownMenuItem
                      className="text-destructive focus:text-destructive focus:bg-destructive/20 cursor-pointer"
                      onSelect={onClearSession}
                    >
                      <Trash2 className="w-4 h-4 mr-2" />
                      Limpar Sessão
                    </DropdownMenuItem>
                    
                    <DropdownMenuSeparator />
                  </>
                )}
                
                <DropdownMenuItem
                  onSelect={handleReindex}
                  disabled={isReindexing}
                  className="cursor-pointer text-foreground focus:bg-muted"
                >
                  <RefreshCw className={`w-4 h-4 mr-2 ${isReindexing ? "animate-spin" : ""}`} />
                  {isReindexing ? "Reindexando..." : "Reindexar Documentação"}
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>
      </header>

      {/* Main content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        <ScrollArea className="flex-1">
          <div className="max-w-7xl mx-auto py-12 px-4">
            {messages.length === 0 && !isLoading ? (
              <div className="flex flex-col items-center justify-center text-center">
                <GitCompare className="w-16 h-16 text-primary mb-4" />
                <h2 className="text-4xl font-semibold mb-4 text-foreground">
                  Análise Comparativa
                </h2>
                <p className="text-muted-foreground mb-8 text-lg">
                  Todas as consultas compararão automaticamente os dados entre Dezembro 2025 e Janeiro 2026
                </p>
              </div>
            ) : (
              <div className="space-y-8">
                {messages.map((message) => (
                  <ChatMessage 
                    key={message.id} 
                    message={message} 
                    onOptionClick={handleDisambiguationOptionClick}
                  />
                ))}
                
                {isLoading && agentSteps.length > 0 && (
                  <AgentProgress
                    steps={agentSteps}
                    currentCode={streamingCode}
                    streamingResponse={streamingResponse}
                    isStreaming={isStreaming}
                    retryCount={retryCount}
                    maxRetries={maxRetries}
                  />
                )}
                
                {isLoading && agentSteps.length === 0 && (
                  <div className="flex justify-start">
                    <div className="flex items-center gap-2 text-muted-foreground">
                      <div className="flex gap-1">
                        <div className="w-2 h-2 bg-primary/60 rounded-full animate-bounce"></div>
                        <div
                          className="w-2 h-2 bg-primary/60 rounded-full animate-bounce"
                          style={{ animationDelay: "0.2s" }}
                        ></div>
                        <div
                          className="w-2 h-2 bg-primary/60 rounded-full animate-bounce"
                          style={{ animationDelay: "0.4s" }}
                        ></div>
                      </div>
                    </div>
                  </div>
                )}
                
                <div ref={messagesEndRef} />
              </div>
            )}
          </div>
        </ScrollArea>

        {/* Input area */}
        <div className="border-t border-border bg-background">
          <div className="max-w-7xl mx-auto px-4 py-4">
            <div className="relative flex items-end gap-3">
              <div className="flex-1 relative">
                <div className="relative flex items-center bg-input border border-border rounded-2xl shadow-sm hover:border-primary/50 transition-colors">
                  <Input
                    placeholder={sessionId ? "Faça uma pergunta para comparar os decks..." : "Inicializando modo comparação..."}
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={handleKeyPress}
                    disabled={!sessionId || isLoading}
                    className="border-0 focus-visible:ring-0 focus-visible:ring-offset-0 bg-transparent text-foreground placeholder:text-muted-foreground text-base pr-12 py-3"
                  />
                </div>
              </div>
              <Button
                onClick={handleSendMessage}
                disabled={!sessionId || !input.trim() || isLoading}
                className="bg-primary hover:bg-primary/90 text-primary-foreground h-9 w-9 p-0 rounded-lg flex-shrink-0 disabled:opacity-50 disabled:cursor-not-allowed"
                size="icon"
              >
                <Send className="w-4 h-4" />
              </Button>
            </div>
            <p className="text-xs text-center text-muted-foreground mt-2">
              Todas as respostas incluirão comparação entre Dezembro 2025 e Janeiro 2026
            </p>
          </div>
        </div>
      </div>
    </main>
  );
}

