"""
Processadores de dados compartilhados.
Contém apenas lógica pura de extração de dados, sem formatação.
"""

from .clast_processor import ClastDataProcessor
from .carga_processor import CargaDataProcessor
from .vazoes_processor import VazoesDataProcessor
from .limites_intercambio_processor import LimitesIntercambioDataProcessor
from .cadastro_processor import CadastroDataProcessor
from .confhd_processor import ConfhdDataProcessor

__all__ = [
    "ClastDataProcessor",
    "CargaDataProcessor",
    "VazoesDataProcessor",
    "LimitesIntercambioDataProcessor",
    "CadastroDataProcessor",
    "ConfhdDataProcessor",
]
