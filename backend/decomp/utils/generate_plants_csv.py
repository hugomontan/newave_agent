"""
Script para gerar CSVs de de-para de usinas do DECOMP.
Coleta nomes do bloco CT (térmicas) e UH (hidrelétricas) de múltiplos decks.

Uso:
    python -m backend.decomp.utils.generate_plants_csv
"""
import os
import sys
from pathlib import Path
import pandas as pd
from typing import Dict, Set, List, Tuple
from collections import defaultdict

# Adicionar caminho do projeto ao sys.path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.decomp.utils.dadger_cache import get_cached_dadger
from backend.decomp.utils.deck_loader import list_available_decks, get_deck_path
from backend.decomp.config import safe_print
from backend.core.config import DATA_DIR


def collect_thermal_plants_from_deck(deck_path: str) -> pd.DataFrame:
    """
    Coleta nomes de usinas térmicas do bloco CT de um deck.
    
    Args:
        deck_path: Caminho do diretório do deck
        
    Returns:
        DataFrame com colunas: codigo, nome_decomp
    """
    try:
        dadger = get_cached_dadger(deck_path)
        if dadger is None:
            return pd.DataFrame()
        
        # Obter dados do bloco CT (estágio 1)
        ct_df = dadger.ct(estagio=1, df=True)
        
        if ct_df is None or (isinstance(ct_df, pd.DataFrame) and ct_df.empty):
            return pd.DataFrame()
        
        # Extrair códigos e nomes únicos
        if 'codigo_usina' not in ct_df.columns or 'nome_usina' not in ct_df.columns:
            return pd.DataFrame()
        
        usinas = ct_df[['codigo_usina', 'nome_usina']].drop_duplicates()
        usinas = usinas.dropna(subset=['nome_usina'])
        
        # Filtrar nomes inválidos
        usinas = usinas[
            (usinas['nome_usina'].astype(str).str.strip() != '') &
            (usinas['nome_usina'].astype(str).str.lower() != 'nan')
        ]
        
        return usinas.rename(columns={
            'codigo_usina': 'codigo',
            'nome_usina': 'nome_decomp'
        })
    except Exception as e:
        safe_print(f"[GERAR CSV] ⚠️ Erro ao coletar térmicas de {deck_path}: {e}")
        return pd.DataFrame()


