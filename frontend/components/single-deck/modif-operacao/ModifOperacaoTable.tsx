"use client";

import React from "react";
import { Download } from "lucide-react";
import { exportToCSV } from "../shared/csvExport";
import type { TableRow } from "../shared/types";

interface ModifOperacaoTableProps {
  data: Array<Record<string, any>>;
  tipo: string;
  explicacao?: {
    nome: string;
    descricao: string;
    unidade: string;
  };
}

export function ModifOperacaoTable({ data, tipo, explicacao }: ModifOperacaoTableProps) {
  if (!data || data.length === 0) {
    return null;
  }

  const handleDownloadCSV = () => {
    exportToCSV(data, `modif-operacao-${tipo.toLowerCase()}`);
  };

  // Determinar colunas baseado no tipo
  const getColumns = () => {
    const tiposVolume = ['VOLMIN', 'VOLMAX', 'VMAXT', 'VMINT', 'VMINP'];
    const tiposVazao = ['VAZMIN', 'VAZMINT', 'VAZMAXT'];
    const tiposNivel = ['CFUGA', 'CMONT'];
    const tiposTurbinamento = ['TURBMAXT', 'TURBMINT'];
    
    if (tiposVolume.includes(tipo)) {
      return ['codigo', 'nome', 'volume', 'unidade', 'data_inicio'];
    } else if (tiposVazao.includes(tipo)) {
      return ['codigo', 'nome', 'vazao', 'data_inicio'];
    } else if (tiposNivel.includes(tipo)) {
      return ['codigo', 'nome', 'nivel', 'data_inicio'];
    } else if (tiposTurbinamento.includes(tipo)) {
      return ['codigo', 'nome', 'patamar', 'turbinamento', 'data_inicio'];
    } else if (tipo === 'NUMCNJ') {
      return ['codigo', 'nome', 'numero'];
    } else if (tipo === 'NUMMAQ') {
      return ['codigo', 'nome', 'conjunto', 'numero_maquinas'];
    } else {
      return ['codigo', 'nome', 'valor'];
    }
  };

  const getColumnHeaders = () => {
    const tiposVolume = ['VOLMIN', 'VOLMAX', 'VMAXT', 'VMINT', 'VMINP'];
    const tiposVazao = ['VAZMIN', 'VAZMINT', 'VAZMAXT'];
    const tiposNivel = ['CFUGA', 'CMONT'];
    const tiposTurbinamento = ['TURBMAXT', 'TURBMINT'];
    
    if (tiposVolume.includes(tipo)) {
      return ['Código', 'Nome Usina', 'Volume', 'Unidade', 'Data Início'];
    } else if (tiposVazao.includes(tipo)) {
      return ['Código', 'Nome Usina', 'Vazão (m³/s)', 'Data Início'];
    } else if (tiposNivel.includes(tipo)) {
      return ['Código', 'Nome Usina', 'Nível (m)', 'Data Início'];
    } else if (tiposTurbinamento.includes(tipo)) {
      return ['Código', 'Nome Usina', 'Patamar', 'Turbinamento (m³/s)', 'Data Início'];
    } else if (tipo === 'NUMCNJ') {
      return ['Código', 'Nome Usina', 'Número de Conjuntos'];
    } else if (tipo === 'NUMMAQ') {
      return ['Código', 'Nome Usina', 'Conjunto', 'Número de Máquinas'];
    } else {
      return ['Código', 'Nome Usina', 'Valor'];
    }
  };

  const formatValue = (value: any, column: string) => {
    if (value === null || value === undefined) return "-";
    
    if (column === 'volume' || column === 'vazao' || column === 'nivel' || column === 'turbinamento') {
      try {
        const numValue = typeof value === 'string' ? parseFloat(value) : value;
        return typeof numValue === 'number' && !isNaN(numValue) 
          ? numValue.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
          : String(value);
      } catch {
        return String(value);
      }
    }
    
    return String(value);
  };

  const columns = getColumns();
  const headers = getColumnHeaders();

  return (
    <div className="bg-card border border-border rounded-lg p-4 sm:p-6">
      {explicacao && (
        <div className="mb-4">
          <h4 className="text-base sm:text-lg font-semibold text-card-foreground mb-2">
            {explicacao.nome} ({tipo})
          </h4>
          <p className="text-sm text-muted-foreground mb-2">{explicacao.descricao}</p>
          <p className="text-xs text-muted-foreground">
            <strong>Total de registros:</strong> {data.length}
          </p>
        </div>
      )}
      
      <div className="flex items-center justify-between mb-4">
        <h5 className="text-sm font-medium text-card-foreground">
          {explicacao ? `Dados - ${explicacao.nome}` : `Tipo: ${tipo}`}
        </h5>
        <button
          onClick={handleDownloadCSV}
          className="flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-card-foreground bg-background/50 hover:bg-background/70 border border-border rounded-lg transition-colors"
        >
          <Download className="w-4 h-4" />
          CSV
        </button>
      </div>

      <div className="overflow-x-auto">
        <table className="min-w-full border-collapse">
          <thead>
            <tr className="border-b border-border bg-background/50">
              {headers.map((header, idx) => (
                <th
                  key={idx}
                  className="px-4 py-3 text-left text-xs font-semibold text-card-foreground uppercase"
                >
                  {header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {data.map((row, index) => (
              <tr
                key={index}
                className="border-b border-border/50 hover:bg-background/30"
              >
                {columns.map((col, idx) => {
                  const value = row[col] || row[col.replace('codigo', 'codigo_usina')] || row[col.replace('nome', 'nome_usina')];
                  return (
                    <td key={idx} className="px-4 py-2.5 text-sm text-card-foreground">
                      {formatValue(value, col)}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
