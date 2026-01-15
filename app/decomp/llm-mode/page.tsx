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
import { FileUploadDecomp } from "@/components/FileUploadDecomp";
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
  queryDecompStream,
  getSession,
  deleteSession,
  reindexDecompDocs,
  loadDecompDeckFromRepo,
  UploadResponse,
  StreamEvent,
} from "@/lib/api";
import { motion } from "framer-motion";
import { Upload, Send, MoreVertical, RefreshCw, Trash2, FileText, ArrowLeft, Brain } from "lucide-react";

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
}

export default function LLMModePage() {
  const router = useRouter();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [selectedDeck, setSelectedDeck] = useState<"december" | "january" | "upload" | null>(null);
  const [files, setFiles] = useState<string[]>([]);
  const [filesCount, setFilesCount] = useState(0);
  const [isReindexing, setIsReindexing] = useState(false);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [isDeckSelectOpen, setIsDeckSelectOpen] = useState(false);
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

  // Refs para capturar estado durante streaming
  const streamingCodeRef = useRef("");
  const streamingResponseRef = useRef("");
  const executionSuccessRef = useRef<boolean | null>(null);
  const executionErrorRef = useRef<string | null>(null);
  const executionOutputRef = useRef<string | null>(null);
  const retryCountRef = useRef(0);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, agentSteps, streamingCode, streamingResponse]);

  const loadDeckFromRepo = async (deck: "december" | "january") => {
    try {
      // Por enquanto, usar nomes genéricos - adaptar quando houver decks DECOMP reais
      const deckName = deck === "december" ? "DC202512" : "DC202601";
      const data = await loadDecompDeckFromRepo(deckName);
      setSessionId(data.session_id);
      setSelectedDeck(deck);
      setFiles([]);
      setFilesCount(data.files_count || 0);

      setMessages([
        {
          id: Date.now().toString(),
          role: "assistant",
          content: `✅ **Deck DECOMP carregado com sucesso!**\n\n**Deck:** ${deck === "december" ? "Dezembro 2025" : "Janeiro 2026"}\n**Arquivos:** ${data.files_count || 0}\n\nAgora você pode fazer consultas usando o **LLM Mode**. Este modo oferece mais liberdade para o LLM codar e entender o projeto, usando RAG completo e LLM Planner.`,
          timestamp: new Date(),
        },
      ]);
    } catch (err) {
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
    } finally {
      setIsDeckSelectOpen(false);
    }
  };

  const handleUploadSuccess = (response: UploadResponse) => {
    setSessionId(response.session_id);
    setSelectedDeck("upload");
    setFilesCount(response.files_count);
    setMessages([
      {
        id: Date.now().toString(),
        role: "assistant",
        content: `✅ **Deck carregado com sucesso!**\n\n**Arquivos:** ${response.files_count}\n\nAgora você pode fazer consultas usando o **LLM Mode**. Este modo oferece mais liberdade para o LLM codar e entender o projeto, usando RAG completo e LLM Planner.`,
        timestamp: new Date(),
      },
    ]);
    setIsDialogOpen(false);
  };

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
        streamingCodeRef.current = "";
        streamingResponseRef.current = "";
        executionSuccessRef.current = null;
        executionErrorRef.current = null;
        executionOutputRef.current = null;
        retryCountRef.current = 0;
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

    try {
      // Usar analysis_mode="llm" para LLM Mode
      for await (const event of queryDecompStream(sessionId, userMessage.content, "llm")) {
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
      
      if (hasContent || hasData || hasCode) {
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
        await deleteSession(sessionId, "decomp");
      } catch (err) {
        console.error("Error deleting session:", err);
      }
    }

    setSessionId(null);
    setSelectedDeck(null);
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

  return (
    <main className="flex flex-col h-screen bg-background overflow-hidden">
      {/* Header */}
      <header className="border-b border-border bg-background">
        <div className="max-w-3xl mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => router.push("/decomp")}
              className="h-8 w-8 text-muted-foreground hover:text-foreground hover:bg-muted"
            >
              <ArrowLeft className="w-4 h-4" />
            </Button>
            <div className="flex items-center gap-2">
              <Brain className="w-5 h-5 text-primary" />
              <h1 className="text-sm font-medium text-foreground">LLM Mode</h1>
            </div>
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
                    
                    {selectedDeck && (
                      <div className="px-2 py-1.5">
                        <p className="text-xs text-muted-foreground font-medium mb-1">Deck Selecionado</p>
                        <p className="text-xs text-foreground">
                          {selectedDeck === "december" ? "Dezembro 2025 (NW202512)" : 
                           selectedDeck === "january" ? "Janeiro 2026 (NW202601)" : 
                           "Upload Manual"}
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
                <div className="flex items-center gap-3 mb-4">
                  <Brain className="w-12 h-12 text-primary" />
                  <h2 className="text-4xl font-semibold text-foreground">
                    LLM Mode
                  </h2>
                </div>
                <p className="text-muted-foreground mb-4 text-lg">
                  Modo avançado com RAG completo e LLM Planner
                </p>
                <p className="text-muted-foreground mb-8 text-base max-w-2xl">
                  {!sessionId 
                    ? "Selecione um deck do repositório ou faça upload de um deck para começar. O LLM Mode oferece mais liberdade para o LLM codar e entender o projeto, usando RAG completo em toda documentação + tools_context.md e um LLM Planner que gera instruções detalhadas."
                    : "Faça sua consulta sobre o deck carregado. O LLM Mode não usa tools pré-programadas - o LLM gera código diretamente baseado no contexto completo."}
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
              LLM Mode - NEWAVE Agent pode cometer erros. Verifique informações importantes.
            </p>
          </div>
        </div>
      </div>

      {/* Upload Dialog */}
      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        <DialogContent className="bg-card border-border">
          <DialogHeader>
            <DialogTitle className="text-card-foreground">Upload do Deck DECOMP</DialogTitle>
          </DialogHeader>
          <FileUploadDecomp onUploadSuccess={handleUploadSuccess} />
        </DialogContent>
      </Dialog>

      {/* Deck Selection Dialog */}
      <Dialog open={isDeckSelectOpen} onOpenChange={setIsDeckSelectOpen}>
        <DialogContent className="bg-card border-border">
          <DialogHeader>
            <DialogTitle className="text-card-foreground">Selecionar Deck do Repositório</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <Button
              onClick={() => loadDeckFromRepo("december")}
              className="w-full"
              variant="outline"
            >
              Dezembro 2025 (NW202512)
            </Button>
            <Button
              onClick={() => loadDeckFromRepo("january")}
              className="w-full"
              variant="outline"
            >
              Janeiro 2026 (NW202601)
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </main>
  );
}

