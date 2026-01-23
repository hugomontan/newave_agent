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
import { DeckSelector, SelectedDecksDisplay, DeckInfo } from "@/components/DeckSelector";
import {
  sendQueryStream,
  deleteSession,
  reindexDocs,
  initComparison,
  StreamEvent,
} from "@/lib/api";
import { motion } from "framer-motion";
import { Send, MoreVertical, RefreshCw, Trash2, ArrowLeft, GitCompare, Settings } from "lucide-react";

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
    comparison_by_type?: Record<string, unknown>;
    comparison_by_usina?: Record<string, unknown>;
    stats?: Record<string, unknown>;
  };
}

export default function ComparisonPage() {
  const router = useRouter();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [isReindexing, setIsReindexing] = useState(false);
  const [selectedDecks, setSelectedDecks] = useState<DeckInfo[]>([]);
  const [isDeckSelectorOpen, setIsDeckSelectorOpen] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Streaming state
  const [agentSteps, setAgentSteps] = useState<AgentStep[]>([]);
  const [streamingResponse, setStreamingResponse] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [retryCount, setRetryCount] = useState(0);
  const [maxRetries, setMaxRetries] = useState(3);
  const [comparisonData, setComparisonData] = useState<Message["comparisonData"] | null>(null);
  const [disambiguationData, setDisambiguationData] = useState<{
    type: string;
    question: string;
    options: Array<{label: string; query: string; tool_name: string}>;
    original_query: string;
  } | null>(null);

  // Refs para capturar estado durante streaming
  const streamingResponseRef = useRef("");
  const retryCountRef = useRef(0);
  const comparisonDataRef = useRef<Message["comparisonData"] | null>(null);
  const disambiguationMessageIdRef = useRef<string | null>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, agentSteps, streamingResponse]);

  // Script para limpar overlays órfãos que podem estar bloqueando
  useEffect(() => {
    const cleanupOverlays = () => {
      if (!isDeckSelectorOpen && !isLoading) {
        // Aguardar um pouco para garantir que animações do dialog terminaram
        setTimeout(() => {
          const overlays = document.querySelectorAll('[data-radix-dialog-overlay]');
          overlays.forEach((overlay) => {
            const style = window.getComputedStyle(overlay);
            // Se o overlay está visível mas o dialog está fechado, pode ser órfão
            if (style.display !== 'none' && !isDeckSelectorOpen) {
              const dialog = overlay.closest('[data-radix-dialog-content]');
              if (!dialog || dialog.getAttribute('data-state') === 'closed') {
                console.warn("[ComparisonPage] Removendo overlay órfão");
                (overlay as HTMLElement).style.display = 'none';
                overlay.remove();
              }
            }
          });
          
          // Verificar se há elementos bloqueando interação
          const body = document.body;
          const bodyStyle = window.getComputedStyle(body);
          if (bodyStyle.pointerEvents === 'none' || bodyStyle.overflow === 'hidden') {
            console.warn("[ComparisonPage] ⚠️ Body está bloqueado! Corrigindo...");
            body.style.pointerEvents = 'auto';
            body.style.overflow = 'auto';
          }
        }, 500);
      }
    };

    cleanupOverlays();
    // Executar periodicamente para limpar overlays órfãos
    const interval = setInterval(cleanupOverlays, 2000);
    
    // Expor função global para debug
    (window as any).debugComparisonPage = {
      cleanupOverlays,
      focusInput: () => {
        const inputElement = document.querySelector('input[placeholder*="pergunta"]') as HTMLInputElement;
        if (inputElement) {
          inputElement.focus();
          inputElement.click();
          console.log("Input focado:", inputElement === document.activeElement);
        }
      },
      checkBlocking: () => {
        const inputElement = document.querySelector('input[placeholder*="pergunta"]') as HTMLInputElement;
        if (inputElement) {
          const rect = inputElement.getBoundingClientRect();
          const centerX = rect.left + rect.width / 2;
          const centerY = rect.top + rect.height / 2;
          const elementAtPoint = document.elementFromPoint(centerX, centerY);
          console.log("Elemento no centro do input:", elementAtPoint);
          return elementAtPoint;
        }
      },
      removeAllOverlays: () => {
        const overlays = document.querySelectorAll('[data-radix-dialog-overlay]');
        overlays.forEach(overlay => overlay.remove());
        console.log(`Removidos ${overlays.length} overlays`);
      }
    };
    
    return () => {
      clearInterval(interval);
      delete (window as any).debugComparisonPage;
    };
  }, [isDeckSelectorOpen, isLoading]);

  // Mecanismo de segurança: resetar isLoading se ficar travado por muito tempo
  useEffect(() => {
    if (isLoading) {
      const timeout = setTimeout(() => {
        console.warn("[ComparisonPage] ⚠️ isLoading ficou true por mais de 60 segundos - resetando forçadamente");
        setIsLoading(false);
        setIsStreaming(false);
        // Limpar overlays que podem estar bloqueando
        const overlays = document.querySelectorAll('[data-radix-dialog-overlay]');
        overlays.forEach((overlay) => {
          const style = window.getComputedStyle(overlay);
          if (style.display !== 'none' && !isDeckSelectorOpen) {
            (overlay as HTMLElement).style.display = 'none';
            overlay.remove();
          }
        });
      }, 60000); // 60 segundos
      
      return () => clearTimeout(timeout);
    }
  }, [isLoading, isDeckSelectorOpen]);

  // Debug: monitorar mudanças no sessionId e isLoading
  useEffect(() => {
    console.log("[ComparisonPage] Estado atualizado - sessionId:", sessionId, "isLoading:", isLoading, "selectedDecks:", selectedDecks.length, "isDeckSelectorOpen:", isDeckSelectorOpen);
    
    // Verificar e limpar overlays órfãos que podem estar bloqueando
    if (!isDeckSelectorOpen && sessionId) {
      // Pequeno delay para garantir que o dialog foi completamente removido do DOM
      setTimeout(() => {
        const overlays = document.querySelectorAll('[data-radix-dialog-overlay]');
        console.log("[ComparisonPage] Overlays encontrados:", overlays.length);
        
        overlays.forEach((overlay, index) => {
          const style = window.getComputedStyle(overlay);
          const isVisible = style.display !== 'none' && style.visibility !== 'hidden';
          console.log(`[ComparisonPage] Overlay ${index}: display=${style.display}, pointer-events=${style.pointerEvents}, z-index=${style.zIndex}, visible=${isVisible}`);
          
          // Se o overlay está visível mas o dialog está fechado, pode ser um overlay órfão
          if (isVisible && !isDeckSelectorOpen) {
            console.warn(`[ComparisonPage] ⚠️ Overlay ${index} pode ser órfão! Tentando remover...`);
            // Não remover automaticamente, apenas logar - pode ser necessário para animações
          }
        });
        
        // Verificar elementos bloqueando o input
        const inputElement = document.querySelector('input[placeholder*="pergunta"]') as HTMLInputElement;
        if (inputElement) {
          const rect = inputElement.getBoundingClientRect();
          const centerX = rect.left + rect.width / 2;
          const centerY = rect.top + rect.height / 2;
          const elementAtPoint = document.elementFromPoint(centerX, centerY);
          console.log("[ComparisonPage] Elemento no centro do input:", elementAtPoint?.tagName, elementAtPoint?.className);
          
          if (elementAtPoint !== inputElement && !inputElement.contains(elementAtPoint)) {
            console.warn("[ComparisonPage] ⚠️ Há um elemento bloqueando o input!", elementAtPoint);
            const blockingStyle = window.getComputedStyle(elementAtPoint as Element);
            console.log("[ComparisonPage] Estilo do elemento bloqueante:", {
              position: blockingStyle.position,
              zIndex: blockingStyle.zIndex,
              pointerEvents: blockingStyle.pointerEvents,
              display: blockingStyle.display
            });
          }
        }
      }, 300);
    }
  }, [sessionId, isLoading, selectedDecks, isDeckSelectorOpen]);

  // Função para inicializar comparação com os decks selecionados
  const initializeComparisonWithDecks = async (decks: DeckInfo[]) => {
    console.log("[ComparisonPage] ========== INICIANDO initializeComparisonWithDecks ==========");
    console.log("[ComparisonPage] Decks recebidos:", decks);
    console.log("[ComparisonPage] Número de decks:", decks.length);
    
    if (!decks || decks.length === 0) {
      console.error("[ComparisonPage] ⚠️ Nenhum deck fornecido!");
      return;
    }
    
    try {
      console.log("[ComparisonPage] Definindo isLoading = true");
      setIsLoading(true);
      
      const deckNames = decks.map(d => d.name);
      console.log("[ComparisonPage] Deck names extraídos:", deckNames);
      
      console.log("[ComparisonPage] Chamando initComparison API...");
      const startTime = Date.now();
      const data = await initComparison(deckNames);
      const duration = Date.now() - startTime;
      console.log("[ComparisonPage] initComparison retornou em", duration, "ms:", data);
      
      if (!data || !data.session_id) {
        throw new Error("Resposta da API não contém session_id");
      }
      
      console.log("[ComparisonPage] Definindo sessionId:", data.session_id);
      setSessionId(data.session_id);
      setSelectedDecks(decks);
      
      // Forçar atualização do estado
      console.log("[ComparisonPage] Estado atualizado - sessionId:", data.session_id, "selectedDecks:", decks.length);
      
      // Pequeno delay para garantir que o estado foi atualizado
      await new Promise(resolve => setTimeout(resolve, 100));

      const deckList = decks.map(d => `**${d.display_name}**`).join(", ");
      const analysisType = decks.length > 2 
        ? `análise histórica de ${decks.length} meses`
        : "comparação direta";

      setMessages([
        {
          id: Date.now().toString(),
          role: "assistant",
          content: `Modo Comparação ativado! Todas as consultas realizarão ${analysisType} entre os decks:\n\n${deckList}\n\nFaça sua primeira consulta para ver os resultados lado a lado com gráficos comparativos.`,
          timestamp: new Date(),
        },
      ]);
      
      console.log("[ComparisonPage] ✅ Inicialização concluída com sucesso");
    } catch (err) {
      console.error("[ComparisonPage] ❌ Error initializing comparison:", err);
      console.error("[ComparisonPage] Stack trace:", err instanceof Error ? err.stack : "N/A");
      
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
      
      // Em caso de erro, garantir que o estado não fique bloqueado
      setSessionId(null);
      setSelectedDecks([]);
    } finally {
      console.log("[ComparisonPage] Definindo isLoading = false");
      setIsLoading(false);
      console.log("[ComparisonPage] ========== FINALIZANDO initializeComparisonWithDecks ==========");
    }
  };

  // Abrir seletor de decks ao montar (sem decks pré-selecionados)
  useEffect(() => {
    console.log("[ComparisonPage] useEffect de inicialização executado");
    // Inicializar com os 2 decks mais recentes por padrão
    const initializeDefault = async () => {
      try {
        console.log("[ComparisonPage] Inicializando com decks padrão...");
        setIsLoading(true);
        const data = await initComparison();
        console.log("[ComparisonPage] initComparison retornou:", data);
        
        setSessionId(data.session_id);
        setSelectedDecks(data.selected_decks);
        console.log("[ComparisonPage] Estado inicial definido - sessionId:", data.session_id);

        const deckList = data.selected_decks.map(d => `**${d.display_name}**`).join(", ");
        
        setMessages([
          {
            id: Date.now().toString(),
            role: "assistant",
            content: `Modo Comparação ativado! Comparando os decks:\n\n${deckList}\n\nVocê pode alterar os decks clicando em "Alterar Decks" no menu. Faça sua primeira consulta para ver os resultados lado a lado com gráficos comparativos.`,
            timestamp: new Date(),
          },
        ]);
      } catch (err) {
        console.error("[ComparisonPage] Error initializing comparison:", err);
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
      } finally {
        setIsLoading(false);
        console.log("[ComparisonPage] Inicialização concluída - isLoading: false");
      }
    };

    initializeDefault();
  }, []);

  const processStreamEvent = useCallback((event: StreamEvent) => {
    switch (event.type) {
      case "start":
        setAgentSteps([]);
        setStreamingResponse("");
        setIsStreaming(true);
        setRetryCount(0);
        setComparisonData(null as any);
        streamingResponseRef.current = "";
        retryCountRef.current = 0;
        comparisonDataRef.current = null as any;
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


      case "execution_result":
        // Evento não mais usado - código removido
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
              node: `retry_${event.retry_count || 0}`,
              name: `Tentativa ${(event.retry_count || 0) + 1}/${event.max_retries || 3}`,
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
        if (event.response) {
          setStreamingResponse(event.response);
          streamingResponseRef.current = event.response;
        }
        if (event.comparison_data) {
          setComparisonData(event.comparison_data as any);
          comparisonDataRef.current = event.comparison_data as any;
          
          // Se há uma mensagem de disambiguation em loading, atualizar com comparison_data
          if (disambiguationMessageIdRef.current) {
            setMessages((prevMessages) => prevMessages.map(msg => {
              if (msg.id === disambiguationMessageIdRef.current) {
                return {
                  ...msg,
                  comparisonData: event.comparison_data as any,
                } as Message;
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
        // Garantir que isLoading seja resetado quando o streaming terminar
        // Isso previne que a interface fique travada se houver algum problema
        setTimeout(() => {
          setIsLoading(false);
        }, 100);
        break;

      case "error":
        setIsStreaming(false);
        // Garantir que isLoading seja resetado em caso de erro
        setTimeout(() => {
          setIsLoading(false);
        }, 100);
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
      let rawData: Record<string, unknown>[] | null = null;
      try {
          // Tentar extrair rawData de outras fontes se necessário
          // Removido: código não mais usado
          if (false) {
          if (jsonMatch) {
            rawData = JSON.parse(jsonMatch[1].trim());
          }
        } catch {
          // Ignora erro de parsing
        }
      }

      const hasContent = streamingResponseRef.current && streamingResponseRef.current.trim();
      const hasData = rawData && rawData.length > 0;
      if (hasContent || hasData || comparisonDataRef.current) {
        const currentComparisonData = comparisonDataRef.current as Message["comparisonData"] | null;
        
        const assistantMessage: Message = {
          id: (Date.now() + 1).toString(),
          role: "assistant",
          content: streamingResponseRef.current || "",
          rawData: rawData,
          retryCount: retryCountRef.current,
          comparisonData: currentComparisonData || undefined,
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
      let rawData: Record<string, unknown>[] | null = null;
      try {
          // Tentar extrair rawData de outras fontes se necessário
          // Removido: código não mais usado
          if (false) {
          if (jsonMatch) {
            rawData = JSON.parse(jsonMatch[1].trim());
          }
        } catch {
          // Ignora erro de parsing
        }
      }

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
              disambiguationData: undefined, // Remover disambiguationData após processar
            };
          }
          return msg;
        }));
      } else {
        // Fallback: criar nova mensagem se não encontrou a mensagem de disambiguation
        if (hasContent || hasData || comparisonDataRef.current) {
          const assistantMessage: Message = {
            id: (Date.now() + 1).toString(),
            role: "assistant",
            content: streamingResponseRef.current || "",
            rawData: rawData,
            retryCount: retryCountRef.current,
            comparisonData: comparisonDataRef.current || undefined,
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
      setIsStreaming(false);
      // Limpar overlays órfãos que podem estar bloqueando
      setTimeout(() => {
        const overlays = document.querySelectorAll('[data-radix-dialog-overlay]');
        overlays.forEach((overlay) => {
          const style = window.getComputedStyle(overlay);
          // Se o overlay está visível mas não há dialog aberto, remover
          if (style.display !== 'none' && !isDeckSelectorOpen) {
            const dialog = overlay.closest('[data-radix-dialog-content]');
            if (!dialog || dialog.getAttribute('data-state') === 'closed') {
              console.warn("[ComparisonPage] Removendo overlay órfão após disambiguation");
              (overlay as HTMLElement).style.display = 'none';
              overlay.remove();
            }
          }
        });
        // Forçar foco no input após limpar overlays
        const inputElement = document.querySelector('input[placeholder*="pergunta"]') as HTMLInputElement;
        if (inputElement && !inputElement.disabled) {
          inputElement.focus();
        }
      }, 200);
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
                  <p className="text-xs text-foreground">
                    Comparação de {selectedDecks.length} Deck{selectedDecks.length !== 1 ? 's' : ''}
                  </p>
                  {selectedDecks.length > 0 && (
                    <div className="mt-2">
                      <SelectedDecksDisplay decks={selectedDecks} compact />
                    </div>
                  )}
                </div>
                
                <DropdownMenuItem
                  onSelect={() => setIsDeckSelectorOpen(true)}
                  className="cursor-pointer text-foreground focus:bg-muted"
                >
                  <Settings className="w-4 h-4 mr-2" />
                  Alterar Decks
                </DropdownMenuItem>
                
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
      <div className="flex-1 flex flex-col overflow-hidden" style={{ position: 'relative', zIndex: 1 }}>
        <ScrollArea className="flex-1" style={{ position: 'relative', zIndex: 1 }}>
          <div className="max-w-7xl mx-auto py-12 px-4" style={{ position: 'relative', zIndex: 1 }}>
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
        <div 
          className="border-t border-border bg-background"
          style={{ zIndex: 10, position: 'relative' }}
        >
          <div className="max-w-7xl mx-auto px-4 py-4" style={{ position: 'relative', zIndex: 10 }}>
            {/* Debug info */}
            {process.env.NODE_ENV === 'development' && (
              <div className="mb-2 text-xs text-muted-foreground">
                Debug: sessionId={sessionId ? "✓" : "✗"}, isLoading={isLoading ? "✓" : "✗"}, 
                isDeckSelectorOpen={isDeckSelectorOpen ? "✓" : "✗"}, 
                selectedDecks={selectedDecks.length}
              </div>
            )}
            <div 
              className="relative flex items-end gap-3" 
              style={{ zIndex: 1000, position: 'relative' }}
              onMouseDown={(e) => {
                // Se clicou na área do input mas não no input em si, forçar foco
                const target = e.target as HTMLElement;
                const inputElement = target.closest('div')?.querySelector('input') as HTMLInputElement;
                if (inputElement && !inputElement.disabled && target.tagName !== 'INPUT') {
                  console.log("[ComparisonPage] Área do input clicada - forçando foco");
                  e.preventDefault();
                  e.stopPropagation();
                  setTimeout(() => {
                    inputElement.focus();
                    inputElement.click();
                  }, 0);
                }
              }}
            >
              <div className="flex-1 relative" style={{ zIndex: 1000 }}>
                <div 
                  className="relative flex items-center bg-input border border-border rounded-2xl shadow-sm hover:border-primary/50 transition-colors"
                  style={{ 
                    zIndex: 1000, 
                    pointerEvents: 'auto',
                    position: 'relative'
                  }}
                  onClick={(e) => {
                    console.log("[ComparisonPage] Container do input clicado");
                    e.stopPropagation();
                    // Se clicou no container mas não no input, focar no input
                    const inputElement = e.currentTarget.querySelector('input') as HTMLInputElement;
                    if (inputElement && !inputElement.disabled) {
                      console.log("[ComparisonPage] Focando no input programaticamente");
                      setTimeout(() => {
                        inputElement.focus();
                        inputElement.click();
                      }, 0);
                    }
                  }}
                  onMouseDown={(e) => {
                    console.log("[ComparisonPage] Container onMouseDown");
                    const inputElement = e.currentTarget.querySelector('input') as HTMLInputElement;
                    if (inputElement && !inputElement.disabled && e.target !== inputElement) {
                      console.log("[ComparisonPage] MouseDown no container - redirecionando para input");
                      e.preventDefault();
                      e.stopPropagation();
                      setTimeout(() => {
                        inputElement.focus();
                        inputElement.click();
                      }, 0);
                    }
                  }}
                >
                  <Input
                    id="comparison-input"
                    placeholder={sessionId ? "Faça uma pergunta para comparar os decks..." : "Inicializando modo comparação..."}
                    value={input}
                    onChange={(e) => {
                      console.log("[ComparisonPage] Input onChange:", e.target.value);
                      setInput(e.target.value);
                    }}
                    onKeyDown={handleKeyPress}
                    disabled={!sessionId || isLoading || isDeckSelectorOpen}
                    className="border-0 focus-visible:ring-0 focus-visible:ring-offset-0 bg-transparent text-foreground placeholder:text-muted-foreground text-base pr-12 py-3"
                    style={{ 
                      zIndex: 1001, 
                      pointerEvents: (!sessionId || isLoading || isDeckSelectorOpen) ? 'none' : 'auto',
                      cursor: (!sessionId || isLoading || isDeckSelectorOpen) ? 'not-allowed' : 'text',
                      position: 'relative'
                    }}
                    onFocus={(e) => {
                      console.log("[ComparisonPage] ✅ Input recebeu foco!");
                      console.log("[ComparisonPage] sessionId:", sessionId);
                      console.log("[ComparisonPage] isLoading:", isLoading);
                      console.log("[ComparisonPage] disabled:", !sessionId || isLoading || isDeckSelectorOpen);
                      console.log("[ComparisonPage] isDeckSelectorOpen:", isDeckSelectorOpen);
                      e.stopPropagation();
                    }}
                    onBlur={() => {
                      console.log("[ComparisonPage] Input perdeu foco");
                    }}
                    onMouseDown={(e) => {
                      console.log("[ComparisonPage] ✅ Input onMouseDown - evento capturado!");
                      if (!sessionId || isLoading || isDeckSelectorOpen) {
                        console.warn("[ComparisonPage] ⚠️ MouseDown bloqueado - input está disabled");
                        e.preventDefault();
                        e.stopPropagation();
                        return;
                      }
                      e.stopPropagation();
                    }}
                    onClick={(e) => {
                      console.log("[ComparisonPage] ✅ Input clicado!");
                      console.log("[ComparisonPage] sessionId:", sessionId);
                      console.log("[ComparisonPage] isLoading:", isLoading);
                      console.log("[ComparisonPage] isDeckSelectorOpen:", isDeckSelectorOpen);
                      if (!sessionId) {
                        console.warn("[ComparisonPage] ⚠️ Input clicado mas sessionId é null!");
                        e.preventDefault();
                        e.stopPropagation();
                        return;
                      }
                      e.stopPropagation();
                    }}
                    onPointerDown={(e) => {
                      console.log("[ComparisonPage] Input onPointerDown");
                      e.stopPropagation();
                    }}
                    tabIndex={(!sessionId || isLoading || isDeckSelectorOpen) ? -1 : 0}
                  />
                </div>
              </div>
              <Button
                onClick={() => {
                  console.log("[ComparisonPage] Botão Send clicado");
                  console.log("[ComparisonPage] sessionId:", sessionId);
                  console.log("[ComparisonPage] input:", input);
                  console.log("[ComparisonPage] isLoading:", isLoading);
                  handleSendMessage();
                }}
                disabled={!sessionId || !input.trim() || isLoading || isDeckSelectorOpen}
                className="bg-primary hover:bg-primary/90 text-primary-foreground h-9 w-9 p-0 rounded-lg flex-shrink-0 disabled:opacity-50 disabled:cursor-not-allowed"
                size="icon"
                title={!sessionId ? "Aguardando inicialização..." : isLoading ? "Processando..." : !input.trim() ? "Digite uma pergunta" : "Enviar"}
              >
                <Send className="w-4 h-4" />
              </Button>
            </div>
            <p className="text-xs text-center text-muted-foreground mt-2">
              {selectedDecks.length > 2 
                ? `Análise histórica de ${selectedDecks.length} decks (${selectedDecks[0]?.display_name} a ${selectedDecks[selectedDecks.length - 1]?.display_name})`
                : selectedDecks.length === 2
                  ? `Comparação entre ${selectedDecks[0]?.display_name} e ${selectedDecks[1]?.display_name}`
                  : "Selecione os decks para comparação"}
            </p>
          </div>
        </div>
      </div>

      {/* Deck Selector Dialog */}
      <DeckSelector
        mode="multi"
        open={isDeckSelectorOpen}
        onOpenChange={(open) => {
          console.log("[ComparisonPage] DeckSelector onOpenChange:", open);
          setIsDeckSelectorOpen(open);
          // Se o dialog está fechando, garantir que isLoading não está bloqueando
          if (!open) {
            console.log("[ComparisonPage] Dialog fechado - verificando estado");
            // Pequeno delay para garantir que o overlay foi removido
            setTimeout(() => {
              console.log("[ComparisonPage] Após fechar dialog - sessionId:", sessionId, "isLoading:", isLoading);
            }, 200);
          }
        }}
        onSelect={(decks) => {
          console.log("[ComparisonPage] DeckSelector onSelect chamado com:", decks);
          initializeComparisonWithDecks(decks);
        }}
        initialSelected={selectedDecks.map(d => d.name)}
        title="Selecionar Decks para Comparação"
        description="Selecione os decks que deseja comparar. Para análise histórica, selecione múltiplos decks consecutivos."
      />
    </main>
  );
}

