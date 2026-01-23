"use client";

import React, { useState, useRef, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { ChatMessage } from "@/components/ChatMessage";
import { FileUpload } from "@/components/FileUpload";
import { AgentProgress, AgentStep } from "@/components/AgentProgress";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  sendQueryStream,
  getSession,
  deleteSession,
  reindexDocs,
  loadDeckFromRepo,
  UploadResponse,
  StreamEvent,
} from "@/lib/api";
import { DeckSelector, DeckInfo } from "@/components/DeckSelector";
import { motion } from "framer-motion";
import { Upload, Send, MoreVertical, RefreshCw, Trash2, FileText, ArrowLeft } from "lucide-react";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  rawData?: Record<string, unknown>[] | null;
  retryCount?: number;
  error?: string | null;
  timestamp: Date;
  disambiguationData?: {
    type: string;
    question: string;
    options: Array<{label: string; query: string; tool_name: string}>;
    original_query: string;
    isLoading?: boolean;
    selectedOption?: string;
  };
  requires_user_choice?: boolean;
  alternative_type?: string;
  visualizationData?: {
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
    }>;
    visualization_type?: string;
    tool_name?: string;
    comparison_by_type?: Record<string, unknown>;
    comparison_by_usina?: Record<string, unknown>;
    matrix_data?: Array<{
      nome_usina: string;
      codigo_usina?: number;
      periodo?: string;
      periodo_inicio?: string;
      periodo_fim?: string;
      gtmin_values?: Record<string, number | null>;
      matrix?: Record<string, number | null>;
      value_groups?: Record<string | number, string[]>;
    }>;
    deck_names?: string[];
    deck_displays?: string[];
    deck_count?: number;
    stats?: Record<string, unknown>;
  };
}

