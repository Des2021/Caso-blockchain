
import os, argparse, pathlib, json, time
from dotenv import load_dotenv
from jsonschema import validate, ValidationError
from bus.local_bus import tail

BASE = pathlib.Path(__file__).parent
STATE_DIR = BASE / ".state"
STATE_DIR.mkdir(exist_ok=True)

def save_offset(path, offset):
    with open(path, "w", encoding="utf-8") as f:
        f.write(str(offset))

def load_offset(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return int(f.read().strip())
    except:
        return 0

def main():
    parser = argparse.ArgumentParser(description="Local Cold Chain consumer")
    parser.add_argument("--k", type=int, default=5, help="Lecturas consecutivas sobre umbral para alerta")
    parser.add_argument("--threshold", type=float, default=8.0, help="Umbral de temperatura")
    parser.add_argument("--follow", action="store_true", help="Modo seguimiento continuo")
    parser.add_argument("--once", action="store_true", help="Procesa lo disponible y sale")
    args = parser.parse_args()

    load_dotenv()
    truck_id = os.getenv("TRUCK_ID", "truck-001")
    shipment_id = os.getenv("SHIPMENT_ID", "shp-001")
    topic = f"coldchain/{truck_id}/{shipment_id}"

    schema = json.load(open(BASE / "schemas" / "message.json", "r", encoding="utf-8"))
    log_path = BASE / "data" / "log.jsonl"
    alerts_path = BASE / "data" / "alerts.jsonl"
    offset_path = STATE_DIR / "consumer.offset"
    last_values = []
    over_count = 0
    alert_active = False

    offset = load_offset(offset_path)
    print(f"[INFO] Leyendo tópico '{topic}' desde offset {offset}")
    gen = tail(topic, from_byte=offset, poll_interval=0.5)
    start = time.time()
    while True:
        try:
            new_off, msg = next(gen)
        except StopIteration:
            break
        except Exception as e:
            # No new message yet
            if args.once:
                break
            if not args.follow:
                break
            time.sleep(0.2)
            continue

        try:
            validate(instance=msg, schema=schema)
        except ValidationError as e:
            print(f"[WARN] Mensaje inválido ignorado: {e.message}")
            save_offset(offset_path, new_off)
            continue

        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(msg, ensure_ascii=False) + "\n")

        # alert logic
        temp = msg.get("temperature_c", 0.0)
        last_values.append(temp)
        last_values = last_values[-5:]
        if temp > args.threshold:
            over_count += 1
        else:
            over_count = 0
            alert_active = False

        if over_count >= args.k and not alert_active:
            alert_active = True
            evt = {
                "ts": msg["ts"],
                "truck_id": msg["truck_id"],
                "shipment_id": msg["shipment_id"],
                "alert_state": "CRITICAL",
                "reason": f"Temperature > {args.threshold}C for {args.k} readings"
            }
            with open(alerts_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(evt, ensure_ascii=False) + "\n")
            print(f"[ALERT] {evt}")

        print(f"[CONSUME] T={temp}°C | últimos: {last_values} | over={over_count}/{args.k} | alert={alert_active}")
        save_offset(offset_path, new_off)

        if args.once and (time.time() - start) > 0.1:  # processed at least once
            break
        if not args.follow and args.once:
            continue
        if not args.follow and not args.once:
            break

if __name__ == "__main__":
    main()
