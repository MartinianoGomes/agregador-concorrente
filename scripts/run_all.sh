#!/usr/bin/env bash
# Sobe os 4 postos e o agregador em processos separados.
# Encerra todos ao receber Ctrl+C (SIGINT).

set -euo pipefail

cd "$(dirname "$0")/.."

PIDS=()

cleanup() {
  echo
  echo ">>> Encerrando processos filhos..."
  for pid in "${PIDS[@]}"; do
    kill "$pid" 2>/dev/null || true
  done
  wait
}
trap cleanup INT TERM EXIT

echo ">>> Subindo 4 postos..."
python -m src.posto --nome A --porta 6001 --anp data/anp_posto_a.csv &
PIDS+=($!)
python -m src.posto --nome B --porta 6002 --anp data/anp_posto_b.csv &
PIDS+=($!)
python -m src.posto --nome C --porta 6003 --anp data/anp_posto_c.csv &
PIDS+=($!)
python -m src.posto --nome D --porta 6004 --anp data/anp_posto_d.csv &
PIDS+=($!)

sleep 1

echo ">>> Subindo agregador na porta 5000..."
python -m src.agregador --porta 5000 \
  --posto A:127.0.0.1:6001 \
  --posto B:127.0.0.1:6002 \
  --posto C:127.0.0.1:6003 \
  --posto D:127.0.0.1:6004 &
PIDS+=($!)

echo
echo ">>> Tudo no ar. Em outro terminal, rode:"
echo "    python -m src.cliente --host localhost --porta 5000"
echo
echo ">>> Ctrl+C para encerrar."
wait
