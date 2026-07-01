# -*- coding: utf-8 -*-
"""
simulador.py
Núcleo do sistema: recebe os dados do cliente e calcula a projeção
de resultados (evolução do patrimônio ao longo do tempo).

Inclui:
 - ClientePerfil: estrutura de dados com as informações do cliente
 - SimuladorFinanceiro: motor de cálculo (determinístico e Monte Carlo)
"""

from dataclasses import dataclass, field
import numpy as np
import pandas as pd

from mercado import retorno_carteira, volatilidade_carteira_simplificada


@dataclass
class ClientePerfil:
    """Representa os dados coletados do cliente."""
    nome: str
    idade: int
    renda_mensal: float
    valor_inicial: float
    aporte_mensal: float
    prazo_anos: int
    perfil_risco: str = "moderado"
    alocacao: dict = field(default_factory=dict)

    def validar(self):
        """Valida os dados básicos do cliente, levantando erro se inválidos."""
        erros = []
        if self.idade <= 0 or self.idade > 120:
            erros.append("Idade inválida.")
        if self.renda_mensal < 0:
            erros.append("Renda mensal não pode ser negativa.")
        if self.valor_inicial < 0:
            erros.append("Valor inicial não pode ser negativo.")
        if self.aporte_mensal < 0:
            erros.append("Aporte mensal não pode ser negativo.")
        if self.prazo_anos <= 0:
            erros.append("Prazo em anos deve ser maior que zero.")
        if erros:
            raise ValueError(" | ".join(erros))


class SimuladorFinanceiro:
    """Motor de cálculo das projeções financeiras do cliente."""

    def __init__(self, cliente: ClientePerfil):
        self.cliente = cliente
        self.cliente.validar()
        self.retorno_anual = retorno_carteira(cliente.alocacao)
        self.volatilidade_anual = volatilidade_carteira_simplificada(cliente.alocacao)
        # Conversão de taxa anual para taxa mensal equivalente
        self.retorno_mensal = (1 + self.retorno_anual) ** (1 / 12) - 1

    def projetar_deterministico(self) -> pd.DataFrame:
        """
        Projeta a evolução do patrimônio mês a mês, de forma determinística,
        aplicando o retorno médio esperado da carteira.
        """
        meses = self.cliente.prazo_anos * 12
        saldo = self.cliente.valor_inicial
        registros = []

        for mes in range(1, meses + 1):
            saldo = saldo * (1 + self.retorno_mensal) + self.cliente.aporte_mensal
            registros.append({
                "mes": mes,
                "ano": round(mes / 12, 2),
                "saldo": saldo,
                "total_aportado": self.cliente.valor_inicial + self.cliente.aporte_mensal * mes,
            })

        df = pd.DataFrame(registros)
        df["rendimento_acumulado"] = df["saldo"] - df["total_aportado"]
        return df

    def projetar_monte_carlo(self, n_simulacoes: int = 500, semente: int = 42) -> pd.DataFrame:
        """
        Executa uma simulação de Monte Carlo, variando o retorno mensal
        de forma aleatória (distribuição normal) para capturar a incerteza
        do mercado. Retorna um DataFrame com os percentis 10, 50 e 90 por mês.
        """
        rng = np.random.default_rng(semente)
        meses = self.cliente.prazo_anos * 12
        vol_mensal = self.volatilidade_anual / np.sqrt(12)

        resultados = np.zeros((n_simulacoes, meses))

        for sim in range(n_simulacoes):
            saldo = self.cliente.valor_inicial
            retornos_mensais = rng.normal(loc=self.retorno_mensal, scale=vol_mensal, size=meses)
            for mes in range(meses):
                saldo = saldo * (1 + retornos_mensais[mes]) + self.cliente.aporte_mensal
                resultados[sim, mes] = saldo

        p10 = np.percentile(resultados, 10, axis=0)
        p50 = np.percentile(resultados, 50, axis=0)
        p90 = np.percentile(resultados, 90, axis=0)

        df = pd.DataFrame({
            "mes": np.arange(1, meses + 1),
            "ano": np.round(np.arange(1, meses + 1) / 12, 2),
            "cenario_pessimista": p10,
            "cenario_esperado": p50,
            "cenario_otimista": p90,
        })
        return df

    def valor_final_estimado(self) -> float:
        """Retorna apenas o valor final projetado (cenário determinístico)."""
        df = self.projetar_deterministico()
        return float(df["saldo"].iloc[-1])