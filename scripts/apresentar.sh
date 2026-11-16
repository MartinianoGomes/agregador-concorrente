#!/usr/bin/env bash
# Demonstração local: 4 postos TCP + agregador. Ctrl+C encerra todos.
set -euo pipefail
cd "$(dirname "$0")/.."
PORTA="${AGREGADOR_PORTA:-15000}"
PIDS=()
cleanup() {
  trap - EXIT INT TERM
  printf "\nEncerrando servidores da demonstração...\n"
  for pid in "${PIDS[@]}"; do kill "$pid" 2>/dev/null || true; done
  for pid in "${PIDS[@]}"; do wait "$pid" 2>/dev/null || true; done
}
trap cleanup EXIT INT TERM
for porta in "$PORTA" 6001 6002 6003 6004; do
  if lsof -nP -iTCP:"$porta" -sTCP:LISTEN 2>/dev/null | grep -q LISTEN; then
    echo "ERRO: porta $porta ocupada; feche a instância anterior." >&2
    exit 1
  fi
done
for nome_porta in "A 6001 a" "B 6002 b" "C 6003 c" "D 6004 d"; do
  read -r nome porta letra <<< "$nome_porta"
  python -m src.posto --nome "$nome" --porta "$porta" --anp "data/anp_posto_${letra}.csv" &
  PIDS+=("$!")
done
sleep 1
python -m src.agregador --host 127.0.0.1 --porta "$PORTA" \
  --posto A:127.0.0.1:6001 \
  --posto B:127.0.0.1:6002 \
  --posto C:127.0.0.1:6003 \
  --posto D:127.0.0.1:6004 &
PIDS+=("$!")
sleep 1
echo "Servidores no ar. Abra outro terminal e execute:"
echo "  AGREGADOR_PORTA=$PORTA python interface_grafica.py"
echo "Ctrl+C encerra os servidores."
wait
