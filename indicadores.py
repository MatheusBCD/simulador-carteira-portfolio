# -*- coding: utf-8 -*-
"""
indicadores.py
Responsável por:
 - Definir o questionário de perfil de risco (suitability)
 - Calcular a pontuação e classificar o perfil (conservador/moderado/arrojado)
 - Sugerir uma alocação de carteira-modelo por perfil
 - Calcular indicadores financeiros (CAGR, taxa real, rentabilidade acumulada)
"""

from mercado import INFLACAO_ANUAL

# Perguntas do questionário de suitability.
# Cada resposta possui uma pontuação de 1 a 4 (quanto maior, mais arrojado)
PERGUNTAS_PERFIL = [
    {
        "pergunta": "Qual seu objetivo principal com os investimentos?",
        "opcoes": {
            "1": ("Preservar o capital, evitando perdas", 1),
            "2": ("Obter renda com baixo risco", 2),
            "3": ("Crescimento do patrimônio no médio prazo", 3),
            "4": ("Maximizar retorno, aceitando oscilações", 4),
        },
    },
    {
        "pergunta": "Qual seu horizonte de investimento?",
        "opcoes": {
            "1": ("Até 1 ano", 1),
            "2": ("De 1 a 3 anos", 2),
            "3": ("De 3 a 7 anos", 3),
            "4": ("Mais de 7 anos", 4),
        },
    },
    {
        "pergunta": "Se sua carteira caísse 15% em um mês, você:",
        "opcoes": {
            "1": ("Resgataria tudo imediatamente", 1),
            "2": ("Resgataria parte do valor", 2),
            "3": ("Manteria o investimento", 3),
            "4": ("Aproveitaria para investir mais", 4),
        },
    },
    {
        "pergunta": "Qual sua experiência com investimentos de risco (ações, fundos)?",
        "opcoes": {
            "1": ("Nenhuma experiência", 1),
            "2": ("Pouca experiência", 2),
            "3": ("Experiência moderada", 3),
            "4": ("Bastante experiência", 4),
        },
    },
]

# Alocação-modelo (percentual por classe de ativo) sugerida por perfil
ALOCACOES_MODELO = {
    "conservador": {
        "renda_fixa_pos": 0.60,
        "renda_fixa_pre": 0.30,
        "multimercado": 0.10,
    },
    "moderado": {
        "renda_fixa_pos": 0.35,
        "renda_fixa_pre": 0.20,
        "multimercado": 0.20,
        "acoes_br": 0.10,
        "fundos_imobiliarios": 0.15,
    },
    "arrojado": {
        "renda_fixa_pos": 0.15,
        "multimercado": 0.20,
        "acoes_br": 0.30,
        "acoes_global": 0.20,
        "fundos_imobiliarios": 0.15,
    },
}


def calcular_pontuacao(respostas: list) -> int:
    """Soma a pontuação das respostas (lista de inteiros de 1 a 4)."""
    return sum(respostas)


def classificar_perfil(pontuacao: int) -> str:
    """
    Classifica o perfil de risco do cliente com base na pontuação total.
    Pontuação mínima possível: 4 | máxima: 16
    """
    if pontuacao <= 7:
        return "conservador"
    elif pontuacao <= 12:
        return "moderado"
    else:
        return "arrojado"


def sugerir_alocacao(perfil: str) -> dict:
    """Retorna a alocação-modelo (dict classe: peso) para o perfil informado."""
    return ALOCACOES_MODELO.get(perfil, ALOCACOES_MODELO["moderado"])


def taxa_real(taxa_nominal_anual: float, inflacao_anual: float = INFLACAO_ANUAL) -> float:
    """
    Calcula a taxa de juros real anual (descontada a inflação),
    usando a fórmula de Fisher.
    """
    return (1 + taxa_nominal_anual) / (1 + inflacao_anual) - 1


def cagr(valor_inicial: float, valor_final: float, anos: float) -> float:
    """Calcula a taxa de crescimento anual composta (CAGR)."""
    if valor_inicial <= 0 or anos <= 0:
        return 0.0
    return (valor_final / valor_inicial) ** (1 / anos) - 1


def rentabilidade_acumulada(valor_inicial: float, valor_final: float) -> float:
    """Calcula o retorno percentual acumulado no período."""
    if valor_inicial <= 0:
        return 0.0
    return (valor_final / valor_inicial) - 1


def resumo_indicadores(valor_inicial: float, valor_final: float, anos: float) -> dict:
    """Retorna um dicionário com os principais indicadores calculados."""
    taxa_cagr = cagr(valor_inicial, valor_final, anos)
    return {
        "valor_inicial": valor_inicial,
        "valor_final": valor_final,
        "rentabilidade_acumulada_%": rentabilidade_acumulada(valor_inicial, valor_final) * 100,
        "cagr_%": taxa_cagr * 100,
        "cagr_real_%": taxa_real(taxa_cagr) * 100,
    }