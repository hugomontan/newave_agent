"""
Script para gerar CSV de referência com todas as usinas hidrelétricas do NEWAVE.

Extrai código e nome de cada usina hidrelétrica do arquivo HIDR.DAT e gera
um CSV estruturado para uso em matching de usinas hidrelétricas.

Uso:
    python -m backend.newave.utils.generate_hydraulic_plants_csv [deck_path]
    
    Se deck_path não for fornecido, usa o primeiro deck encontrado em decks/.
"""
import os
import sys
import csv
import argparse
from pathlib import Path
from typing import List, Dict, Any

# Adicionar raiz do projeto ao path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from inewave.newave import Hidr
except ImportError:
    print("❌ Erro: Biblioteca 'inewave' não encontrada")
    print("   Instale com: pip install inewave")
    sys.exit(1)


def find_deck_path(provided_path: str = None) -> str:
    """
    Encontra o caminho do deck NEWAVE.
    
    Args:
        provided_path: Caminho fornecido pelo usuário
        
    Returns:
        Caminho do deck encontrado
        
    Raises:
        FileNotFoundError: Se nenhum deck for encontrado
    """
    if provided_path and os.path.exists(provided_path):
        hidr_path = os.path.join(provided_path, "HIDR.DAT")
        if not os.path.exists(hidr_path):
            hidr_path = os.path.join(provided_path, "hidr.dat")
        if os.path.exists(hidr_path):
            return provided_path
    
    # Tentar encontrar em diretórios comuns
    possible_paths = [
        "decks",
        "../decks",
        "../../decks",
        os.path.join(project_root, "decks"),
    ]
    
    for base_path in possible_paths:
        if os.path.exists(base_path):
            for item in os.listdir(base_path):
                item_path = os.path.join(base_path, item)
                if os.path.isdir(item_path):
                    hidr_path = os.path.join(item_path, "HIDR.DAT")
                    if not os.path.exists(hidr_path):
                        hidr_path = os.path.join(item_path, "hidr.dat")
                    if os.path.exists(hidr_path):
                        print(f"✅ Deck encontrado: {item_path}")
                        return item_path
    
    raise FileNotFoundError(
        "Nenhum deck NEWAVE encontrado. "
        "Forneça o caminho do deck como argumento ou coloque-o em 'decks/'"
    )


def extract_hydraulic_plants(deck_path: str) -> List[Dict[str, Any]]:
    """
    Extrai todas as usinas hidrelétricas do HIDR.DAT.
    
    Args:
        deck_path: Caminho do deck NEWAVE
        
    Returns:
        Lista de dicionários com código e nome de cada usina
    """
    hidr_path = os.path.join(deck_path, "HIDR.DAT")
    if not os.path.exists(hidr_path):
        hidr_path = os.path.join(deck_path, "hidr.dat")
    
    if not os.path.exists(hidr_path):
        raise FileNotFoundError(f"Arquivo HIDR.DAT não encontrado em {deck_path}")
    
    print(f"📖 Lendo arquivo: {hidr_path}")
    
    try:
        hidr = Hidr.read(hidr_path)
    except Exception as e:
        print(f"❌ Erro ao ler HIDR.DAT: {e}")
        raise
    
    cadastro = hidr.cadastro
    if cadastro is None or cadastro.empty:
        print("⚠️  Nenhuma usina encontrada no cadastro")
        return []
    
    print(f"✅ {len(cadastro)} usinas encontradas no cadastro")
    
    usinas = []
    for idx, row in cadastro.iterrows():
        # Código da usina = índice + 1 (1-based)
        codigo = idx + 1
        
        # Nome da usina
        nome = str(row.get('nome_usina', '')).strip()
        
        # Ignorar se não tiver nome
        if not nome or nome.lower() == 'nan' or nome == '':
            print(f"⚠️  Usina {codigo} sem nome, pulando...")
            continue
        
        # Informações adicionais (se disponíveis)
        posto = row.get('posto', '')
        submercado = row.get('submercado', '')
        empresa = row.get('empresa', '')
        
        usinas.append({
            'codigo': codigo,
            'nome_arquivo': nome,  # Nome como aparece no arquivo
            'nome_completo': nome,  # Por enquanto igual ao nome_arquivo
            'posto': str(posto).strip() if posto else '',
            'submercado': str(submercado).strip() if submercado else '',
            'empresa': str(empresa).strip() if empresa else '',
            'arquivo_fonte': 'HIDR',
            'tipo': 'usina'
        })
    
    return usinas


