"use client";

import React from "react";
import { useRouter } from "next/navigation";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { motion } from "framer-motion";
import { FileText, GitCompare, ArrowRight, Brain } from "lucide-react";

export default function Home() {
  const router = useRouter();

  return (
    <div className="min-h-screen bg-background flex flex-col">
      {/* Header */}
      <header className="border-b border-border bg-card/50 backdrop-blur-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <FileText className="w-8 h-8 text-primary" />
              <h1 className="text-2xl font-bold text-foreground">NEWAVE Agent</h1>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 flex items-center justify-center p-4">
        <div className="max-w-4xl w-full space-y-8">
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="text-center space-y-4"
          >
            <h2 className="text-4xl font-bold text-foreground">
              Escolha o Modo de Análise
            </h2>
            <p className="text-lg text-muted-foreground">
              Selecione como deseja analisar os decks NEWAVE disponíveis
            </p>
          </motion.div>

          <div className="grid md:grid-cols-3 gap-6">
            {/* Análise Single Deck */}
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.5, delay: 0.2 }}
            >
              <Card className="h-full hover:shadow-lg transition-shadow cursor-pointer border-2 hover:border-primary/50">
                <CardHeader>
                  <div className="flex items-center space-x-3 mb-2">
                    <div className="p-3 bg-primary/10 rounded-lg">
                      <FileText className="w-6 h-6 text-primary" />
                    </div>
                    <CardTitle className="text-2xl">Análise Single Deck</CardTitle>
                  </div>
                  <CardDescription className="text-base">
                    Analise um deck NEWAVE específico. Faça upload de um deck ou escolha entre os decks disponíveis no repositório.
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="space-y-2">
                      <p className="text-sm font-medium text-foreground">Decks Disponíveis:</p>
                      <ul className="text-sm text-muted-foreground space-y-1">
                        <li>• Dezembro 2025 (NW202512)</li>
                        <li>• Janeiro 2026 (NW202601)</li>
                      </ul>
                    </div>
                    <Button
                      onClick={() => router.push("/analysis")}
                      className="w-full"
                      size="lg"
                    >
                      Acessar Análise Single Deck
                      <ArrowRight className="w-4 h-4 ml-2" />
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </motion.div>

            {/* Análise Comparativa */}
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.5, delay: 0.3 }}
            >
              <Card className="h-full hover:shadow-lg transition-shadow cursor-pointer border-2 hover:border-primary/50">
                <CardHeader>
                  <div className="flex items-center space-x-3 mb-2">
                    <div className="p-3 bg-primary/10 rounded-lg">
                      <GitCompare className="w-6 h-6 text-primary" />
                    </div>
                    <CardTitle className="text-2xl">Análise Comparativa</CardTitle>
                  </div>
                  <CardDescription className="text-base">
                    Compare automaticamente os dados entre Dezembro 2025 e Janeiro 2026. Todas as consultas retornam resultados lado a lado com gráficos comparativos.
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="space-y-2">
                      <p className="text-sm font-medium text-foreground">Comparação Automática:</p>
                      <ul className="text-sm text-muted-foreground space-y-1">
                        <li>• Todas as queries comparam ambos os decks</li>
                        <li>• Resultados lado a lado</li>
                        <li>• Gráficos comparativos automáticos</li>
                      </ul>
                    </div>
                    <Button
                      onClick={() => router.push("/comparison")}
                      className="w-full"
                      size="lg"
                      variant="default"
                    >
                      Acessar Análise Comparativa
                      <ArrowRight className="w-4 h-4 ml-2" />
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </motion.div>

            {/* LLM Mode */}
            <motion.div
              initial={{ opacity: 0, x: 0 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.5, delay: 0.4 }}
            >
              <Card className="h-full hover:shadow-lg transition-shadow cursor-pointer border-2 hover:border-primary/50">
                <CardHeader>
                  <div className="flex items-center space-x-3 mb-2">
                    <div className="p-3 bg-primary/10 rounded-lg">
                      <Brain className="w-6 h-6 text-primary" />
                    </div>
                    <CardTitle className="text-2xl">LLM Mode</CardTitle>
                  </div>
                  <CardDescription className="text-base">
                    Modo avançado com RAG completo e LLM Planner. Mais liberdade para o LLM codar e entender o projeto, sem usar tools pré-programadas.
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="space-y-2">
                      <p className="text-sm font-medium text-foreground">Características:</p>
                      <ul className="text-sm text-muted-foreground space-y-1">
                        <li>• RAG completo em toda documentação</li>
                        <li>• LLM Planner gera instruções detalhadas</li>
                        <li>• Coder com mais contexto e liberdade</li>
                        <li>• Sem tools pré-programadas</li>
                      </ul>
                    </div>
                    <Button
                      onClick={() => router.push("/llm-mode")}
                      className="w-full"
                      size="lg"
                      variant="outline"
                    >
                      Acessar LLM Mode
                      <ArrowRight className="w-4 h-4 ml-2" />
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          </div>

          {/* Footer Info */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.5, delay: 0.5 }}
            className="text-center text-sm text-muted-foreground"
          >
            <p>
              Os decks estão disponíveis no repositório e serão carregados automaticamente
            </p>
          </motion.div>
        </div>
      </main>
    </div>
  );
}
