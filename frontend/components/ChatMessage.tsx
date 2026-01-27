"use client";

import React, { useState } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { oneDark } from "react-syntax-highlighter/dist/esm/styles/prism";
import { DataTable } from "./DataTable";
import { ComparisonView } from "./ComparisonView";
import { SingleDeckRouter } from "./single-deck/SingleDeckRouter";
import { PlantCorrectionPrompt } from "./PlantCorrectionPrompt";
import { motion } from "framer-motion";
import { Copy, Check, Download, User, Bot } from "lucide-react";
import type { SingleDeckVisualizationData } from "./single-deck/shared/types";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  rawData?: Record<string, unknown>[] | null;
  retryCount?: number;
  error?: string | null;
  timestamp: Date;
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
  disambiguationData?: {
    type: string;
    question: string;
    options: Array<{label: string; query: string; tool_name: string}>;
    original_query: string;
    isLoading?: boolean;
    selectedOption?: string;
  };
  plantCorrectionData?: {
    type: "plant_correction";
    message: string;
    selectedPlant: {
      type: "hydraulic" | "thermal";
      codigo: number;
      nome: string;
      nome_completo: string;
      tool_name: string;
    };
    allPlants: Array<{codigo: number; nome: string; nome_completo: string}>;
    originalQuery: string;
  };
  requires_user_choice?: boolean;
  alternative_type?: string;
  visualizationData?: SingleDeckVisualizationData;
}

interface ChatMessageProps {
  message: Message;
  onOptionClick?: (query: string, messageId?: string) => void;
}

