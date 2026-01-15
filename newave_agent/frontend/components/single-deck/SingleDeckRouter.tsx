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
      return <RestricaoEletricaView visualizationData={visualizationData} />;
    
    default:
      return null;
  }
}
