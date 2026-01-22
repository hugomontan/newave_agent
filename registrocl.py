from typing import Optional, List
from cfinterface.components.register import Register
from cfinterface.components.line import Line
from cfinterface.components.integerfield import IntegerField
from cfinterface.components.floatfield import FloatField
from cfinterface.components.literalfield import LiteralField


class GL(Register):
    """
    Registro que contém os cadastros de restrições elétricas.
    """

    __slots__ = []

    IDENTIFIER = "GL  "
    IDENTIFIER_DIGITS = 4
    LINE = Line(
        [
            IntegerField(3, 4),
            IntegerField(2, 9),
            IntegerField(2, 14),
            FloatField(10, 19, 2),
            FloatField(5, 29, 0),
            FloatField(10, 34, 2),
            FloatField(5, 44, 0),
            FloatField(10, 49, 2),
            FloatField(5, 59, 0),
            LiteralField(8, 65),
        ]
    )

    @property
    def codigo_usina(self) -> Optional[int]:
        """
        O código da UTE despachada no registro GL

        :return: O código.
        :rtype: Optional[int]
        """
        return self.data[0]

    @codigo_usina.setter
    def codigo_usina(self, c: int):
        self.data[0] = c

    @property
    def codigo_submercado(self) -> Optional[int]:
        """
        O código do submercado de despacho da UTE

        :return: O código do submercado.
        :rtype: Optional[int]
        """
        return self.data[1]

    @codigo_submercado.setter
    def codigo_submercado(self, e: int):
        self.data[1] = e

    @property
    def estagio(self) -> Optional[int]:
        """
        O estágio de despacho da UTE

        :return: O estágio.
        :rtype: Optional[int]
        """
        return self.data[2]

    @estagio.setter
    def estagio(self, e: int):
        self.data[2] = e

    @property
    def geracao(self) -> List[float]:
        """
        Os valores de geração por patamar para o despacho
        da UTE

        :return: As gerações como `list[float]`
        """
        return [v for v in self.data[3:8:2] if v is not None]

    @geracao.setter
    def geracao(self, gers: List[float]):
        novos = len(gers)
        atuais = len(self.geracao)
        if novos != atuais:
            raise ValueError(
                "Número de gerações incompatível. De"
                + f"vem ser fornecidos {atuais}, mas foram {novos}"
            )
        self.data[3:9:2] = gers

    @property
    def duracao(self) -> List[float]:
        """
        As durações de cada patamar para o despacho
        da UTE

        :return: As durações como `list[float]`
        """
        return [v for v in self.data[4:9:2] if v is not None]

    @duracao.setter
    def duracao(self, durs: List[float]):
        novos = len(durs)
        atuais = len(self.duracao)
        if novos != atuais:
            raise ValueError(
                "Número de durações incompatível. De"
                + f"vem ser fornecidos {atuais}, mas foram {novos}"
            )
        self.data[4:9:2] = durs

    @property
    def data_inicio(self) -> Optional[str]:
        """
        A data de despacho da UTE

        :return: A data no formato DDMMYYYY.
        :rtype: Optional[str]
        """
        return self.data[9]

    @data_inicio.setter
    def data_inicio(self, d: str):
        self.data[9] = d