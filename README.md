# Barrido SMA200 (USA + Europa)

Cada día laborable a las 22:30 UTC GitHub Actions descarga 2 años de velas diarias
de ~1.000 valores (S&P 500, Nasdaq 100, DAX, CAC 40, IBEX 35, FTSE 100, AEX, FTSE MIB, SMI)
y escribe `candidatos.csv` con los que:

- cierran entre +0,1% y +2% sobre su SMA200,
- vienen cayendo (cierre < cierre de hace 5 y de hace 10 sesiones),
- no han tocado la SMA200 en las últimas 20 sesiones (mínimo diario > SMA200).

## Puesta en marcha (una vez)

1. Crea un repositorio **privado** en GitHub llamado `sma200` y sube estos archivos
   (manteniendo la carpeta `.github/workflows/`).
2. Settings → Actions → General → Workflow permissions → **Read and write permissions** → Save.
3. Pestaña Actions → "Barrido SMA200" → **Run workflow** para la primera ejecución. Tarda 5-15 min.
4. Cuando termine, abre `candidatos.csv` en el repo → botón **Raw** → copia la URL. Ese enlace es el que lee la Alerta C.

## Ajustes

Parámetros al principio de `barrido_sma200.py`: banda de distancia, sesiones de caída, filtro "sin tocar".
Añadir o quitar índices: diccionario `WIKI`.

## Si un día no hay CSV nuevo

Actions → última ejecución → log. Causas habituales: Yahoo cambió algo (actualizar `yfinance` en
`requirements.txt` y relanzar) o Wikipedia cambió una tabla (el script lo avisa y sigue con el resto).
