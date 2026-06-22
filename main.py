import os
import sys
import subprocess
import time
import signal

def print_banner():
    print("=" * 70)
    print("        FlowZint Support BOT - Multi-Server Quick Startup Launcher")
    print("=" * 70)
    print(" Starting all 3 servers simultaneously:")
    print("  1. Backend API Server  : http://localhost:8000")
    print("  2. Operations Dashboard : http://localhost:5173")
    print("  3. Customer Website    : http://localhost:5174")
    print("=" * 70)

def main():
    print_banner()
    
    root_dir = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.join(root_dir, "backend")
    frontend_dir = os.path.join(root_dir, "frontend")
    
    # 1. Check directories
    if not os.path.exists(backend_dir):
        print(f"[Error] Backend directory not found at {backend_dir}")
        sys.exit(1)
    if not os.path.exists(frontend_dir):
        print(f"[Error] Frontend directory not found at {frontend_dir}")
        sys.exit(1)
        
    processes = []
    
    # Windows specific console creation flag
    creation_flag = 0
    if sys.platform == "win32":
        creation_flag = subprocess.CREATE_NEW_CONSOLE
        
    try:
        # A. Start FastAPI Backend
        print("Launching Backend Server (Port 8000)...")
        backend_cmd = [sys.executable, "-m", "uvicorn", "app.main:app", "--port", "8000", "--reload"]
        p_backend = subprocess.Popen(
            backend_cmd,
            cwd=backend_dir,
            creationflags=creation_flag
        )
        processes.append(("Backend", p_backend))
        
        # Give backend a moment to start
        time.sleep(1.5)
        
        # B. Start Dashboard Frontend
        print("Launching Dashboard Frontend (Port 5173)...")
        dashboard_cmd = "npm run dev -- --port 5173 --strictPort"
        p_dashboard = subprocess.Popen(
            dashboard_cmd,
            cwd=frontend_dir,
            shell=True,
            creationflags=creation_flag
        )
        processes.append(("Dashboard", p_dashboard))
        
        # C. Start Customer Website Frontend
        print("Launching Customer Website Frontend (Port 5174)...")
        website_cmd = "npm run dev -- --port 5174 --strictPort"
        p_website = subprocess.Popen(
            website_cmd,
            cwd=frontend_dir,
            shell=True,
            creationflags=creation_flag
        )
        processes.append(("Website", p_website))
        
        print("\n" + "=" * 70)
        print(" [SUCCESS] All servers started successfully!")
        if sys.platform == "win32":
            print(" They are running in 3 separate terminal windows.")
        print(" Press Enter or Ctrl+C in this window to stop all servers and exit.")
        print("=" * 70)
        
        # Wait for user input or keyboard interrupt
        try:
            input()
        except KeyboardInterrupt:
            print("\nShutting down...")
            
    except Exception as e:
        print(f"[Error] Failed to launch servers: {e}")
        
    finally:
        print("\nTerminating all servers...")
        for name, proc in processes:
            try:
                if sys.platform == "win32":
                    # On Windows, terminating shell=True processes needs taskkill to clean up children
                    print(f"Stopping {name} process (PID: {proc.pid})...")
                    subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)], capture_output=True)
                else:
                    print(f"Terminating {name}...")
                    proc.terminate()
                    proc.wait(timeout=2)
            except Exception as e:
                print(f"Error stopping {name}: {e}")
                
        print("\nAll servers stopped cleanly. Goodbye!")

if __name__ == "__main__":
    main()
