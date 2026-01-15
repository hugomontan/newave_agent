"""
Registry de tools para modo Multi-Deck.
Suporta N decks para comparação dinâmica.
"""

from typing import List, Optional
from app.tools.base import NEWAVETool
from app.tools.carga_mensal_tool import CargaMensalTool
from app.tools.clast_valores_tool import ClastValoresTool
from app.tools.expt_operacao_tool import ExptOperacaoTool
from app.tools.modif_operacao_tool import ModifOperacaoTool
from app.tools.limites_intercambio_tool import LimitesIntercambioTool
from app.tools.agrint_tool import AgrintTool
from app.tools.vazoes_tool import VazoesTool
from app.tools.cadic_tool import CadicTool
from app.tools.hidr_cadastro_tool import HidrCadastroTool
from app.tools.confhd_tool import ConfhdTool
from app.tools.dsvagua_tool import DsvaguaTool
from app.tools.usinas_nao_simuladas_tool import UsinasNaoSimuladasTool
from app.tools.restricao_eletrica_tool import RestricaoEletricaTool
from app.tools.term_cadastro_tool import TermCadastroTool
from app.tools.multi_deck_comparison_tool import MultiDeckComparisonTool
from app.tools.mudancas_geracoes_termicas_tool import MudancasGeracoesTermicasTool
from app.tools.mudancas_vazao_minima_tool import MudancasVazaoMinimaTool
from app.tools.variacao_reservatorio_inicial_tool import VariacaoReservatorioInicialTool


# Registry de tools para modo comparison (lista completa, independente)
# Tools que suportam selected_decks como parâmetro
MULTI_DECK_TOOLS = [
    VariacaoReservatorioInicialTool,  # Suporta N decks
    MudancasGeracoesTermicasTool,     # Suporta N decks
    MudancasVazaoMinimaTool,          # Suporta N decks
    MultiDeckComparisonTool,          # Suporta N decks
]

# Tools que operam em um único deck (serão executadas via MultiDeckComparisonTool)
SINGLE_DECK_TOOLS = [
    CargaMensalTool,
    ClastValoresTool,
    ExptOperacaoTool,
    ModifOperacaoTool,
    LimitesIntercambioTool,
    AgrintTool,
    VazoesTool,
    CadicTool,
    HidrCadastroTool,
    ConfhdTool,
    DsvaguaTool,
    UsinasNaoSimuladasTool,
    RestricaoEletricaTool,
    TermCadastroTool,
]

TOOLS_REGISTRY_COMPARISON = MULTI_DECK_TOOLS + SINGLE_DECK_TOOLS


def get_available_tools(
    deck_path: str, 
    selected_decks: Optional[List[str]] = None
) -> List[NEWAVETool]:
    """
    Retorna instâncias de todas as tools disponíveis para modo multi-deck.
    
    Args:
        deck_path: Caminho do diretório do deck NEWAVE
        selected_decks: Lista de nomes dos decks selecionados para comparação
        
    Returns:
        Lista de instâncias de tools
    """
    tools = []
    
    for ToolClass in TOOLS_REGISTRY_COMPARISON:
        # Tools que suportam selected_decks
        if ToolClass in MULTI_DECK_TOOLS:
            try:
                tool = ToolClass(deck_path, selected_decks=selected_decks)
            except TypeError:
                # Fallback se a tool não aceitar selected_decks
                tool = ToolClass(deck_path)
        else:
            # Tools de single deck
            tool = ToolClass(deck_path)
        
        tools.append(tool)
    
    return tools
