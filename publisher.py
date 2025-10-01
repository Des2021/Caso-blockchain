
import os, time, json, argparse, math, random, hashlib
from datetime import datetime, timezone
from dotenv import load_dotenv
from jsonschema import validate, ValidationError
import pathlib
from bus.local_bus import publish

BASE = pathlib.Path(__file__).parent
SCHEMA_PATH = BASE / "schemas" / "message.json"

def load_schema():
    import json
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def sign_msg(m: dict) -> str:
    s = f"{m['device_id']}{m['ts']}{m['temperature_c']:.2f}{m['humidity']:.2f}{m['gps']['lat']:.5f}{m['gps']['lon']:.5f}"
    return hashlib.sha256(s.encode()).hexdigest()

def main():
    parser = argparse.ArgumentParser(description="Local Cold Chain publisher")
    parser.add_argument("--count", type=int, default=0, help="Número de mensajes y terminar (0 = infinito)")
    parser.add_argument("--interval", type=float, default=2.0, help="Segundos entre mensajes")
    args = parser.parse_args()

    load_dotenv()
    truck_id = os.getenv("TRUCK_ID", "truck-001")
    shipment_id = os.getenv("SHIPMENT_ID", "shp-001")
    device_id = os.getenv("DEVICE_ID", "dev-001")
    topic = f"coldchain/{truck_id}/{shipment_id}"

    schema = load_schema()

    # Estado inicial simulado
    temp = 5.0 + random.uniform(-1, 1)
    hum = 75.0 + random.uniform(-5, 5)
    lat, lon = 40.4168, -3.7038  # Madrid centro
    step = 0

    sent = 0
    while True:
        # pequeñas variaciones correlacionadas
        drift = math.sin(step/15.0)*0.2 + random.uniform(-0.15, 0.15)
        temp = max(0.0, min(12.0, temp + drift))
        hum = max(60.0, min(95.0, hum + drift*2 + random.uniform(-0.2,0.2)))
        lat += random.uniform(-0.0005, 0.0005)
        lon += random.uniform(-0.0005, 0.0005)

        msg = {
            "device_id": device_id,
            "ts": datetime.now(timezone.utc).isoformat(),
            "temperature_c": round(temp, 2),
            "humidity": round(hum, 2),
            "gps": {"lat": round(lat, 6), "lon": round(lon, 6)},
            "truck_id": truck_id,
            "shipment_id": shipment_id,
        }
        msg["signature"] = sign_msg(msg)
        try:
            validate(instance=msg, schema=schema)
            publish(topic, msg)
            print(f"[PUBLISH] {topic} -> {msg}")
        except ValidationError as e:
            print(f"[WARN] Mensaje inválido: {e.message}")

        sent += 1
        step += 1
        if args.count and sent >= args.count:
            break
        time.sleep(args.interval)

if __name__ == "__main__":
    main()
