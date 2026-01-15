"use client";

import React from "react";
import { useRouter } from "next/navigation";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { motion } from "framer-motion";
import { FileText, ArrowRight, Zap, Calendar } from "lucide-react";

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
              <h1 className="text-2xl font-bold text-foreground">NW Multi Agent</h1>
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
              Selecione o Modelo
            </h2>
            <p className="text-lg text-muted-foreground">
              Escolha entre NEWAVE ou DECOMP para análise de decks
            </p>
          </motion.div>

          <div className="grid md:grid-cols-2 gap-6">
            {/* NEWAVE */}
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.5, delay: 0.2 }}
            >
              <Card className="h-full hover:shadow-lg transition-shadow cursor-pointer border-2 hover:border-primary/50">
                <CardHeader>
                  <div className="flex items-center space-x-3 mb-2">
                    <div className="p-3 bg-primary/10 rounded-lg">
                      <Calendar className="w-6 h-6 text-primary" />
                    </div>
                    <CardTitle className="text-2xl">NEWAVE</CardTitle>
                  </div>
                  <CardDescription className="text-base">
                    Modelo de médio a longo prazo (até 5 anos, discretização mensal). Planejamento estratégico e geração de FCF.
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="space-y-2">
                      <p className="text-sm font-medium text-foreground">Características:</p>
                      <ul className="text-sm text-muted-foreground space-y-1">
                        <li>• Horizonte: até 5 anos</li>
                        <li>• Discretização: mensal</li>
                        <li>• Planejamento estratégico</li>
                        <li>• Geração de FCF</li>
                      </ul>
                    </div>
                    <Button
                      onClick={() => router.push("/newave")}
                      className="w-full"
                      size="lg"
                    >
                      Acessar NEWAVE
                      <ArrowRight className="w-4 h-4 ml-2" />
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </motion.div>

            {/* DECOMP */}
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.5, delay: 0.3 }}
            >
              <Card className="h-full hover:shadow-lg transition-shadow cursor-pointer border-2 hover:border-primary/50">
                <CardHeader>
                  <div className="flex items-center space-x-3 mb-2">
                    <div className="p-3 bg-primary/10 rounded-lg">
                      <Zap className="w-6 h-6 text-primary" />
                    </div>
                    <CardTitle className="text-2xl">DECOMP</CardTitle>
                  </div>
                  <CardDescription className="text-base">
                    Modelo de curto prazo (até 12 meses, discretização semanal/mensal). Usinas individuais, PMO, PLD semanal.
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="space-y-2">
                      <p className="text-sm font-medium text-foreground">Características:</p>
                      <ul className="text-sm text-muted-foreground space-y-1">
                        <li>• Horizonte: até 12 meses</li>
                        <li>• Discretização: semanal/mensal</li>
                        <li>• Usinas individuais</li>
                        <li>• PMO e PLD semanal</li>
                      </ul>
                    </div>
                    <Button
                      onClick={() => router.push("/decomp")}
                      className="w-full"
                      size="lg"
                      variant="default"
                    >
                      Acessar DECOMP
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
