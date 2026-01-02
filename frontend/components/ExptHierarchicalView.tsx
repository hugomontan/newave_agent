"use client";

import React, { useState } from "react";
import { DifferencesTable } from "./DifferencesTable";
import { motion } from "framer-motion";
import { ChevronDown, ChevronRight, Building2, Settings } from "lucide-react";

interface ExptHierarchicalViewProps {
  comparison: {
    comparison_by_type?: Record<string, {
      comparison_table: Array<{
        codigo_usina?: number;
        nome_usina?: string;
        tipo: string;
        data_inicio?: string | null;
        data_fim?: string | null;
        deck_1_value?: number | null;
        deck_2_value?: number | null;
        difference?: number | null;
        difference_percent?: number | null;
        status: string;
      }>;
      summary: {
        total_dezembro: number;
        total_janeiro: number;
        added_count: number;
        removed_count: number;
        modified_count: number;
      };
    }>;
    comparison_by_usina?: Record<string, {
      codigo_usina: number;
      nome_usina: string;
      comparison_table: Array<{
        tipo: string;
        data_inicio?: string | null;
        data_fim?: string | null;
        deck_1_value?: number | null;
        deck_2_value?: number | null;
        difference?: number | null;
        difference_percent?: number | null;
        status: string;
      }>;
      summary: {
        total_modificacoes_dezembro: number;
        total_modificacoes_janeiro: number;
        novas_modificacoes: number;
        modificacoes_removidas: number;
        modificacoes_alteradas: number;
      };
    }>;
    deck_1: {
      name: string;
    };
    deck_2: {
      name: string;
    };
  };
}

const TIPO_LABELS: Record<string, string> = {
  POTEF: "Potência Efetiva",
  GTMIN: "Geração Mínima",
  FCMAX: "Fator de Capacidade Máximo",
  IPTER: "Indisponibilidade Programada",
  TEIFT: "Taxa de Indisponibilidade Forçada",
};

const STATUS_COLORS: Record<string, string> = {
  added: "text-green-400",
  removed: "text-red-400",
  modified: "text-yellow-400",
  unchanged: "text-gray-400",
};

const STATUS_LABELS: Record<string, string> = {
  added: "Adicionado",
  removed: "Removido",
  modified: "Modificado",
  unchanged: "Sem alteração",
};

