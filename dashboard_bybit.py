import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timezone
import matplotlib.pyplot as plt

# --- CONFIG ---
st.set_page_config(page_title="Bybit Futures Dashboard", layout="wide")

st.title("📊 Performances Journalières - Bybit Futures")

# --- Fonction pour récupérer les données Bybit ---
def get_bybit_data(symbol: str):
    """
    Récupère les données kline (1h) depuis 00:00 UTC pour une paire Bybit Futures.
    """
    url = "https://api.bybit.com/v5/market/kline"
    now = datetime.now(timezone.utc)
    start_of_day = datetime(now.year, now.month, now.day, 0, 0, 0, tzinfo=timezone.utc)
    start_ts = int(start_of_day.timestamp() * 1000)

    params = {
        "category": "linear",
        "symbol": symbol,
        "interval": "60",
        "start": start_ts
    }

    r = requests.get(url, params=params)
    data = r.json()

    if data.get("retCode") != 0 or not data["result"]["list"]:
        return None

    df = pd.DataFrame(data["result"]["list"], columns=[
        "timestamp", "open", "high", "low", "close", "volume", "turnover"
    ])
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    df = df.astype({"open": float, "high": float, "low": float, "close": float})
    return df

# --- Liste de paires surveillées ---
TICKERS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT", "DOGEUSDT"]

# --- Sidebar : options utilisateur ---
st.sidebar.header("⚙️ Options")
selected_tickers = st.sidebar.multiselect(
    "Sélectionne les paires à afficher :", TICKERS, default=TICKERS
)

# --- Calcul des performances ---
perf_data = []
for sym in selected_tickers:
    df = get_bybit_data(sym)
    if df is None or df.empty:
        continue
    open_price = df.iloc[0]["open"]
    last_price = df.iloc[-1]["close"]
    perf = (last_price / open_price - 1) * 100
    perf_data.append({"Symbol": sym, "Perf (%)": perf})

# --- Affichage des résultats ---
if perf_data:
    df_perf = pd.DataFrame(perf_data).sort_values("Perf (%)", ascending=False).reset_index(drop=True)
    st.subheader("📈 Performance journalière depuis 00:00 UTC")
    st.dataframe(df_perf, use_container_width=True)

    # --- Graphique ---
    fig, ax = plt.subplots(figsize=(8, 4))
    colors = ["#16a34a" if x > 0 else "#dc2626" for x in df_perf["Perf (%)"]]
    ax.bar(df_perf["Symbol"], df_perf["Perf (%)"], color=colors)
    ax.axhline(0, color="black", linewidth=0.8)
    ax.set_title("Performance (%) depuis 00:00 UTC")
    ax.set_ylabel("Variation (%)")
    st.pyplot(fig)
else:
    st.warning("Aucune donnée disponible pour les paires sélectionnées.")