def collect_hydraulic_plants_from_deck(deck_path: str) -> pd.DataFrame:
    """
    Coleta nomes de usinas hidrelétricas do bloco UH e HIDR.DAT de um deck.
    
    Args:
        deck_path: Caminho do diretório do deck
        
    Returns:
        DataFrame com colunas: codigo, nome_decomp
    """
    try:
        dadger = get_cached_dadger(deck_path)
        if dadger is None:
            return pd.DataFrame()
        
        # Obter códigos do bloco UH
        uh_df = dadger.uh(df=True)
        
        codigos_usinas = set()
        if uh_df is not None and not (isinstance(uh_df, pd.DataFrame) and uh_df.empty):
            if 'codigo_usina' in uh_df.columns:
                codigos_usinas = set(uh_df['codigo_usina'].dropna().unique())
        
        if not codigos_usinas:
            return pd.DataFrame()
        
        # Tentar buscar nomes do HIDR.DAT (mesmo processo da UH Tool)
        mapeamento = {}
        
        # Prioridade 1: Tentar hidr.dat do próprio deck DECOMP
        from pathlib import Path
        deck_path_obj = Path(deck_path)
        hidr_paths_to_try = [
            deck_path_obj / "hidr.dat",
            deck_path_obj / "HIDR.DAT",
        ]
        
        # Prioridade 2: Buscar em data/newave/decks (3 mais recentes)
        from backend.core.config import DATA_DIR
        newave_decks_dir = DATA_DIR / "newave" / "decks"
        
        if newave_decks_dir.exists():
            try:
                import os
                deck_dirs = [d for d in os.listdir(newave_decks_dir) 
                            if os.path.isdir(os.path.join(newave_decks_dir, d))]
                deck_dirs.sort(reverse=True)  # Mais recente primeiro
                
                for deck_dir in deck_dirs[:3]:  # Apenas os 3 mais recentes
                    deck_full_path = newave_decks_dir / deck_dir
                    hidr_paths_to_try.extend([
                        deck_full_path / "HIDR.DAT",
                        deck_full_path / "hidr.dat",
                    ])
            except Exception:
                pass
        
        # Tentar cada caminho até encontrar um válido
        for hidr_path in hidr_paths_to_try:
            if not hidr_path.exists():
                continue
            
            try:
                from inewave.newave import Hidr
                hidr = Hidr.read(str(hidr_path))
                
                if hidr.cadastro is not None and not hidr.cadastro.empty:
                    for idx, hidr_row in hidr.cadastro.iterrows():
                        codigo_hidr = None
                        nome_hidr = None
                        
                        # Tentar usar o índice como código
                        try:
                            if isinstance(idx, (int, float)) and idx > 0:
                                codigo_hidr = int(idx)
                        except (ValueError, TypeError):
                            pass
                        
                        # Tentar diferentes nomes de coluna para código
                        if codigo_hidr is None:
                            for cod_col in ['codigo_usina', 'codigo', 'codigo_usina_hidr', 'numero_usina', 'numero']:
                                if cod_col in hidr_row.index:
                                    try:
                                        val = hidr_row[cod_col]
                                        if pd.notna(val):
                                            codigo_hidr = int(val)
                                            break
                                    except (ValueError, TypeError):
                                        continue
                        
                        # Tentar diferentes nomes de coluna para nome
                        for nome_col in ['nome_usina', 'nome', 'nome_da_usina', 'usina', 'nome_do_posto']:
                            if nome_col in hidr_row.index:
                                val = hidr_row[nome_col]
                                if pd.notna(val):
                                    nome_hidr = str(val).strip()
                                    if nome_hidr and nome_hidr != 'nan' and nome_hidr != '' and nome_hidr.lower() != 'none':
                                        break
                        
                        if codigo_hidr and codigo_hidr > 0 and nome_hidr:
                            # Só adicionar se o código está no bloco UH
                            if codigo_hidr in codigos_usinas:
                                mapeamento[codigo_hidr] = nome_hidr
                    
                    if mapeamento:
                        break  # Se encontrou mapeamento, parar de procurar
            except Exception as e:
                continue
        
        # Criar DataFrame com os dados coletados
        if not mapeamento:
            # Se não encontrou nomes, criar apenas com códigos
            data = [{'codigo': cod, 'nome_decomp': f'Usina {cod}'} for cod in sorted(codigos_usinas)]
        else:
            # Usar nomes encontrados, preencher códigos sem nome
            data = []
            for codigo in sorted(codigos_usinas):
                nome = mapeamento.get(codigo, f'Usina {codigo}')
                data.append({'codigo': codigo, 'nome_decomp': nome})
        
        return pd.DataFrame(data)
    except Exception as e:
        safe_print(f"[GERAR CSV] ⚠️ Erro ao coletar hidrelétricas de {deck_path}: {e}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame()


def consolidate_plants(all_plants: List[pd.DataFrame]) -> pd.DataFrame:
    """
    Consolida plantas de múltiplos decks, mantendo todos os nomes únicos por código.
    
    Args:
        all_plants: Lista de DataFrames com plantas coletadas
        
    Returns:
        DataFrame consolidado com código e nome_decomp (mantém todos os nomes únicos)
    """
    if not all_plants:
        return pd.DataFrame()
    
    # Concatenar todos os DataFrames
    consolidated = pd.concat(all_plants, ignore_index=True)
    
    # Remover duplicatas exatas (mesmo código e mesmo nome)
    consolidated = consolidated.drop_duplicates(subset=['codigo', 'nome_decomp'])
    
    # Ordenar por código e nome
    consolidated = consolidated.sort_values(['codigo', 'nome_decomp'])
    
    return consolidated.reset_index(drop=True)


def generate_thermal_csv(output_path: Path, max_decks: int = 10):
    """
    Gera CSV de de-para para usinas térmicas.
    
    Args:
        output_path: Caminho onde salvar o CSV
        max_decks: Número máximo de decks para processar
    """
    safe_print("[GERAR CSV] ===== Coletando usinas térmicas =====")
    
    # Listar decks disponíveis
    decks = list_available_decks()
    safe_print(f"[GERAR CSV] Encontrados {len(decks)} decks disponíveis")
    
    if not decks:
        safe_print("[GERAR CSV] ❌ Nenhum deck encontrado")
        return
    
    # Limitar número de decks para não demorar muito
    decks_to_process = decks[:max_decks]
    safe_print(f"[GERAR CSV] Processando {len(decks_to_process)} decks...")
    
    all_thermal_plants = []
    processed = 0
    
    for deck_info in decks_to_process:
        deck_path = get_deck_path(deck_info['name'])
        if not deck_path:
            continue
        
        safe_print(f"[GERAR CSV] Processando deck: {deck_info['name']}")
        thermal_df = collect_thermal_plants_from_deck(deck_path)
        
        if not thermal_df.empty:
            all_thermal_plants.append(thermal_df)
            safe_print(f"[GERAR CSV]   ✅ {len(thermal_df)} usinas térmicas coletadas")
            processed += 1
        else:
            safe_print(f"[GERAR CSV]   ⚠️ Nenhuma usina térmica encontrada")
    
    if not all_thermal_plants:
        safe_print("[GERAR CSV] ❌ Nenhuma usina térmica coletada")
        return
    
    # Consolidar plantas
    consolidated = consolidate_plants(all_thermal_plants)
    safe_print(f"[GERAR CSV] Total de registros únicos: {len(consolidated)}")
    
    # Adicionar colunas vazias para preenchimento manual
    consolidated['nome_completo'] = ''
    consolidated['arquivo_fonte'] = 'CT'
    consolidated['tipo'] = 'usina'
    consolidated['notas'] = ''
    
    # Reordenar colunas
    consolidated = consolidated[['codigo', 'nome_decomp', 'nome_completo', 'arquivo_fonte', 'tipo', 'notas']]
    
    # Salvar CSV
    output_path.parent.mkdir(parents=True, exist_ok=True)
    consolidated.to_csv(output_path, index=False, encoding='utf-8')
    
    safe_print(f"[GERAR CSV] ✅ CSV gerado: {output_path}")
    safe_print(f"[GERAR CSV]   Total de usinas: {len(consolidated)}")
    safe_print(f"[GERAR CSV]   Decks processados: {processed}/{len(decks_to_process)}")
    safe_print(f"[GERAR CSV]   ⚠️ IMPORTANTE: Preencha manualmente a coluna 'nome_completo'")


def generate_hydraulic_csv(output_path: Path, max_decks: int = 10):
    """
    Gera CSV de de-para para usinas hidrelétricas.
    
    Args:
        output_path: Caminho onde salvar o CSV
        max_decks: Número máximo de decks para processar
    """
    safe_print("[GERAR CSV] ===== Coletando usinas hidrelétricas =====")
    
    # Listar decks disponíveis
    decks = list_available_decks()
    safe_print(f"[GERAR CSV] Encontrados {len(decks)} decks disponíveis")
    
    if not decks:
        safe_print("[GERAR CSV] ❌ Nenhum deck encontrado")
        return
    
    # Limitar número de decks para não demorar muito
    decks_to_process = decks[:max_decks]
    safe_print(f"[GERAR CSV] Processando {len(decks_to_process)} decks...")
    
    all_hydraulic_plants = []
    processed = 0
    
    for deck_info in decks_to_process:
        deck_path = get_deck_path(deck_info['name'])
        if not deck_path:
            continue
        
        safe_print(f"[GERAR CSV] Processando deck: {deck_info['name']}")
        hydraulic_df = collect_hydraulic_plants_from_deck(deck_path)
        
        if not hydraulic_df.empty:
            all_hydraulic_plants.append(hydraulic_df)
            safe_print(f"[GERAR CSV]   ✅ {len(hydraulic_df)} usinas hidrelétricas coletadas")
            processed += 1
        else:
            safe_print(f"[GERAR CSV]   ⚠️ Nenhuma usina hidrelétrica encontrada")
    
    if not all_hydraulic_plants:
        safe_print("[GERAR CSV] ❌ Nenhuma usina hidrelétrica coletada")
        return
    
    # Consolidar plantas
    consolidated = consolidate_plants(all_hydraulic_plants)
    safe_print(f"[GERAR CSV] Total de registros únicos: {len(consolidated)}")
    
    # Adicionar colunas vazias para preenchimento manual
    consolidated['nome_completo'] = ''
    consolidated['posto'] = ''
    consolidated['submercado'] = ''
    consolidated['empresa'] = ''
    consolidated['arquivo_fonte'] = 'UH'
    consolidated['tipo'] = 'usina'
    consolidated['notas'] = ''
    
    # Reordenar colunas
    consolidated = consolidated[[
        'codigo', 'nome_decomp', 'nome_completo', 'posto', 
        'submercado', 'empresa', 'arquivo_fonte', 'tipo', 'notas'
    ]]
    
    # Salvar CSV
    output_path.parent.mkdir(parents=True, exist_ok=True)
    consolidated.to_csv(output_path, index=False, encoding='utf-8')
    
    safe_print(f"[GERAR CSV] ✅ CSV gerado: {output_path}")
    safe_print(f"[GERAR CSV]   Total de usinas: {len(consolidated)}")
    safe_print(f"[GERAR CSV]   Decks processados: {processed}/{len(decks_to_process)}")
    safe_print(f"[GERAR CSV]   ⚠️ IMPORTANTE: Preencha manualmente a coluna 'nome_completo'")


def main():
    """Função principal."""
    # Criar diretório data se não existir
    decomp_data_dir = DATA_DIR / "decomp" / "data"
    decomp_data_dir.mkdir(parents=True, exist_ok=True)
    
    # Caminhos dos CSVs
    thermal_csv_path = decomp_data_dir / "deparatermicas_decomp.csv"
    hydraulic_csv_path = decomp_data_dir / "deparahidro_decomp.csv"
    
    safe_print("[GERAR CSV] ========================================")
    safe_print("[GERAR CSV] Gerando CSVs de de-para para DECOMP")
    safe_print("[GERAR CSV] ========================================")
    
    # Gerar CSV de térmicas
    generate_thermal_csv(thermal_csv_path, max_decks=10)
    
    safe_print("\n")
    
    # Gerar CSV de hidrelétricas
    generate_hydraulic_csv(hydraulic_csv_path, max_decks=10)
    
    safe_print("\n[GERAR CSV] ========================================")
    safe_print("[GERAR CSV] ✅ Processo concluído!")
    safe_print("[GERAR CSV] ========================================")


if __name__ == "__main__":
    main()
