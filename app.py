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
import threading

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt

import mercado
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
        self.geometry("1300x700")
        self.resizable(True, True)

        self.respostas_vars = []
        self._construir_layout()
        self._atualizar_mercado_async()

    # ---------------- ATUALIZAÇÃO DE MERCADO (em segundo plano) ----------------
    def _atualizar_mercado_async(self):
        """
        Busca dados reais de mercado (Selic, IPCA, Ibovespa) em uma thread
        separada, para não travar a janela enquanto espera a internet.
        """
        self.status_mercado.set("Atualizando dados de mercado...")
        if hasattr(self, "btn_atualizar_mercado"):
            self.btn_atualizar_mercado.configure(state="disabled")

        def tarefa():
            sucesso = mercado.atualizar_premissas(mostrar_mensagem=False)
            self.after(0, lambda: self._finalizar_atualizacao_mercado(sucesso))

        threading.Thread(target=tarefa, daemon=True).start()

    def _finalizar_atualizacao_mercado(self, sucesso: bool):
        if sucesso:
            texto = f"Dados de mercado atualizados em {mercado.DATA_ULTIMA_ATUALIZACAO}."
        else:
            texto = "Não foi possível atualizar. Usando valores de referência."
        self.status_mercado.set(texto)
        self._exibir_dados_mercado()
        self.btn_atualizar_mercado.configure(state="normal")

    def _exibir_dados_mercado(self):
        """Preenche o painel 'Premissas de Mercado' com os dados atuais
        (reais, se a atualização deu certo, ou de referência, se não)."""
        self.texto_mercado.configure(state="normal")
        self.texto_mercado.delete("1.0", tk.END)

        if mercado.DATA_ULTIMA_ATUALIZACAO:
            cabecalho = f"Atualizado em: {mercado.DATA_ULTIMA_ATUALIZACAO}\n(dados reais — BCB / Ibovespa)\n"
        else:
            cabecalho = "NÃO ATUALIZADO\n(usando valores de referência)\n"

        linhas = [
            cabecalho,
            "",
            f"Inflação anual estimada: {mercado.INFLACAO_ANUAL * 100:.2f}%",
            f"Taxa livre de risco (CDI/Selic): {mercado.TAXA_LIVRE_RISCO_ANUAL * 100:.2f}%",
            "",
            "Classes de ativos:",
        ]
        for dados in mercado.CLASSES_ATIVOS.values():
            linhas.append(
                f"  • {dados['nome']}\n"
                f"      retorno {dados['retorno_anual']*100:.2f}%  |  "
                f"risco {dados['volatilidade_anual']*100:.2f}%"
            )

        self.texto_mercado.insert(tk.END, "\n".join(linhas))
        self.texto_mercado.configure(state="disabled")

    # ---------------- LAYOUT ----------------
    def _construir_layout(self):
        topo = ttk.Frame(self)
        topo.pack(fill="x", padx=15, pady=(8, 0))

        self.status_mercado = tk.StringVar(value="Iniciando...")
        status_label = ttk.Label(topo, textvariable=self.status_mercado,
                                  font=("Segoe UI", 8, "italic"), foreground="#555")
        status_label.pack(side="left")

        self.btn_atualizar_mercado = ttk.Button(
            topo, text="Atualizar dados de mercado",
            command=self._atualizar_mercado_async, state="disabled"
        )
        self.btn_atualizar_mercado.pack(side="right")

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

        # --- Coluna extra: premissas de mercado (dados reais) ---
        mercado_frame = ttk.LabelFrame(container, text="Premissas de Mercado", padding=12)
        mercado_frame.grid(row=0, column=2, rowspan=3, sticky="ns", padx=(10, 0))

        self.texto_mercado = tk.Text(mercado_frame, width=38, height=28, wrap="word",
                                      font=("Consolas", 9))
        self.texto_mercado.pack(fill="both", expand=True)
        self.texto_mercado.insert(tk.END, "Buscando dados de mercado...")
        self.texto_mercado.configure(state="disabled")

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

            self._exibir_texto(cliente, simulador, valor_final, total_aportado, indicadores)
            self._exibir_grafico(df)

        except ValueError as e:
            messagebox.showerror("Erro nos dados", f"Verifique os campos preenchidos.\n{e}")
        except Exception as e:
            messagebox.showerror("Erro inesperado", str(e))

    def _exibir_texto(self, cliente, simulador, valor_final, total_aportado, indicadores):
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