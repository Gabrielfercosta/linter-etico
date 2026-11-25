"""Lista candidatos para a classificação manual dos contratos reais.
Uso: python inspecionar.py amostras/real/slack_openapi.yaml amostras/real/stripe_openapi.yaml ...
Requer: pip install pyyaml
Este script NÃO decide nada: só mostra onde olhar. O gabarito é feito por leitura sua.
"""
import re, sys, yaml
try: Loader = yaml.CSafeLoader
except AttributeError: Loader = yaml.SafeLoader

SENS = re.compile(r"(cpf|rg|ssn|social_security|birth|nascimento|biometr|latitude|longitude|location|localizacao|address|endereco|phone|telefone|email|contact)", re.I)
FLAGS = re.compile(r"(consent|opt_?in|marketing|newsletter|tracking)", re.I)
ASSIN = re.compile(r"(assinatura|subscri|plano|plan|membership)", re.I)
MAXL = 25

def resolve(spec, node, depth=0):
    while isinstance(node, dict) and "$ref" in node and depth < 6:
        ref = node["$ref"]
        if not ref.startswith("#/"): break
        cur = spec
        for part in ref[2:].split("/"):
            cur = cur.get(part.replace("~1", "/").replace("~0", "~"), {}) if isinstance(cur, dict) else {}
        node, depth = cur, depth + 1
    return node

def required_fields(spec, schema, depth=0):
    schema = resolve(spec, schema)
    if not isinstance(schema, dict) or depth > 4: return set()
    out = set(schema.get("required") or [])
    for k in ("allOf", "oneOf", "anyOf"):
        for s in schema.get(k) or []: out |= required_fields(spec, s, depth + 1)
    return out

def walk(node, path=""):
    if isinstance(node, dict):
        for k, v in node.items():
            yield path + "/" + str(k), k, v
            yield from walk(v, path + "/" + str(k))
    elif isinstance(node, list):
        for i, v in enumerate(node): yield from walk(v, f"{path}[{i}]")

for arq in sys.argv[1:]:
    print("=" * 70); print(arq)
    spec = yaml.load(open(arq, encoding="utf-8"), Loader=Loader)
    n = 0
    print("\n[1] Campos obrigatórios que parecem dado pessoal (POST/PUT/PATCH):")
    for p, ops in (spec.get("paths") or {}).items():
        for m in ("post", "put", "patch"):
            op = (ops or {}).get(m)
            if not isinstance(op, dict): continue
            rb = resolve(spec, op.get("requestBody") or {})
            for ct, body in ((rb.get("content") or {}).items()):
                for f in sorted(required_fields(spec, (body or {}).get("schema") or {})):
                    if SENS.search(str(f)) and n < MAXL:
                        print(f"   {m.upper()} {p}  campo obrigatório: {f}"); n += 1
    print("\n[2] Rotas ligadas a assinatura/plano e métodos disponíveis:")
    n = 0
    for p, ops in (spec.get("paths") or {}).items():
        if ASSIN.search(p) and n < MAXL:
            print(f"   {p}: {', '.join(m.upper() for m in (ops or {}) if m in ('get','post','put','patch','delete'))}"); n += 1
    print("\n[3] Chaves de consentimento/marketing/rastreamento com valor padrão:")
    n = 0
    for p, k, v in walk(spec):
        if FLAGS.search(str(k)) and isinstance(v, dict) and "default" in v and n < MAXL:
            print(f"   {p}: default={v['default']}"); n += 1
    print()
