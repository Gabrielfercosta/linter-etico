# Kit do MVP (versão com variantes)

Mudanças em relação ao kit anterior (as REGRAS não mudaram; continuam as da tag `v0.1-regras-congeladas`):
- `amostras/variantes/`: 23 arquivos novos com casos-limite (descrições em `descricao_variantes.csv`).
- `gabarito.csv`: agora com 4 sintéticos + 12 defeitos das variantes (coluna `descricao`).
- `gabarito_real.csv`: vazio de propósito. Se você confirmar, lendo os contratos, que não há defeito ético, deixe assim.
- `avaliar.py --repeticoes N`: métricas por conjunto e por classe, tempo médio, e os arquivos `resultados.txt`, `resultados_por_arquivo.csv`, `metricas.csv`.
- `inspecionar.py`: lista pontos dos contratos reais para você ler.
- `grafico.py`: gera 3 figuras (precisa de matplotlib).

## Como rodar (dentro da pasta, no Prompt)
    npm install
    python avaliar.py --repeticoes 3
    pip install matplotlib pyyaml
    python grafico.py
    python inspecionar.py amostras/real/slack_openapi.yaml amostras/real/spotify_openapi.yaml amostras/real/stripe_openapi.yaml

## Versionamento (sem mexer nas regras)
    git add .
    git commit -m "Adiciona variantes, gabarito e scripts de avaliacao"
    git tag v0.1-avaliacao
    git push origin master --tags

## Importante
- O gabarito é seu: leia cada variante e confira `classe`/`descricao`. Se discordar, mude pela leitura do arquivo, nunca pelo resultado do línter.
