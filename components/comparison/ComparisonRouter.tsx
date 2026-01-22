"use client";

import React from "react";
import { CargaMensalView } from "./carga-mensal";
import { LimitesIntercambioView } from "./limites-intercambio";
import { GTMINView } from "./gtmin";
import { VazaoMinimaView } from "./vazao-minima";
import { CVUView } from "./cvu";
import { ReservatorioInicialView } from "./reservatorio-inicial";
import { UsinasNaoSimuladasView } from "./usinas-nao-simuladas";
import { RestricaoEletricaView } from "./restricao-eletrica";
import { InflexibilidadeComparisonView } from "./inflexibilidade";
import { CVUComparisonView } from "./cvu-decomp";
import { VolumeInicialComparisonView } from "./volume-inicial";
import { DPComparisonView } from "./dp-decomp";
import { PQComparisonView } from "./pq-decomp";
import { CargaAndeComparisonView } from "./carga-ande-decomp";
import { LimitesIntercambioComparisonView } from "./limites-intercambio-decomp";
import { RestricoesEletricasComparisonView } from "./restricao-eletrica-decomp";
import { RestricoesVazaoHQComparisonView } from "./restricao-vazao-hq-decomp";
import { GLComparisonView } from "./gl-decomp/GLComparisonView";
import type { ComparisonData } from "./shared/types";

interface ComparisonRouterProps {
  comparison: ComparisonData;
}

