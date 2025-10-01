
import json, argparse, pathlib, hashlib
BASE = pathlib.Path(__file__).parent

def json_dumps_canon(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

def build_ledger(log_path=BASE/"data/log.jsonl", out_path=BASE/"data/ledger.jsonl"):
    prev = "0"*64
    index = 0
    with open(out_path, "w", encoding="utf-8") as out:
        with open(log_path, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                evt = json.loads(line)
                payload = json_dumps_canon(evt) + prev
                entry_hash = hashlib.sha256(payload.encode()).hexdigest()
                block = {
                    "index": index,
                    "ts": evt.get("ts"),
                    "message_id": evt.get("signature"),
                    "entry_hash": entry_hash,
                    "prev_hash": prev
                }
                out.write(json_dumps_canon(block) + "\n")
                prev = entry_hash
                index += 1
    return index

def verify_ledger(path=BASE/"data/ledger.jsonl", log_path=BASE/"data/log.jsonl"):
    prev = "0"*64
    idx = 0
    with open(path, "r", encoding="utf-8") as led, open(log_path, "r", encoding="utf-8") as log:
        for block_line, evt_line in zip(led, log):
            if not block_line.strip():
                continue
            block = json.loads(block_line)
            evt = json.loads(evt_line)
            calc = hashlib.sha256((json_dumps_canon(evt) + prev).encode()).hexdigest()
            if block["entry_hash"] != calc or block["prev_hash"] != prev:
                return ("FAIL", idx)
            prev = block["entry_hash"]
            idx += 1
    return ("OK", None)

def main():
    ap = argparse.ArgumentParser(description="Ledger builder/verifier")
    ap.add_argument("cmd", choices=["build","verify"])
    args = ap.parse_args()
    if args.cmd == "build":
        n = build_ledger()
        print(f"[LEDGER] Construidos {n} bloques")
    else:
        status, pos = verify_ledger()
        print(f"[VERIFY] {status}" + (f" en bloque {pos}" if pos is not None else ""))

if __name__ == "__main__":
    main()
