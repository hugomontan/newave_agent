"use client";

import React from "react";
import { motion } from "framer-motion";
import { ModifOperacaoTable } from "./ModifOperacaoTable";
import type { SingleDeckVisualizationData } from "../shared/types";

interface ModifOperacaoViewProps {
  visualizationData: SingleDeckVisualizationData;
}

// Dicionário de explicações para cada tipo
const explicacoes_tipos: Record<string, { nome: string; descricao: string; unidade: string }> = {
  'VOLMIN': {
    'nome': 'Volume Mínimo Operativo',
    'descricao': 'Volume mínimo operativo da usina hidrelétrica. Pode ser especificado em H/h (hectômetros cúbicos) ou % (percentual do volume útil).',
    'unidade': 'H/h ou %'
  },
  'VOLMAX': {
    'nome': 'Volume Máximo Operativo',
    'descricao': 'Volume máximo operativo da usina hidrelétrica. Pode ser especificado em H/h (hectômetros cúbicos) ou % (percentual do volume útil).',
    'unidade': 'H/h ou %'
  },
  'VMAXT': {
    'nome': 'Volume Máximo com Data',
    'descricao': 'Volume máximo operativo com data de início. Modificação temporal que altera o volume máximo a partir de uma data específica. Referenciado ao final do período.',
    'unidade': 'H/h ou %'
  },
  'VMINT': {
    'nome': 'Volume Mínimo com Data',
    'descricao': 'Volume mínimo operativo com data de início. Modificação temporal que altera o volume mínimo a partir de uma data específica. Referenciado ao final do período.',
    'unidade': 'H/h ou %'
  },
  'VMINP': {
    'nome': 'Volume Mínimo com Penalidade',
    'descricao': 'Volume mínimo com adoção de penalidade, com data. Implementa mecanismo de aversão a risco. O valor considerado será o mais restritivo entre MODIF.DAT (por usina) e CURVA.DAT (por REE).',
    'unidade': 'H/h ou %'
  },
  'VAZMIN': {
    'nome': 'Vazão Mínima',
    'descricao': 'Vazão mínima obrigatória da usina. Pode ter até dois valores: requisito total e valor para relaxamento (opcional, menor que o primeiro).',
    'unidade': 'm³/s'
  },
  'VAZMINT': {
    'nome': 'Vazão Mínima com Data',
    'descricao': 'Vazão mínima obrigatória com data de início. Modificação temporal que altera a vazão mínima a partir de uma data específica.',
    'unidade': 'm³/s'
  },
  'VAZMAXT': {
    'nome': 'Vazão Máxima com Data',
    'descricao': 'Vazão máxima (defluência máxima) com data. Considerada apenas em períodos individualizados, se os flags apropriados estiverem habilitados no dger.dat.',
    'unidade': 'm³/s'
  },
  'CFUGA': {
    'nome': 'Canal de Fuga',
    'descricao': 'Nível do canal de fuga da usina. Modificação temporal que altera o nível do canal de fuga a partir de uma data específica. Referenciado ao início do período.',
    'unidade': 'm'
  },
  'CMONT': {
    'nome': 'Nível de Montante',
    'descricao': 'Nível de montante da usina. Modificação temporal que altera o nível de montante a partir de uma data específica. Permitido somente para usinas fio d\'água.',
    'unidade': 'm'
  },
  'TURBMAXT': {
    'nome': 'Turbinamento Máximo com Data',
    'descricao': 'Turbinamento máximo com data e por patamar. Considerado apenas em períodos individualizados, se os flags apropriados estiverem habilitados no dger.dat.',
    'unidade': 'm³/s'
  },
  'TURBMINT': {
    'nome': 'Turbinamento Mínimo com Data',
    'descricao': 'Turbinamento mínimo com data e por patamar. Considerado apenas em períodos individualizados, se os flags apropriados estiverem habilitados no dger.dat.',
    'unidade': 'm³/s'
  },
  'POTEFE': {
    'nome': 'Potência Efetiva',
    'descricao': 'Potência efetiva da usina hidrelétrica. Modificação da potência efetiva por conjunto de máquinas.',
    'unidade': 'MW'
  },
  'TEIF': {
    'nome': 'Taxa Esperada de Indisponibilidade Forçada',
    'descricao': 'Taxa esperada de indisponibilidade forçada da usina. Representa indisponibilidades não programadas (forçadas).',
    'unidade': '%'
  },
  'IP': {
    'nome': 'Indisponibilidade Programada',
    'descricao': 'Indisponibilidade programada da usina. Representa períodos de manutenção programada onde a usina não estará disponível.',
    'unidade': '%'
  },
  'NUMCNJ': {
    'nome': 'Número de Conjuntos de Máquinas',
    'descricao': 'Número de conjuntos de máquinas da usina. Modifica a quantidade de conjuntos de máquinas.',
    'unidade': 'unidade'
  },
  'NUMMAQ': {
    'nome': 'Número de Máquinas por Conjunto',
    'descricao': 'Número de máquinas por conjunto. Modifica a quantidade de máquinas em um conjunto específico.',
    'unidade': 'unidade'
  }
};

export function ModifOperacaoView({ visualizationData }: ModifOperacaoViewProps) {
  const { table, tables_by_tipo, filtros, stats_geral } = visualizationData;

  if (!table || table.length === 0) {
    return (
      <div className="bg-card border border-border rounded-lg p-4 sm:p-6 mt-4">
        <h3 className="text-base sm:text-lg font-semibold text-card-foreground mb-2">
          Modificações Hídricas
        </h3>
        <p className="text-sm text-muted-foreground">Nenhum dado disponível.</p>
      </div>
    );
  }

  // Se houver múltiplos tipos, renderizar tabelas separadas
  const hasMultipleTipos = tables_by_tipo && Object.keys(tables_by_tipo).length > 1;

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="w-full mt-4 space-y-6"
    >
      {/* Informações sobre filtros */}
      {filtros && (
        <div className="bg-card border border-border rounded-lg p-4 sm:p-6">
          <h3 className="text-base sm:text-lg font-semibold text-card-foreground mb-3">
            Filtros Aplicados
          </h3>
          <div className="space-y-2 text-sm">
            {filtros.usina && (
              <p>
                <strong>Usina:</strong> {filtros.usina.nome} (Código: {filtros.usina.codigo})
              </p>
            )}
            {filtros.tipo_modificacao && (
              <p>
                <strong>Tipo de Modificação:</strong> {filtros.tipo_modificacao}
              </p>
            )}
          </div>
        </div>
      )}

      {/* Tabelas por tipo */}
      {hasMultipleTipos && tables_by_tipo ? (
        // Renderizar tabela separada para cada tipo
        Object.entries(tables_by_tipo).map(([tipo, tableData]) => (
          <ModifOperacaoTable
            key={tipo}
            data={tableData as Array<Record<string, any>>}
            tipo={tipo}
            explicacao={explicacoes_tipos[tipo]}
          />
        ))
      ) : (
        // Renderizar tabela única
        tables_by_tipo && Object.keys(tables_by_tipo).length === 1 ? (
          Object.entries(tables_by_tipo).map(([tipo, tableData]) => (
            <ModifOperacaoTable
              key={tipo}
              data={tableData as Array<Record<string, any>>}
              tipo={tipo}
              explicacao={explicacoes_tipos[tipo]}
            />
          ))
        ) : (
          <div className="bg-card border border-border rounded-lg p-4 sm:p-6">
            <p className="text-sm text-muted-foreground">Dados não disponíveis em formato tabular.</p>
          </div>
        )
      )}
    </motion.div>
  );
}
