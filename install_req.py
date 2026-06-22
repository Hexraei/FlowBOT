import os
import sys
import subprocess
import shutil
import urllib.request
import json

def print_section(title):
    print("\n" + "=" * 60)
    print(f" {title}")
    print("=" * 60)

def check_python_packages():
    print_section("Checking Python Dependencies")
    
    # Map package names in requirements.txt to import names
    package_to_import = {
        "fastapi": "fastapi",
        "uvicorn": "uvicorn",
        "sqlalchemy": "sqlalchemy",
        "chromadb": "chromadb",
        "sentence-transformers": "sentence_transformers",
        "requests": "requests",
        "python-dotenv": "dotenv",
        "pydantic": "pydantic",
        "pydantic-settings": "pydantic_settings",
        "httpx": "httpx",
        "slowapi": "slowapi",
        "redis": "redis",
        "sse-starlette": "sse_starlette"
    }
    
    missing_packages = []
    
    # Read requirements.txt
    req_file = os.path.join(os.path.dirname(__file__), "requirements.txt")
    if not os.path.exists(req_file):
        print(f"[Error] requirements.txt not found at {req_file}")
        return False
        
    with open(req_file, "r") as f:
        lines = f.readlines()
        
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        # Split on == or >= or <= or @
        pkg = line.split("==")[0].split(">=")[0].split("<=")[0].strip()
        import_name = package_to_import.get(pkg.lower(), pkg.replace("-", "_"))
        
        try:
            __import__(import_name)
            print(f"[OK] Python package '{pkg}' is already installed.")
        except ImportError:
            print(f"[MISSING] Python package '{pkg}' needs to be installed.")
            missing_packages.append(line)
            
    if missing_packages:
        print(f"\nInstalling missing packages: {', '.join(missing_packages)}")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "-r", req_file], check=True)
            print("[Success] All Python dependencies successfully installed.")
        except subprocess.CalledProcessError as e:
            print(f"[Error] Failed to install Python dependencies: {e}")
            return False
    else:
        print("[Success] All Python dependencies are already satisfied.")
    return True

def check_node_and_npm():
    print_section("Checking Node.js & npm")
    node_installed = False
    npm_installed = False

    # Use platform-specific binary names; avoid shell=True for security
    node_bin = "node.exe" if sys.platform == "win32" else "node"
    npm_bin = "npm.cmd" if sys.platform == "win32" else "npm"

    try:
        node_ver = subprocess.run([node_bin, "--version"], capture_output=True, text=True, check=True)
        print(f"[OK] Node.js is installed. Version: {node_ver.stdout.strip()}")
        node_installed = True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("[MISSING] Node.js is not installed or not in system PATH.")
        print("Please download and install Node.js from https://nodejs.org/")

    try:
        npm_ver = subprocess.run([npm_bin, "--version"], capture_output=True, text=True, check=True)
        print(f"[OK] npm is installed. Version: {npm_ver.stdout.strip()}")
        npm_installed = True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("[MISSING] npm is not installed or not in system PATH.")

    return node_installed and npm_installed

def check_frontend_deps():
    print_section("Checking Frontend dependencies")
    frontend_dir = os.path.join(os.path.dirname(__file__), "frontend")
    if not os.path.exists(frontend_dir):
        print("[Error] Frontend directory not found.")
        return False
        
    node_modules_dir = os.path.join(frontend_dir, "node_modules")
    if os.path.exists(node_modules_dir):
        print("[OK] Frontend dependencies already installed (node_modules exists).")
        return True
        
    print("[MISSING] frontend/node_modules not found. Running npm install...")
    try:
        npm_bin = "npm.cmd" if sys.platform == "win32" else "npm"
        subprocess.run([npm_bin, "install"], cwd=frontend_dir, check=True)
        print("[Success] Frontend dependencies successfully installed.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[Error] Failed to run npm install: {e}")
        return False