export default function AnalysisPage() {
  const router = useRouter();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [selectedDeckInfo, setSelectedDeckInfo] = useState<DeckInfo | null>(null);
  const [files, setFiles] = useState<string[]>([]);
  const [filesCount, setFilesCount] = useState(0);
  const [isReindexing, setIsReindexing] = useState(false);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [isDeckSelectOpen, setIsDeckSelectOpen] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Streaming state
  const [agentSteps, setAgentSteps] = useState<AgentStep[]>([]);
  const [streamingResponse, setStreamingResponse] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
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
  const streamingResponseRef = useRef("");
  const retryCountRef = useRef(0);
  const comparisonDataRef = useRef<Message["comparisonData"]>(null);
  const visualizationDataRef = useRef<Message["visualizationData"]>(null);
  const requiresUserChoiceRef = useRef(false);
  const alternativeTypeRef = useRef<string | undefined>(undefined);
  const disambiguationMessageIdRef = useRef<string | null>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, agentSteps, streamingResponse]);

  // Carregar deck do repositório usando o novo DeckSelector
  const handleDeckSelection = async (decks: DeckInfo[]) => {
    if (decks.length === 0) return;
    
    const deck = decks[0]; // Modo single - apenas um deck
    
    try {
      const data = await loadDeckFromRepo(deck.name);
      setSessionId(data.session_id);
      setFilesCount(data.files_count || 0);
      setSelectedDeckInfo(deck);
      setIsDeckSelectOpen(false);

      setMessages([
        {
          id: Date.now().toString(),
          role: "assistant",
          content: `Deck **${deck.display_name}** carregado do repositório. Faça sua consulta.`,
          timestamp: new Date(),
        },
      ]);
    } catch (err) {
      console.error("Error loading deck:", err);
      setMessages([
        {
          id: Date.now().toString(),
          role: "assistant",
          content: `❌ **Erro ao carregar deck:**\n\n${
            err instanceof Error ? err.message : "Erro desconhecido"
          }`,
          timestamp: new Date(),
        },
      ]);
    }
  };

  const handleUploadSuccess = async (response: UploadResponse) => {
    setSessionId(response.session_id);
    setFilesCount(response.files_count);
    setSelectedDeckInfo(null); // Upload manual, sem DeckInfo

    try {
      const sessionInfo = await getSession(response.session_id);
      setFiles(sessionInfo.files);
    } catch (err) {
      console.error("Error getting session info:", err);
    }

    setMessages([
      {
        id: Date.now().toString(),
        role: "assistant",
        content: `Deck NEWAVE carregado, faça sua consulta.`,
        timestamp: new Date(),
      },
    ]);

    setIsDialogOpen(false);
  };

  const processStreamEvent = useCallback((event: StreamEvent) => {
    switch (event.type) {
      case "start":
        setAgentSteps([]);
        setStreamingResponse("");
        setIsStreaming(true);
        setRetryCount(0);
        setComparisonData(null);
        streamingResponseRef.current = "";
        retryCountRef.current = 0;
        comparisonDataRef.current = null;
        visualizationDataRef.current = null;
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

      case "retry":
        if (event.retry_count !== undefined) {
          setRetryCount(event.retry_count);
          retryCountRef.current = event.retry_count;
          if (event.max_retries) {
            setMaxRetries(event.max_retries);
          }
          
          // Atualizar retryCount na mensagem de disambiguation
          if (disambiguationMessageIdRef.current) {
            setMessages((prevMessages) => prevMessages.map(msg => {
              if (msg.id === disambiguationMessageIdRef.current) {
                return {
                  ...msg,
                  retryCount: event.retry_count,
                };
              }
              return msg;
            }));
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
        console.log("[FRONTEND] response_start recebido");
        setStreamingResponse("");
        streamingResponseRef.current = "";
        break;

      case "response_chunk":
        if (event.chunk) {
          console.log("[FRONTEND] response_chunk recebido:", event.chunk.length, "caracteres");
          setStreamingResponse((prev) => {
            const newResponse = prev + event.chunk;
            streamingResponseRef.current = newResponse;
            
            // Se há uma mensagem de disambiguation em loading, atualizar ela em tempo real
            if (disambiguationMessageIdRef.current) {
              setMessages((prevMessages) => prevMessages.map(msg => {
                if (msg.id === disambiguationMessageIdRef.current) {
                  return {
                    ...msg,
                    content: newResponse,
                    disambiguationData: msg.disambiguationData ? {
                      ...msg.disambiguationData,
                      isLoading: true
                    } : undefined
                  };
                }
                return msg;
              }));
            }
            
            return newResponse;
          });
        }
        break;

      case "response_complete":
        console.log("[FRONTEND] response_complete recebido - evento completo:", {
          has_response: !!event.response,
          response_length: event.response?.length || 0,
          requires_user_choice: event.requires_user_choice,
          alternative_type: event.alternative_type,
          event_keys: Object.keys(event)
        });
        
        if (event.response) {
          setStreamingResponse(event.response);
          streamingResponseRef.current = event.response;
        }
        if (event.requires_user_choice) {
          console.log("[FRONTEND] ✅ requires_user_choice detectado, alternative_type:", event.alternative_type);
          requiresUserChoiceRef.current = true;
          if (event.alternative_type) {
            alternativeTypeRef.current = event.alternative_type;
          }
        } else {
          console.log("[FRONTEND] requires_user_choice NÃO detectado no evento");
          requiresUserChoiceRef.current = false;
          alternativeTypeRef.current = undefined;
        }
        if (event.comparison_data) {
          console.log("[FRONTEND] comparison_data recebido");
          setComparisonData(event.comparison_data);
          comparisonDataRef.current = event.comparison_data;
          
          // Se há uma mensagem de disambiguation em loading, atualizar com comparison_data
          if (disambiguationMessageIdRef.current) {
            setMessages((prevMessages) => prevMessages.map(msg => {
              if (msg.id === disambiguationMessageIdRef.current) {
                return {
                  ...msg,
                  comparisonData: event.comparison_data,
                };
              }
              return msg;
            }));
          }
        }
        
        if (event.visualization_data) {
          console.log("[FRONTEND] visualization_data recebido:", event.visualization_data.tool_name);
          visualizationDataRef.current = event.visualization_data;
          
          // Se há uma mensagem de disambiguation em loading, atualizar com visualization_data
          if (disambiguationMessageIdRef.current) {
            setMessages((prevMessages) => prevMessages.map(msg => {
              if (msg.id === disambiguationMessageIdRef.current) {
                return {
                  ...msg,
                  visualizationData: event.visualization_data,
                };
              }
              return msg;
            }));
          }
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
    streamingResponseRef.current = "";
    requiresUserChoiceRef.current = false;
    alternativeTypeRef.current = undefined;
    setRetryCount(0);
    setComparisonData(null);
    comparisonDataRef.current = null;
    visualizationDataRef.current = null;

    try {
      for await (const event of sendQueryStream(sessionId, userMessage.content)) {
        processStreamEvent(event);
      }

      await new Promise(resolve => setTimeout(resolve, 100));

      let rawData: Record<string, unknown>[] | null = null;

      const hasContent = streamingResponseRef.current && streamingResponseRef.current.trim();
      const hasData = rawData && rawData.length > 0;
      
      if (hasContent || hasData) {
        const assistantMessage: Message = {
          id: (Date.now() + 1).toString(),
          role: "assistant",
          content: streamingResponseRef.current || "",
          rawData: rawData,
          retryCount: retryCountRef.current,
          comparisonData: comparisonDataRef.current || undefined,
          visualizationData: visualizationDataRef.current || undefined,
          requires_user_choice: requiresUserChoiceRef.current ? true : undefined,
          alternative_type: alternativeTypeRef.current,
          timestamp: new Date(),
        };

        setMessages((prev) => [...prev, assistantMessage]);
      }
      
      setAgentSteps([]);
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
    setSelectedDeckInfo(null);
    setFiles([]);
    setFilesCount(0);
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

  const handleDisambiguationOptionClick = async (query: string, messageId?: string) => {
    if (!sessionId) return;
    
    // Encontrar a mensagem de disambiguation e marcar como loading
    const targetMessageId = messageId || (() => {
      const msg = messages.find(m => m.disambiguationData && !m.disambiguationData.isLoading);
      return msg?.id;
    })();
    
    if (targetMessageId) {
      disambiguationMessageIdRef.current = targetMessageId;
      
      // Marcar a mensagem como loading
      setMessages((prev) => prev.map(msg => {
        if (msg.id === targetMessageId && msg.disambiguationData) {
          return {
            ...msg,
            disambiguationData: {
              ...msg.disambiguationData,
              isLoading: true,
              selectedOption: query
            }
          };
        }
        return msg;
      }));
    }
    
    setInput("");
    setIsLoading(true);
    setAgentSteps([]);
        setStreamingResponse("");
    setRetryCount(0);
    setComparisonData(null);
    comparisonDataRef.current = null;
    visualizationDataRef.current = null;

    try {
      for await (const event of sendQueryStream(sessionId, query)) {
        processStreamEvent(event);
      }

      await new Promise(resolve => setTimeout(resolve, 100));

      let rawData: Record<string, unknown>[] | null = null;

      const hasContent = streamingResponseRef.current && streamingResponseRef.current.trim();
      const hasData = rawData && rawData.length > 0;
      const hasComparisonData = comparisonDataRef.current !== null;
      
      // Atualizar a mensagem existente ao invés de criar nova
      // Atualizar sempre que houver qualquer dado, mesmo sem conteúdo de texto
      if (targetMessageId) {
        setMessages((prev) => prev.map(msg => {
          if (msg.id === targetMessageId) {
            return {
              ...msg,
              content: streamingResponseRef.current || "",
              rawData: rawData,
              retryCount: retryCountRef.current,
              comparisonData: comparisonDataRef.current || undefined,
              visualizationData: visualizationDataRef.current || undefined,
              requires_user_choice: requiresUserChoiceRef.current ? true : undefined,
              alternative_type: alternativeTypeRef.current,
              disambiguationData: undefined, // Remover disambiguationData após processar
            };
          }
          return msg;
        }));
      } else {
        // Fallback: criar nova mensagem se não encontrou a mensagem de disambiguation
        if (hasContent || hasData) {
          const assistantMessage: Message = {
            id: (Date.now() + 1).toString(),
            role: "assistant",
            content: streamingResponseRef.current || "",
            rawData: rawData,
            retryCount: retryCountRef.current,
            comparisonData: comparisonDataRef.current || undefined,
            visualizationData: visualizationDataRef.current || undefined,
            requires_user_choice: requiresUserChoiceRef.current ? true : undefined,
            alternative_type: alternativeTypeRef.current,
            timestamp: new Date(),
          };

          setMessages((prev) => [...prev, assistantMessage]);
        }
      }
      
      setAgentSteps([]);
      setStreamingResponse("");
      disambiguationMessageIdRef.current = null;

    } catch (err) {
      // Em caso de erro, atualizar a mensagem de disambiguation com o erro
      if (targetMessageId) {
        setMessages((prev) => prev.map(msg => {
          if (msg.id === targetMessageId) {
            return {
              ...msg,
              content: `❌ **Erro ao processar sua pergunta:**\n\n${
                err instanceof Error ? err.message : "Erro desconhecido"
              }`,
              disambiguationData: undefined,
            };
          }
          return msg;
        }));
      } else {
        const errorMessage: Message = {
          id: (Date.now() + 1).toString(),
          role: "assistant",
          content: `❌ **Erro ao processar sua pergunta:**\n\n${
            err instanceof Error ? err.message : "Erro desconhecido"
          }`,
          timestamp: new Date(),
        };

        setMessages((prev) => [...prev, errorMessage]);
      }
      
      setAgentSteps([]);
      setStreamingResponse("");
      disambiguationMessageIdRef.current = null;
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <main className="flex flex-col h-screen bg-background overflow-hidden">
      {/* Header */}
      <header className="border-b border-border bg-background">
        <div className="max-w-3xl mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => router.push("/")}
              className="h-8 w-8 text-muted-foreground hover:text-foreground hover:bg-muted"
            >
              <ArrowLeft className="w-4 h-4" />
            </Button>
            <h1 className="text-sm font-medium text-foreground">Análise Single Deck</h1>
          </div>
          <div className="flex items-center gap-1">
            {!sessionId && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => setIsDeckSelectOpen(true)}
                className="text-muted-foreground hover:text-foreground"
              >
                Selecionar Deck
              </Button>
            )}
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setIsDialogOpen(true)}
              className="h-8 w-8 text-muted-foreground hover:text-foreground hover:bg-muted"
            >
              <Upload className="w-4 h-4" />
            </Button>
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
                
                {sessionId && (
                  <>
                    <div className="px-2 py-1.5">
                      <p className="text-xs text-muted-foreground font-medium mb-1">Session ID</p>
                      <code className="text-xs bg-background text-foreground px-2 py-1 rounded block overflow-hidden text-ellipsis border border-border font-mono break-all">
                        {sessionId}
                      </code>
                    </div>
                    
                    {(selectedDeckInfo || sessionId) && (
                      <div className="px-2 py-1.5">
                        <p className="text-xs text-muted-foreground font-medium mb-1">Deck Selecionado</p>
                        <p className="text-xs text-foreground">
                          {selectedDeckInfo 
                            ? `${selectedDeckInfo.display_name} (${selectedDeckInfo.name})`
                            : "Upload Manual"}
                        </p>
                      </div>
                    )}
                    
                    {filesCount > 0 && (
                      <div className="px-2 py-1.5">
                        <p className="text-xs text-muted-foreground font-medium mb-2">
                          Arquivos ({filesCount})
                        </p>
                        <div className="max-h-32 overflow-y-auto space-y-1">
                          {files.slice(0, 10).map((file, index) => (
                            <div
                              key={index}
                              className="text-xs bg-background px-2 py-1 rounded flex items-center gap-2 border border-border"
                            >
                              <FileText className="w-3 h-3 text-muted-foreground flex-shrink-0" />
                              <span className="truncate text-foreground">{file}</span>
                            </div>
                          ))}
                          {files.length > 10 && (
                            <p className="text-xs text-muted-foreground italic pl-2">
                              +{files.length - 10} arquivos...
                            </p>
                          )}
                        </div>
                      </div>
                    )}
                    
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
          <div className="max-w-3xl mx-auto py-12 px-4">
            {messages.length === 0 && !isLoading ? (
              <div className="flex flex-col items-center justify-center text-center">
                <h2 className="text-4xl font-semibold mb-4 text-foreground">
                  Análise Single Deck
                </h2>
                <p className="text-muted-foreground mb-8 text-lg">
                  {!sessionId 
                    ? "Selecione um deck do repositório ou faça upload de um deck para começar"
                    : "Faça sua consulta sobre o deck carregado"}
                </p>
                {!sessionId && (
                  <div className="flex gap-4">
                    <Button 
                      onClick={() => setIsDeckSelectOpen(true)}
                      className="bg-primary hover:bg-primary/90 text-primary-foreground"
                    >
                      Selecionar Deck do Repositório
                    </Button>
                    <Button 
                      onClick={() => setIsDialogOpen(true)}
                      variant="outline"
                    >
                      <Upload className="w-4 h-4 mr-2" />
                      Upload do Deck
                    </Button>
                  </div>
                )}
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
                
                {isLoading && agentSteps.length > 0 && !messages.some(msg => msg.disambiguationData?.isLoading) && (
                  <AgentProgress
                    steps={agentSteps}
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
          <div className="max-w-3xl mx-auto px-4 py-4">
            <div className="relative flex items-end gap-3">
              <div className="flex-1 relative">
                <div className="relative flex items-center bg-input border border-border rounded-2xl shadow-sm hover:border-primary/50 transition-colors">
                  <Input
                    placeholder={sessionId ? "Faça uma pergunta sobre os dados..." : "Selecione um deck ou faça upload para começar"}
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
              NEWAVE Agent pode cometer erros. Verifique informações importantes.
            </p>
          </div>
        </div>
      </div>

      {/* Upload Dialog */}
      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        <DialogContent className="bg-card border-border">
          <DialogHeader>
            <DialogTitle className="text-card-foreground">Upload do Deck NEWAVE</DialogTitle>
          </DialogHeader>
          <FileUpload onUploadSuccess={handleUploadSuccess} />
        </DialogContent>
      </Dialog>

      {/* Deck Selection using DeckSelector component */}
      <DeckSelector
        mode="single"
        open={isDeckSelectOpen}
        onOpenChange={setIsDeckSelectOpen}
        onSelect={handleDeckSelection}
        initialSelected={selectedDeckInfo ? [selectedDeckInfo.name] : []}
        title="Selecionar Deck para Análise"
        description="Escolha um deck do repositório para analisar"
      />
    </main>
  );
}

