# -*- coding: utf-8 -*-
"""
graficos.py
Responsável por gerar os gráficos de apoio à análise:
 - Evolução do patrimônio (determinístico)
 - Comparativo de cenários (Monte Carlo: pessimista / esperado / otimista)
 - Alocação da carteira (pizza)

Os gráficos são salvos como arquivos .png na pasta informada.
"""

import os
import matplotlib # type: ignore
matplotlib.use("Agg")  # backend sem interface gráfica (salva direto em arquivo)
import matplotlib.pyplot as plt # type: ignore

from mercado import CLASSES_ATIVOS


def _preparar_pasta(pasta_saida: str):
    os.makedirs(pasta_saida, exist_ok=True)


def plotar_evolucao_patrimonio(df, nome_cliente: str, pasta_saida: str = "saida") -> str:
    """Gera gráfico de linha com a evolução do saldo x total aportado."""
    _preparar_pasta(pasta_saida)
    fig, ax = plt.subplots(figsize=(9, 5))

    ax.plot(df["ano"], df["saldo"], label="Saldo projetado", color="#2E86AB", linewidth=2)
    ax.plot(df["ano"], df["total_aportado"], label="Total aportado", color="#A23B72",
            linestyle="--", linewidth=1.5)
    ax.fill_between(df["ano"], df["total_aportado"], df["saldo"],
                     color="#2E86AB", alpha=0.15, label="Rendimento")

    ax.set_title(f"Evolução do Patrimônio — {nome_cliente}", fontsize=13, fontweight="bold")
    ax.set_xlabel("Anos")
    ax.set_ylabel("Valor (R$)")
    ax.legend()
    ax.grid(alpha=0.3)

    caminho = os.path.join(pasta_saida, "evolucao_patrimonio.png")
    fig.tight_layout()
    fig.savefig(caminho, dpi=120)
    plt.close(fig)
    return caminho


def plotar_comparativo_cenarios(df_mc, nome_cliente: str, pasta_saida: str = "saida") -> str:
    """Gera gráfico com os três cenários da simulação de Monte Carlo."""
    _preparar_pasta(pasta_saida)
    fig, ax = plt.subplots(figsize=(9, 5))

    ax.plot(df_mc["ano"], df_mc["cenario_otimista"], label="Otimista (perc. 90)",
            color="#06A77D", linewidth=1.8)
    ax.plot(df_mc["ano"], df_mc["cenario_esperado"], label="Esperado (mediana)",
            color="#2E86AB", linewidth=2.2)
    ax.plot(df_mc["ano"], df_mc["cenario_pessimista"], label="Pessimista (perc. 10)",
            color="#D62246", linewidth=1.8)

    ax.fill_between(df_mc["ano"], df_mc["cenario_pessimista"], df_mc["cenario_otimista"],
                     color="#2E86AB", alpha=0.1)

    ax.set_title(f"Cenários de Projeção (Monte Carlo) — {nome_cliente}", fontsize=13, fontweight="bold")
    ax.set_xlabel("Anos")
    ax.set_ylabel("Valor (R$)")
    ax.legend()
    ax.grid(alpha=0.3)

    caminho = os.path.join(pasta_saida, "cenarios_monte_carlo.png")
    fig.tight_layout()
    fig.savefig(caminho, dpi=120)
    plt.close(fig)
    return caminho


def plotar_alocacao(alocacao: dict, nome_cliente: str, pasta_saida: str = "saida") -> str:
    """Gera gráfico de pizza com a alocação sugerida da carteira."""
    _preparar_pasta(pasta_saida)
    labels = [CLASSES_ATIVOS[c]["nome"] for c in alocacao.keys()]
    valores = list(alocacao.values())

    fig, ax = plt.subplots(figsize=(7, 7))
    cores = plt.cm.Set2.colors
    ax.pie(valores, labels=labels, autopct="%1.1f%%", startangle=90,
           colors=cores, textprops={"fontsize": 9})
    ax.set_title(f"Alocação Sugerida da Carteira — {nome_cliente}", fontsize=13, fontweight="bold")
    ax.axis("equal")

    caminho = os.path.join(pasta_saida, "alocacao_carteira.png")
    fig.tight_layout()
    fig.savefig(caminho, dpi=120)
    plt.close(fig)
    return caminho


def gerar_todos_graficos(df_determ, df_mc, alocacao, nome_cliente, pasta_saida="saida") -> list:
    """Gera todos os gráficos de uma vez e retorna a lista de caminhos gerados."""
    caminhos = [
        plotar_evolucao_patrimonio(df_determ, nome_cliente, pasta_saida),
        plotar_comparativo_cenarios(df_mc, nome_cliente, pasta_saida),
        plotar_alocacao(alocacao, nome_cliente, pasta_saida),
    ]
    return caminhos