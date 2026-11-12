"""
excecoes.py - Exceções personalizadas do sistema (Apostila 2º Bimestre, Cap. 4.4).

Cada exceção representa um tipo de problema de negócio. O app.py converte
cada uma em uma resposta HTTP adequada (400, 404, 409).
"""


class ValidacaoError(Exception):
    """Dado inválido enviado pelo usuário (campo vazio, número negativo, etc.)."""
    pass


class NaoEncontradoError(Exception):
    """Registro procurado não existe no banco de dados."""
    pass


class EstoqueInsuficienteError(Exception):
    """Tentativa de dar saída em uma quantidade maior que a do estoque."""

    def __init__(self, disponivel, solicitado):
        self.disponivel = disponivel
        self.solicitado = solicitado
        super().__init__(
            f"Estoque insuficiente! Disponível: {disponivel}, solicitado: {solicitado}"
        )