export function ChatMessage({ message, onOptionClick }: ChatMessageProps) {
  const isUser = message.role === "user";
  const [copied, setCopied] = useState(false);

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const downloadAsCSV = () => {
    if (!message.rawData || message.rawData.length === 0) return;
    
    const columns = Object.keys(message.rawData[0]);
    const headers = columns.join(",");
    const rows = message.rawData.map((row) =>
      columns.map((col) => {
        const value = row[col];
        const stringValue = String(value ?? "");
        if (stringValue.includes(",") || stringValue.includes('"')) {
          return `"${stringValue.replace(/"/g, '""')}"`;
        }
        return stringValue;
      }).join(",")
    );
    const csv = [headers, ...rows].join("\n");
    
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `data_${new Date().toISOString().slice(0, 10)}.csv`;
    link.click();
    URL.revokeObjectURL(url);
  };

  const downloadAsJSON = () => {
    if (!message.rawData) return;
    const json = JSON.stringify(message.rawData, null, 2);
    const blob = new Blob([json], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `data_${new Date().toISOString().slice(0, 10)}.json`;
    link.click();
    URL.revokeObjectURL(url);
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2, ease: "easeOut" }}
      className={`flex ${isUser ? "justify-end" : "justify-start"} mb-8`}
    >
      <div className={`flex items-start gap-3.5 max-w-[98%] ${isUser ? "flex-row-reverse" : ""}`}>
        {/* Avatar */}
        <div
          className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
            isUser
              ? "bg-primary text-primary-foreground"
              : "bg-secondary text-secondary-foreground"
          }`}
        >
          {isUser ? (
            <User className="w-4 h-4" />
          ) : (
            <Bot className="w-4 h-4" />
          )}
        </div>

        {/* Message content */}
        <div className="flex-1 min-w-0">
          {isUser ? (
            <div className="bg-[hsl(210,70%,55%)] text-white rounded-2xl rounded-tr-sm px-4 py-3">
              <p className="whitespace-pre-wrap text-[15px] leading-relaxed">
                {message.content.startsWith("__DISAMBIG__:") 
                  ? (() => {
                      const parts = message.content.split(":", 2);
                      return parts.length === 3 ? parts[2].trim() : message.content;
                    })()
                  : message.content}
              </p>
            </div>
          ) : (
            <div className="bg-[hsl(222,47%,18%)] rounded-2xl rounded-tl-sm px-4 py-3 w-full max-w-full overflow-x-auto">
              <div className="space-y-4 min-w-0">
                {/* Retry badge */}
                {message.retryCount && message.retryCount > 0 && (
                  <Badge variant="secondary" className="mb-2">
                    Corrigido após {message.retryCount} {message.retryCount === 1 ? "tentativa" : "tentativas"}
                  </Badge>
                )}

                {/* User Choice Options (requires_user_choice) */}
                {(() => {
                  const shouldRender = message.requires_user_choice && message.alternative_type;
                  console.log("[ChatMessage] Verificando renderização de botões:", {
                    requires_user_choice: message.requires_user_choice,
                    alternative_type: message.alternative_type,
                    shouldRender
                  });
                  
                  if (!shouldRender) {
                    return null;
                  }
                  
                  // Extrair mensagem da escolha do conteúdo (remover markdown headers)
                  const choiceMessage = message.content
                    .replace(/^##\s+/gm, '')
                    .replace(/\n+/g, ' ')
                    .trim();
                  
                  return (
                    <div className="mb-4 p-4 border border-primary/30 rounded-lg bg-primary/5">
                      <h3 className="text-base font-semibold text-white mb-3">
                        {choiceMessage || "Deseja buscar os dados alternativos?"}
                      </h3>
                      <div className="space-y-2">
                        <Button
                          onClick={() => {
                            // Quando clicar em "Sim", fazer query com o tipo alternativo (VAZMINT).
                            // Preferir o NOME da usina (ex: "P. PRIMAVERA") em "usina 46 (P. PRIMAVERA)",
                            // para que o backend resolva pela usina correta. O código "46" na mensagem
                            // é interno ao MODIF; na reconsulta, "usina 46" é interpretado como código
                            // do CSV e pode apontar para outra usina (ex: JUPIA).
                            let query = "vazão mínima por período";
                            const usinaComNome = message.content.match(/usina\s+\d+\s*\(([^)]+)\)/i);
                            if (usinaComNome) {
                              query += ` de ${usinaComNome[1].trim()}`;
                            } else {
                              const usinaMatch = message.content.match(/usina\s+(\d+)/i);
                              if (usinaMatch) {
                                query += ` da usina ${usinaMatch[1]}`;
                              } else {
                                const nomeMatch = message.content.match(/\(([^)]+)\)/);
                                if (nomeMatch) {
                                  query += ` de ${nomeMatch[1].trim()}`;
                                }
                              }
                            }
                            console.log("[ChatMessage] Botão Sim clicado, query gerada:", query);
                            onOptionClick?.(query);
                          }}
                          variant="outline"
                          className="w-full text-left justify-start bg-background/50 hover:bg-background border-border hover:border-primary/50 text-foreground"
                        >
                          <span className="font-bold mr-2 text-primary">1.</span>
                          <span>Sim</span>
                        </Button>
                        <Button
                          onClick={() => {
                            // Quando clicar em "Não", não fazer nada (ou cancelar)
                            // A mensagem já foi exibida
                            console.log("[ChatMessage] Botão Não clicado");
                          }}
                          variant="outline"
                          className="w-full text-left justify-start bg-background/50 hover:bg-background border-border hover:border-primary/50 text-foreground"
                        >
                          <span className="font-bold mr-2 text-primary">2.</span>
                          <span>Não</span>
                        </Button>
                      </div>
                    </div>
                  );
                })()}

                {/* Disambiguation Options */}
                {message.disambiguationData && (
                  <div className="mb-4 p-4 border border-primary/30 rounded-lg bg-primary/5">
                    {message.disambiguationData.isLoading ? (
                      <div className="space-y-4">
                        <div className="flex flex-col items-center justify-center py-4">
                          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mb-4"></div>
                          <p className="text-sm text-muted-foreground">Processando sua escolha...</p>
                        </div>
                        {/* Mostrar conteúdo que está chegando durante o streaming */}
                        {message.content && message.content.trim() && (
                          <div className="prose prose-sm max-w-none prose-invert prose-headings:text-white prose-p:text-white prose-strong:text-white prose-code:text-white prose-ul:text-white prose-ol:text-white prose-li:text-white prose-a:text-blue-400 prose-blockquote:text-gray-300 prose-th:text-white prose-td:text-gray-200 border-t border-primary/20 pt-4">
                            <ReactMarkdown
                              remarkPlugins={[remarkGfm]}
                              components={{
                                h1: ({ children }) => (
                                  <h1 className="text-xl font-semibold text-white mt-5 mb-3 tracking-tight" style={{ color: '#ffffff' }}>{children}</h1>
                                ),
                                h2: ({ children }) => (
                                  <h2 className="text-lg font-semibold text-foreground mt-4 mb-2.5 border-b border-border pb-1.5 tracking-tight">
                                    {children}
                                  </h2>
                                ),
                                h3: ({ children }) => (
                                  <h3 className="text-base font-medium text-white mt-3 mb-2 tracking-tight" style={{ color: '#ffffff' }}>{children}</h3>
                                ),
                                h4: ({ children }) => (
                                  <h4 className="text-base font-semibold text-white mb-2" style={{ color: '#ffffff' }}>{children}</h4>
                                ),
                                h5: ({ children }) => (
                                  <h5 className="text-sm font-semibold text-white mb-1" style={{ color: '#ffffff' }}>{children}</h5>
                                ),
                                h6: ({ children }) => (
                                  <h6 className="text-sm font-medium text-white mb-1" style={{ color: '#ffffff' }}>{children}</h6>
                                ),
                                p: ({ children }) => (
                                  <p className="text-white my-2.5 leading-relaxed text-[15px]">{children}</p>
                                ),
                                ul: ({ children }) => (
                                  <ul className="list-disc list-inside space-y-1 my-2 text-white">{children}</ul>
                                ),
                                ol: ({ children }) => (
                                  <ol className="list-decimal list-inside space-y-1 my-2 text-white">{children}</ol>
                                ),
                                li: ({ children }) => (
                                  <li className="text-white text-[15px] leading-relaxed">{children}</li>
                                ),
                                strong: ({ children }) => (
                                  <strong className="font-semibold text-white">{children}</strong>
                                ),
                                table: ({ children }) => (
                                  <div className="overflow-x-auto my-4">
                                    <table className="min-w-full border-collapse border border-border rounded-lg overflow-hidden">
                                      {children}
                                    </table>
                                  </div>
                                ),
                                thead: ({ children }) => (
                                  <thead className="bg-background">{children}</thead>
                                ),
                                th: ({ children }) => (
                                  <th className="border border-border px-4 py-2.5 text-left text-xs font-semibold text-foreground uppercase tracking-wider">
                                    {children}
                                  </th>
                                ),
                                td: ({ children }) => (
                                  <td className="border border-border px-4 py-2.5 text-sm text-foreground/90">
                                    {children}
                                  </td>
                                ),
                                blockquote: ({ children }) => (
                                  <blockquote className="border-l-4 border-border pl-4 my-4 text-muted-foreground italic text-[15px]">
                                    {children}
                                  </blockquote>
                                ),
                                img: ({ src, alt, ...props }) => {
                                  if (src && src.startsWith("data:image")) {
                                    return (
                                      <div className="my-4 flex justify-center">
                                        <img 
                                          src={src} 
                                          alt={alt || "Gráfico"} 
                                          className="max-w-full h-auto rounded-lg border border-border"
                                          {...props}
                                        />
                                      </div>
                                    );
                                  }
                                  return (
                                    <div className="my-4 flex justify-center">
                                      <img 
                                        src={src} 
                                        alt={alt || "Imagem"} 
                                        className="max-w-full h-auto rounded-lg border border-border"
                                        {...props}
                                      />
                                    </div>
                                  );
                                },
                                code({ node, className, children, ...props }) {
                                  const match = /language-(\w+)/.exec(className || "");
                                  const isInline = !match;
                                  return !isInline ? (
                                    <div className="relative group my-3">
                                      <SyntaxHighlighter
                                        style={oneDark}
                                        language={match[1]}
                                        PreTag="div"
                                        className="rounded-lg text-sm !bg-[#1e1e2e]"
                                        showLineNumbers={match[1] === "python"}
                                      >
                                        {String(children).replace(/\n$/, "")}
                                      </SyntaxHighlighter>
                                      <Button
                                        size="sm"
                                        variant="ghost"
                                        className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity bg-muted hover:bg-muted/80 text-foreground h-8 w-8 p-0"
                                        onClick={() => copyToClipboard(String(children))}
                                      >
                                        {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                                      </Button>
                                    </div>
                                  ) : (
                                    <code
                                      className="bg-background text-foreground px-1.5 py-0.5 rounded text-sm font-mono border border-border"
                                      {...props}
                                    >
                                      {children}
                                    </code>
                                  );
                                },
                              }}
                            >
                              {message.content}
                            </ReactMarkdown>
                          </div>
                        )}
                      </div>
                    ) : (
                      <>
                        <h3 className="text-base font-semibold text-white mb-3">
                          {message.disambiguationData.question}
                        </h3>
                        <div className="space-y-2">
                          {message.disambiguationData.options.map((option, idx) => (
                            <Button
                              key={idx}
                              onClick={() => onOptionClick?.(option.query, message.id)}
                              variant="outline"
                              className="w-full text-left justify-start bg-background/50 hover:bg-background border-border hover:border-primary/50 text-foreground"
                            >
                              <span className="font-bold mr-2 text-primary">{idx + 1}.</span>
                              <span>{option.label}</span>
                            </Button>
                          ))}
                        </div>
                      </>
                    )}
                  </div>
                )}

                {/* Response content with markdown - apenas se houver conteúdo e não for apenas disambiguation ou requires_user_choice */}
                {/* Não mostrar conteúdo aqui se estiver em loading de disambiguation (já mostrado acima) */}
                {message.content && message.content.trim() && !message.requires_user_choice && !(message.disambiguationData && message.disambiguationData.isLoading) && (
                <div className="prose prose-sm max-w-none prose-invert prose-headings:text-white prose-p:text-white prose-strong:text-white prose-code:text-white prose-ul:text-white prose-ol:text-white prose-li:text-white prose-a:text-blue-400 prose-blockquote:text-gray-300 prose-th:text-white prose-td:text-gray-200">
                <ReactMarkdown
                      remarkPlugins={[remarkGfm]}
                      components={{
                        h1: ({ children }) => (
                          <h1 className="text-xl font-semibold text-white mt-5 mb-3 tracking-tight" style={{ color: '#ffffff' }}>{children}</h1>
                        ),
                        h2: ({ children }) => (
                          <h2 className="text-xl font-semibold text-white mt-4 mb-4 tracking-tight" style={{ color: '#ffffff' }}>
                            {children}
                          </h2>
                        ),
                        h3: ({ children }) => (
                          <h3 className="text-base font-medium text-white mt-3 mb-2 tracking-tight" style={{ color: '#ffffff' }}>{children}</h3>
                        ),
                        h4: ({ children }) => (
                          <h4 className="text-base font-semibold text-white mb-2" style={{ color: '#ffffff' }}>{children}</h4>
                        ),
                        h5: ({ children }) => (
                          <h5 className="text-sm font-semibold text-white mb-1" style={{ color: '#ffffff' }}>{children}</h5>
                        ),
                        h6: ({ children }) => (
                          <h6 className="text-sm font-medium text-white mb-1" style={{ color: '#ffffff' }}>{children}</h6>
                        ),
                        p: ({ children }) => (
                          <p className="text-white my-2.5 leading-relaxed text-[15px]">{children}</p>
                        ),
                        ul: ({ children }) => (
                          <ul className="list-disc list-inside space-y-1 my-2 text-white">{children}</ul>
                        ),
                        ol: ({ children }) => (
                          <ol className="list-decimal list-inside space-y-1 my-2 text-white">{children}</ol>
                        ),
                        li: ({ children }) => (
                          <li className="text-white text-[15px] leading-relaxed">{children}</li>
                        ),
                        strong: ({ children }) => (
                          <strong className="font-semibold text-white">{children}</strong>
                        ),
                        table: ({ children }) => (
                          <div className="overflow-x-auto my-4">
                            <table className="min-w-full border-collapse border border-border rounded-lg overflow-hidden">
                              {children}
                            </table>
                          </div>
                        ),
                        thead: ({ children }) => (
                          <thead className="bg-background">{children}</thead>
                        ),
                        th: ({ children }) => (
                          <th className="border border-border px-4 py-2.5 text-left text-xs font-semibold text-foreground uppercase tracking-wider">
                            {children}
                          </th>
                        ),
                        td: ({ children }) => (
                          <td className="border border-border px-4 py-2.5 text-sm text-foreground/90">
                            {children}
                          </td>
                        ),
                        blockquote: ({ children }) => (
                          <blockquote className="border-l-4 border-border pl-4 my-4 text-muted-foreground italic text-[15px]">
                            {children}
                          </blockquote>
                        ),
                        img: ({ src, alt, ...props }) => {
                          // Suportar imagens base64 inline
                          if (src && src.startsWith("data:image")) {
                            return (
                              <div className="my-4 flex justify-center">
                                <img 
                                  src={src} 
                                  alt={alt || "Gráfico"} 
                                  className="max-w-full h-auto rounded-lg border border-border"
                                  {...props}
                                />
                              </div>
                            );
                          }
                          // Imagens externas normais
                          return (
                            <div className="my-4 flex justify-center">
                              <img 
                                src={src} 
                                alt={alt || "Imagem"} 
                                className="max-w-full h-auto rounded-lg border border-border"
                                {...props}
                              />
                            </div>
                          );
                        },
                        code({ node, className, children, ...props }) {
                          const match = /language-(\w+)/.exec(className || "");
                          const isInline = !match;
                          return !isInline ? (
                            <div className="relative group my-3">
                              <SyntaxHighlighter
                                style={oneDark}
                                language={match[1]}
                                PreTag="div"
                                className="rounded-lg text-sm !bg-[#1e1e2e]"
                                showLineNumbers={match[1] === "python"}
                              >
                                {String(children).replace(/\n$/, "")}
                              </SyntaxHighlighter>
                              <Button
                                size="sm"
                                variant="ghost"
                                className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity bg-muted hover:bg-muted/80 text-foreground h-8 w-8 p-0"
                                onClick={() => copyToClipboard(String(children))}
                              >
                                {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                              </Button>
                            </div>
                          ) : (
                            <code
                              className="bg-background text-foreground px-1.5 py-0.5 rounded text-sm font-mono border border-border"
                              {...props}
                            >
                              {children}
                            </code>
                          );
                        },
                      }}
                    >
                      {message.content}
                    </ReactMarkdown>
                </div>
                )}

              </div>

              {/* Comparison View - mostrar mesmo durante loading de disambiguation */}
              {message.comparisonData && (
                <div className="w-full max-w-full min-w-0">
                  <ComparisonView comparison={message.comparisonData as any} />
                </div>
              )}

              {/* Single Deck Visualization */}
              {message.visualizationData && (
                <div className="w-full -mx-4 sm:-mx-6 md:-mx-8 px-4 sm:px-6 md:px-8 max-w-full">
                  <div className="min-w-0 w-full">
                    <SingleDeckRouter visualizationData={message.visualizationData} />
                  </div>
                </div>
              )}

              {/* Raw Data Table - mostrar mesmo durante loading de disambiguation */}
              {message.rawData && message.rawData.length > 0 && !message.comparisonData && !message.visualizationData && (
                <div className="w-full -mx-4 sm:-mx-6 md:-mx-8 px-4 sm:px-6 md:px-8">
                  <DataTable 
                    data={message.rawData} 
                    title=" Dados Extraídos"
                  />
                </div>
              )}

              {/* Plant Correction Prompt - no final da mensagem */}
              {message.plantCorrectionData && message.plantCorrectionData.selectedPlant && (
                <div className="mt-4">
                  <PlantCorrectionPrompt
                    selectedPlant={message.plantCorrectionData.selectedPlant}
                    allPlants={message.plantCorrectionData.allPlants}
                    originalQuery={message.plantCorrectionData.originalQuery}
                    onSelectPlant={(codigo, toolName, query) => {
                      const correctionQuery = `__PLANT_CORR__:${toolName}:${codigo}:${query}`;
                      onOptionClick?.(correctionQuery, message.id);
                    }}
                  />
                </div>
              )}

              {/* Download buttons - Elegant */}
              {message.rawData && message.rawData.length > 0 && (
                <div className="flex items-center gap-2.5 pt-3 mt-4 border-t border-btg-graphite-200/60">
                  <span className="text-xs text-btg-graphite-500 font-medium">Exportar dados:</span>
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button
                        variant="outline"
                        size="sm"
                        className="h-8"
                      >
                        <Download className="w-3 h-3 mr-1" />
                        Download
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent>
                      <DropdownMenuItem onSelect={downloadAsCSV}>
                        📄 CSV (Excel)
                      </DropdownMenuItem>
                      <DropdownMenuItem onSelect={downloadAsJSON}>
                        📋 JSON
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </div>
              )}
            </div>
          )}

          {/* Timestamp */}
          <p className={`text-xs text-[hsl(220,9%,65%)] mt-1 ${isUser ? "text-right" : "text-left"}`}>
            {message.timestamp.toLocaleTimeString("pt-BR", {
              hour: "2-digit",
              minute: "2-digit",
            })}
          </p>
        </div>
      </div>
    </motion.div>
  );
}
