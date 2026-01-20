"use client";

import React from "react";
import type { SingleDeckVisualizationData } from "./shared/types";
import { CVUView } from "./cvu";
import { CargaMensalView } from "./carga-mensal";
import { CadicView } from "./cadic";
import { VazoesView } from "./vazoes";
import { DsvaguaView } from "./dsvagua";
import { LimitesIntercambioView } from "./limites-intercambio";
import { CadastroHidrView } from "./cadastro-hidr";
import { CadastroTermView } from "./cadastro-term";
import { ConfhdView } from "./confhd";
import { UsinasNaoSimuladasView } from "./usinas-nao-simuladas";
import { ModifOperacaoView } from "./modif-operacao";
import { RestricaoEletricaView } from "./restricao-eletrica";
import { UHView } from "./uh";
import { CTView } from "./ct";
import { DPView } from "./dp";
import { DisponibilidadeUsinaView } from "./disponibilidade-usina";
import { InflexibilidadeUsinaView } from "./inflexibilidade-usina";
import { PQView } from "./pq";
import { CargaAndeView } from "./carga-ande";

interface SingleDeckRouterProps {
  visualizationData: SingleDeckVisualizationData;
}

export function SingleDeckRouter({ visualizationData }: SingleDeckRouterProps) {
  const { tool_name } = visualizationData;

  if (!tool_name) {
    return null;
  }

  // Router por tool_name específico (modularização completa)
  switch (tool_name) {
    case "ClastValoresTool":
      return <CVUView visualizationData={visualizationData} />;
    
    case "CargaMensalTool":
      return <CargaMensalView visualizationData={visualizationData} />;
    
    case "CadicTool":
      return <CadicView visualizationData={visualizationData} />;
    
    case "VazoesTool":
      return <VazoesView visualizationData={visualizationData} />;
    
    case "DsvaguaTool":
      return <DsvaguaView visualizationData={visualizationData} />;
    
    case "LimitesIntercambioTool":
    case "LimitesIntercambioDECOMPTool":
      return <LimitesIntercambioView visualizationData={visualizationData} />;
    
    case "HidrCadastroTool":
      return <CadastroHidrView visualizationData={visualizationData} />;
    
    case "TermCadastroTool":
      return <CadastroTermView visualizationData={visualizationData} />;
    
    case "ConfhdTool":
      return <ConfhdView visualizationData={visualizationData} />;
    
    case "UsinasNaoSimuladasTool":
      return <UsinasNaoSimuladasView visualizationData={visualizationData} />;
    
    case "ModifOperacaoTool":
      return <ModifOperacaoView visualizationData={visualizationData} />;
    
    case "RestricaoEletricaTool":
    case "RestricoesEletricasDECOMPTool":
      return <RestricaoEletricaView visualizationData={visualizationData} />;
    
    case "UHUsinasHidrelétricasTool":
      return <UHView visualizationData={visualizationData} />;
    
    case "CTUsinasTermelétricasTool":
      return <CTView visualizationData={visualizationData} />;
    
    case "DPCargaSubsistemasTool":
      return <DPView visualizationData={visualizationData} />;
    
    case "DisponibilidadeUsinaTool":
      return <DisponibilidadeUsinaView visualizationData={visualizationData} />;
    
    case "InflexibilidadeUsinaTool":
      return <InflexibilidadeUsinaView visualizationData={visualizationData} />;
    
    case "PQPequenasUsinasTool":
      return <PQView visualizationData={visualizationData} />;
    
    case "CargaAndeTool":
      return <CargaAndeView visualizationData={visualizationData} />;
    
    default:
      return null;
  }
}
