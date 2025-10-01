
# Cold Chain IoT — Local Template

Simulación 100% local del flujo IoT para transporte de perecederos: **publisher → bus de archivos → consumer → ledger → dashboard (Streamlit)**.

## Requisitos
- Python 3.10+
- pip / venv

## Instalación rápida
```bash
python -m venv venv
# Windows: venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # opcional
```

## Demo rápida (datos reales simulados)
```bash
python demo.py
streamlit run streamlit_app.py
```

## Uso manual
En tres terminales o secuencial:
```bash
# 1) Generar lecturas
python publisher.py --count 50  # o --interval 2 --count 0 para infinito

# 2) Consumir y persistir
python consumer.py --once       # o --follow

# 3) Ledger
python ledger.py build
python ledger.py verify

# 4) Dashboard
streamlit run streamlit_app.py
```

## Tests básicos (sin pytest)
```bash
python tests/run_basic_checks.py
```

## Arquitectura (local)
```
publisher  ->  data/bus/<topic>.jsonl  ->  consumer  ->  data/log.jsonl
                                                  \->  data/alerts.jsonl
log.jsonl  ->  ledger.py build  ->  data/ledger.jsonl  ->  verify en dashboard
```

## Parámetros clave
- Umbral de temperatura por defecto: **8°C**
- Consecutivas para alerta (k): **5** (con `publisher` cada 2s ≈ 10s simulados)

## Limitaciones
- El ledger es una **prueba de integridad local**; no provee consenso distribuido.
- No hay autenticación ni firmas criptográficas reales.

## Entregables sugeridos para alumnos
- Repo con código y README.
- Captura del dashboard.
- Evidencia de `ledger verify` OK y FAIL (tras alterar una línea y rehacer ledger).
- Reflexión breve (3–5 líneas).