def check_ollama_and_qwen():
    print_section("Checking Ollama & Qwen model")
    
    # 1. Check if Ollama is running
    ollama_running = False
    try:
        # Check local running port
        with urllib.request.urlopen("http://localhost:11434/", timeout=2) as response:
            if response.status == 200:
                print("[OK] Ollama service is running on http://localhost:11434")
                ollama_running = True
    except Exception:
        print("[WARN] Ollama service is not running or not responding at http://localhost:11434")
        
    if not ollama_running:
        # Check if ollama is installed in PATH
        ollama_bin = shutil.who("ollama")
        if ollama_bin:
            print(f"[OK] Ollama CLI is installed at: {ollama_bin}")
            print("Please start Ollama application or service, then re-run this setup script.")
        else:
            print("[MISSING] Ollama is not installed.")
            print("Please download and install Ollama from: https://ollama.com/")
        return False
        
    # 2. Check if model is pulled
    model_name = "qwen2.5:1.5b"
    try:
        with urllib.request.urlopen("http://localhost:11434/api/tags", timeout=5) as response:
            data = json.loads(response.read().decode("utf-8"))
            models = [m["name"] for m in data.get("models", [])]
            
            # Ollama sometimes returns version qualifiers or exact match, check fuzzy/full
            has_model = any(model_name in m or m.startswith(model_name) for m in models)
            
            if has_model:
                print(f"[OK] Ollama model '{model_name}' is already downloaded.")
                return True
            else:
                print(f"[MISSING] Ollama model '{model_name}' is not downloaded yet.")
    except Exception as e:
        print(f"[Error] Failed to query Ollama models list: {e}")
        
    # 3. Pull the model
    print(f"Pulling Ollama model '{model_name}'... (This may take a few minutes)")
    try:
        subprocess.run(["ollama", "pull", model_name], check=True)
        print(f"[Success] Ollama model '{model_name}' successfully downloaded!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[Error] Failed to pull model '{model_name}': {e}")
        print(f"Please pull it manually by running: ollama pull {model_name}")
        return False


def check_redis():
    print_section("Checking Redis Server")
    try:
        import redis
        r = redis.Redis(host="localhost", port=6379, socket_connect_timeout=2)
        r.ping()
        print("[OK] Redis is running on localhost:6379.")
        return True
    except Exception:
        print("[WARN] Redis is not running or not installed.")
        print("Rate limiting will fall back to in-memory mode (resets on server restart).")
        print("To install Redis on Windows: https://redis.io/docs/getting-started/installation/install-redis-on-windows/")
        print("To install Redis on macOS:   brew install redis && brew services start redis")
        print("To install Redis on Linux:   sudo apt install redis-server && sudo systemctl start redis")
        return False  # Non-fatal: app still works, just with degraded rate limit persistence

def main():
    print("=" * 60)
    print(" FlowZint Support BOT - Installation & Pre-requisites Check")
    print("=" * 60)

    python_ok = check_python_packages()
    node_ok = check_node_and_npm()

    if node_ok:
        frontend_ok = check_frontend_deps()
    else:
        frontend_ok = False
        print("[WARN] Skipping npm package installations until Node.js is installed.")

    ollama_ok = check_ollama_and_qwen()
    redis_ok = check_redis()

    print_section("Setup Summary")
    print(f"Python Dependencies : {'[OK]' if python_ok else '[FAILED]'}")
    print(f"Node.js & npm       : {'[OK]' if node_ok else '[FAILED]'}")
    print(f"Frontend packages   : {'[OK]' if frontend_ok else '[FAILED]'}")
    print(f"Ollama & Qwen Model : {'[OK]' if ollama_ok else '[FAILED]'}")
    print(f"Redis Server        : {'[OK]' if redis_ok else '[WARN - rate limiting will use in-memory fallback]'}")

    if python_ok and node_ok and frontend_ok and ollama_ok:
        print("\n[SUCCESS] Core setup complete! Run 'python main.py' to start the servers.")
        if not redis_ok:
            print("[NOTE] Redis is optional but recommended for persistent rate limiting.")
    else:
        print("\n[WARNING] Some installation checks failed or require manual action. Please address them before running the app.")


if __name__ == "__main__":
    main()
