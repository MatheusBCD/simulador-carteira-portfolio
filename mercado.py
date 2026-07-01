# -*- coding: utf-8 -*-
"""
mercado.py
Contém as premissas de mercado utilizadas pelo simulador:
retornos esperados, volatilidade e inflação por classe de ativo.
Esses números são estimativas de referência e podem ser ajustados
conforme cenário macroeconômico atual.
"""

# Inflação média anual esperada (ex: IPCA) — valor de referência (fallback)
INFLACAO_ANUAL = 0.045  # 4,5% ao ano

# Retorno livre de risco (ex: Selic / CDI) — valor de referência (fallback)
TAXA_LIVRE_RISCO_ANUAL = 0.105  # 10,5% ao ano

# Data/hora da última atualização com dados reais (None = ainda não atualizado,
# está usando os valores fixos de referência acima)
DATA_ULTIMA_ATUALIZACAO = None

# Premissas de retorno e risco (volatilidade) por classe de ativo
# retorno_anual: retorno médio esperado ao ano (nominal)
# volatilidade_anual: desvio padrão anual (quanto maior, mais risco)
# Todos os valores abaixo são de referência (fallback) até que
# atualizar_premissas() seja chamada com sucesso.
CLASSES_ATIVOS = {
    "renda_fixa_pos": {
        "nome": "Renda Fixa Pós-fixada (CDI/Tesouro Selic)",
        "retorno_anual": 0.105,
        "volatilidade_anual": 0.02,
    },
    "renda_fixa_pre": {
        "nome": "Renda Fixa Prefixada / Inflação",
        "retorno_anual": 0.095,
        "volatilidade_anual": 0.06,
    },
    "multimercado": {
        "nome": "Fundos Multimercado",
        "retorno_anual": 0.12,
        "volatilidade_anual": 0.09,
    },
    "acoes_br": {
        "nome": "Ações Brasil",
        "retorno_anual": 0.15,
        "volatilidade_anual": 0.22,
    },
    "acoes_global": {
        "nome": "Ações Globais",
        "retorno_anual": 0.13,
        "volatilidade_anual": 0.18,
    },
    "fundos_imobiliarios": {
        "nome": "Fundos Imobiliários (FIIs)",
        "retorno_anual": 0.11,
        "volatilidade_anual": 0.13,
    },
}


def atualizar_premissas(mostrar_mensagem: bool = True) -> bool:
    """
    Tenta atualizar as premissas de mercado com dados reais (Selic, IPCA,
    Ibovespa). Se a busca falhar (sem internet, API fora do ar, biblioteca
    não instalada), mantém os valores de referência (fallback) e avisa —
    o programa nunca trava por causa disso.

    Retorna True se conseguiu atualizar com dados reais, False se manteve
    o fallback.
    """
    global INFLACAO_ANUAL, TAXA_LIVRE_RISCO_ANUAL, DATA_ULTIMA_ATUALIZACAO

    try:
        from dados_reais import buscar_todas_premissas
    except ImportError:
        if mostrar_mensagem:
            print("[Info] dados_reais.py não encontrado. Usando valores de referência.")
        return False

    dados = buscar_todas_premissas()
    atualizou_algo = False

    if dados.get("selic") is not None:
        TAXA_LIVRE_RISCO_ANUAL = dados["selic"]
        CLASSES_ATIVOS["renda_fixa_pos"]["retorno_anual"] = dados["selic"]
        atualizou_algo = True

    if dados.get("ipca") is not None:
        INFLACAO_ANUAL = dados["ipca"]
        atualizou_algo = True

    if dados.get("retorno_ibovespa") is not None and dados.get("volatilidade_ibovespa") is not None:
        CLASSES_ATIVOS["acoes_br"]["retorno_anual"] = dados["retorno_ibovespa"]
        CLASSES_ATIVOS["acoes_br"]["volatilidade_anual"] = dados["volatilidade_ibovespa"]
        atualizou_algo = True

    if atualizou_algo:
        DATA_ULTIMA_ATUALIZACAO = dados["data_atualizacao"]
        if mostrar_mensagem:
            print(f"[Info] Premissas de mercado atualizadas em {DATA_ULTIMA_ATUALIZACAO}.")
    else:
        if mostrar_mensagem:
            print("[Info] Não foi possível atualizar. Usando valores de referência.")

    return atualizou_algo


def listar_classes():
    """Retorna a lista de chaves das classes de ativos disponíveis."""
    return list(CLASSES_ATIVOS.keys())


def retorno_esperado(classe: str) -> float:
    """Retorna o retorno anual esperado de uma classe de ativo."""
    return CLASSES_ATIVOS[classe]["retorno_anual"]


def volatilidade_esperada(classe: str) -> float:
    """Retorna a volatilidade anual esperada de uma classe de ativo."""
    return CLASSES_ATIVOS[classe]["volatilidade_anual"]


def retorno_carteira(alocacao: dict) -> float:
    """
    Calcula o retorno anual esperado ponderado de uma carteira.
    alocacao: dict {classe_ativo: peso (0 a 1)}
    """
    retorno = 0.0
    for classe, peso in alocacao.items():
        retorno += peso * retorno_esperado(classe)
    return retorno


def volatilidade_carteira_simplificada(alocacao: dict) -> float:
    """
    Aproximação simplificada (sem considerar correlação entre ativos)
    da volatilidade da carteira, apenas para referência didática.
    """
    vol = 0.0
    for classe, peso in alocacao.items():
        vol += peso * volatilidade_esperada(classe)
    return vol


def resumo_mercado() -> str:
    """Retorna um texto formatado com o cenário de mercado atual."""
    status = (f"Premissas atualizadas em: {DATA_ULTIMA_ATUALIZACAO}"
              if DATA_ULTIMA_ATUALIZACAO
              else "Premissas atualizadas em: NÃO ATUALIZADO (usando valores de referência)")
    linhas = [
        "=== Premissas de Mercado ===",
        status,
        f"Inflação anual estimada: {INFLACAO_ANUAL * 100:.2f}%",
        f"Taxa livre de risco (CDI/Selic): {TAXA_LIVRE_RISCO_ANUAL * 100:.2f}%",
        "",
        "Classes de ativos disponíveis:",
    ]
    for chave, dados in CLASSES_ATIVOS.items():
        linhas.append(
            f"  - {dados['nome']}: retorno {dados['retorno_anual']*100:.2f}% "
            f"| risco {dados['volatilidade_anual']*100:.2f}%"
        )
    return "\n".join(linhas)


if __name__ == "__main__":
    print(resumo_mercado())