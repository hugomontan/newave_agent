"use client";

import React, { useState, useRef, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { ChatMessage } from "@/components/ChatMessage";
import { AgentProgress, AgentStep } from "@/components/AgentProgress";
import {
  sendQueryStream,
  StreamEvent,
  uploadDeck,
  getSession,
  UploadResponse,
} from "@/lib/api";
import { motion } from "framer-motion";
import { Send, ArrowLeft, MessageSquare, Upload, FolderOpen } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { FileUpload } from "@/components/FileUpload";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
}

export default function LLMPage() {
  const router = useRouter();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [selectedDeck, setSelectedDeck] = useState<"december" | "january" | "upload" | null>(null);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [isDeckSelectOpen, setIsDeckSelectOpen] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Streaming state
  const [agentSteps, setAgentSteps] = useState<AgentStep[]>([]);
  const [streamingResponse, setStreamingResponse] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);

  // Refs para capturar estado durante streaming
  const streamingResponseRef = useRef("");

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, streamingResponse]);

  const processStreamEvent = useCallback((event: StreamEvent) => {
    switch (event.type) {
      case "start":
        setIsStreaming(true);
        setAgentSteps([]);
        setStreamingResponse("");
        streamingResponseRef.current = "";
        break;

      case "node_start":
        if (event.node && event.info) {
          setAgentSteps((prev) => [
            ...prev.filter((s) => s.name !== event.info!.name),
            {
              node: event.node || "",
              name: event.info!.name,
              icon: event.info!.icon,
              description: event.info!.description,
              status: "running",
            },
          ]);
        }
        break;

      case "node_complete":
        if (event.node && event.info) {
          setAgentSteps((prev) =>
            prev.map((step) =>
              step.name === event.info!.name
                ? { ...step, status: "completed" as const }
                : step
            )
          );
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
        break;
    }
  }, []);

  // Carregar deck do repositório
  const loadDeckFromRepo = async (deckName: "december" | "january") => {
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/load-deck`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          deck_name: deckName === "december" ? "NW202512" : "NW202601",
        }),
      });

      if (!response.ok) {
        throw new Error("Erro ao carregar deck do repositório");
      }

      const data = await response.json();
      setSessionId(data.session_id);
      setSelectedDeck(deckName);
      setIsDeckSelectOpen(false);

      setMessages([
        {
          id: Date.now().toString(),
          role: "assistant",
          content: `✅ Deck ${deckName === "december" ? "Dezembro 2025" : "Janeiro 2026"} carregado do repositório. Faça sua consulta.`,
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
    setSelectedDeck("upload");

    setMessages([
      {
        id: Date.now().toString(),
        role: "assistant",
        content: `✅ Deck NEWAVE carregado com sucesso. Faça sua consulta.`,
        timestamp: new Date(),
      },
    ]);

    setIsDialogOpen(false);
  };

  const handleSendMessage = async () => {
    if (!input.trim() || isLoading) return;

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
    setStreamingResponse("");
    streamingResponseRef.current = "";

    try {
      // Usar sessionId se disponível, senão usar session fixo para modo LLM sem deck
      const currentSessionId = sessionId || "llm-only-session";
      
      for await (const event of sendQueryStream(currentSessionId, userMessage.content, "llm_only")) {
        processStreamEvent(event);
      }

      await new Promise(resolve => setTimeout(resolve, 100));

      const hasContent = streamingResponseRef.current && streamingResponseRef.current.trim();
      
      if (hasContent) {
        const assistantMessage: Message = {
          id: (Date.now() + 1).toString(),
          role: "assistant",
          content: streamingResponseRef.current || "",
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

  const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div className="min-h-screen bg-background flex flex-col">
      {/* Header */}
      <header className="border-b border-border bg-card/50 backdrop-blur-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => router.push("/")}
                className="flex items-center space-x-2"
              >
                <ArrowLeft className="w-4 h-4" />
                <span>Voltar</span>
              </Button>
              <div className="flex items-center space-x-3">
                <MessageSquare className="w-6 h-6 text-primary" />
                <h1 className="text-xl font-bold text-foreground">Modo LLM</h1>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 flex flex-col max-w-7xl mx-auto w-full px-4 sm:px-6 lg:px-8 py-6">
        <div className="flex-1 flex flex-col space-y-4">
          {/* Info Card */}
          <Card className="bg-muted/50">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <p className="text-sm text-muted-foreground">
                  💡 <strong>Modo LLM:</strong> Faça perguntas sobre NEWAVE, arquivos, ferramentas e conceitos.
                  {sessionId ? (
                    <span className="text-green-600 dark:text-green-400"> Deck carregado.</span>
                  ) : (
                    <span> Opcionalmente, carregue um deck para análises específicas.</span>
                  )}
                </p>
                <div className="flex space-x-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setIsDeckSelectOpen(true)}
                    className="flex items-center space-x-2"
                  >
                    <FolderOpen className="w-4 h-4" />
                    <span>Repositório</span>
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setIsDialogOpen(true)}
                    className="flex items-center space-x-2"
                  >
                    <Upload className="w-4 h-4" />
                    <span>Upload</span>
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Messages */}
          <ScrollArea className="flex-1 rounded-lg border border-border bg-card p-4">
            <div className="space-y-4">
              {messages.length === 0 && !isStreaming && (
                <div className="text-center text-muted-foreground py-12">
                  <MessageSquare className="w-12 h-12 mx-auto mb-4 opacity-50" />
                  <p className="text-lg font-medium mb-2">Comece uma conversa</p>
                  <p className="text-sm">
                    Faça perguntas sobre NEWAVE, arquivos, ferramentas ou conceitos do sistema.
                  </p>
                </div>
              )}

              {messages.map((message) => (
                <ChatMessage key={message.id} message={message} />
              ))}

              {isStreaming && streamingResponse && (
                <ChatMessage
                  message={{
                    id: "streaming",
                    role: "assistant",
                    content: streamingResponse,
                    timestamp: new Date(),
                  }}
                />
              )}

              <div ref={messagesEndRef} />
            </div>
          </ScrollArea>

          {/* Agent Progress */}
          {agentSteps.length > 0 && (
            <AgentProgress 
              steps={agentSteps} 
              streamingResponse={streamingResponse}
              isStreaming={isStreaming}
            />
          )}

          {/* Input */}
          <Card>
            <CardContent className="pt-6">
              <div className="flex space-x-2">
                <Input
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Digite sua pergunta sobre NEWAVE..."
                  disabled={isLoading}
                  className="flex-1"
                />
                <Button
                  onClick={handleSendMessage}
                  disabled={!input.trim() || isLoading}
                  size="default"
                >
                  <Send className="w-4 h-4" />
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </main>

      {/* Upload Dialog */}
      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        <DialogContent className="bg-card border-border">
          <DialogHeader>
            <DialogTitle className="text-card-foreground">Upload do Deck NEWAVE</DialogTitle>
          </DialogHeader>
          <FileUpload model="newave" onUploadSuccess={handleUploadSuccess} />
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
    </div>
  );
}

