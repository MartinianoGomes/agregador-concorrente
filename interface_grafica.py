"""Interface desktop para o agregador TCP de combustíveis.

Com os servidores TCP ativos (scripts/run_all.sh ou scripts/apresentar.sh),
execute em outro terminal:
    python interface_grafica.py                        # agregador na porta 5000
    python interface_grafica.py --porta 15000          # ex.: macOS, porta 5000 ocupada
    AGREGADOR_PORTA=15000 python interface_grafica.py  # idem, por variável de ambiente
    python interface_grafica.py --rastreio             # mostra as mensagens no terminal

A consulta de preços sempre usa src.cliente.consultar (socket TCP), enviando o
estado (UF) e o município escolhidos no seletor. Os CSVs locais são lidos
somente para preencher o seletor de municípios. Requer o Tkinter (no Linux,
pacote python3-tk).
"""

from __future__ import annotations

import argparse
import os
import queue
import threading
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

from src import municipios as mun
from src import protocolo as p
from src.cliente import consultar
from src.protocolo import COMBUSTIVEIS, ESTRATEGIA_CONCORRENTE, ESTRATEGIA_SEQUENCIAL

PASTA_DADOS = Path(__file__).resolve().parent / "data"
HOST_AGREGADOR = "127.0.0.1"
PORTA_AGREGADOR = int(os.environ.get("AGREGADOR_PORTA", "5000"))


