
import streamlit as st
import json, pathlib, math
import pandas as pd
from ledger import verify_ledger

BASE = pathlib.Path(__file__).parent
LOG_PATH = BASE / "data" / "log.jsonl"
ALERTS_PATH = BASE / "data" / "alerts.jsonl"
LEDGER_PATH = BASE / "data" / "ledger.jsonl"

st.set_page_config(page_title="Cold Chain IoT — Local Dashboard", layout="wide")
st.title("Cold Chain IoT — Local Dashboard")

with st.sidebar:
    st.header("Parámetros")
    threshold = st.number_input("Umbral temperatura (°C)", value=8.0, step=0.5)
    k = st.number_input("Consecutivas para alerta", value=5, step=1)
    st.caption("Ajusta los parámetros del sistema simulado (para referencia visual).")
    refresh = st.button("Refrescar")
    verify = st.button("Verificar ledger")

def load_jsonl(path: pathlib.Path):
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]

logs = load_jsonl(LOG_PATH)
alerts = load_jsonl(ALERTS_PATH)

if len(logs) == 0:
    st.info("No hay datos en log.jsonl. Ejecuta el publisher y el consumer, o usa los datos de ejemplo.")
else:
    df = pd.DataFrame(logs)
    df["ts"] = pd.to_datetime(df["ts"])
    df = df.sort_values("ts")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Lecturas", f"{len(df)}")
    col2.metric("Temp. actual (°C)", f"{df['temperature_c'].iloc[-1]:.2f}")
    col3.metric("Humedad actual (%)", f"{df['humidity'].iloc[-1]:.1f}")
    over = (df["temperature_c"].rolling(int(k)).apply(lambda x: (x>threshold).all(), raw=True).fillna(0).astype(bool))
    state = "CRITICAL" if over.any() else "OK"
    col4.metric("Estado alerta", state)

    st.subheader("Series temporales")
    st.line_chart(df.set_index("ts")[["temperature_c","humidity"]])

    st.subheader("Ubicación (lat/lon)")
    st.dataframe(df[["ts","gps"]].tail(10))

st.subheader("Eventos de alerta")
if len(alerts) == 0:
    st.write("—")
else:
    st.dataframe(pd.DataFrame(alerts).sort_values("ts", ascending=False).head(20))

st.subheader("Integridad de datos")
if verify:
    status, pos = verify_ledger(str(LEDGER_PATH), str(LOG_PATH))
    if status == "OK":
        st.success("Ledger OK")
    else:
        st.error(f"Ledger FAIL en bloque {pos}")
st.caption("Usa `ledger.py build` y luego ‘Verificar ledger’.")
