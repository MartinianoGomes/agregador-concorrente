@echo off
rem Sobe os 4 postos e o agregador em janelas separadas (Windows).

cd /d "%~dp0\.."

echo === Subindo 4 postos ===
start "Posto A" cmd /k python -m src.posto --nome A --porta 6001 --anp data\anp_posto_a.csv --rastreio
start "Posto B" cmd /k python -m src.posto --nome B --porta 6002 --anp data\anp_posto_b.csv --rastreio
start "Posto C" cmd /k python -m src.posto --nome C --porta 6003 --anp data\anp_posto_c.csv --rastreio
start "Posto D" cmd /k python -m src.posto --nome D --porta 6004 --anp data\anp_posto_d.csv --rastreio

timeout /t 2 /nobreak >nul

echo === Subindo agregador na porta 5000 ===
start "Agregador" cmd /k python -m src.agregador --porta 5000 --rastreio ^
  --posto A:127.0.0.1:6001 ^
  --posto B:127.0.0.1:6002 ^
  --posto C:127.0.0.1:6003 ^
  --posto D:127.0.0.1:6004

echo.
echo === Tudo no ar. Em outro cmd, rode:
echo     python -m src.cliente --host localhost --porta 5000 --rastreio
echo.
echo === Feche as janelas abertas para encerrar.
