"use client";

import React, { useState } from "react";
import { Download } from "lucide-react";
import { exportToCSV } from "../shared/csvExport";
import type { TableRow } from "../shared/types";

interface CargaMensalTableProps {
  data: TableRow[];
  deck1Name: string;
  deck2Name: string;
  deckNames?: string[]; // Suporte para N decks
}

// Função para converter "Dez/2025" para "2025-12"
const convertPeriodoToYYYYMM = (periodo: string): string => {
  // Mapeamento de meses
  const mesesMap: Record<string, string> = {
    "Jan": "01", "Fev": "02", "Mar": "03", "Abr": "04",
    "Mai": "05", "Jun": "06", "Jul": "07", "Ago": "08",
    "Set": "09", "Out": "10", "Nov": "11", "Dez": "12"
  };
  
  // Tentar padrão "Mês/Ano" (ex: "Dez/2025")
  const match = periodo.match(/^([A-Za-z]{3})\/(\d{4})$/);
  if (match) {
    const [, mesNome, ano] = match;
    const mesNum = mesesMap[mesNome];
    if (mesNum) {
      return `${ano}-${mesNum}`;
    }
  }
  
  // Se já estiver no formato YYYY-MM, retornar direto
  if (periodo.match(/^\d{4}-\d{2}$/)) {
    return periodo;
  }
  
  return periodo; // Fallback: retornar original
};

// Função para formatar valores de carga (sempre inteiros, sem decimais)
const formatCargaValue = (value: number | null | undefined): string => {
  if (value === null || value === undefined) return "-";
  // Converter para inteiro (arredondar)
  const intValue = Math.round(Number(value));
  return intValue.toLocaleString('pt-BR', { 
    minimumFractionDigits: 0, 
    maximumFractionDigits: 0 
  });
};