class InterfaceAgregador(tk.Tk):
    def __init__(self, host: str = HOST_AGREGADOR, porta: int = PORTA_AGREGADOR) -> None:
        super().__init__()
        self.host, self.porta = host, porta
        self.title("Agregador de combustíveis | Região Norte")
        self.geometry("900x750")
        self.minsize(750, 640)
        self.configure(bg="#F3F6F9")

        self.cidade = tk.StringVar(value="BELEM - PA")
        self.municipios = mun.carregar_municipios(PASTA_DADOS)
        self.combustivel = tk.StringVar(value="gasolina_comum")
        self.estrategia = tk.StringVar(value=ESTRATEGIA_CONCORRENTE)
        self.status = tk.StringVar(value="Pronto para consultar o agregador TCP.")
        self.menor = tk.StringVar(value="—")
        self.tempo = tk.StringVar(value="—")
        self.respostas: queue.Queue[tuple[str, object]] = queue.Queue()
        self.consulta_ativa = False

        self._montar_tela()
        self.after(100, self._verificar_respostas)

    def _montar_tela(self) -> None:
        estilo = ttk.Style(self)
        if "clam" in estilo.theme_names():
            estilo.theme_use("clam")
        estilo.configure("Form.TFrame", background="#FFFFFF")
        estilo.configure("TLabel", font=("Arial", 11))
        estilo.configure("Treeview", font=("Arial", 11), rowheight=29)
        estilo.configure("Treeview.Heading", font=("Arial", 11, "bold"))
        estilo.configure("Consultar.TButton", font=("Arial", 11, "bold"), padding=10)

        cabecalho = tk.Frame(self, bg="#173B60", padx=24, pady=22)
        cabecalho.pack(fill="x")
        tk.Label(cabecalho, text="Agregador de preços de combustíveis", fg="white",
                 bg="#173B60", font=("Arial", 19, "bold")).pack(anchor="w")
        tk.Label(cabecalho, text=f"Região Norte · Dados históricos ANP · Agregador TCP em {self.host}:{self.porta}",
                 fg="#D8E8F6", bg="#173B60", font=("Arial", 11)).pack(anchor="w", pady=(6, 0))

        painel = ttk.Frame(self, style="Form.TFrame", padding=18)
        painel.pack(fill="x", padx=20, pady=16)
        painel.columnconfigure(0, weight=2)
        painel.columnconfigure(1, weight=2)

        ttk.Label(painel, text="Município - UF").grid(row=0, column=0, sticky="w")
        ttk.Label(painel, text="Combustível").grid(row=0, column=1, sticky="w", padx=(15, 0))
        self.campo_municipio = ttk.Combobox(
            painel, textvariable=self.cidade, values=self.municipios,
            state="normal", font=("Arial", 12))
        self.campo_municipio.grid(row=1, column=0, sticky="ew", pady=(5, 12))
        self.campo_municipio.bind("<KeyRelease>", self._filtrar_municipios)
        ttk.Combobox(painel, textvariable=self.combustivel, values=COMBUSTIVEIS,
                     state="readonly", font=("Arial", 11)).grid(
            row=1, column=1, sticky="ew", padx=(15, 0), pady=(5, 12))

        ttk.Label(painel, text="Estratégia de consulta").grid(row=2, column=0, sticky="w")
        opcoes = ttk.Frame(painel, style="Form.TFrame")
        opcoes.grid(row=3, column=0, columnspan=2, sticky="w", pady=(6, 12))
        ttk.Radiobutton(opcoes, text="Sequencial", variable=self.estrategia,
                        value=ESTRATEGIA_SEQUENCIAL).pack(side="left", padx=(0, 18))
        ttk.Radiobutton(opcoes, text="Concorrente (threads)", variable=self.estrategia,
                        value=ESTRATEGIA_CONCORRENTE).pack(side="left")

        self.botao = ttk.Button(painel, text="Consultar os quatro postos", style="Consultar.TButton",
                                command=self._iniciar_consulta)
        self.botao.grid(row=4, column=0, columnspan=2, sticky="ew")

        indicadores = tk.Frame(self, bg="#F3F6F9")
        indicadores.pack(fill="x", padx=20, pady=(0, 10))
        for i in (0, 1):
            indicadores.columnconfigure(i, weight=1)
        self._indicador(indicadores, "MENOR PREÇO", self.menor, 0)
        self._indicador(indicadores, "TEMPO DO AGREGADOR", self.tempo, 1)

        area = tk.Frame(self, bg="#F3F6F9")
        area.pack(fill="both", expand=True, padx=20)
        tk.Label(area, text="Ranking por preço", bg="#F3F6F9", fg="#173B60",
                 font=("Arial", 13, "bold")).pack(anchor="w", pady=(0, 7))
        colunas = ("posto", "preco", "situacao")
        self.tabela = ttk.Treeview(area, columns=colunas, show="headings", height=6)
        for nome, titulo, largura in (("posto", "Posto", 130), ("preco", "Preço", 160),
                                      ("situacao", "Situação", 340)):
            self.tabela.heading(nome, text=titulo)
            self.tabela.column(nome, width=largura, anchor="center" if nome != "situacao" else "w")
        self.tabela.pack(fill="both", expand=True)
        self.tabela.tag_configure("melhor", background="#DFF4E8")
        self.tabela.tag_configure("falha", foreground="#A04433")

        rodape = tk.Frame(self, bg="#F3F6F9", padx=20, pady=13)
        rodape.pack(fill="x")
        tk.Label(rodape, textvariable=self.status, bg="#F3F6F9", fg="#334F68",
                 font=("Arial", 10), anchor="w", wraplength=720).pack(fill="x")
        tk.Label(rodape, text="A interface não consulta a ANP diretamente: Cliente → socket TCP → Agregador → Postos",
                 bg="#F3F6F9", fg="#64748B", font=("Arial", 9)).pack(anchor="w", pady=(6, 0))

    def _indicador(self, pai: tk.Frame, titulo: str, variavel: tk.StringVar, coluna: int) -> None:
        caixa = tk.Frame(pai, bg="#FFFFFF", padx=18, pady=14, highlightbackground="#DFE7EE",
                         highlightthickness=1)
        caixa.grid(row=0, column=coluna, sticky="ew", padx=(0, 6) if coluna == 0 else (6, 0))
        tk.Label(caixa, text=titulo, fg="#526779", bg="#FFFFFF",
                 font=("Arial", 9, "bold")).pack(anchor="w")
        tk.Label(caixa, textvariable=variavel, fg="#173B60", bg="#FFFFFF",
                 font=("Arial", 21, "bold")).pack(anchor="w", pady=(5, 0))

    def _filtrar_municipios(self, evento: tk.Event) -> None:
        """Permite digitar parte do nome sem perder o dropdown de municípios."""
        if evento.keysym in {"Up", "Down", "Return", "Escape", "Tab"}:
            return
        # ignora acentos e maiúsculas: "belém" encontra "BELEM - PA"
        self.campo_municipio["values"] = mun.filtrar(self.cidade.get(), self.municipios)

    def _iniciar_consulta(self) -> None:
        texto = self.cidade.get().strip()
        if not texto:
            messagebox.showwarning("Município obrigatório", "Selecione ou informe um município.")
            return
        if self.municipios:
            encontrado = mun.localizar(texto, self.municipios)
            if encontrado is None:
                messagebox.showwarning(
                    "Município não encontrado",
                    "Selecione um município da lista de dados históricos disponíveis.",
                )
                return
            texto = encontrado
        try:
            estado, cidade = mun.separar_municipio(texto)
        except ValueError as erro:
            messagebox.showwarning("Município inválido", str(erro).capitalize() + ".")
            return
        if self.consulta_ativa:
            return
        self.consulta_ativa = True
        self.botao.configure(state="disabled")
        self.status.set("Consultando os postos pelo agregador TCP...")
        self.menor.set("—")
        self.tempo.set("—")
        for item in self.tabela.get_children():
            self.tabela.delete(item)
        threading.Thread(target=self._consultar_em_segundo_plano,
                         args=(estado, cidade, self.combustivel.get(), self.estrategia.get()),
                         daemon=True).start()

    def _consultar_em_segundo_plano(self, estado: str, cidade: str, combustivel: str,
                                    estrategia: str) -> None:
        try:
            resposta = consultar(self.host, self.porta, estado, cidade, combustivel, estrategia)
            self.respostas.put(("sucesso", resposta))
        except (OSError, ValueError, KeyError, TypeError) as erro:
            self.respostas.put(("erro", str(erro)))

    def _verificar_respostas(self) -> None:
        try:
            while True:
                tipo, dados = self.respostas.get_nowait()
                self.consulta_ativa = False
                self.botao.configure(state="normal")
                if tipo == "sucesso":
                    self._mostrar_resultado(dados)
                else:
                    self.status.set(f"Falha na consulta: {dados}")
                    messagebox.showerror("Erro de comunicação", f"Não foi possível consultar o agregador.\n\n{dados}\n\nVerifique se o agregador TCP está ativo em {self.host}:{self.porta}.")
        except queue.Empty:
            pass
        self.after(100, self._verificar_respostas)

    def _mostrar_resultado(self, resposta: object) -> None:
        if not isinstance(resposta, dict):
            self.status.set("O agregador retornou uma resposta inválida.")
            return
        if resposta.get("status") == "erro":
            self.status.set(f"Requisição rejeitada: {resposta.get('mensagem', 'erro desconhecido')}")
            return
        melhor = resposta.get("menor_preco")
        if melhor:
            self.menor.set(f"R$ {melhor['preco']:.2f} · Posto {melhor['posto']}")
        self.tempo.set(f"{resposta.get('tempo_ms', '—')} ms")
        for pos, item in enumerate(resposta.get("resultados", []), 1):
            tags = ("melhor",) if melhor and item["posto"] == melhor["posto"] else ()
            self.tabela.insert("", "end", values=(f"{pos}. Posto {item['posto']}",
                                                   f"R$ {item['preco']:.2f}", "Disponível"), tags=tags)
        for item in resposta.get("indisponiveis", []):
            self.tabela.insert("", "end", values=(f"Posto {item.get('posto', '?')}", "—",
                                                   item.get("status", "sem resposta")), tags=("falha",))
        n = len(resposta.get("resultados", []))
        falhas = len(resposta.get("indisponiveis", []))
        self.status.set(f"Consulta finalizada: {n} posto(s) no ranking; {falhas} sem resposta "
                        f"[id {resposta.get('id', '-')}]. "
                        "Valores históricos da ANP, não preços em tempo real.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Interface gráfica do agregador de combustíveis.")
    parser.add_argument("--host", default=HOST_AGREGADOR)
    parser.add_argument("--porta", type=int, default=PORTA_AGREGADOR,
                        help="porta do agregador (padrão: $AGREGADOR_PORTA ou 5000)")
    parser.add_argument("--rastreio", action="store_true",
                        help="mostra no terminal cada mensagem enviada e recebida")
    args = parser.parse_args()
    if args.rastreio:
        p.configurar_rastreio("interface")
    InterfaceAgregador(args.host, args.porta).mainloop()


if __name__ == "__main__":
    main()
