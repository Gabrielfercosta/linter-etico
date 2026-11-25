"""Compara os alertas do línter com o gabarito e calcula precisão, revocação, F1 e tempo."""
import csv, json, os, subprocess, time
from collections import defaultdict
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

def normaliza(p):
    return Path(p).as_posix()

# 1) gabarito: pares (arquivo, classe) que DEVEM ser detectados
esperado = set()
with open("gabarito.csv", encoding="utf-8") as f:
    for linha in csv.DictReader(f):
        esperado.add((normaliza(linha["arquivo"]), linha["classe"]))

# 2) executa o línter em cada arquivo e mede o tempo
arquivos = sorted(normaliza(p) for ext in ("yaml", "yml", "json")
                  for p in Path("amostras").rglob(f"*.{ext}"))
detectado, tempos = set(), {}
for arq in arquivos:
    t0 = time.perf_counter()
    subprocess.run([NPX, "spectral", "lint", arq, "-r", ".spectral.yaml",
                    "-f", "json", "-o", SAIDA], capture_output=True, text=True, encoding="utf-8")
    tempos[arq] = time.perf_counter() - t0
    try:
        alertas = json.loads(Path(SAIDA).read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        print("Falha ao ler a saída do línter em", arq); continue
    for a in alertas:
        if a["code"] in CLASSE:
            detectado.add((arq, CLASSE[a["code"]]))

# 3) métricas
def metricas(esp, det):
    vp, fp, fn = len(esp & det), len(det - esp), len(esp - det)
    p = vp / (vp + fp) if vp + fp else 0.0
    r = vp / (vp + fn) if vp + fn else 0.0
    f1 = 2 * p * r / (p + r) if p + r else 0.0
    return vp, fp, fn, p, r, f1

print(f"Arquivos analisados: {len(arquivos)} | tempo médio por arquivo: {sum(tempos.values())/len(tempos):.2f} s")
vp, fp, fn, p, r, f1 = metricas(esperado, detectado)
print(f"GERAL  VP={vp} FP={fp} FN={fn}  precisão={p:.2f} revocação={r:.2f} F1={f1:.2f}")
for classe in sorted(set(CLASSE.values())):
    e = {x for x in esperado if x[1] == classe}
    d = {x for x in detectado if x[1] == classe}
    vp, fp, fn, p, r, f1 = metricas(e, d)
    print(f"{classe:26} VP={vp} FP={fp} FN={fn}  precisão={p:.2f} revocação={r:.2f} F1={f1:.2f}")
print("Falsos positivos:", sorted(detectado - esperado))
print("Falsos negativos:", sorted(esperado - detectado))
