
import subprocess, sys

def run(cmd):
    print(">>", " ".join(cmd))
    subprocess.run(cmd, check=True)

if __name__ == "__main__":
    run([sys.executable, "publisher.py", "--count", "50"])
    run([sys.executable, "consumer.py", "--once"])
    run([sys.executable, "ledger.py", "build"])
    print("\nDemo lista. Lanza ahora: streamlit run streamlit_app.py")
