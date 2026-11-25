"""Compara os alertas do línter com o gabarito e calcula precisão, revocação, F1 e tempo.

Uso:  python avaliar.py [--repeticoes N]
Gera: resultados.txt, resultados_por_arquivo.csv e metricas.csv
Conjuntos = subpastas de amostras/ (sintetica, variantes, real).
Gabarito: gabarito.csv e gabarito_real.csv (arquivos que DEVEM gerar alerta; arquivo ausente = sem defeito).
"""
import argparse, csv, json, os, subprocess, sys, time
from pathlib import Path

NPX = "npx.cmd" if os.name == "nt" else "npx"
SAIDA = "saida_spectral.json"
CLASSE = {
    "etico-coleta-excessiva": "coleta_excessiva",
    "etico-sem-recusa": "sem_recusa",
    "etico-notificacao-manipulativa": "notificacao_manipulativa",
    "etico-urgencia-artificial": "notificacao_manipulativa",
    "etico-cancelamento-obstruido": "obstrucao_cancelamento",
}
CLASSES = sorted(set(CLASSE.values()))

ap = argparse.ArgumentParser()
ap.add_argument("--repeticoes", type=int, default=1, help="vezes que cada arquivo é executado (para o tempo médio)")
args = ap.parse_args()

linhas_txt = []
def say(*a):
    s = " ".join(str(x) for x in a)
    print(s); linhas_txt.append(s)

def normaliza(p): return Path(p).as_posix()

# 1) gabarito
esperado = set()
for nome in ("gabarito.csv", "gabarito_real.csv"):
    if Path(nome).exists():
        with open(nome, encoding="utf-8", newline="") as f:
            for l in csv.DictReader(f):
                if l.get("arquivo") and l.get("classe"):
                    esperado.add((normaliza(l["arquivo"]), l["classe"]))

# 2) executa o línter em cada arquivo
arquivos = sorted(normaliza(p) for ext in ("yaml", "yml", "json")
                  for p in Path("amostras").rglob(f"*.{ext}"))
conjunto = lambda a: a.split("/")[1]
detectado, tempos, nao_eticos = set(), {}, {}
for arq in arquivos:
    ts = []
    for i in range(args.repeticoes):
        t0 = time.perf_counter()
        subprocess.run([NPX, "spectral", "lint", arq, "-r", ".spectral.yaml", "-f", "json", "-o", SAIDA],
                       capture_output=True, text=True, encoding="utf-8")
        ts.append(time.perf_counter() - t0)
        if i == 0:
            try:
                alertas = json.loads(Path(SAIDA).read_text(encoding="utf-8"))
            except (FileNotFoundError, json.JSONDecodeError):
                print("Falha ao ler a saída do línter em", arq); alertas = []
    tempos[arq] = sum(ts) / len(ts)
    nao_eticos[arq] = sum(1 for a in alertas if a["code"] not in CLASSE)
    for a in alertas:
        if a["code"] in CLASSE:
            detectado.add((arq, CLASSE[a["code"]]))
    print(f"  {arq}: {tempos[arq]:.2f} s", flush=True)

# 3) métricas
def metricas(esp, det):
    vp, fp, fn = len(esp & det), len(det - esp), len(esp - det)
    p = vp / (vp + fp) if vp + fp else 0.0
    r = vp / (vp + fn) if vp + fn else 0.0
    f1 = 2 * p * r / (p + r) if p + r else 0.0
    return vp, fp, fn, p, r, f1

def filtra(s, conj=None, classe=None):
    return {x for x in s if (conj is None or conjunto(x[0]) == conj) and (classe is None or x[1] == classe)}

conjuntos = sorted({conjunto(a) for a in arquivos})
tabela = []  # (escopo, nome, vp, fp, fn, p, r, f1, n_arquivos, tempo_medio)
def linha(escopo, nome, conj=None, classe=None):
    arqs = [a for a in arquivos if conj is None or conjunto(a) == conj]
    m = metricas(filtra(esperado, conj, classe), filtra(detectado, conj, classe))
    tm = sum(tempos[a] for a in arqs) / len(arqs) if arqs else 0
    tabela.append((escopo, nome, *m, len(arqs), tm))

for c in conjuntos: linha("conjunto", c, conj=c)
linha("conjunto", "total")
for cl in CLASSES: linha("classe", cl, classe=cl)
for c in conjuntos:
    for cl in CLASSES: linha(f"classe_em_{c}", cl, conj=c, classe=cl)

say(f"Arquivos analisados: {len(arquivos)} | repetições por arquivo: {args.repeticoes} | tempo médio por arquivo: {sum(tempos.values())/len(tempos):.2f} s")
say(f"{'':28}{'arqs':>5} {'VP':>3} {'FP':>3} {'FN':>3} {'prec':>6} {'rev':>6} {'F1':>6}  tempo(s)")
for esc, nome, vp, fp, fn, p, r, f1, n, tm in tabela:
    if esc == "conjunto":
        say(f"{nome:28}{n:>5} {vp:>3} {fp:>3} {fn:>3} {p:6.2f} {r:6.2f} {f1:6.2f}  {tm:.2f}")
say("\nPor classe de risco (todos os conjuntos):")
for esc, nome, vp, fp, fn, p, r, f1, n, tm in tabela:
    if esc == "classe":
        say(f"{nome:28}{'':>5} {vp:>3} {fp:>3} {fn:>3} {p:6.2f} {r:6.2f} {f1:6.2f}")
say("\nFalsos positivos (alerta sem defeito no gabarito):")
for x in sorted(detectado - esperado): say("  ", x)
say("Falsos negativos (defeito no gabarito sem alerta):")
for x in sorted(esperado - detectado): say("  ", x)
say("\nAlertas não éticos (ignorados, ex.: invalid-ref):")
for a, n in nao_eticos.items():
    if n: say(f"   {a}: {n}")

# 4) arquivos de saída
Path("resultados.txt").write_text("\n".join(str(l) for l in linhas_txt), encoding="utf-8")
with open("resultados_por_arquivo.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["arquivo", "conjunto", "classe", "esperado", "detectado", "resultado", "tempo_medio_s", "alertas_nao_eticos"])
    for a in arquivos:
        pares = {x for x in esperado | detectado if x[0] == a}
        if not pares:
            w.writerow([a, conjunto(a), "", 0, 0, "sem_defeito_sem_alerta", f"{tempos[a]:.3f}", nao_eticos[a]])
        for (_, cl) in sorted(pares):
            e, d = (a, cl) in esperado, (a, cl) in detectado
            res = "VP" if e and d else "FP" if d else "FN"
            w.writerow([a, conjunto(a), cl, int(e), int(d), res, f"{tempos[a]:.3f}", nao_eticos[a]])
with open("metricas.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["escopo", "nome", "VP", "FP", "FN", "precisao", "revocacao", "f1", "arquivos", "tempo_medio_s"])
    for esc, nome, vp, fp, fn, p, r, f1, n, tm in tabela:
        w.writerow([esc, nome, vp, fp, fn, f"{p:.4f}", f"{r:.4f}", f"{f1:.4f}", n, f"{tm:.3f}"])
print("\nGerados: resultados.txt, resultados_por_arquivo.csv, metricas.csv")
