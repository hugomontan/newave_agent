"""
Script para extrair absolutamente todas as informações do arquivo HIDR.DAT.
Este script extrai todos os dados cadastrais disponíveis e salva em um arquivo CSV.
"""
import os
from inewave.newave import Hidr
import pandas as pd
from datetime import datetime


def extrair_todas_informacoes_hidr(output_csv=None):
    """
    Extrai todas as informações disponíveis do arquivo HIDR.DAT.
    
    Args:
        output_csv: Caminho do arquivo CSV de saída. Se None, usa nome padrão.
    
    Returns:
        pd.DataFrame: DataFrame com todas as informações ou None em caso de erro
    """
    # Caminho do arquivo HIDR.DAT na raiz
    hidr_path = os.path.join(os.path.dirname(__file__), "HIDR.DAT")
    
    # Verificar se existe com maiúsculas ou minúsculas
    if not os.path.exists(hidr_path):
        hidr_path_lower = os.path.join(os.path.dirname(__file__), "hidr.dat")
        if os.path.exists(hidr_path_lower):
            hidr_path = hidr_path_lower
        else:
            print(f"❌ Arquivo HIDR.DAT não encontrado na raiz do projeto")
            return None
    
    try:
        # Ler arquivo usando inewave
        print(f"📖 Lendo arquivo: {hidr_path}")
        hidr = Hidr.read(hidr_path)
        
        # Acessar cadastro
        cadastro = hidr.cadastro
        
        if cadastro is None or cadastro.empty:
            print("⚠️ Nenhuma usina encontrada no cadastro")
            return None
        
        print(f"✅ {len(cadastro)} usina(s) encontrada(s)")
        print(f"✅ {len(cadastro.columns)} coluna(s) disponível(is)")
        
        # Criar uma cópia do DataFrame para trabalhar
        df_completo = cadastro.copy()
        
        # Resetar índice para evitar ambiguidade entre índice e colunas
        # O índice original será perdido, mas vamos criar codigo_usina a partir dele
        indices_originais = df_completo.index.values
        df_completo = df_completo.reset_index(drop=True)
        
        # Verificar se já existe uma coluna 'codigo_usina'
        if 'codigo_usina' in df_completo.columns:
            # Se já existe, remover e recriar baseado no índice original
            print("⚠️  Coluna 'codigo_usina' já existe. Recriando baseado no índice original...")
            df_completo = df_completo.drop(columns=['codigo_usina'])
        
        # Criar coluna codigo_usina baseada nos índices originais
        # Os índices originais do DataFrame são 0-based, mas o código da usina é 1-based
        df_completo.insert(0, 'codigo_usina', indices_originais + 1)
        
        # Processar todas as colunas, garantindo tipos adequados e valores nulos tratados
        print("📊 Processando dados...")
        
        # Converter tipos de dados para garantir que sejam serializáveis no CSV
        for col in df_completo.columns:
            # Pular codigo_usina que já está correto
            if col == 'codigo_usina':
                df_completo[col] = df_completo[col].astype(int)
                continue
                
            # Converter tipos específicos do pandas que podem causar problemas no CSV
            if df_completo[col].dtype == 'object':
                # Manter strings como estão, mas tratar NaN
                df_completo[col] = df_completo[col].astype(str).replace('nan', '')
            elif pd.api.types.is_integer_dtype(df_completo[col]):
                # Garantir que inteiros sejam tratados corretamente
                df_completo[col] = df_completo[col].fillna(0).astype('Int64')
            elif pd.api.types.is_float_dtype(df_completo[col]):
                # Manter floats como estão, mas garantir NaN como string vazia no CSV
                df_completo[col] = df_completo[col].astype(float)
        
        # Ordenar por código da usina
        df_completo = df_completo.sort_values('codigo_usina')
        
        # Definir caminho do arquivo CSV de saída
        if output_csv is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_csv = os.path.join(os.path.dirname(__file__), f"hidr_completo_{timestamp}.csv")
        
        # Salvar em CSV
        print(f"💾 Salvando dados completos em: {output_csv}")
        df_completo.to_csv(output_csv, index=False, encoding='utf-8-sig', sep=';')
        
        print(f"✅ Arquivo CSV salvo com sucesso!")
        print(f"   - Total de usinas: {len(df_completo)}")
        print(f"   - Total de colunas: {len(df_completo.columns)}")
        print(f"   - Tamanho do arquivo: {os.path.getsize(output_csv) / 1024:.2f} KB")
        
        # Exibir lista de colunas
        print(f"\n📋 Colunas extraídas ({len(df_completo.columns)}):")
        for i, col in enumerate(df_completo.columns, 1):
            tipo = str(df_completo[col].dtype)
            nao_nulos = df_completo[col].notna().sum()
            print(f"   {i:3d}. {col:<50} [{tipo:<10}] ({nao_nulos} valores não-nulos)")
        
        return df_completo
        
    except Exception as e:
        print(f"❌ Erro ao processar arquivo HIDR.DAT: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return None


def listar_resumo_usinas(df_completo):
    """
    Lista um resumo das usinas extraídas.
    
    Args:
        df_completo: DataFrame completo com todas as informações
    """
    if df_completo is None or df_completo.empty:
        print("⚠️ Nenhum dado disponível para resumo")
        return
    
    print("\n" + "=" * 80)
    print("RESUMO DAS USINAS")
    print("=" * 80)
    
    # Selecionar apenas colunas principais para exibição
    colunas_principais = ['codigo_usina', 'nome_usina', 'posto', 'submercado', 'empresa']
    colunas_disponiveis = [col for col in colunas_principais if col in df_completo.columns]
    
    if colunas_disponiveis:
        print("\n📊 Primeiras 20 usinas:")
        print("-" * 80)
        df_resumo = df_completo[colunas_disponiveis].head(20)
        
        # Formatar para exibição
        for _, row in df_resumo.iterrows():
            codigo = row.get('codigo_usina', '-')
            nome = str(row.get('nome_usina', '-')).strip()[:30]
            posto = row.get('posto', '-')
            submercado = row.get('submercado', '-')
            empresa = row.get('empresa', '-')
            print(f"  Código {codigo:3d}: {nome:<30} | Posto: {posto:4} | Submercado: {submercado:2} | Empresa: {empresa:3}")
        
        if len(df_completo) > 20:
            print(f"\n  ... e mais {len(df_completo) - 20} usina(s)")
    
    # Estatísticas
    print("\n📈 ESTATÍSTICAS:")
    print(f"   - Total de usinas: {len(df_completo)}")
    
    # Usinas por submercado
    if 'submercado' in df_completo.columns:
        submercados = df_completo['submercado'].value_counts().sort_index()
        print(f"   - Usinas por submercado:")
        for sub, count in submercados.items():
            print(f"     * Submercado {sub}: {count} usinas")
    
    # Calcular potência total se disponível
    if 'potencia_nominal_conjunto_1' in df_completo.columns:
        potencia_total = 0.0
        for i in range(1, 6):
            pot_col = f'potencia_nominal_conjunto_{i}'
            maq_col = f'maquinas_conjunto_{i}'
            if pot_col in df_completo.columns and maq_col in df_completo.columns:
                for _, row in df_completo.iterrows():
                    potencia = row.get(pot_col, 0)
                    maquinas = row.get(maq_col, 0)
                    if pd.notna(potencia) and pd.notna(maquinas):
                        potencia_total += float(potencia) * float(maquinas)
        
        if potencia_total > 0:
            print(f"   - Potência total instalada: {potencia_total:.2f} MWmed")
    
    # Volume máximo total
    if 'volume_maximo' in df_completo.columns:
        volume_max_total = df_completo['volume_maximo'].fillna(0).sum()
        if volume_max_total > 0:
            print(f"   - Volume máximo total: {volume_max_total:.2f} hm³")
    
    print("=" * 80)


def main():
    """
    Função principal que executa a extração completa e salva em CSV.
    """
    print("=" * 80)
    print("EXTRAÇÃO COMPLETA DE DADOS DO HIDR.DAT")
    print("=" * 80)
    print()
    
    # Extrair todas as informações
    df_completo = extrair_todas_informacoes_hidr()
    
    if df_completo is not None:
        # Exibir resumo
        listar_resumo_usinas(df_completo)
        
        print()
        print("✅ Extração concluída com sucesso!")
        print()
        print("💡 Dica: Abra o arquivo CSV gerado em Excel ou outro editor de planilhas")
        print("   para visualizar todas as informações das usinas hidrelétricas.")
        print()
    else:
        print()
        print("❌ Falha na extração dos dados.")
        print()
    
    return df_completo


if __name__ == "__main__":
    df = main()
