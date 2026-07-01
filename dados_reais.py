# -*- coding: utf-8 -*-
"""
dados_reais.py
Busca dados reais de mercado para atualizar as premissas do simulador:
 - Selic (Banco Central, via biblioteca python-bcb)
 - IPCA acumulado 12 meses (Banco Central, via python-bcb)
 - Retorno e volatilidade históricos do Ibovespa (via yfinance)

Todas as funções têm tratamento de erro: se a internet cair ou a API
mudar, elas retornam None em vez de travar o programa. Quem chama essas
funções decide o que fazer (normalmente: manter o valor de referência
antigo).

Dependências (instale com pip):
    pip install python-bcb yfinance
"""

from datetime import datetime
import numpy as np

# Códigos das séries no SGS (Sistema Gerenciador de Séries Temporais do
# Banco Central). Se algum dia pararem de funcionar, consulte a lista
# oficial em: https://www3.bcb.gov.br/sgspub
CODIGO_SGS_SELIC_META = 432    # Meta Selic definida pelo Copom (% a.a.)
CODIGO_SGS_IPCA_12M = 13522    # IPCA acumulado em 12 meses (%)


def buscar_selic_atual():
    """
    Busca a taxa Selic meta mais recente no Banco Central.
    Retorna a taxa em formato decimal (ex: 0.105 para 10,5%) ou None se falhar.
    """
    try:
        from bcb import sgs
        df = sgs.get({"selic": CODIGO_SGS_SELIC_META}, last=1)
        valor = df["selic"].iloc[-1]
        return round(float(valor) / 100, 4)
    except Exception as e:
        print(f"[Aviso] Não foi possível buscar a Selic: {e}")
        return None


def buscar_ipca_12meses():
    """
    Busca o IPCA acumulado nos últimos 12 meses no Banco Central.
    Retorna a taxa em formato decimal (ex: 0.045 para 4,5%) ou None se falhar.
    """
    try:
        from bcb import sgs
        df = sgs.get({"ipca12m": CODIGO_SGS_IPCA_12M}, last=1)
        valor = df["ipca12m"].iloc[-1]
        return round(float(valor) / 100, 4)
    except Exception as e:
        print(f"[Aviso] Não foi possível buscar o IPCA: {e}")
        return None


def buscar_retorno_volatilidade_ibovespa(anos: int = 5):
    """
    Baixa o histórico mensal do Ibovespa (ticker ^BVSP) dos últimos `anos`
    anos e calcula o retorno médio anualizado e a volatilidade anualizada.
    Retorna uma tupla (retorno_anual, volatilidade_anual), ou (None, None)
    se falhar.
    """
    try:
        import yfinance as yf
        import pandas as pd

        dados = yf.download("^BVSP", period=f"{anos}y", interval="1mo",
                             progress=False, auto_adjust=True)
        if dados.empty or "Close" not in dados:
            print("[Aviso] Ibovespa: dados vazios retornados pela API.")
            return None, None

        precos = dados["Close"]
        # Versões recentes do yfinance retornam colunas em MultiIndex
        # (Campo, Ticker) mesmo para um único ticker — isso faz dados["Close"]
        # vir como uma tabela (DataFrame) em vez de uma série simples (Series).
        # Aqui garantimos que sempre trabalhamos com uma Series de 1 dimensão.
        if isinstance(precos, pd.DataFrame):
            precos = precos.iloc[:, 0]
        precos = precos.dropna()

        retornos_mensais = precos.pct_change().dropna()
        if len(retornos_mensais) < 6:
            print("[Aviso] Ibovespa: histórico insuficiente para calcular.")
            return None, None

        media_mensal = float(retornos_mensais.mean())
        retorno_anual = (1 + media_mensal) ** 12 - 1
        volatilidade_anual = float(retornos_mensais.std()) * np.sqrt(12)
        return round(retorno_anual, 4), round(volatilidade_anual, 4)
    except Exception as e:
        print(f"[Aviso] Não foi possível buscar dados do Ibovespa: {e}")
        return None, None


def buscar_todas_premissas() -> dict:
    """
    Busca todos os dados reais disponíveis de uma vez.
    Retorna um dicionário; qualquer campo que falhar vem como None.
    """
    retorno_ibov, vol_ibov = buscar_retorno_volatilidade_ibovespa()
    return {
        "selic": buscar_selic_atual(),
        "ipca": buscar_ipca_12meses(),
        "retorno_ibovespa": retorno_ibov,
        "volatilidade_ibovespa": vol_ibov,
        "data_atualizacao": datetime.now().strftime("%d/%m/%Y %H:%M"),
    }


if __name__ == "__main__":
    print("Buscando dados reais de mercado (isso pode levar alguns segundos)...\n")
    dados = buscar_todas_premissas()
    for chave, valor in dados.items():
        print(f"{chave}: {valor}")