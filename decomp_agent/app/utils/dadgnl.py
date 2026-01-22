"""
Classe para ler arquivo dadgnl do DECOMP.
Similar ao Dadger, mas para o arquivo dadgnl que contém registros GL.
"""
from typing import Optional, List, TypeVar, Union, Type
from cfinterface.components.register import Register
from cfinterface.files.registerfile import RegisterFile
import sys
import os

# Adicionar diretório raiz ao path para importar registrocl
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
from registrocl import GL


T = TypeVar("T", bound=Register)


class Dadgnl(RegisterFile):
    """
    Armazena os dados do arquivo dadgnl do DECOMP.
    
    Esta classe lida com as informações de gerações de termelétricas GNL
    já comandadas no arquivo `dadgnl.rv*`. Possui métodos para acessar
    individualmente os registros GL.
    """
    
    REGISTERS = [GL]
    
    def __init__(self, data=...) -> None:
        super().__init__(data)
    
    def __registros_ou_df(
        self, t: Type[T], **kwargs
    ) -> Optional[Union[T, List[T]]]:
        """
        Método auxiliar para obter registros ou DataFrame.
        Similar ao padrão usado no Dadger.
        """
        kwargs_sem_df = {k: v for k, v in kwargs.items() if k != "df"}
        return self.data.get_registers_of_type(t, **kwargs_sem_df)
    
    def gl(
        self,
        codigo_usina: Optional[int] = None,
        codigo_submercado: Optional[int] = None,
        estagio: Optional[int] = None,
        df: bool = False,
    ) -> Optional[Union[GL, List[GL]]]:
        """
        Obtém registros GL (Gerações de Termelétricas GNL já Comandadas).
        
        Args:
            codigo_usina: Código da usina (filtro opcional)
            codigo_submercado: Código do submercado (filtro opcional)
            estagio: Estágio/semana (filtro opcional)
            df: Se True, retorna DataFrame em vez de objetos Register (não implementado ainda)
            
        Returns:
            Registros GL correspondentes
        """
        return self.__registros_ou_df(
            GL,
            codigo_usina=codigo_usina,
            codigo_submercado=codigo_submercado,
            estagio=estagio,
            df=df
        )
