import os
import subprocess
import threading
import sys
import time
import signal

def run_backend():
    """Run backend service"""
    backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend')
    os.chdir(backend_dir)
    print("Starting backend service...")
    
    # Use shell=True on Windows
    if sys.platform == 'win32':
        backend_process = subprocess.Popen(
            'uvicorn main:app --reload --port 8002',
            shell=True
        )
    else:
        backend_process = subprocess.Popen(
            ['uvicorn', 'main:app', '--reload', '--port', '8002']
        )
    
    return backend_process

def run_frontend():
    """Run frontend service"""
    frontend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'frontend')
    os.chdir(frontend_dir)
    print("Starting frontend service...")
    
    # Use shell=True on Windows
    if sys.platform == 'win32':
        frontend_process = subprocess.Popen(
            'npm start',
            shell=True
        )
    else:
        frontend_process = subprocess.Popen(
            ['npm', 'start']
        )
    
    return frontend_process

def main():
    # Store original working directory
    original_dir = os.getcwd()
    
    try:
        # Start backend
        backend_process = run_backend()
        
        # Wait a few seconds to ensure backend is started
        time.sleep(2)
        
        # Return to original directory
        os.chdir(original_dir)
        
        # Start frontend
        frontend_process = run_frontend()
        
        # Wait for user to press Ctrl+C
        try:
            backend_process.wait()
            frontend_process.wait()
        except KeyboardInterrupt:
            print("\nShutting down services...")
            
            # 在 Windows 上
            if sys.platform == 'win32':
                backend_process.terminate()
                frontend_process.terminate()
            else:
                # 在 Unix 系统上发送 SIGTERM 信号
                backend_process.send_signal(signal.SIGTERM)
                frontend_process.send_signal(signal.SIGTERM)
            
            # Wait for processes to end
            backend_process.wait()
            frontend_process.wait()
            
            print("Services have been shut down")
            
    except Exception as e:
        print(f"An error occurred: {e}")
        # Ensure processes are terminated
        try:
            backend_process.terminate()
            frontend_process.terminate()
        except:
            pass
        
        sys.exit(1)

if __name__ == "__main__":
    main()