export function ComparisonRouter({ comparison }: ComparisonRouterProps) {
  const { visualization_type, tool_name, comparison_table, chart_data, chart_config } = comparison;

  // Normalizar visualization_type (remover espaços, converter para string)
  const normalizedVizType = visualization_type?.toString().trim();
  // Normalizar tool_name com múltiplas tentativas (case-insensitive, remover espaços)
  const normalizedToolName = tool_name 
    ? tool_name.toString().trim() 
    : (chart_config as any)?.tool_name?.toString().trim() || "";
  
  // DEBUG: Log para identificar problemas
  if (process.env.NODE_ENV === 'development') {
    console.log('[ComparisonRouter] Debug:', {
      tool_name,
      normalizedToolName,
      visualization_type: normalizedVizType,
      chart_config_tool_name: (chart_config as any)?.tool_name,
      hasTableData: comparison_table && comparison_table.length > 0,
      hasChartData: chart_data && chart_data.labels && chart_data.labels.length > 0
    });
  }
  
  // Verificar se há dados para renderizar mesmo sem visualization_type específico
  const hasTableData = comparison_table && comparison_table.length > 0;
  const hasChartData = chart_data && chart_data.labels && chart_data.labels.length > 0;
  
  // Verificar tool_name PRIMEIRO, antes do switch (prioridade máxima)
  // SEMPRE usar UsinasNaoSimuladasView para UsinasNaoSimuladasTool, SEM EXCEÇÃO
  // Verificação case-insensitive para garantir que funcione mesmo com variações
  if (normalizedToolName.toLowerCase() === "usinasnaosimuladastool") {
    if (process.env.NODE_ENV === 'development') {
      console.log('[ComparisonRouter] ✅ Usando UsinasNaoSimuladasView para UsinasNaoSimuladasTool');
    }
    return <UsinasNaoSimuladasView comparison={comparison} />;
  }
  
  // Verificar GL (multi-deck) - ANTES do switch para garantir detecção
  const isGLTool = (
    normalizedToolName === "GLGeracoesGNLTool" || 
    normalizedToolName === "GLMultiDeckTool" ||
    normalizedToolName.toLowerCase().includes("glgeracoesgnl") ||
    normalizedToolName.toLowerCase().includes("geracoes gnl") ||
    normalizedToolName.toLowerCase().includes("gerações gnl") ||
    normalizedToolName.toLowerCase().startsWith("gl") ||
    normalizedVizType === "gl_comparison"
  );
  
  if (isGLTool && comparison.is_multi_deck) {
    if (process.env.NODE_ENV === 'development') {
      console.log('[ComparisonRouter] ✅ Usando GLComparisonView para GL tool (detectado antes do switch)');
    }
    return <GLComparisonView comparison={comparison} />;
  }
  
  // Verificar InflexibilidadeUsinaTool ou InflexibilidadeMultiDeckTool
  if (
    normalizedToolName.toLowerCase() === "inflexibilidadeusinatool" ||
    normalizedToolName.toLowerCase() === "inflexibilidademultidecktool" ||
    normalizedToolName.toLowerCase().includes("inflexibilidade")
  ) {
    if (process.env.NODE_ENV === 'development') {
      console.log('[ComparisonRouter] ✅ Usando InflexibilidadeComparisonView para InflexibilidadeTool');
    }
    return <InflexibilidadeComparisonView comparison={comparison} />;
  }
  
  // Verificar VolumeInicialMultiDeckTool ou UHUsinasHidrelétricasTool (em contexto multi-deck)
  if (
    normalizedToolName.toLowerCase() === "volumeinicialmultidecktool" ||
    normalizedToolName.toLowerCase() === "uhusinashidrelétricastool" ||
    (normalizedToolName.toLowerCase().includes("volume inicial") && comparison.is_multi_deck) ||
    (normalizedToolName.toLowerCase().includes("volumeinicial") && comparison.is_multi_deck)
  ) {
    // Verificar se é realmente volume inicial pela estrutura dos dados
    if (comparison_table && comparison_table.length > 0) {
      const firstRow = comparison_table[0] as any;
      if (firstRow.volume_inicial !== undefined) {
        if (process.env.NODE_ENV === 'development') {
          console.log('[ComparisonRouter] ✅ Usando VolumeInicialComparisonView para VolumeInicialMultiDeckTool');
        }
        return <VolumeInicialComparisonView comparison={comparison} />;
      }
    }
  }
  
  // Verificar DPMultiDeckTool ou DPCargaSubsistemasTool (em contexto multi-deck)
  if (
    normalizedToolName.toLowerCase() === "dpmultidecktool" ||
    normalizedToolName.toLowerCase() === "dpcargasubsistemastool" ||
    (normalizedToolName.toLowerCase().includes("dp") && comparison.is_multi_deck) ||
    (normalizedToolName.toLowerCase().includes("carga subsistemas") && comparison.is_multi_deck)
  ) {
    if (process.env.NODE_ENV === 'development') {
      console.log('[ComparisonRouter] ✅ Usando DPComparisonView para DPMultiDeckTool');
    }
    return <DPComparisonView comparison={comparison} />;
  }
  
  // Verificar CVUMultiDeckTool ou CTUsinasTermelétricasTool (em contexto multi-deck)
  if (
    normalizedToolName.toLowerCase() === "cvumultidecktool" ||
    normalizedToolName.toLowerCase() === "ctusinastermelétricastool" ||
    (normalizedToolName.toLowerCase().includes("cvu") && comparison.is_multi_deck)
  ) {
    if (process.env.NODE_ENV === 'development') {
      console.log('[ComparisonRouter] ✅ Usando CVUComparisonView para CVUMultiDeckTool');
    }
    return <CVUComparisonView comparison={comparison} />;
  }
  
  // Verificar PQMultiDeckTool ou PQPequenasUsinasTool (em contexto multi-deck)
  if (
    normalizedToolName.toLowerCase() === "pqmultidecktool" ||
    normalizedToolName.toLowerCase() === "pqpequenasusinastool" ||
    (normalizedToolName.toLowerCase().includes("pq") && comparison.is_multi_deck) ||
    (normalizedToolName.toLowerCase().includes("pequenas usinas") && comparison.is_multi_deck)
  ) {
    if (process.env.NODE_ENV === 'development') {
      console.log('[ComparisonRouter] ✅ Usando PQComparisonView para PQMultiDeckTool');
    }
    return <PQComparisonView comparison={comparison} />;
  }
  
  // Verificar Restrições de Vazão (multi-deck DECOMP) - antes do switch
  if (
    (normalizedToolName === "RestricoesVazaoHQTool" || 
     normalizedToolName === "RestricoesVazaoHQConjuntaTool" ||
     normalizedToolName === "RestricoesVazaoHQMultiDeckTool" ||
     normalizedToolName.toLowerCase().includes("restricoesvazao") ||
     normalizedToolName.toLowerCase().includes("restrições de vazão") ||
     normalizedToolName.toLowerCase().includes("restricoes de vazao") ||
     normalizedToolName.toLowerCase().includes("vazao hq") ||
     normalizedToolName.toLowerCase().includes("vazão hq")) && 
    comparison.is_multi_deck
  ) {
    if (process.env.NODE_ENV === 'development') {
      console.log('[ComparisonRouter] ✅ Usando RestricoesVazaoHQComparisonView para RestricoesVazaoHQTool');
    }
    return <RestricoesVazaoHQComparisonView comparison={comparison} />;
  }
  
  // Verificação adicional: se chart_config indica UsinasNaoSimuladasTool mas tool_name não está presente
  const chartConfigToolName = (chart_config as any)?.tool_name?.toString().trim() || "";
  if (chartConfigToolName.toLowerCase() === "usinasnaosimuladastool") {
    if (process.env.NODE_ENV === 'development') {
      console.log('[ComparisonRouter] ✅ Usando UsinasNaoSimuladasView (detectado via chart_config)');
    }
    return <UsinasNaoSimuladasView comparison={comparison} />;
  }

  switch (normalizedVizType) {
    case "table_with_line_chart":
      // Tools que compartilham table_with_line_chart
      // IMPORTANTE: UsinasNaoSimuladasTool e InflexibilidadeTool já foram tratados acima, não devem chegar aqui
      if (normalizedToolName === "CargaMensalTool" || normalizedToolName === "CadicTool") {
        return <CargaMensalView comparison={comparison} />;
      }
      if (normalizedToolName === "ClastValoresTool") {
        return <CVUView comparison={comparison} />;
      }
      // Verificar InflexibilidadeTool
      if (
        normalizedToolName.toLowerCase().includes("inflexibilidade")
      ) {
        return <InflexibilidadeComparisonView comparison={comparison} />;
      }
      // Verificar Carga ANDE (multi-deck)
      if (
        (normalizedToolName === "CargaAndeTool" || 
         normalizedToolName === "CargaAndeMultiDeckTool" ||
         normalizedToolName.toLowerCase().includes("cargaande") ||
         normalizedToolName.toLowerCase().includes("carga ande")) && 
        comparison.is_multi_deck
      ) {
        return <CargaAndeComparisonView comparison={comparison} />;
      }
      // Verificar DP (multi-deck)
      if (
        (normalizedToolName === "DPCargaSubsistemasTool" || 
         normalizedToolName === "DPMultiDeckTool" ||
         normalizedToolName.toLowerCase().includes("dpcargasubsistemas")) && 
        comparison.is_multi_deck
      ) {
        return <DPComparisonView comparison={comparison} />;
      }
      // Verificar PQ (multi-deck)
      if (
        (normalizedToolName === "PQPequenasUsinasTool" || 
         normalizedToolName === "PQMultiDeckTool" ||
         normalizedToolName.toLowerCase().includes("pqpequenasusinas")) && 
        comparison.is_multi_deck
      ) {
        return <PQComparisonView comparison={comparison} />;
      }
      // Verificar Limites de Intercâmbio (multi-deck)
      if (
        (normalizedToolName === "LimitesIntercambioDECOMPTool" || 
         normalizedToolName === "LimitesIntercambioMultiDeckTool" ||
         normalizedToolName.toLowerCase().includes("limitesintercambio") ||
         normalizedToolName.toLowerCase().includes("limites de intercambio") ||
         normalizedToolName.toLowerCase().includes("limites de intercâmbio")) && 
        comparison.is_multi_deck
      ) {
        return <LimitesIntercambioComparisonView comparison={comparison} />;
      }
      // Verificar Restrições Elétricas (multi-deck DECOMP)
      if (
        (normalizedToolName === "RestricoesEletricasDECOMPTool" || 
         normalizedToolName === "RestricoesEletricasMultiDeckTool" ||
         normalizedToolName.toLowerCase().includes("restricoeseletricas") ||
         normalizedToolName.toLowerCase().includes("restrições elétricas") ||
         normalizedToolName.toLowerCase().includes("restricoes eletricas")) && 
        comparison.is_multi_deck
      ) {
        return <RestricoesEletricasComparisonView comparison={comparison} />;
      }
      // Verificar Restrições de Vazão (multi-deck DECOMP)
      if (
        (normalizedToolName === "RestricoesVazaoHQTool" || 
         normalizedToolName === "RestricoesVazaoHQConjuntaTool" ||
         normalizedToolName === "RestricoesVazaoHQMultiDeckTool" ||
         normalizedToolName.toLowerCase().includes("restricoesvazao") ||
         normalizedToolName.toLowerCase().includes("restrições de vazão") ||
         normalizedToolName.toLowerCase().includes("restricoes de vazao") ||
         normalizedToolName.toLowerCase().includes("vazao hq") ||
         normalizedToolName.toLowerCase().includes("vazão hq")) && 
        comparison.is_multi_deck
      ) {
        return <RestricoesVazaoHQComparisonView comparison={comparison} />;
      }
      // GL já foi verificado antes do switch, não precisa verificar novamente aqui
      // Verificar CVU (multi-deck)
      if (
        normalizedToolName.toLowerCase().includes("cvu") && comparison.is_multi_deck
      ) {
        return <CVUComparisonView comparison={comparison} />;
      }
      // Fallback: tentar renderizar com CVUView se houver dados (mas não para UsinasNaoSimuladasTool)
      if (hasTableData || hasChartData) {
        return <CVUView comparison={comparison} />;
      }
      // Fallback para outras tools com table_with_line_chart
      return (
        <div className="w-full space-y-6 mt-4">
          <p className="text-sm text-muted-foreground">
            Visualização não implementada para tool: {normalizedToolName || "desconhecida"}
          </p>
        </div>
      );

    case "reservatorio_inicial_table":
      return <ReservatorioInicialView comparison={comparison} />;

    case "limites_intercambio":
      return <LimitesIntercambioView comparison={comparison} />;

    case "gtmin_changes_table":
    case "gtmin_matrix":
      return <GTMINView comparison={comparison} />;

    case "vazao_minima_changes_table":
      return <VazaoMinimaView comparison={comparison} />;

    case "restricao_eletrica":
      return <RestricaoEletricaView comparison={comparison} />;

    case "restricoes_eletricas_comparison":
      return <RestricoesEletricasComparisonView comparison={comparison} />;

    case "restricoes_vazao_hq_comparison":
      return <RestricoesVazaoHQComparisonView comparison={comparison} />;

    case "line_chart":
      // Tools que usam line_chart padrão
      // IMPORTANTE: UsinasNaoSimuladasTool já foi tratado acima, não deve chegar aqui
      if (normalizedToolName === "VazoesTool" || normalizedToolName === "DsvaguaTool") {
        // Usar componente genérico ou criar específico se necessário
        if (hasTableData || hasChartData) {
          return <UsinasNaoSimuladasView comparison={comparison} />;
        }
      }
      // Fallback para outras tools com line_chart (mas não UsinasNaoSimuladasTool)
      if (hasTableData || hasChartData) {
        return <UsinasNaoSimuladasView comparison={comparison} />;
      }
      break;

    case "llm_free":
    case "unknown":
    case "desconhecido":
      // Tentar renderizar com base no tool_name e dados disponíveis
      // IMPORTANTE: UsinasNaoSimuladasTool já foi tratado acima, não deve chegar aqui
      if (normalizedToolName === "ClastValoresTool" && (hasTableData || hasChartData)) {
        return <CVUView comparison={comparison} />;
      }
      if ((normalizedToolName === "CargaMensalTool" || normalizedToolName === "CadicTool") && (hasTableData || hasChartData)) {
        return <CargaMensalView comparison={comparison} />;
      }
      if ((normalizedToolName === "VazoesTool" || normalizedToolName === "DsvaguaTool") && (hasTableData || hasChartData)) {
        return <UsinasNaoSimuladasView comparison={comparison} />;
      }
      if (normalizedToolName === "RestricaoEletricaTool" && (hasTableData || comparison.charts_by_restricao)) {
        return <RestricaoEletricaView comparison={comparison} />;
      }
      if (
        (normalizedToolName === "RestricoesVazaoHQTool" || 
         normalizedToolName === "RestricoesVazaoHQConjuntaTool" ||
         normalizedToolName === "RestricoesVazaoHQMultiDeckTool") && 
        (hasTableData || hasChartData)
      ) {
        return <RestricoesVazaoHQComparisonView comparison={comparison} />;
      }
      // Se não há dados, mostrar mensagem
      if (!hasTableData && !hasChartData) {
        return (
          <div className="w-full space-y-6 mt-4">
            <p className="text-sm text-muted-foreground">
              Visualização não implementada para este tipo: {visualization_type || "desconhecido"}
            </p>
          </div>
        );
      }
      // Se há dados mas não há visualização específica, tentar renderizar genérico
      return <CVUView comparison={comparison} />;

    default:
      // Fallback: tentar renderizar com base em tool_name e dados disponíveis
      // IMPORTANTE: UsinasNaoSimuladasTool já foi tratado acima, não deve chegar aqui
      if (normalizedToolName === "ClastValoresTool" && (hasTableData || hasChartData)) {
        return <CVUView comparison={comparison} />;
      }
      if ((normalizedToolName === "CargaMensalTool" || normalizedToolName === "CadicTool") && (hasTableData || hasChartData)) {
        return <CargaMensalView comparison={comparison} />;
      }
      if ((normalizedToolName === "VazoesTool" || normalizedToolName === "DsvaguaTool") && (hasTableData || hasChartData)) {
        return <UsinasNaoSimuladasView comparison={comparison} />;
      }
      if (normalizedToolName === "RestricaoEletricaTool" && (hasTableData || comparison.charts_by_restricao)) {
        return <RestricaoEletricaView comparison={comparison} />;
      }
      if (
        (normalizedToolName === "RestricoesVazaoHQTool" || 
         normalizedToolName === "RestricoesVazaoHQConjuntaTool" ||
         normalizedToolName === "RestricoesVazaoHQMultiDeckTool") && 
        (hasTableData || hasChartData)
      ) {
        return <RestricoesVazaoHQComparisonView comparison={comparison} />;
      }
      // Se não há dados, mostrar mensagem
      if (!hasTableData && !hasChartData) {
        return (
          <div className="w-full space-y-6 mt-4">
            <p className="text-sm text-muted-foreground">
              Visualização não implementada para este tipo: {visualization_type || "desconhecido"}
            </p>
          </div>
        );
      }
      // Se há dados mas não há visualização específica, tentar renderizar genérico
      // Mas não usar CVUView como fallback genérico - usar UsinasNaoSimuladasView que é mais genérico
      if (hasTableData || hasChartData) {
        return <UsinasNaoSimuladasView comparison={comparison} />;
      }
      return (
        <div className="w-full space-y-6 mt-4">
          <p className="text-sm text-muted-foreground">
            Visualização não implementada para este tipo: {visualization_type || "desconhecido"}
          </p>
        </div>
      );
  }
}
