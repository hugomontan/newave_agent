"""
Tool para consultar informações do Registro GL (Gerações de Termelétricas GNL já Comandadas) do DECOMP.
Acessa dados de geração por patamar, duração, data de início, etc.
"""
from decomp_agent.app.tools.base import DECOMPTool
from decomp_agent.app.config import safe_print
import os
import sys
import re
from typing import Dict, Any, Optional, List
from pathlib import Path

# Importar Dadgnl
from decomp_agent.app.utils.dadgnl import Dadgnl
from registrocl import GL


class GLGeracoesGNLTool(DECOMPTool):
    """
    Tool para consultar informações do Registro GL (Gerações de Termelétricas GNL já Comandadas) do DECOMP.
    
    Dados disponíveis:
    - Código da usina
    - Código do submercado
    - Estágio/Semana
    - Geração por patamar (1=PESADA, 2=MÉDIA, 3=LEVE)
    - Duração por patamar (horas)
    - Data de início (DDMMYYYY)
    """
    
    def get_name(self) -> str:
        return "GLGeracoesGNLTool"
    
    def can_handle(self, query: str) -> bool:
        """
        Verifica se a query é sobre gerações GNL já comandadas do Registro GL.
        
        Args:
            query: Query do usuário
            
        Returns:
            True se a tool pode processar a query
        """
        query_lower = query.lower()
        
        keywords = [
            "geracoes gnl",
            "gerações gnl",
            "geracao gnl",
            "geração gnl",
            "registro gl",
            "bloco gl",
            "gl decomp",
            "despacho antecipado",
            "despacho antecipado gnl",
            "termelétricas gnl",
            "termeletricas gnl",
            "gnl já comandadas",
            "gnl ja comandadas",
            "geracoes comandadas",
            "gerações comandadas",
            "geracao comandada",
            "geração comandada",
        ]
        
        # Verificar se há keywords relacionados a GL/GNL
        tem_keyword = any(kw in query_lower for kw in keywords)
        
        # Verificar se menciona "gl" junto com termos relacionados a geração/usina
        tem_gl = "gl" in query_lower
        tem_termo_geracao = any(termo in query_lower for termo in [
            "geracao", "geração", "despacho", "gnl", "usina", "termelétrica", "termeletrica"
        ])
        
        return tem_keyword or (tem_gl and tem_termo_geracao)
    
    def get_description(self) -> str:
        return """
        Tool para consultar informações do Registro GL (Gerações de Termelétricas GNL já Comandadas) do DECOMP.
        
        Acessa dados do registro GL que define:
        - Gerações de termelétricas GNL já comandadas (despacho antecipado)
        - Código da usina e submercado
        - Estágio/Semana de despacho
        - Dados por patamar (1=PESADA, 2=MÉDIA, 3=LEVE):
          * Geração (MW)
          * Duração do patamar (horas)
        - Data de início do despacho (DDMMYYYY)
        
        Exemplos de queries:
        - "Gerações GNL da usina 86"
        - "Registro GL de Santa Cruz"
        - "Despacho antecipado da usina 224"
        - "GL GNL usina 15"
        - "Gerações comandadas GNL"
        """
    
    def execute(self, query: str, **kwargs) -> Dict[str, Any]:
        """
        Executa a consulta sobre gerações GNL já comandadas do Registro GL.
        
        Args:
            query: Query do usuário
            **kwargs: Argumentos adicionais opcionais
            
        Returns:
            Dict com dados das gerações GNL formatados
        """
        try:
            # ⚡ OTIMIZAÇÃO: Usar cache global do Dadgnl
            from decomp_agent.app.utils.dadgnl_cache import get_cached_dadgnl
            dadgnl = get_cached_dadgnl(self.deck_path)
            
            if dadgnl is None:
                return {
                    "success": False,
                    "error": "Arquivo dadgnl não encontrado (nenhum arquivo dadgnl.rv* encontrado)"
                }
            
            # Extrair código da usina da query
            codigo_usina = self._extract_codigo_usina(query)
            
            safe_print(f"[GL TOOL] Query recebida: {query}")
            safe_print(f"[GL TOOL] Código usina extraído: {codigo_usina}")
            
            # Obter todos os registros GL usando método gl() do Dadgnl
            # Primeiro obter todos, depois filtrar manualmente se necessário
            gl_registros = dadgnl.gl(df=False)
            
            if not gl_registros:
                return {
                    "success": False,
                    "error": "Nenhum registro GL encontrado no arquivo dadgnl"
                }
            
            # Converter para lista se for único registro
            if isinstance(gl_registros, GL):
                gl_registros = [gl_registros]
            
            safe_print(f"[GL TOOL] Total de registros GL encontrados: {len(gl_registros)}")
            
            # Filtrar por código de usina se especificado
            if codigo_usina is not None:
                gl_registros = [
                    gl for gl in gl_registros 
                    if gl.codigo_usina == codigo_usina
                ]
                safe_print(f"[GL TOOL] Registros GL após filtro por usina {codigo_usina}: {len(gl_registros)}")
            
            if not gl_registros:
                return {
                    "success": False,
                    "error": f"Nenhum registro GL encontrado para a usina {codigo_usina}" if codigo_usina else "Nenhum registro GL encontrado"
                }
            
            # Converter registros para lista de dicts
            data = []
            for gl in gl_registros:
                geracao = gl.geracao
                duracao = gl.duracao
                
                # Garantir que temos 3 valores de geração e duração (preencher com None se necessário)
                geracao_pat1 = geracao[0] if len(geracao) > 0 else None
                geracao_pat2 = geracao[1] if len(geracao) > 1 else None
                geracao_pat3 = geracao[2] if len(geracao) > 2 else None
                
                duracao_pat1 = duracao[0] if len(duracao) > 0 else None
                duracao_pat2 = duracao[1] if len(duracao) > 1 else None
                duracao_pat3 = duracao[2] if len(duracao) > 2 else None
                
                record = {
                    "codigo_usina": gl.codigo_usina,
                    "codigo_submercado": gl.codigo_submercado,
                    "estagio": gl.estagio,
                    "semana": gl.estagio,  # Alias para compatibilidade
                    "geracao_patamar_1": geracao_pat1,
                    "geracao_patamar_2": geracao_pat2,
                    "geracao_patamar_3": geracao_pat3,
                    "duracao_patamar_1": duracao_pat1,
                    "duracao_patamar_2": duracao_pat2,
                    "duracao_patamar_3": duracao_pat3,
                    "data_inicio": gl.data_inicio,
                }
                data.append(record)
            
            # Se não especificou usina, tentar extrair da query
            if codigo_usina is None:
                # Tentar buscar por nome de usina conhecida
                codigo_usina_extraido = self._extract_usina_from_query(query)
                if codigo_usina_extraido is not None:
                    codigo_usina = codigo_usina_extraido
                    data = [d for d in data if d.get('codigo_usina') == codigo_usina]
                    safe_print(f"[GL TOOL] Filtro aplicado por usina extraída: {codigo_usina}")
            
            # Obter código da usina dos dados (se houver)
            if data:
                codigo_usina_final = data[0].get('codigo_usina')
            else:
                codigo_usina_final = codigo_usina
            
            # Buscar nome da usina através do bloco CT
            nome_usina = None
            if codigo_usina_final is not None:
                safe_print(f"[GL TOOL] 🔍 Buscando nome da usina {codigo_usina_final} no bloco CT...")
                nome_usina = self._get_nome_usina(codigo_usina_final)
                if nome_usina:
                    safe_print(f"[GL TOOL] ✅ Nome encontrado: '{nome_usina}'")
                else:
                    safe_print(f"[GL TOOL] ⚠️ Nome não encontrado para usina {codigo_usina_final}")
            
            safe_print(f"[GL TOOL] Retornando {len(data)} registros GL")
            safe_print(f"[GL TOOL] 📋 Resultado final: codigo_usina={codigo_usina_final}, nome_usina={nome_usina}")
            
            return {
                "success": True,
                "data": data,
                "total_registros": len(data),
                "codigo_usina": codigo_usina_final,
                "nome_usina": nome_usina,
                "tool": self.get_name()
            }
            
        except Exception as e:
            safe_print(f"[GL TOOL] ❌ Erro ao consultar Registro GL: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": f"Erro ao consultar Registro GL: {str(e)}",
                "tool": self.get_name()
            }
    
    def _extract_codigo_usina(self, query: str) -> Optional[int]:
        """Extrai código da usina da query."""
        patterns = [
            r'usina\s*(\d+)',
            r'ute\s*(\d+)',
            r'gl\s*(\d+)',
            r'código\s*(\d+)',
            r'codigo\s*(\d+)',
        ]
        for pattern in patterns:
            match = re.search(pattern, query.lower())
            if match:
                try:
                    return int(match.group(1))
                except ValueError:
                    continue
        return None
    
    def _extract_usina_from_query(self, query: str) -> Optional[int]:
        """
        Extrai código da usina da query usando nomes conhecidos.
        """
        query_lower = query.lower()
        
        # Mapeamento de nomes conhecidos para códigos
        usinas_conhecidas = {
            "santa cruz": 86,
            "luiz ormelo": 15,
            "luizormelo": 15,
            "psergipe": 224,
            "psergipe i": 224,
        }
        
        for nome, codigo in usinas_conhecidas.items():
            if nome in query_lower:
                safe_print(f"[GL TOOL] ✅ Usina encontrada por nome: {nome} -> {codigo}")
                return codigo
        
        return None
    
    def _get_nome_usina(self, codigo_usina: int) -> Optional[str]:
        """
        Busca o nome da usina usando mapeamento hardcoded.
        As usinas GL não estão cadastradas no bloco CT, então usamos mapeamento fixo.
        
        Args:
            codigo_usina: Código da usina
            
        Returns:
            Nome da usina ou None se não encontrado
        """
        # Mapeamento hardcoded das usinas GL (não estão no bloco CT)
        mapeamento_gl = {
            86: "SANTA CRUZ",
            224: "PSERGIPE I",
        }
        
        nome_usina = mapeamento_gl.get(codigo_usina)
        if nome_usina:
            safe_print(f"[GL TOOL] ✅ Nome encontrado para usina {codigo_usina} (hardcoded): '{nome_usina}'")
            return nome_usina
        
        safe_print(f"[GL TOOL] ⚠️ Usina {codigo_usina} não encontrada no mapeamento GL")
        return None