def generate_csv(usinas: List[Dict[str, Any]], output_path: str = None) -> str:
    """
    Gera CSV com os dados das usinas hidrelétricas.
    
    Args:
        usinas: Lista de dicionários com dados das usinas
        output_path: Caminho do arquivo de saída (opcional)
        
    Returns:
        Caminho do arquivo gerado
    """
    if output_path is None:
        # Salvar em backend/newave/data/
        data_dir = Path(__file__).parent.parent / "data"
        data_dir.mkdir(exist_ok=True)
        output_path = str(data_dir / "usinas_hidreletricas_reference.csv")
    
    print(f"📝 Gerando CSV: {output_path}")
    
    # Ordenar por código
    usinas_sorted = sorted(usinas, key=lambda x: x['codigo'])
    
    # Campos do CSV
    fieldnames = [
        'codigo',
        'nome_arquivo',
        'nome_completo',
        'posto',
        'submercado',
        'empresa',
        'arquivo_fonte',
        'tipo'
    ]
    
    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for usina in usinas_sorted:
            writer.writerow(usina)
    
    print(f"✅ CSV gerado com sucesso: {len(usinas_sorted)} usinas")
    return output_path


def main():
    """Função principal."""
    parser = argparse.ArgumentParser(
        description="Gera CSV de referência com usinas hidrelétricas do NEWAVE"
    )
    parser.add_argument(
        'deck_path',
        nargs='?',
        help='Caminho do deck NEWAVE (opcional, busca automaticamente se não fornecido)'
    )
    parser.add_argument(
        '-o', '--output',
        help='Caminho do arquivo CSV de saída (padrão: backend/newave/data/usinas_hidreletricas_reference.csv)'
    )
    
    args = parser.parse_args()
    
    try:
        print("=" * 70)
        print("GERADOR DE CSV DE USINAS HIDRELÉTRICAS - NEWAVE")
        print("=" * 70)
        print()
        
        # Encontrar deck
        deck_path = find_deck_path(args.deck_path)
        print(f"📁 Deck: {deck_path}")
        print()
        
        # Extrair usinas
        usinas = extract_hydraulic_plants(deck_path)
        
        if not usinas:
            print("❌ Nenhuma usina encontrada")
            return 1
        
        print()
        print(f"📊 Estatísticas:")
        print(f"   Total de usinas: {len(usinas)}")
        
        # Estatísticas por submercado
        submercados = {}
        for usina in usinas:
            sub = usina.get('submercado', 'N/A')
            submercados[sub] = submercados.get(sub, 0) + 1
        
        if submercados:
            print(f"   Por submercado:")
            for sub, count in sorted(submercados.items()):
                print(f"      {sub}: {count} usinas")
        
        print()
        
        # Gerar CSV
        output_path = generate_csv(usinas, args.output)
        
        print()
        print("=" * 70)
        print("✅ CONCLUÍDO COM SUCESSO")
        print("=" * 70)
        print(f"📄 Arquivo gerado: {output_path}")
        print()
        print("💡 Próximos passos:")
        print("   1. Revise o CSV gerado")
        print("   2. Adicione coluna 'usina' com nomes expandidos/curados (opcional)")
        print("   3. Use o CSV como referência para matching de usinas hidrelétricas")
        print()
        
        return 0
        
    except FileNotFoundError as e:
        print(f"❌ Erro: {e}")
        return 1
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
