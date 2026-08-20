"""
Barrido diario SMA200 — USA + Europa — GitHub Actions + yfinance
Regla: precio entre 0,1% y 2% por encima de la SMA200, viene cayendo
(cierre < cierre hace 5 y hace 10 sesiones) y el mínimo de las últimas
20 sesiones no ha tocado la SMA200.
Salida: candidatos.csv (siempre) + historico/candidatos_YYYY-MM-DD.csv
"""
import datetime as dt, os, sys, time
import pandas as pd
import yfinance as yf

DIST_MIN, DIST_MAX = 0.001, 0.02
DIAS_SIN_TOCAR = 20          # 0 = desactivado
LOOKBACKS = (5, 10)          # "viene cayendo": cierre < cierre de hace N sesiones, para todos los N
HIST = "2y"

WIKI = {
    "sp500":   ("https://en.wikipedia.org/wiki/List_of_S%26P_500_companies", "Symbol", ""),
    "ndx100":  ("https://en.wikipedia.org/wiki/Nasdaq-100", "Ticker", ""),
    "dax":     ("https://en.wikipedia.org/wiki/DAX", "Ticker", ".DE"),
    "cac40":   ("https://en.wikipedia.org/wiki/CAC_40", "Ticker", ".PA"),
    "ibex35":  ("https://en.wikipedia.org/wiki/IBEX_35", "Ticker", ".MC"),
    "ftse100": ("https://en.wikipedia.org/wiki/FTSE_100_Index", "Ticker", ".L"),
    "aex":     ("https://en.wikipedia.org/wiki/AEX_index", "Ticker", ".AS"),
    "ftsemib": ("https://en.wikipedia.org/wiki/FTSE_MIB", "Ticker", ".MI"),
    "smi":     ("https://en.wikipedia.org/wiki/Swiss_Market_Index", "Ticker", ".SW"),
}
SUFIJOS = tuple(v[2] for v in WIKI.values() if v[2])
HDR = {"User-Agent": "Mozilla/5.0 (sma200-screener)"}

def universo():
    ticks = {}
    for nombre, (url, col, suf) in WIKI.items():
        try:
            import requests, io
            html = requests.get(url, headers=HDR, timeout=30).text
            t = next(t for t in pd.read_html(io.StringIO(html)) if col in t.columns)
        except Exception as e:
            print(f"[{nombre}] FALLO Wikipedia: {e}", file=sys.stderr); continue
        n = 0
        for s in t[col].astype(str):
            s = s.strip().split()[0]
            if not s or s.lower() == "nan": continue
            if suf:
                base = s
                for k in SUFIJOS:
                    if base.endswith(k): base = base[: -len(k)]
                s = base + suf
            else:
                s = s.replace(".", "-")          # BRK.B -> BRK-B (Yahoo)
            ticks[s] = nombre; n += 1
        print(f"[{nombre}] {n} tickers")
    return ticks

def descargar(tickers):
    data, fallos = {}, 0
    lote = 150
    for i in range(0, len(tickers), lote):
        sub = tickers[i:i+lote]
        for intento in range(3):
            try:
                raw = yf.download(sub, period=HIST, auto_adjust=True, group_by="ticker",
                                  threads=True, progress=False)
                break
            except Exception as e:
                print(f"lote {i}: reintento {intento+1}: {e}", file=sys.stderr); time.sleep(10)
        else:
            fallos += len(sub); continue
        for t in sub:
            try:
                df = raw[t].dropna(how="all")
                if len(df) >= 205: data[t] = df
                else: fallos += 1
            except KeyError:
                fallos += 1
        time.sleep(2)
    return data, fallos

def evaluar(t, mercado, df):
    c, lo = df["Close"], df["Low"]
    sma = c.rolling(200).mean()
    precio, s = float(c.iloc[-1]), float(sma.iloc[-1])
    if pd.isna(s) or s <= 0 or pd.isna(precio): return None
    dist = precio / s - 1
    cayendo = all(precio < float(c.iloc[-1 - n]) for n in LOOKBACKS)
    sin_tocar = True if not DIAS_SIN_TOCAR else bool(
        (lo.iloc[-DIAS_SIN_TOCAR:] > sma.iloc[-DIAS_SIN_TOCAR:]).all())
    if cayendo and DIST_MIN <= dist <= DIST_MAX and sin_tocar:
        return {"ticker": t, "mercado": mercado, "cierre": round(precio, 2), "sma200": round(s, 2),
                "dist_%": round(dist * 100, 2),
                "ret5d_%": round((precio / float(c.iloc[-6]) - 1) * 100, 2),
                "ret10d_%": round((precio / float(c.iloc[-11]) - 1) * 100, 2),
                "pend_sma200_%": round((s / float(sma.iloc[-21]) - 1) * 100, 2),
                "fecha_vela": str(df.index[-1].date())}
    return None

def main():
    uni = universo()
    tickers = sorted(uni)
    print(f"Universo: {len(tickers)} tickers")
    data, fallos = descargar(tickers)
    print(f"Con datos: {len(data)} · sin datos: {fallos}")
    filas = [r for t, df in data.items() if (r := evaluar(t, uni[t], df))]
    cols = ["ticker","mercado","cierre","sma200","dist_%","ret5d_%","ret10d_%","pend_sma200_%","fecha_vela"]
    out = pd.DataFrame(filas, columns=cols).sort_values("dist_%") if filas else pd.DataFrame(columns=cols)
    hoy = dt.date.today().isoformat()
    out["fecha_barrido"] = hoy
    out["universo"] = len(tickers)
    out["sin_datos"] = fallos
    os.makedirs("historico", exist_ok=True)
    out.to_csv("candidatos.csv", index=False)
    out.to_csv(f"historico/candidatos_{hoy}.csv", index=False)
    print(out.to_string(index=False) if filas else "Sin candidatos hoy.")

if __name__ == "__main__":
    main()