export function CargaMensalTable({ data, deck1Name, deck2Name, deckNames }: CargaMensalTableProps) {
  // Determinar quais decks usar (suporte N decks)
  const allDeckNames = deckNames && deckNames.length > 0 ? deckNames : [deck1Name, deck2Name];
  
  // Verificar quantos decks estão presentes nos dados
  const detectDeckCount = () => {
    if (!data || data.length === 0) return allDeckNames.length;
    const firstRow = data[0];
    if (!firstRow) return allDeckNames.length;
    
    // Contar colunas deck_N nos dados
    let maxDeckIndex = 0;
    for (const key in firstRow) {
      if (key.startsWith('deck_')) {
        const match = key.match(/^deck_(\d+)$/);
        if (match) {
          const deckIndex = parseInt(match[1]);
          if (deckIndex > maxDeckIndex) {
            maxDeckIndex = deckIndex;
          }
        }
      }
    }
    
    // Se encontrou colunas deck_N, usar o máximo encontrado
    if (maxDeckIndex > 0) {
      return Math.max(maxDeckIndex, allDeckNames.length);
    }
    
    return allDeckNames.length;
  };
  
  const deckCount = detectDeckCount();
  const deckNamesToUse = allDeckNames.slice(0, deckCount);
  const [isExpanded, setIsExpanded] = useState(false);
  const INITIAL_ROWS = 10;
  const hasMoreRows = data.length > INITIAL_ROWS;
  const displayedData = isExpanded ? data : data.slice(0, INITIAL_ROWS);

  if (!data || data.length === 0) {
    return (
      <div className="bg-card border border-border rounded-lg p-4 sm:p-6">
        <h3 className="text-base sm:text-lg font-semibold text-card-foreground mb-2">
          Comparação de Carga Mensal
        </h3>
        <p className="text-sm text-muted-foreground">
          Nenhum dado disponível.
        </p>
      </div>
    );
  }

  const handleDownloadCSV = () => {
    const csvData = data.map((row) => {
      let dataFormatada = "";
      const ano = row.ano;
      const mes = row.mes;
      
      if (ano !== undefined && ano !== null && mes !== undefined && mes !== null) {
        const mesFormatado = String(mes).padStart(2, '0');
        dataFormatada = `${ano}-${mesFormatado}`;
      } else if (row.data) {
        dataFormatada = convertPeriodoToYYYYMM(String(row.data));
      }
      
      const csvRow: Record<string, any> = {
        Data: dataFormatada || "-",
      };
      
      // Adicionar colunas para todos os decks
      deckNamesToUse.forEach((name, index) => {
        const deckKey = `deck_${index + 1}` as keyof TableRow;
        csvRow[name] = (row[deckKey] as number | null) ?? null;
      });
      
      return csvRow;
    });
    exportToCSV(csvData, "carga_mensal");
  };

  return (
    <div className="bg-card border border-border rounded-lg p-4 sm:p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-base sm:text-lg font-semibold text-card-foreground">
          Comparação de Carga Mensal
        </h3>
        <div className="flex items-center gap-3">
          <span className="text-sm text-muted-foreground">
            {data.length} registros
          </span>
          <button
            onClick={handleDownloadCSV}
            className="flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-card-foreground bg-background/50 hover:bg-background/70 border border-border rounded-lg transition-colors"
            title="Baixar como CSV"
          >
            <Download className="w-4 h-4" />
            CSV
          </button>
        </div>
      </div>

      <div className="overflow-x-auto -mx-4 sm:mx-0">
        <div className="inline-block min-w-full align-middle px-4 sm:px-0">
          <table className="min-w-full border-collapse">
            <thead>
              <tr className="border-b border-border bg-background/50">
                <th className="px-3 sm:px-4 py-3 text-left text-xs font-semibold text-card-foreground uppercase tracking-wider whitespace-nowrap">
                  Data
                </th>
                {deckNamesToUse.map((name, index) => {
                  const colors = ["text-blue-400", "text-purple-400", "text-green-400", "text-yellow-400", "text-pink-400", "text-cyan-400", "text-orange-400", "text-indigo-400", "text-red-400", "text-teal-400", "text-lime-400", "text-amber-400"];
                  return (
                    <th 
                      key={name}
                      className={`px-3 sm:px-4 py-3 text-right text-xs font-semibold ${colors[index % colors.length]} uppercase tracking-wider whitespace-nowrap`}
                    >
                      {name}
                    </th>
                  );
                })}
              </tr>
            </thead>
          <tbody>
            {displayedData.map((row, index) => {
              // Construir formato YYYY-MM
              let dataFormatada = "";
              const ano = row.ano;
              const mes = row.mes;
              
              if (ano !== undefined && ano !== null && mes !== undefined && mes !== null) {
                // Formatar como YYYY-MM (ex: "2025-12")
                const mesFormatado = String(mes).padStart(2, '0');
                dataFormatada = `${ano}-${mesFormatado}`;
              } else if (row.data) {
                // Converter "Dez/2025" para "2025-12"
                dataFormatada = convertPeriodoToYYYYMM(String(row.data));
              }
              
              return (
                <tr
                  key={`${dataFormatada}-${index}`}
                  className="border-b border-border/50 hover:bg-background/30 transition-colors"
                >
                  <td className="px-3 sm:px-4 py-2.5 text-sm text-card-foreground font-medium whitespace-nowrap">
                    {dataFormatada || "-"}
                  </td>
                  {deckNamesToUse.map((name, deckIndex) => {
                    const deckKey = `deck_${deckIndex + 1}` as keyof TableRow;
                    const value = (row[deckKey] as number | null) ?? null;
                    const colors = ["text-blue-400", "text-purple-400", "text-green-400", "text-yellow-400", "text-pink-400", "text-cyan-400", "text-orange-400", "text-indigo-400", "text-red-400", "text-teal-400", "text-lime-400", "text-amber-400"];
                    return (
                      <td 
                        key={name}
                        className={`px-3 sm:px-4 py-2.5 text-sm ${colors[deckIndex % colors.length]} text-right whitespace-nowrap font-mono`}
                      >
                        {formatCargaValue(value)}
                      </td>
                    );
                  })}
                </tr>
              );
            })}
            </tbody>
          </table>
        </div>
      </div>

      {hasMoreRows && (
        <div className="mt-4 flex justify-center">
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="px-4 py-2 text-sm font-medium text-card-foreground bg-background/50 hover:bg-background/70 border border-border rounded-lg transition-colors"
          >
            {isExpanded 
              ? `Mostrar menos (${INITIAL_ROWS} primeiros)` 
              : `Mostrar todos (${data.length - INITIAL_ROWS} restantes)`}
          </button>
        </div>
      )}
    </div>
  );
}
