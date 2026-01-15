"use client";

import React, { useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronDown, Check, Loader2, Code } from "lucide-react";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { oneDark } from "react-syntax-highlighter/dist/esm/styles/prism";

export interface AgentStep {
  node: string;
  name: string;
  icon: string;
  description: string;
  status: "pending" | "running" | "completed";
  detail?: string;
}

interface AgentProgressProps {
  steps: AgentStep[];
  currentCode: string;
  streamingResponse: string;
  isStreaming: boolean;
  retryCount?: number;
  maxRetries?: number;
}

export function AgentProgress({
  steps,
  currentCode,
  streamingResponse,
  isStreaming,
  retryCount = 0,
  maxRetries = 3,
}: AgentProgressProps) {
  const [isExpanded, setIsExpanded] = useState(true);
  const [showCode, setShowCode] = useState(false);
  
  const completedSteps = steps.filter((s) => s.status === "completed").length;
  const currentStep = steps.find((s) => s.status === "running");
  const progress = (completedSteps / Math.max(steps.length, 1)) * 100;

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="w-full mb-6"
    >
      <Card className="bg-card border-border shadow-sm rounded-lg">
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3 flex-1">
              {/* Status indicator */}
              {isStreaming ? (
                <div className="relative">
                  <Loader2 className="h-5 w-5 animate-spin text-primary" />
                  <motion.div
                    className="absolute inset-0 rounded-full bg-primary/20"
                    animate={{ scale: [1, 1.5, 1], opacity: [0.5, 0, 0.5] }}
                    transition={{ repeat: Infinity, duration: 1.5 }}
                  />
                </div>
              ) : (
                <div className="w-5 h-5 rounded-full bg-green-500 flex items-center justify-center">
                  <Check className="w-3 h-3 text-white" />
                </div>
              )}

              {/* Current status text */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium text-card-foreground">
                    {isStreaming ? (currentStep?.name || "Processando...") : "Concluído"}
                  </span>
                  {retryCount > 0 && (
                    <Badge variant="secondary">
                      Tentativa {retryCount + 1}/{maxRetries}
                    </Badge>
                  )}
                </div>
                {currentStep?.detail && isStreaming && (
                  <p className="text-xs text-muted-foreground truncate">
                    {currentStep.detail}
                  </p>
                )}
              </div>

              {/* Progress mini */}
              <div className="hidden sm:flex items-center gap-2 text-xs text-muted-foreground">
                <span>{completedSteps}/{steps.length}</span>
                <Progress value={progress} className="w-20 h-1.5" />
              </div>
            </div>

            {/* Expand/Collapse button */}
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setIsExpanded(!isExpanded)}
              className="ml-2 h-8 w-8 text-muted-foreground hover:text-foreground"
            >
              <motion.div
                animate={{ rotate: isExpanded ? 180 : 0 }}
                transition={{ duration: 0.2 }}
              >
                <ChevronDown className="w-4 h-4" />
              </motion.div>
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Conteúdo expandido */}
      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="overflow-hidden"
          >
            <Card className="bg-background border-border mt-2 rounded-lg">
              <CardContent className="p-4 space-y-4">
                {/* Steps list */}
                <div className="space-y-2">
                  {steps.map((step, index) => (
                    <div key={step.node} className="flex items-start gap-3">
                      <div className="flex-shrink-0 mt-0.5">
                        {step.status === "completed" ? (
                          <div className="w-5 h-5 rounded-full bg-green-500 flex items-center justify-center">
                            <Check className="w-3 h-3 text-white" />
                          </div>
                        ) : step.status === "running" ? (
                          <Loader2 className="h-5 w-5 animate-spin text-primary" />
                        ) : (
                          <div className="w-5 h-5 rounded-full border-2 border-muted-foreground/30" />
                        )}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <span className="text-sm">{step.icon}</span>
                          <span className="text-sm font-medium text-foreground">{step.name}</span>
                        </div>
                        <p className="text-xs text-muted-foreground">{step.description}</p>
                        {step.detail && (
                          <p className="text-xs text-muted-foreground/80 mt-1">{step.detail}</p>
                        )}
                      </div>
                    </div>
                  ))}
                </div>

                {/* Code viewer */}
                {currentCode && (
                  <div className="mt-4">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => setShowCode(!showCode)}
                      className="mb-2"
                    >
                      <Code className="w-4 h-4 mr-2" />
                      {showCode ? "Ocultar" : "Mostrar"} código gerado
                    </Button>
                    {showCode && (
                      <div className="relative mt-2">
                        <SyntaxHighlighter
                          style={oneDark}
                          language="python"
                          PreTag="div"
                          className="rounded-lg text-sm !bg-[#1e1e2e]"
                          showLineNumbers
                        >
                          {currentCode}
                        </SyntaxHighlighter>
                      </div>
                    )}
                  </div>
                )}

                {/* Streaming response preview */}
                {streamingResponse && isStreaming && (
                  <div className="mt-4 p-3.5 bg-card border border-border rounded-lg">
                    <p className="text-xs text-muted-foreground mb-2 font-medium uppercase tracking-wide">Resposta:</p>
                    <p className="text-sm text-card-foreground whitespace-pre-wrap">{streamingResponse}</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
