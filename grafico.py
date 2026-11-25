"""Gera as figuras do Capítulo 4 a partir de metricas.csv e resultados_por_arquivo.csv.
Requer: pip install matplotlib
Saída: figura_metricas_por_conjunto.png, figura_metricas_por_classe.png, figura_tempo_por_arquivo.png
"""
import csv
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

COR = {"precisao": "#1f6fb4", "revocacao": "#e08a1e", "f1": "#3a3a3a"}
ROT = {"precisao": "Precisão", "revocacao": "Revocação", "f1": "F1"}
NOME = {"sintetica": "Sintéticos", "variantes": "Variantes", "real": "Reais", "total": "Total",
        "coleta_excessiva": "Coleta excessiva", "sem_recusa": "Ausência de recusa",
        "notificacao_manipulativa": "Notificação manipulativa", "obstrucao_cancelamento": "Obstrução de cancelamento"}

met = list(csv.DictReader(open("metricas.csv", encoding="utf-8")))

def barras(linhas, titulo, arq):
    fig, ax = plt.subplots(figsize=(8, 4.2), dpi=200)
    n = len(linhas); w = 0.26
    for i, m in enumerate(("precisao", "revocacao", "f1")):
        xs = [j + (i - 1) * w for j in range(n)]
        vals = [float(l[m]) for l in linhas]
        b = ax.bar(xs, vals, w, label=ROT[m], color=COR[m])
        for x, v in zip(xs, vals): ax.text(x, v + 0.015, f"{v:.2f}".replace(".", ","), ha="center", fontsize=7)
    ax.set_xticks(range(n)); ax.set_xticklabels([NOME.get(l["nome"], l["nome"]) for l in linhas], fontsize=8)
    ax.set_ylim(0, 1.12); ax.set_ylabel("Valor da métrica")
    ax.set_title(titulo, fontsize=10); ax.legend(fontsize=8, frameon=False, ncol=3, loc="upper center", bbox_to_anchor=(0.5, -0.12))
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout(); fig.savefig(arq); plt.close(fig)

barras([l for l in met if l["escopo"] == "conjunto"], "Métricas por conjunto de arquivos", "figura_metricas_por_conjunto.png")
barras([l for l in met if l["escopo"] == "classe"], "Métricas por classe de risco (todos os conjuntos)", "figura_metricas_por_classe.png")

tempos = {}
for l in csv.DictReader(open("resultados_por_arquivo.csv", encoding="utf-8")):
    tempos[l["arquivo"]] = float(l["tempo_medio_s"])
itens = sorted(tempos.items(), key=lambda x: x[1])
fig, ax = plt.subplots(figsize=(8, max(4, len(itens) * 0.2)), dpi=200)
cores = {"sintetica": "#6b6b6b", "variantes": "#e08a1e", "real": "#1f6fb4"}
ax.barh([a.split("/")[-1] for a, _ in itens], [t for _, t in itens], color=[cores.get(a.split("/")[1], "#999") for a, _ in itens])
ax.set_xlabel("Tempo médio de execução (s)"); ax.set_title("Tempo por arquivo", fontsize=10)
ax.tick_params(axis="y", labelsize=6)
from matplotlib.patches import Patch
ax.legend(handles=[Patch(color=c, label=NOME[k]) for k, c in cores.items()], fontsize=8, frameon=False, loc="lower right")
ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout(); fig.savefig("figura_tempo_por_arquivo.png"); plt.close(fig)
print("Geradas: figura_metricas_por_conjunto.png, figura_metricas_por_classe.png, figura_tempo_por_arquivo.png")
