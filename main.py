# -*- coding: utf-8 -*-
"""
main.py
Ponto de entrada via terminal (linha de comando).
Coleta os dados do cliente, aplica o questionário de perfil de risco,
executa a simulação e apresenta os resultados + gera os gráficos.

Para executar:
    python main.py
"""

import sys
from mercado import resumo_mercado
from indicadores import (
    PERGUNTAS_PERFIL,
    calcular_pontuacao,
    classificar_perfil,
    sugerir_alocacao,
    resumo_indicadores,
)
from simulador import ClientePerfil, SimuladorFinanceiro
from graficos import gerar_todos_graficos


def ler_float(mensagem: str) -> float:
    while True:
        try:
            return float(input(mensagem).replace(",", "."))
        except ValueError:
            print("  Valor inválido. Digite apenas números (ex: 1500.50).")


def ler_int(mensagem: str) -> int:
    while True:
        try:
            return int(input(mensagem))
        except ValueError:
            print("  Valor inválido. Digite um número inteiro.")


def aplicar_questionario() -> str:
    print("\n=== Questionário de Perfil de Risco ===")
    respostas = []
    for item in PERGUNTAS_PERFIL:
        print(f"\n{item['pergunta']}")
        for chave, (texto, _) in item["opcoes"].items():
            print(f"  [{chave}] {texto}")
        while True:
            escolha = input("Escolha uma opção: ").strip()
            if escolha in item["opcoes"]:
                respostas.append(item["opcoes"][escolha][1])
                break
            print("  Opção inválida, tente novamente.")

    pontuacao = calcular_pontuacao(respostas)
    perfil = classificar_perfil(pontuacao)
    print(f"\n>> Pontuação total: {pontuacao} | Perfil identificado: {perfil.upper()}")
    return perfil


def coletar_dados_cliente() -> ClientePerfil:
    print("\n=== Dados do Cliente ===")
    nome = input("Nome do cliente: ").strip() or "Cliente"
    idade = ler_int("Idade: ")
    renda_mensal = ler_float("Renda mensal (R$): ")
    valor_inicial = ler_float("Valor inicial disponível para investir (R$): ")
    aporte_mensal = ler_float("Aporte mensal planejado (R$): ")
    prazo_anos = ler_int("Prazo do investimento (em anos): ")

    perfil_risco = aplicar_questionario()
    alocacao = sugerir_alocacao(perfil_risco)

    cliente = ClientePerfil(
        nome=nome,
        idade=idade,
        renda_mensal=renda_mensal,
        valor_inicial=valor_inicial,
        aporte_mensal=aporte_mensal,
        prazo_anos=prazo_anos,
        perfil_risco=perfil_risco,
        alocacao=alocacao,
    )
    return cliente


def exibir_resultados(cliente: ClientePerfil, simulador: SimuladorFinanceiro):
    df = simulador.projetar_deterministico()
    valor_final = df["saldo"].iloc[-1]
    total_aportado = df["total_aportado"].iloc[-1]
    rendimento = valor_final - total_aportado

    print("\n=== Resultado da Projeção ===")
    print(f"Cliente: {cliente.nome} | Perfil: {cliente.perfil_risco.upper()}")
    print(f"Retorno médio anual estimado da carteira: {simulador.retorno_anual*100:.2f}%")
    print(f"Prazo: {cliente.prazo_anos} anos")
    print(f"Total investido (aportes + inicial): R$ {total_aportado:,.2f}")
    print(f"Valor final projetado: R$ {valor_final:,.2f}")
    print(f"Rendimento projetado: R$ {rendimento:,.2f}")

    indicadores = resumo_indicadores(total_aportado, valor_final, cliente.prazo_anos)
    print("\n=== Indicadores ===")
    for chave, valor in indicadores.items():
        if "valor" in chave:
            print(f"{chave}: R$ {valor:,.2f}")
        else:
            print(f"{chave}: {valor:.2f}%")

    return df


def main():
    print(resumo_mercado())
    cliente = coletar_dados_cliente()
    simulador = SimuladorFinanceiro(cliente)

    df_determ = exibir_resultados(cliente, simulador)
    print("\nExecutando simulação de Monte Carlo (isso pode levar alguns segundos)...")
    df_mc = simulador.projetar_monte_carlo(n_simulacoes=300)
    valor_otimista = df_mc["cenario_otimista"].iloc[-1]
    valor_esperado = df_mc["cenario_esperado"].iloc[-1]
    valor_pessimista = df_mc["cenario_pessimista"].iloc[-1]

    print("\n=== Cenários de Projeção (Monte Carlo) ===")
    print(f"Cenário otimista: R$ {valor_otimista:,.2f}")
    print(f"Cenário esperado: R$ {valor_esperado:,.2f}")
    print(f"Cenário pessimista: R$ {valor_pessimista:,.2f}")

    caminhos = gerar_todos_graficos(df_determ, df_mc, cliente.alocacao, cliente.nome)
    print("\n=== Gráficos gerados ===")
    for c in caminhos:
        print(f"  - {c}")

    print("\nAnálise concluída com sucesso!")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nOperação cancelada pelo usuário.")
        sys.exit(0)
