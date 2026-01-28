"use client";

import React, { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { motion } from "framer-motion";
import { Activity, ArrowLeft, ArrowRight, FileText } from "lucide-react";
import { listAvailableDessemDecks, DeckInfo } from "@/lib/api";

export default function DessemHomePage() {
  const router = useRouter();
  const [availableDecks, setAvailableDecks] = useState<DeckInfo[]>([]);
  const [isLoadingDecks, setIsLoadingDecks] = useState(true);

  useEffect(() => {
    const fetchDecks = async () => {
      try {
        const response = await listAvailableDessemDecks();
        setAvailableDecks(response.decks || []);
      } catch (err) {
        console.error("Erro ao buscar decks DESSEM:", err);
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
              <h1 className="text-2xl font-bold text-foreground">DESSEM Agent</h1>
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
            <h2 className="text-4xl font-bold text-foreground">Escolha o modo de análise DESSEM</h2>
            <p className="text-lg text-muted-foreground">
              Utilize o DESSEM Agent para analisar e, futuramente, comparar decks DESSEM.
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
                      <Activity className="w-6 h-6 text-primary" />
                    </div>
                    <CardTitle className="text-2xl">Análise Single Deck</CardTitle>
                  </div>
                  <CardDescription className="text-base">
                    Analise um único deck DESSEM, carregando via upload ou selecionando do repositório.
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="space-y-2">
                      <p className="text-sm font-medium text-foreground flex items-center gap-2">
                        Decks disponíveis:
                        {!isLoadingDecks && (
                          <Badge variant="secondary" className="ml-1">
                            {availableDecks.length}
                          </Badge>
                        )}
                      </p>
                      {isLoadingDecks ? (
                        <div className="flex gap-1">
                          <div className="w-2 h-2 bg-primary/60 rounded-full animate-bounce" />
                          <div
                            className="w-2 h-2 bg-primary/60 rounded-full animate-bounce"
                            style={{ animationDelay: "0.2s" }}
                          />
                          <div
                            className="w-2 h-2 bg-primary/60 rounded-full animate-bounce"
                            style={{ animationDelay: "0.4s" }}
                          />
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
                      onClick={() => router.push("/dessem/analysis")}
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
                      <Activity className="w-6 h-6 text-primary" />
                    </div>
                    <CardTitle className="text-2xl">Análise Comparativa</CardTitle>
                  </div>
                  <CardDescription className="text-base">
                    (Em construção) Comparação entre múltiplos decks DESSEM com visualizações dedicadas.
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <Button
                    onClick={() => router.push("/dessem/comparison")}
                    className="w-full"
                    size="lg"
                  >
                    Acessar Análise Comparativa
                    <ArrowRight className="w-4 h-4 ml-2" />
                  </Button>
                </CardContent>
              </Card>
            </motion.div>
          </div>
        </div>
      </main>
    </div>
  );
}

