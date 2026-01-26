"use client";

import React, { useState, useMemo } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";

interface PlantCorrectionPromptProps {
  selectedPlant: {
    type: "hydraulic" | "thermal";
    codigo: number;
    nome: string;
    nome_completo: string;
    tool_name: string;
  };
  allPlants: Array<{
    codigo: number;
    nome: string;
    nome_completo: string;
  }>;
  originalQuery: string;
  onSelectPlant: (codigo: number, toolName: string, query: string) => void;
}

export function PlantCorrectionPrompt({
  selectedPlant,
  allPlants,
  originalQuery,
  onSelectPlant,
}: PlantCorrectionPromptProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");

  // Verificar se selectedPlant está definido
  if (!selectedPlant) {
    return null;
  }

  // Garantir que allPlants seja sempre um array
  const safeAllPlants = Array.isArray(allPlants) ? allPlants : [];

  const filteredPlants = useMemo(() => {
    if (!searchTerm.trim()) {
      return safeAllPlants.slice(0, 10); // Mostrar apenas 10 primeiros quando não há busca
    }

    const term = searchTerm.toLowerCase().trim();
    return safeAllPlants
      .filter((plant) => {
        const codigoStr = plant.codigo.toString();
        const nome = (plant.nome || "").toLowerCase();
        const nomeCompleto = (plant.nome_completo || "").toLowerCase();

        return (
          codigoStr.includes(term) ||
          nome.includes(term) ||
          nomeCompleto.includes(term)
        );
      })
      .slice(0, 10); // Limitar a 10 resultados
  }, [searchTerm, safeAllPlants]);

  const handleSelect = (codigo: number) => {
    const toolName = selectedPlant?.tool_name || "";
    onSelectPlant(codigo, toolName, originalQuery || "");
  };

  if (!isExpanded) {
    const plantType = selectedPlant?.type || "thermal";
    return (
      <div className="mt-4 p-3 rounded-lg bg-background/50 border border-border">
        <p className="text-sm text-foreground mb-2">
          {plantType === "hydraulic" ? "Essa usina hidrelétrica" : "Essa usina térmica"} não condiz com sua busca?
        </p>
        <Button
          variant="outline"
          size="sm"
          onClick={() => setIsExpanded(true)}
          className="w-full"
        >
          Selecionar outra usina
        </Button>
      </div>
    );
  }

  return (
    <div className="mt-4 p-4 rounded-lg bg-background/50 border border-border max-w-lg w-full">
      <p className="text-sm font-semibold text-foreground mb-3">
        Selecione a usina correta:
      </p>
      <Input
        type="text"
        placeholder="Buscar por nome ou código..."
        value={searchTerm}
        onChange={(e) => setSearchTerm(e.target.value)}
        className="mb-3"
      />
      <ScrollArea className="h-[250px]">
        <div className="space-y-2">
          {filteredPlants.length > 0 ? (
            filteredPlants.map((plant) => (
              <Button
                key={plant.codigo}
                variant="outline"
                className="w-full text-left justify-start bg-background hover:bg-background/80"
                onClick={() => handleSelect(plant.codigo)}
              >
                <div className="flex items-center gap-3 w-full">
                  <span className="font-mono text-xs text-muted-foreground min-w-[50px]">
                    {plant.codigo}
                  </span>
                  <div className="flex-1 min-w-0">
                    <div className="font-medium text-sm truncate">
                      {plant.nome}
                    </div>
                    {plant.nome_completo && plant.nome_completo !== plant.nome && (
                      <div className="text-xs text-muted-foreground truncate">
                        {plant.nome_completo}
                      </div>
                    )}
                  </div>
                </div>
              </Button>
            ))
          ) : (
            <p className="text-sm text-muted-foreground text-center py-4">
              Nenhuma usina encontrada
            </p>
          )}
        </div>
      </ScrollArea>
      <Button
        variant="ghost"
        size="sm"
        onClick={() => {
          setIsExpanded(false);
          setSearchTerm("");
        }}
        className="w-full mt-3"
      >
        Cancelar
      </Button>
    </div>
  );
}
