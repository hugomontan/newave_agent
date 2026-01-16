"""
Script para extrair todas as térmicas do NEWAVE e DECOMP e gerar CSV consolidado.
"""
import os
import sys
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

# Adicionar paths dos módulos
sys.path.insert(0, str(Path(__file__).parent.parent / "newave_agent"))
sys.path.insert(0, str(Path(__file__).parent.parent / "decomp_agent"))

from newave_agent.app.utils.deck_loader import list_available_decks as list_newave_decks, DECKS_DIR as NEWAVE_DECKS_DIR
from decomp_agent.app.utils.deck_loader import list_available_decks as list_decomp_decks, DECKS_DIR as DECOMP_DECKS_DIR
from inewave.newave import Term, Clast


def extract_newave_termicas(deck_path: str, deck_name: str) -> List[Dict[str, Any]]:
    """Extrai usinas térmicas individuais do TERM.DAT."""
    termicas = []
    
    term_path = os.path.join(deck_path, "TERM.DAT")
    if not os.path.exists(term_path):
        term_path = os.path.join(deck_path, "term.dat")
    
    if not os.path.exists(term_path):
        print(f"  ⚠️ TERM.DAT não encontrado em {deck_name}")
        return termicas
    
    try:
        term = Term.read(term_path)
        if term.usinas is not None and not term.usinas.empty:
            for _, row in term.usinas.iterrows():
                termicas.append({
                    'modelo': 'NEWAVE',
                    'deck': deck_name,
                    'tipo': 'Usina Térmica Individual',
                    'codigo': row.get('codigo_usina'),
                    'nome': row.get('nome_usina', ''),
                    'potencia_efetiva': row.get('pot_efetiva', row.get('potencia_efetiva')),
                    'fcmax': row.get('fcmax', row.get('fator_capacidade_maximo')),
                    'teif': row.get('teif', row.get('taxa_indisponibilidade_forcada')),
                    'ip': row.get('ip', row.get('indisponibilidade_programada')),
                    'arquivo_origem': 'TERM.DAT'
                })
            print(f"  ✅ {len(termicas)} usinas térmicas individuais do TERM.DAT")
    except Exception as e:
        print(f"  ❌ Erro ao ler TERM.DAT: {e}")
    
    return termicas


def extract_newave_classes(deck_path: str, deck_name: str) -> List[Dict[str, Any]]:
    """Extrai classes térmicas do CLAST.DAT."""
    classes = []
    
    clast_path = os.path.join(deck_path, "CLAST.DAT")
    if not os.path.exists(clast_path):
        clast_path = os.path.join(deck_path, "clast.dat")
    
    if not os.path.exists(clast_path):
        print(f"  ⚠️ CLAST.DAT não encontrado em {deck_name}")
        return classes
    
    try:
        clast = Clast.read(clast_path)
        if clast.usinas is not None and not clast.usinas.empty:
            # Pegar classes únicas (código + nome)
            classes_unicas = clast.usinas[['codigo_usina', 'nome_usina', 'tipo_combustivel']].drop_duplicates()
            
            for _, row in classes_unicas.iterrows():
                classes.append({
                    'modelo': 'NEWAVE',
                    'deck': deck_name,
                    'tipo': 'Classe Térmica',
                    'codigo': row.get('codigo_usina'),
                    'nome': row.get('nome_usina', ''),
                    'tipo_combustivel': row.get('tipo_combustivel', ''),
                    'arquivo_origem': 'CLAST.DAT'
                })
            print(f"  ✅ {len(classes)} classes térmicas do CLAST.DAT")
    except Exception as e:
        print(f"  ❌ Erro ao ler CLAST.DAT: {e}")
    
    return classes


def extract_decomp_termicas(deck_path: str, deck_name: str) -> List[Dict[str, Any]]:
    """Extrai usinas térmicas do DECOMP via dadger.ct()."""
    termicas = []
    
    try:
        from decompclass import Dadger
        
        # Procurar arquivo dadger
        dadger_files = list(Path(deck_path).glob("dadger.rv*"))
        if not dadger_files:
            print(f"  ⚠️ Nenhum arquivo dadger.rv* encontrado em {deck_name}")
            return termicas
        
        # Usar o primeiro arquivo encontrado
        dadger_path = dadger_files[0]
        dadger = Dadger.read(str(dadger_path))
        
        # Obter todas as térmicas (sem filtros)
        ct_data = dadger.ct(df=True)
        
        if ct_data is not None and not ct_data.empty:
            # Pegar usinas únicas (código + nome)
            if 'codigo_usina' in ct_data.columns and 'nome_usina' in ct_data.columns:
                usinas_unicas = ct_data[['codigo_usina', 'nome_usina']].drop_duplicates()
                
                for _, row in usinas_unicas.iterrows():
                    termicas.append({
                        'modelo': 'DECOMP',
                        'deck': deck_name,
                        'tipo': 'Usina Térmica Individual',
                        'codigo': row.get('codigo_usina'),
                        'nome': row.get('nome_usina', ''),
                        'arquivo_origem': f'dadger.{dadger_path.suffix}'
                    })
                print(f"  ✅ {len(termicas)} usinas térmicas do DECOMP")
            else:
                print(f"  ⚠️ Colunas esperadas não encontradas no dadger.ct()")
    except ImportError:
        print(f"  ⚠️ decompclass não disponível - pulando DECOMP")
    except Exception as e:
        print(f"  ❌ Erro ao ler DECOMP: {e}")
        import traceback
        traceback.print_exc()
    
    return termicas


