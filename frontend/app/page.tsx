"use client";

import React from "react";
import { useRouter } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
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
              <h1 className="text-2xl font-bold text-foreground">ENA - Energy Agent</h1>
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
              <Card 
                className="h-full hover:shadow-lg transition-shadow cursor-pointer border-2 hover:border-primary/50"
                onClick={(e) => {
                  // Permitir cliques no botão sem propagação dupla
                  if ((e.target as HTMLElement).closest('button')) {
                    return;
                  }
                  router.push("/newave");
                }}
              >
                <CardHeader>
                  <div className="flex items-center space-x-3">
                    <div className="p-3 bg-primary/10 rounded-lg">
                      <Calendar className="w-6 h-6 text-primary" />
                    </div>
                    <CardTitle className="text-2xl">NEWAVE</CardTitle>
                  </div>
                </CardHeader>
                <CardContent>
                  <Button
                      onClick={(e) => {
                        e.stopPropagation();
                        router.push("/newave");
                      }}
                      className="w-full"
                      size="lg"
                    >
                      Acessar NEWAVE
                      <ArrowRight className="w-4 h-4 ml-2" />
                    </Button>
                </CardContent>
              </Card>
            </motion.div>

            {/* DECOMP */}
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.5, delay: 0.3 }}
            >
              <Card 
                className="h-full hover:shadow-lg transition-shadow cursor-pointer border-2 hover:border-primary/50"
                onClick={(e) => {
                  // Permitir cliques no botão sem propagação dupla
                  if ((e.target as HTMLElement).closest('button')) {
                    return;
                  }
                  router.push("/decomp");
                }}
              >
                <CardHeader>
                  <div className="flex items-center space-x-3">
                    <div className="p-3 bg-primary/10 rounded-lg">
                      <Zap className="w-6 h-6 text-primary" />
                    </div>
                    <CardTitle className="text-2xl">DECOMP</CardTitle>
                  </div>
                </CardHeader>
                <CardContent>
                  <Button
                      onClick={(e) => {
                        e.stopPropagation();
                        router.push("/decomp");
                      }}
                      className="w-full"
                      size="lg"
                      variant="default"
                    >
                      Acessar DECOMP
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
