# -*- coding: utf-8 -*-
"""
app.py
Interface gráfica (Tkinter) do Simulador de Perfil do Cliente.
Permite preencher os dados, responder o questionário de perfil de risco,
gerar a projeção e visualizar o resultado dentro da própria janela,
sem precisar usar o terminal.

Para executar:
    python app.py
"""

import tkinter as tk
from tkinter import ttk, messagebox

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg # type: ignore
import matplotlib.pyplot as plt # type: ignore

from indicadores import (
    PERGUNTAS_PERFIL,
    calcular_pontuacao,
    classificar_perfil,
    sugerir_alocacao,
    resumo_indicadores,
)
from simulador import ClientePerfil, SimuladorFinanceiro


class SimuladorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Simulador de Perfil do Cliente — Projeção Financeira")
        self.geometry("950x680")
        self.resizable(True, True)

        self.respostas_vars = []
        self._construir_layout()

    # ---------------- LAYOUT ----------------
    def _construir_layout(self):
        container = ttk.Frame(self, padding=15)
        container.pack(fill="both", expand=True)

        # --- Coluna esquerda: formulário ---
        form = ttk.LabelFrame(container, text="Dados do Cliente", padding=12)
        form.grid(row=0, column=0, sticky="n", padx=(0, 10))

        campos = [
            ("Nome", "nome"),
            ("Idade", "idade"),
            ("Renda mensal (R$)", "renda_mensal"),
            ("Valor inicial (R$)", "valor_inicial"),
            ("Aporte mensal (R$)", "aporte_mensal"),
            ("Prazo (anos)", "prazo_anos"),
        ]
        self.entradas = {}
        for i, (rotulo, chave) in enumerate(campos):
            ttk.Label(form, text=rotulo + ":").grid(row=i, column=0, sticky="w", pady=4)
            entrada = ttk.Entry(form, width=22)
            entrada.grid(row=i, column=1, pady=4)
            self.entradas[chave] = entrada

        # --- Questionário de perfil de risco ---
        quest = ttk.LabelFrame(container, text="Perfil de Risco", padding=12)
        quest.grid(row=1, column=0, sticky="n", pady=(10, 0), padx=(0, 10))

        for i, item in enumerate(PERGUNTAS_PERFIL):
            ttk.Label(quest, text=item["pergunta"], wraplength=280,
                      font=("Segoe UI", 9, "bold")).grid(row=i * 2, column=0, sticky="w", pady=(6, 0))
            var = tk.StringVar(value="1")
            self.respostas_vars.append((var, item["opcoes"]))
            opcoes_frame = ttk.Frame(quest)
            opcoes_frame.grid(row=i * 2 + 1, column=0, sticky="w")
            for chave, (texto, _) in item["opcoes"].items():
                ttk.Radiobutton(opcoes_frame, text=texto, value=chave, variable=var,
                                 width=32).pack(anchor="w")

        ttk.Button(container, text="Calcular Projeção", command=self._calcular
                   ).grid(row=2, column=0, pady=15)

        # --- Coluna direita: resultados ---
        resultado_frame = ttk.LabelFrame(container, text="Resultado", padding=12)
        resultado_frame.grid(row=0, column=1, rowspan=3, sticky="nsew")
        container.columnconfigure(1, weight=1)
        container.rowconfigure(0, weight=1)

        self.texto_resultado = tk.Text(resultado_frame, width=55, height=14, wrap="word")
        self.texto_resultado.pack(fill="x", pady=(0, 10))
        self.texto_resultado.configure(state="disabled")

        self.grafico_container = ttk.Frame(resultado_frame)
        self.grafico_container.pack(fill="both", expand=True)

    # ---------------- LÓGICA ----------------
    
    def _ler_dados_formulario(self) -> ClientePerfil:
        nome = self.entradas["nome"].get().strip() or "Cliente"
        idade = int(self.entradas["idade"].get())
        renda_mensal = float(self.entradas["renda_mensal"].get().replace(",", "."))
        valor_inicial = float(self.entradas["valor_inicial"].get().replace(",", "."))
        aporte_mensal = float(self.entradas["aporte_mensal"].get().replace(",", "."))
        prazo_anos = int(self.entradas["prazo_anos"].get())

        respostas = [int(item["opcoes"][var.get()][1]) for var, item in
                     [(v, {"opcoes": o}) for v, o in self.respostas_vars]]
        pontuacao = calcular_pontuacao(respostas)
        perfil = classificar_perfil(pontuacao)
        alocacao = sugerir_alocacao(perfil)

        return ClientePerfil(
            nome=nome, idade=idade, renda_mensal=renda_mensal,
            valor_inicial=valor_inicial, aporte_mensal=aporte_mensal,
            prazo_anos=prazo_anos, perfil_risco=perfil, alocacao=alocacao,
        )

    def _calcular(self):
        try:
            cliente = self._ler_dados_formulario()
            simulador = SimuladorFinanceiro(cliente)
            df = simulador.projetar_deterministico()

            valor_final = df["saldo"].iloc[-1]
            total_aportado = df["total_aportado"].iloc[-1]
            indicadores = resumo_indicadores(total_aportado, valor_final, cliente.prazo_anos)

            df_mc = simulador.projetar_monte_carlo(n_simulacoes=300)
            cenarios = {
                "otimista": df_mc["cenario_otimista"].iloc[-1],
                "esperado": df_mc["cenario_esperado"].iloc[-1],
                "pessimista": df_mc["cenario_pessimista"].iloc[-1],
            }

            self._exibir_texto(cliente, simulador, valor_final, total_aportado, indicadores, cenarios)
            self._exibir_grafico(df)

        except ValueError as e:
            messagebox.showerror("Erro nos dados", f"Verifique os campos preenchidos.\n{e}")
        except Exception as e:
            messagebox.showerror("Erro inesperado", str(e))

    def _exibir_texto(self, cliente, simulador, valor_final, total_aportado, indicadores, cenarios):
        self.texto_resultado.configure(state="normal")
        self.texto_resultado.delete("1.0", tk.END)
        texto = (
            f"Cliente: {cliente.nome} | Perfil: {cliente.perfil_risco.upper()}\n"
            f"Retorno médio anual estimado: {simulador.retorno_anual*100:.2f}%\n"
            f"Prazo: {cliente.prazo_anos} anos\n\n"
            f"Total investido: R$ {total_aportado:,.2f}\n"
            f"Valor final projetado: R$ {valor_final:,.2f}\n"
            f"Rendimento projetado: R$ {valor_final - total_aportado:,.2f}\n\n"
            f"Rentabilidade acumulada: {indicadores['rentabilidade_acumulada_%']:.2f}%\n"
            f"CAGR: {indicadores['cagr_%']:.2f}%  |  CAGR real: {indicadores['cagr_real_%']:.2f}%\n"
            f"=== Cenários de Projeção (Monte Carlo) ===\n"
            f"Cenário otimista: R$ {cenarios['otimista']:,.2f}\n"
            f"Cenário esperado: R$ {cenarios['esperado']:,.2f}\n"
            f"Cenário pessimista: R$ {cenarios['pessimista']:,.2f}\n"
        )
        self.texto_resultado.insert(tk.END, texto)
        self.texto_resultado.configure(state="disabled")

    def _exibir_grafico(self, df):
        for widget in self.grafico_container.winfo_children():
            widget.destroy()

        fig, ax = plt.subplots(figsize=(5.5, 3.6))
        ax.plot(df["ano"], df["saldo"], label="Saldo projetado", color="#2E86AB")
        ax.plot(df["ano"], df["total_aportado"], label="Total aportado",
                color="#A23B72", linestyle="--")
        ax.fill_between(df["ano"], df["total_aportado"], df["saldo"], color="#2E86AB", alpha=0.15)
        ax.set_xlabel("Anos")
        ax.set_ylabel("R$")
        ax.legend(fontsize=8)
        ax.grid(alpha=0.3)
        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=self.grafico_container)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)


if __name__ == "__main__":
    app = SimuladorApp()
    app.mainloop()