def main():
    """Função principal."""
    print("=" * 80)
    print("EXTRAÇÃO DE TODAS AS TÉRMICAS - NEWAVE E DECOMP")
    print("=" * 80)
    print()
    
    all_termicas = []
    
    # 1. Processar decks NEWAVE
    print("📦 Processando decks NEWAVE...")
    print("-" * 80)
    
    newave_decks = list_newave_decks()
    print(f"Encontrados {len(newave_decks)} decks NEWAVE")
    print()
    
    for deck_info in newave_decks:
        deck_name = deck_info['name']
        deck_path = deck_info.get('extracted_path') or deck_info.get('zip_path')
        
        if not deck_path or not os.path.exists(deck_path):
            print(f"⚠️ Deck {deck_name} não encontrado ou não extraído")
            continue
        
        print(f"📂 Processando {deck_name}...")
        
        # Extrair usinas térmicas individuais
        termicas = extract_newave_termicas(deck_path, deck_name)
        all_termicas.extend(termicas)
        
        # Extrair classes térmicas
        classes = extract_newave_classes(deck_path, deck_name)
        all_termicas.extend(classes)
        
        print()
    
    # 2. Processar decks DECOMP
    print("📦 Processando decks DECOMP...")
    print("-" * 80)
    
    decomp_decks = list_decomp_decks()
    print(f"Encontrados {len(decomp_decks)} decks DECOMP")
    print()
    
    for deck_info in decomp_decks:
        deck_name = deck_info['name']
        deck_path = deck_info.get('extracted_path')
        
        if not deck_path or not os.path.exists(deck_path):
            print(f"⚠️ Deck {deck_name} não encontrado ou não extraído")
            continue
        
        print(f"📂 Processando {deck_name}...")
        
        # Extrair usinas térmicas
        termicas = extract_decomp_termicas(deck_path, deck_name)
        all_termicas.extend(termicas)
        
        print()
    
    # 3. Criar DataFrame e salvar CSV
    if not all_termicas:
        print("❌ Nenhuma térmica encontrada!")
        return
    
    print("=" * 80)
    print("CONSOLIDANDO DADOS...")
    print("=" * 80)
    
    df = pd.DataFrame(all_termicas)
    
    # Remover duplicatas baseado apenas em código e nome de usina
    total_antes = len(df)
    df = df.drop_duplicates(subset=['codigo', 'nome'], keep='first')
    total_depois = len(df)
    
    # Ordenar por código de usina para agrupar linhas com mesmo código
    df = df.sort_values(by='codigo', na_position='last')
    
    print(f"Total de registros: {total_antes}")
    print(f"Após remoção de duplicatas: {total_depois}")
    print()
    
    # Estatísticas
    print("📊 ESTATÍSTICAS:")
    print(f"  - Total de térmicas únicas: {total_depois}")
    print(f"  - NEWAVE: {len(df[df['modelo'] == 'NEWAVE'])}")
    print(f"  - DECOMP: {len(df[df['modelo'] == 'DECOMP'])}")
    print(f"  - Usinas individuais: {len(df[df['tipo'] == 'Usina Térmica Individual'])}")
    print(f"  - Classes térmicas: {len(df[df['tipo'] == 'Classe Térmica'])}")
    print()
    
    # Salvar CSV
    output_file = f"todas_termicas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    df.to_csv(output_file, index=False, encoding='utf-8-sig')
    
    print("=" * 80)
    print(f"✅ CSV gerado com sucesso: {output_file}")
    print("=" * 80)
    print()
    print("Colunas do CSV:")
    for col in df.columns:
        print(f"  - {col}")
    print()
    print(f"Primeiras linhas:")
    print(df.head(10).to_string())


if __name__ == "__main__":
    main()