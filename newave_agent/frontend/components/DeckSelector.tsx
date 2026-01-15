"use client";

import React, { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import { Calendar, Check, X } from "lucide-react";

// Interface para informações de deck
export interface DeckInfo {
  name: string;
  display_name: string;
  year: number;
  month: number;
}

// Props do componente
interface DeckSelectorProps {
  mode: "single" | "multi";
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSelect: (decks: DeckInfo[]) => void;
  initialSelected?: string[];
  title?: string;
  description?: string;
  model?: "newave" | "decomp"; // Modelo para determinar qual API usar
}

// Função para buscar decks disponíveis
export async function fetchAvailableDecks(model: "newave" | "decomp" = "newave"): Promise<DeckInfo[]> {
  const baseUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  const apiUrl = model === "decomp" 
    ? `${baseUrl}/api/decomp/decks`
    : `${baseUrl}/decks/list`;
  const response = await fetch(apiUrl);
  if (!response.ok) {
    const errorText = await response.text();
    let errorMessage = "Erro ao buscar decks disponíveis";
    try {
      const errorJson = JSON.parse(errorText);
      errorMessage = errorJson.detail || errorMessage;
    } catch {
      errorMessage = errorText || errorMessage;
    }
    throw new Error(errorMessage);
  }
  const data = await response.json();
  return data.decks;
}

export function DeckSelector({
  mode,
  open,
  onOpenChange,
  onSelect,
  initialSelected = [],
  title,
  description,
  model = "newave",
}: DeckSelectorProps) {
  const [decks, setDecks] = useState<DeckInfo[]>([]);
  const [selectedDecks, setSelectedDecks] = useState<Set<string>>(new Set(initialSelected));
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Carregar decks disponíveis
  useEffect(() => {
    if (open) {
      loadDecks();
    }
  }, [open, model]);

  // Atualizar seleção quando initialSelected mudar
  useEffect(() => {
    setSelectedDecks(new Set(initialSelected));
  }, [initialSelected]);

  const loadDecks = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const availableDecks = await fetchAvailableDecks(model);
      setDecks(availableDecks);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro desconhecido");
    } finally {
      setIsLoading(false);
    }
  };

  const handleDeckClick = (deck: DeckInfo) => {
    if (mode === "single") {
      // Modo single: seleciona apenas um deck
      const newSelected = new Set<string>();
      newSelected.add(deck.name);
      setSelectedDecks(newSelected);
    } else {
      // Modo multi: toggle na seleção
      const newSelected = new Set(selectedDecks);
      if (newSelected.has(deck.name)) {
        newSelected.delete(deck.name);
      } else {
        newSelected.add(deck.name);
      }
      setSelectedDecks(newSelected);
    }
  };

  const handleConfirm = () => {
    console.log("[DeckSelector] handleConfirm chamado");
    console.log("[DeckSelector] selectedDecks:", Array.from(selectedDecks));
    console.log("[DeckSelector] decks disponíveis:", decks.length);
    
    const selectedDecksList = decks.filter((d) => selectedDecks.has(d.name));
    console.log("[DeckSelector] selectedDecksList filtrado:", selectedDecksList);
    
    if (selectedDecksList.length === 0) {
      console.warn("[DeckSelector] ⚠️ Nenhum deck selecionado!");
      return;
    }
    
    // Ordenar por data (mais antigo primeiro)
    selectedDecksList.sort((a, b) => {
      if (a.year !== b.year) return a.year - b.year;
      return a.month - b.month;
    });
    
    console.log("[DeckSelector] selectedDecksList ordenado:", selectedDecksList);
    console.log("[DeckSelector] Chamando onSelect com", selectedDecksList.length, "decks");
    
    // Chamar onSelect primeiro (antes de fechar o dialog)
    // Isso garante que o estado seja atualizado antes do dialog fechar
    onSelect(selectedDecksList);
    
    // Fechar dialog após um pequeno delay para garantir que onSelect foi processado
    setTimeout(() => {
      console.log("[DeckSelector] Fechando dialog");
      onOpenChange(false);
    }, 50);
  };

  const handleSelectAll = () => {
    if (selectedDecks.size === decks.length) {
      // Desselecionar todos
      setSelectedDecks(new Set());
    } else {
      // Selecionar todos
      setSelectedDecks(new Set(decks.map((d) => d.name)));
    }
  };

  const handleClearSelection = () => {
    setSelectedDecks(new Set());
  };

  const dialogTitle = title || (mode === "single" ? "Selecionar Deck" : "Selecionar Decks para Comparação");
  const dialogDescription = description || (mode === "single" 
    ? "Escolha um deck do repositório para analisar"
    : "Selecione os decks que deseja comparar (mínimo 2)");

  const canConfirm = mode === "single" ? selectedDecks.size === 1 : selectedDecks.size >= 2;

  // Debug: monitorar mudanças no estado do dialog
  useEffect(() => {
    console.log("[DeckSelector] Dialog open mudou para:", open);
    
    // Quando o dialog fecha, garantir que todos os overlays são removidos
    if (!open) {
      setTimeout(() => {
        const overlays = document.querySelectorAll('[data-radix-dialog-overlay]');
        console.log("[DeckSelector] Dialog fechado - verificando overlays:", overlays.length);
        overlays.forEach((overlay) => {
          const dialogContent = overlay.parentElement?.querySelector('[data-radix-dialog-content]');
          const isOpen = dialogContent?.getAttribute('data-state') === 'open';
          if (!isOpen) {
            console.log("[DeckSelector] Removendo overlay órfão");
            (overlay as HTMLElement).style.display = 'none';
            overlay.remove();
          }
        });
      }, 300);
    }
  }, [open]);

  return (
    <Dialog 
      open={open} 
      onOpenChange={(newOpen) => {
        console.log("[DeckSelector] Dialog onOpenChange chamado com:", newOpen);
        onOpenChange(newOpen);
        
        // Se está fechando, forçar remoção de overlays após um delay
        if (!newOpen) {
          setTimeout(() => {
            const overlays = document.querySelectorAll('[data-radix-dialog-overlay]');
            overlays.forEach(overlay => {
              const dialogContent = overlay.parentElement?.querySelector('[data-radix-dialog-content]');
              if (!dialogContent || dialogContent.getAttribute('data-state') !== 'open') {
                console.log("[DeckSelector] Forçando remoção de overlay após fechar");
                (overlay as HTMLElement).style.display = 'none';
                overlay.remove();
              }
            });
          }, 500);
        }
      }}
    >
      <DialogContent 
        className="bg-card border-border max-w-2xl h-[85vh] flex flex-col overflow-hidden"
        onPointerDownOutside={(e) => {
          console.log("[DeckSelector] onPointerDownOutside - permitindo fechar");
        }}
        onEscapeKeyDown={(e) => {
          console.log("[DeckSelector] onEscapeKeyDown - permitindo fechar");
        }}
      >
        <DialogHeader className="flex-shrink-0">
          <DialogTitle className="text-card-foreground flex items-center gap-2">
            <Calendar className="w-5 h-5 text-primary" />
            {dialogTitle}
          </DialogTitle>
          <DialogDescription className="text-muted-foreground">
            {dialogDescription}
          </DialogDescription>
        </DialogHeader>

        {isLoading ? (
          <div className="flex items-center justify-center py-8 flex-shrink-0">
            <div className="flex gap-1">
              <div className="w-2 h-2 bg-primary/60 rounded-full animate-bounce"></div>
              <div className="w-2 h-2 bg-primary/60 rounded-full animate-bounce" style={{ animationDelay: "0.2s" }}></div>
              <div className="w-2 h-2 bg-primary/60 rounded-full animate-bounce" style={{ animationDelay: "0.4s" }}></div>
            </div>
          </div>
        ) : error ? (
          <div className="text-destructive text-center py-8 flex-shrink-0">
            {error}
            <Button variant="outline" size="sm" onClick={loadDecks} className="ml-2">
              Tentar novamente
            </Button>
          </div>
        ) : (
          <div className="flex flex-col flex-1 min-h-0 overflow-hidden">
            {/* Controles de seleção (apenas para modo multi) */}
            {mode === "multi" && (
              <div className="flex items-center justify-between py-2 border-b border-border flex-shrink-0">
                <div className="flex items-center gap-2">
                  <Badge variant={selectedDecks.size > 0 ? "default" : "secondary"}>
                    {selectedDecks.size} selecionado(s)
                  </Badge>
                  {selectedDecks.size >= 2 && (
                    <span className="text-xs text-muted-foreground">
                      (análise de {selectedDecks.size} decks)
                    </span>
                  )}
                </div>
                <div className="flex gap-2">
                  <Button variant="ghost" size="sm" onClick={handleSelectAll}>
                    {selectedDecks.size === decks.length ? "Desselecionar Todos" : "Selecionar Todos"}
                  </Button>
                  {selectedDecks.size > 0 && (
                    <Button variant="ghost" size="sm" onClick={handleClearSelection}>
                      <X className="w-4 h-4 mr-1" />
                      Limpar
                    </Button>
                  )}
                </div>
              </div>
            )}

            {/* Lista de decks */}
            <ScrollArea className="flex-1 min-h-0">
              <div className="grid gap-2 py-2 pr-4">
                {decks.map((deck) => {
                  const isSelected = selectedDecks.has(deck.name);
                  return (
                    <Card
                      key={deck.name}
                      className={`cursor-pointer transition-all duration-200 border-2 ${
                        isSelected
                          ? "border-primary bg-primary/5"
                          : "border-border hover:border-primary/50"
                      }`}
                      onClick={() => handleDeckClick(deck)}
                    >
                      <CardContent className="py-3 px-4 flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <div
                            className={`w-5 h-5 rounded-full border-2 flex items-center justify-center transition-colors ${
                              isSelected
                                ? "bg-primary border-primary"
                                : "border-muted-foreground"
                            }`}
                          >
                            {isSelected && <Check className="w-3 h-3 text-primary-foreground" />}
                          </div>
                          <div>
                            <p className="font-medium text-foreground">{deck.display_name}</p>
                            <p className="text-xs text-muted-foreground">Código: {deck.name}</p>
                          </div>
                        </div>
                        <Badge variant="outline" className="text-xs">
                          {deck.month.toString().padStart(2, "0")}/{deck.year}
                        </Badge>
                      </CardContent>
                    </Card>
                  );
                })}
              </div>
            </ScrollArea>
          </div>
        )}

        <DialogFooter className="pt-4 border-t border-border flex-shrink-0">
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancelar
          </Button>
          <Button onClick={handleConfirm} disabled={!canConfirm || isLoading}>
            {mode === "single" ? "Selecionar" : `Comparar ${selectedDecks.size} Decks`}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

// Componente auxiliar para exibir decks selecionados
interface SelectedDecksDisplayProps {
  decks: DeckInfo[];
  onRemove?: (deckName: string) => void;
  compact?: boolean;
}

export function SelectedDecksDisplay({ decks, onRemove, compact = false }: SelectedDecksDisplayProps) {
  if (decks.length === 0) return null;

  if (compact) {
    return (
      <div className="flex flex-wrap gap-1">
        {decks.map((deck) => (
          <Badge key={deck.name} variant="secondary" className="text-xs">
            {deck.display_name}
            {onRemove && (
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onRemove(deck.name);
                }}
                className="ml-1 hover:text-destructive"
              >
                <X className="w-3 h-3" />
              </button>
            )}
          </Badge>
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <p className="text-xs text-muted-foreground font-medium">Decks Selecionados:</p>
      <div className="flex flex-wrap gap-2">
        {decks.map((deck, index) => (
          <div key={deck.name} className="flex items-center gap-1">
            <Badge variant={index === 0 ? "default" : index === decks.length - 1 ? "default" : "secondary"}>
              {deck.display_name}
            </Badge>
            {index < decks.length - 1 && <span className="text-muted-foreground">→</span>}
          </div>
        ))}
      </div>
      {decks.length > 2 && (
        <p className="text-xs text-muted-foreground">
          Análise histórica de {decks.length} meses
        </p>
      )}
    </div>
  );
}
