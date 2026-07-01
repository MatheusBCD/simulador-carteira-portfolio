# Simulador de Perfil do Cliente — Projeção de Resultados

Sistema em Python que coleta os dados de um cliente, identifica o perfil de
risco (suitability), monta uma carteira sugerida e projeta a evolução do
patrimônio ao longo do tempo (cenário determinístico + Monte Carlo).

## Estrutura do projeto

| Arquivo         | Responsabilidade                                                        |
|-----------------|---------------------------------------------------------------------------|
| `mercado.py`    | Premissas de mercado: retorno, risco e inflação por classe de ativo      |
| `indicadores.py`| Questionário de perfil de risco, alocação-modelo e indicadores (CAGR...) |
| `simulador.py`  | Motor de cálculo: projeção determinística e simulação de Monte Carlo     |
| `graficos.py`   | Geração dos gráficos (evolução, cenários, alocação) em PNG               |
| `main.py`       | Versão via terminal (linha de comando)                                   |
| `app.py`        | Versão com interface gráfica (Tkinter)                                   |

## Como configurar no Visual Studio

1. Instale a **carga de trabalho "Desenvolvimento Python"** no Visual Studio
   (se ainda não tiver).
2. Crie um novo projeto Python vazio ou abra a pasta `simulador_cliente`
   diretamente (**Arquivo > Abrir > Pasta...**).
3. Certifique-se de que os 6 arquivos `.py` estejam todos na mesma pasta.
4. Abra o **Terminal do Desenvolvedor** (ou o Terminal integrado) na pasta
   do projeto e instale as dependências:

   ```
   pip install -r requirements.txt
   ```

5. Para rodar a versão de terminal:

   ```
   python main.py
   ```

6. Para rodar a versão com interface gráfica:

   ```
   python app.py
   ```

   > O `tkinter` já vem incluído na instalação padrão do Python no Windows.
   > Se ele não estiver disponível, reinstale o Python marcando a opção
   > "tcl/tk and IDLE" no instalador oficial (python.org).

## Fluxo de uso

1. Preencha os dados do cliente (nome, idade, renda, valor inicial, aporte
   mensal e prazo).
2. Responda o questionário de perfil de risco (4 perguntas).
3. O sistema classifica o perfil como **conservador**, **moderado** ou
   **arrojado** e sugere automaticamente uma alocação de carteira.
4. É calculada a projeção do patrimônio mês a mês, considerando o retorno
   médio esperado da carteira sugerida.
5. É rodada uma simulação de Monte Carlo (várias trajetórias aleatórias)
   para mostrar os cenários pessimista, esperado e otimista.
6. Os gráficos são salvos na pasta `saida/`:
   - `evolucao_patrimonio.png`
   - `cenarios_monte_carlo.png`
   - `alocacao_carteira.png`

## Personalização

- Para ajustar as premissas de retorno/risco de mercado, edite o dicionário
  `CLASSES_ATIVOS` em `mercado.py`.
- Para alterar as perguntas do questionário ou as carteiras-modelo por
  perfil, edite `PERGUNTAS_PERFIL` e `ALOCACOES_MODELO` em `indicadores.py`.
- Para mudar a quantidade de simulações do Monte Carlo, altere o parâmetro
  `n_simulacoes` na chamada de `simulador.projetar_monte_carlo()`.