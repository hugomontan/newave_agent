"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { motion } from "framer-motion";
import { FileText, GitCompare, ArrowRight, Calendar, ArrowLeft } from "lucide-react";
import { listAvailableDecks, DeckInfo } from "@/lib/api";

export default function NewaveHome() {
  const router = useRouter();
  const [availableDecks, setAvailableDecks] = useState<DeckInfo[]>([]);
  const [isLoadingDecks, setIsLoadingDecks] = useState(true);

  useEffect(() => {
    const fetchDecks = async () => {
      try {
        const response = await listAvailableDecks();
        setAvailableDecks(response.decks);
      } catch (err) {
        console.error("Error fetching decks:", err);
      } finally {
        setIsLoadingDecks(false);
      }
    };
    fetchDecks();
  }, []);

  return (
    <div className="min-h-screen bg-background flex flex-col">
      <header className="border-b border-border bg-card/50 backdrop-blur-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <Button variant="ghost" size="sm" onClick={() => router.push("/")}>
                <ArrowLeft className="w-4 h-4 mr-2" />
                Voltar
              </Button>
              <FileText className="w-8 h-8 text-primary" />
              <h1 className="text-2xl font-bold text-foreground">NEWAVE Agent</h1>
            </div>
          </div>
        </div>
      </header>

      <main className="flex-1 flex items-center justify-center p-4">
        <div className="max-w-4xl w-full space-y-8">
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="text-center space-y-4"
          >
            <h2 className="text-4xl font-bold text-foreground">
              Escolha o Modo de Análise NEWAVE
            </h2>
            <p className="text-lg text-muted-foreground">
              Selecione como deseja analisar os decks NEWAVE disponíveis
            </p>
          </motion.div>

          <div className="grid md:grid-cols-2 gap-6">
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
                      <p className="text-sm font-medium text-foreground flex items-center gap-2">
                        <Calendar className="w-4 h-4" />
                        Decks Disponíveis:
                        {!isLoadingDecks && (
                          <Badge variant="secondary" className="ml-1">
                            {availableDecks.length}
                          </Badge>
                        )}
                      </p>
                      {isLoadingDecks ? (
                        <div className="flex gap-1">
                          <div className="w-2 h-2 bg-primary/60 rounded-full animate-bounce"></div>
                          <div className="w-2 h-2 bg-primary/60 rounded-full animate-bounce" style={{ animationDelay: "0.2s" }}></div>
                          <div className="w-2 h-2 bg-primary/60 rounded-full animate-bounce" style={{ animationDelay: "0.4s" }}></div>
                        </div>
                      ) : (
                        <ul className="text-sm text-muted-foreground space-y-1 max-h-24 overflow-y-auto">
                          {availableDecks.slice(-4).map((deck) => (
                            <li key={deck.name}>• {deck.display_name}</li>
                          ))}
                          {availableDecks.length > 4 && (
                            <li className="text-xs italic">+ {availableDecks.length - 4} mais...</li>
                          )}
                        </ul>
                      )}
                    </div>
                    <Button
                      onClick={() => router.push("/newave/analysis")}
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
                    Compare dados entre múltiplos decks NEWAVE. Selecione N decks para análise histórica ou compare apenas dois para comparação direta.
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="space-y-2">
                      <p className="text-sm font-medium text-foreground">Comparação N Decks:</p>
                      <ul className="text-sm text-muted-foreground space-y-1">
                        <li>• Selecione múltiplos decks para comparar</li>
                        <li>• Análise histórica com todos os decks</li>
                        <li>• Gráficos de evolução temporal</li>
                        <li>• Resultados lado a lado automáticos</li>
                      </ul>
                    </div>
                    <Button
                      onClick={() => router.push("/newave/comparison")}
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
          </div>
        </div>
      </main>
    </div>
  );
}
