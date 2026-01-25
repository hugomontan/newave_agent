"use client";

import React from "react";
import { motion } from "framer-motion";
import { Download } from "lucide-react";
import { exportToCSV } from "../shared/csvExport";

interface ExptOperacaoTableProps {
  data: Array<Record<string, any>>;
  tipo: string;
  tipoInfo: { nome: string; unidade: string };
}

export function ExptOperacaoTable({ data, tipo, tipoInfo }: ExptOperacaoTableProps) {
  if (!data || data.length === 0) {
    return null;
  }

  const handleDownloadCSV = () => {
    const csvData = data.map((row) => ({
      Código: row.codigo_usina || "",
      "Nome Usina": row.nome_usina || "",
      Valor: row.modificacao ?? null,
      "Data Início": row.data_inicio || "",
      "Data Fim": row.data_fim || "",
    }));
    exportToCSV(csvData, `expt-operacao-${tipo.toLowerCase()}`);
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-card border border-border rounded-lg overflow-hidden"
    >
      <div className="p-4 sm:p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-base sm:text-lg font-semibold text-card-foreground">
            {tipoInfo.nome}
          </h3>
          <button
            onClick={handleDownloadCSV}
            className="flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-card-foreground bg-background/50 hover:bg-background/70 border border-border rounded-lg transition-colors"
            title="Baixar como CSV"
          >
            <Download className="w-4 h-4" />
            CSV
          </button>
        </div>
        
        <div className="w-full">
          <table className="w-full text-sm table-fixed">
            <colgroup>
              <col className="w-[10%]" />
              <col className="w-[30%]" />
              <col className="w-[20%]" />
              <col className="w-[20%]" />
              <col className="w-[20%]" />
            </colgroup>
            <thead>
              <tr className="border-b border-border">
                <th className="text-left px-4 py-3 font-medium text-muted-foreground">Código</th>
                <th className="text-left px-4 py-3 font-medium text-muted-foreground">Nome Usina</th>
                <th className="text-right px-4 py-3 font-medium text-muted-foreground">Valor</th>
                <th className="text-left px-4 py-3 font-medium text-muted-foreground">Data Início</th>
                <th className="text-left px-4 py-3 font-medium text-muted-foreground">Data Fim</th>
              </tr>
            </thead>
            <tbody>
              {data.map((row, index) => (
                <tr
                  key={index}
                  className="border-b border-border/50 hover:bg-muted/30 transition-colors"
                >
                  <td className="px-4 py-3 whitespace-nowrap">{row.codigo_usina || 'N/A'}</td>
                  <td className="px-4 py-3 whitespace-nowrap">{row.nome_usina || 'N/A'}</td>
                  <td className="px-4 py-3 text-right font-mono whitespace-nowrap">
                    {row.valor_formatado || `${row.modificacao || 0} ${tipoInfo.unidade}`}
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap">{row.data_inicio || 'N/A'}</td>
                  <td className="px-4 py-3 whitespace-nowrap">{row.data_fim || 'N/A'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </motion.div>
  );
}
