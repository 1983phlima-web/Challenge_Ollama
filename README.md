# Challenge Automation — pacote **Ollama (local)**

Triagem de reclamações com IA **100% local**: nenhum texto sai da máquina.

## Pré-requisitos
- Windows 10/11 ou Server, Python 3.11+
- [Ollama](https://ollama.com) instalado e em execução; modelo baixado: `ollama pull llama3.1:8b`
  (troque `llm_model` em `config\settings.yaml` se preferir outro; modelos maiores classificam melhor e são mais lentos)

## Instalação
```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
```

## Configuração
1. **Substitua** `config\motor_regras.txt` e `config\politica.txt` pelos seus TXT (formato na SPEC §5.3–5.4; se o layout real diferir, adapte somente `rules/engine.py` e `rules/policy.py`).
2. Revise `config\settings.yaml` (`base_dir`, `llm_model`, `llm_workers`, `llm_timeout_s`).
3. Teste a conexão: `curl http://localhost:11434/api/tags`.

## Execução
```powershell
challenge preprocess   # Processo 1
challenge perform      # Processo 2 (com ciclo _loop)
challenge run-all      # ambos
```

## Pastas e arquivos gerados
```
C:\Challenge\
  dataset_challenge.csv          (entrada)
  Fila\       processadas_<ts>.csv · rejeitadas_<ts>.csv
  Output\     processadas_<ts>_read.csv  →  _ok.csv (respondidos) | _loop.csv (pendentes) | _nok.csv (humano)
  Logs\       *.log (JSON) · audit_*.jsonl · stats_*.json
  Relatorios\ relatorio_*.md / .html   (Resumo, Tendências, Top Riscos)
```

## Ciclo `_loop` (itens sem resposta)
| Situação | Resultado |
|---|---|
| Todos respondidos | `<lote>_ok.csv` completo, na ordem da fila; nada pendente |
| Alguns sem resposta | respondidos → `_ok.csv`; **só os pendentes** → `_loop.csv` (sem coluna `Resposta`) |
| Mesma execução | pendentes ganham `loop_rounds_per_run − 1` rodada(s) extra(s) |
| Ainda pendentes | `_loop.csv` espera a **próxima execução** (agende a tarefa periodicamente) |
| `max_loop_cycles` atingido | pendentes → `_nok.csv` para análise humana |
| Arquivo ilegível / colunas ausentes | `_nok.csv` |

Códigos de saída: `0` tudo concluído · `1` há `_loop`/`_nok` · `2` entrada/config inválida · `3` erro inesperado.

## Operação
```powershell
challenge run-all --config C:\Challenge\config\settings.yaml
schtasks /Create /SC HOURLY /TN "Challenge" /TR "C:\Challenge\.venv\Scripts\challenge.exe run-all --config C:\Challenge\config\settings.yaml"
```
Lock órfão (`*.lock` em `Output\`) após queda: apague só depois de confirmar que nenhum processo está ativo.

## Testes e validação com 500 casos
```powershell
pytest -q                 # suíte completa (inclui o dataset de 500 casos com gabarito)
ruff check src tests ; mypy src
python tests\dataset_factory.py --valid 500 --invalid 40 --out C:\Challenge\dataset_challenge.csv --expected gabarito.csv
```
`tests\data\dataset_500.csv` traz **500 reclamações bancárias distintas** (clientes que ameaçam, insatisfeitos e satisfeitos, em 9 produtos) **mais 40 linhas inválidas** (540 linhas). `dataset_500_expected.csv` é o gabarito: fila esperada, motivo da rejeição e cenário por linha. O gerador é `tests\corpus.py`. Copie o CSV para `C:\Challenge\dataset_challenge.csv` para uma validação ponta a ponta com a IA real.

## Validação da implantação
```powershell
challenge check                 # ambiente, TXT, pastas, IA (tensão, resposta, concorrência)
challenge check --smoke --rows 40   # Processos 1 e 2 reais em amostra temporária
challenge check --golden        # 500 textos distintos vs. gabarito (use --golden-rows 150 para amostra)
```
Saída `0` = sem FAIL; `1` = há FAIL. Relatório JSON em `Logs\preflight_<ts>.json`. Roteiro completo, com critérios de aceite e Go/No-Go, em `docs\DEPLOY.md`.

## Documentação
`docs\DEPLOY.md` (requisitos do ambiente e gates de aceite) · `docs\SPEC.md` (requisitos, contratos, regras, estados) · `docs\C4.md` (C4 níveis 1–4, dinâmico, estados, implantação) · `docs\ADR.md`.

## Dicas para Ollama
- `llm_workers` alto em máquina sem GPU só enfileira: comece com 2.
- Timeouts frequentes → aumente `llm_timeout_s`; itens que estourarem caem no ciclo `_loop` e são retentados.
