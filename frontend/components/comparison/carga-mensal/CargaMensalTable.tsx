"use client";

import React, { useState } from "react";
import { Download } from "lucide-react";
import { exportToCSV } from "../shared/csvExport";
import type { TableRow } from "../shared/types";

interface CargaMensalTableProps {
  data: TableRow[];
  deck1Name: string;
  deck2Name: string;
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

export function CargaMensalTable({ data, deck1Name, deck2Name }: CargaMensalTableProps) {
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
      
      return {
        Data: dataFormatada || "-",
        [deck1Name]: row.deck_1 ?? row.deck_1_value ?? null,
        [deck2Name]: row.deck_2 ?? row.deck_2_value ?? null,
      };
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
                <th className="px-3 sm:px-4 py-3 text-right text-xs font-semibold text-blue-400 uppercase tracking-wider whitespace-nowrap">
                  {deck1Name}
                </th>
                <th className="px-3 sm:px-4 py-3 text-right text-xs font-semibold text-purple-400 uppercase tracking-wider whitespace-nowrap">
                  {deck2Name}
                </th>
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
              
              const deck1Value = row.deck_1 ?? row.deck_1_value ?? null;
              const deck2Value = row.deck_2 ?? row.deck_2_value ?? null;

              return (
                <tr
                  key={`${dataFormatada}-${index}`}
                  className="border-b border-border/50 hover:bg-background/30 transition-colors"
                >
                  <td className="px-3 sm:px-4 py-2.5 text-sm text-card-foreground font-medium whitespace-nowrap">
                    {dataFormatada || "-"}
                  </td>
                  <td className="px-3 sm:px-4 py-2.5 text-sm text-blue-400 text-right whitespace-nowrap font-mono">
                    {formatCargaValue(deck1Value)}
                  </td>
                  <td className="px-3 sm:px-4 py-2.5 text-sm text-purple-400 text-right whitespace-nowrap font-mono">
                    {formatCargaValue(deck2Value)}
                  </td>
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