export function ExptHierarchicalView({ comparison }: ExptHierarchicalViewProps) {
  const [expandedTypes, setExpandedTypes] = useState<Set<string>>(new Set());
  const [expandedUsinas, setExpandedUsinas] = useState<Set<string>>(new Set());
  const [activeTab, setActiveTab] = useState<"type" | "usina">("type");

  const comparison_by_type = comparison.comparison_by_type || {};
  const comparison_by_usina = comparison.comparison_by_usina || {};

  const toggleType = (tipo: string) => {
    const newExpanded = new Set(expandedTypes);
    if (newExpanded.has(tipo)) {
      newExpanded.delete(tipo);
    } else {
      newExpanded.add(tipo);
    }
    setExpandedTypes(newExpanded);
  };

  const toggleUsina = (codigo: string) => {
    const newExpanded = new Set(expandedUsinas);
    if (newExpanded.has(codigo)) {
      newExpanded.delete(codigo);
    } else {
      newExpanded.add(codigo);
    }
    setExpandedUsinas(newExpanded);
  };

  const formatTableRow = (row: any) => {
    // Determinar o campo de período baseado no tipo de visualização
    let period = "";
    if (activeTab === "type") {
      // Na visualização por tipo, mostrar usina e datas
      period = `${row.nome_usina || `Usina ${row.codigo_usina}`}`;
      if (row.data_inicio) {
        period += ` (${row.data_inicio}`;
        if (row.data_fim) {
          period += ` - ${row.data_fim}`;
        }
        period += ")";
      }
    } else {
      // Na visualização por usina, mostrar tipo e datas
      period = `${TIPO_LABELS[row.tipo] || row.tipo}`;
      if (row.data_inicio) {
        period += ` (${row.data_inicio}`;
        if (row.data_fim) {
          period += ` - ${row.data_fim}`;
        }
        period += ")";
      }
    }

    return {
      field: row.tipo || "",
      period: period,
      deck_1_value: row.deck_1_value ?? 0,
      deck_2_value: row.deck_2_value ?? 0,
      difference: row.difference ?? 0,
      difference_percent: row.difference_percent ?? 0,
    };
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="w-full space-y-6 mt-4"
    >
      {/* Tabs para alternar entre visualização por tipo e por usina */}
      <div className="flex gap-2 border-b border-border">
        <button
          onClick={() => setActiveTab("type")}
          className={`px-4 py-2 text-sm font-medium transition-colors ${
            activeTab === "type"
              ? "text-primary border-b-2 border-primary"
              : "text-muted-foreground hover:text-foreground"
          }`}
        >
          <Settings className="inline w-4 h-4 mr-2" />
          Por Tipo de Modificação
        </button>
        <button
          onClick={() => setActiveTab("usina")}
          className={`px-4 py-2 text-sm font-medium transition-colors ${
            activeTab === "usina"
              ? "text-primary border-b-2 border-primary"
              : "text-muted-foreground hover:text-foreground"
          }`}
        >
          <Building2 className="inline w-4 h-4 mr-2" />
          Por Usina
        </button>
      </div>

      {/* Visualização por Tipo */}
      {activeTab === "type" && (
        <div className="space-y-4">
          {Object.entries(comparison_by_type).map(([tipo, data]) => {
            const isExpanded = expandedTypes.has(tipo);
            const tipoLabel = TIPO_LABELS[tipo] || tipo;
            const { summary, comparison_table } = data;

            return (
              <motion.div
                key={tipo}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="border border-border rounded-lg overflow-hidden"
              >
                {/* Cabeçalho do tipo */}
                <button
                  onClick={() => toggleType(tipo)}
                  className="w-full px-4 py-3 bg-muted/50 hover:bg-muted/70 transition-colors flex items-center justify-between"
                >
                  <div className="flex items-center gap-3">
                    {isExpanded ? (
                      <ChevronDown className="w-4 h-4" />
                    ) : (
                      <ChevronRight className="w-4 h-4" />
                    )}
                    <span className="font-semibold text-sm">{tipoLabel}</span>
                    <span className="text-xs text-muted-foreground">
                      ({summary.total_dezembro} → {summary.total_janeiro})
                    </span>
                  </div>
                  <div className="flex gap-2 text-xs">
                    {summary.added_count > 0 && (
                      <span className="text-green-400">+{summary.added_count}</span>
                    )}
                    {summary.removed_count > 0 && (
                      <span className="text-red-400">-{summary.removed_count}</span>
                    )}
                    {summary.modified_count > 0 && (
                      <span className="text-yellow-400">~{summary.modified_count}</span>
                    )}
                  </div>
                </button>

                {/* Tabela do tipo (expandida) */}
                {isExpanded && comparison_table && comparison_table.length > 0 && (
                  <div className="p-4">
                    <DifferencesTable
                      differences={comparison_table.map(formatTableRow)}
                      deck1Name={comparison.deck_1.name}
                      deck2Name={comparison.deck_2.name}
                    />
                  </div>
                )}
              </motion.div>
            );
          })}
        </div>
      )}

      {/* Visualização por Usina */}
      {activeTab === "usina" && (
        <div className="space-y-4">
          {Object.entries(comparison_by_usina).map(([codigo, data]) => {
            const isExpanded = expandedUsinas.has(codigo);
            const { nome_usina, summary, comparison_table } = data;

            return (
              <motion.div
                key={codigo}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="border border-border rounded-lg overflow-hidden"
              >
                {/* Cabeçalho da usina */}
                <button
                  onClick={() => toggleUsina(codigo)}
                  className="w-full px-4 py-3 bg-muted/50 hover:bg-muted/70 transition-colors flex items-center justify-between"
                >
                  <div className="flex items-center gap-3">
                    {isExpanded ? (
                      <ChevronDown className="w-4 h-4" />
                    ) : (
                      <ChevronRight className="w-4 h-4" />
                    )}
                    <span className="font-semibold text-sm">
                      {nome_usina} (Código: {codigo})
                    </span>
                    <span className="text-xs text-muted-foreground">
                      ({summary.total_modificacoes_dezembro} → {summary.total_modificacoes_janeiro})
                    </span>
                  </div>
                  <div className="flex gap-2 text-xs">
                    {summary.novas_modificacoes > 0 && (
                      <span className="text-green-400">+{summary.novas_modificacoes}</span>
                    )}
                    {summary.modificacoes_removidas > 0 && (
                      <span className="text-red-400">-{summary.modificacoes_removidas}</span>
                    )}
                    {summary.modificacoes_alteradas > 0 && (
                      <span className="text-yellow-400">~{summary.modificacoes_alteradas}</span>
                    )}
                  </div>
                </button>

                {/* Tabela da usina (expandida) */}
                {isExpanded && comparison_table && comparison_table.length > 0 && (
                  <div className="p-4">
                    <DifferencesTable
                      differences={comparison_table.map(formatTableRow)}
                      deck1Name={comparison.deck_1.name}
                      deck2Name={comparison.deck_2.name}
                    />
                  </div>
                )}
              </motion.div>
            );
          })}
        </div>
      )}

      {/* Mensagem se não houver dados */}
      {Object.keys(comparison_by_type).length === 0 && Object.keys(comparison_by_usina).length === 0 && (
        <div className="text-center py-8 text-muted-foreground">
          Nenhuma modificação térmica encontrada para comparação.
        </div>
      )}
    </motion.div>
  );
}

