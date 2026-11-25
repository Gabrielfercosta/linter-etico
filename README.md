# MVP: línter ético (Spectral + CI/CD)

## Rodar no seu computador
```
npm install
npx spectral --version        # anote a versão para o Capítulo 3.2
npx spectral lint "amostras/**/*.yaml" -r .spectral.yaml
python avaliar.py             # calcula precisão, revocação, F1 e tempo
```
No Windows, use o Prompt de Comando ou o PowerShell. Precisa de Node.js e Python instalados.

## Onde está cada coisa
- `.spectral.yaml`: as regras do línter (uma por classe de risco).
- `regras/cancelamento.js`: função própria da regra de obstrução de cancelamento.
- `amostras/sintetica/`: arquivos de teste, em pares (com defeito e `_ok`).
- `amostras/real/`: coloque aqui os arquivos reais que você escolher.
- `gabarito.csv`: lista do que o línter DEVE achar (arquivo, classe).
- `avaliar.py`: roda o línter em cada arquivo e compara com o gabarito.
- `.github/workflows/linter-etico.yml`: o pipeline de CI/CD.

## Classes e nomes usados no gabarito
`coleta_excessiva`, `sem_recusa`, `notificacao_manipulativa`, `obstrucao_cancelamento`
