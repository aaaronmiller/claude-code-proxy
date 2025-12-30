import subprocess
import os
import time
from pathlib import Path

# Configuration matching the valid one-liner
PROXY_URL = "http://127.0.0.1:8082"
TIMEOUT = 60
PROMPT = "Please create a poem about coding and save it as poem.txt, then list the folder contents."

def run_simple_test():
    print(f"Running Simple Verification Test")
    print(f"Proxy: {PROXY_URL}")
    print(f"Time limit: {TIMEOUT}s")
    
    # Environment Setup
    env = os.environ.copy()
    env['ANTHROPIC_BASE_URL'] = PROXY_URL
    env['ANTHROPIC_API_KEY'] = 'pass'
    env['NO_PROXY'] = 'localhost,127.0.0.1'
    
    # Command Structure
    cmd = [
        'timeout', str(TIMEOUT),
        'claude',
        '--dangerously-skip-permissions',
        '--no-chrome',
        '--no-session-persistence',
        '--verbose',
        '-p', PROMPT,
        '--allowedTools', 'Read,Edit,Bash'
    ]
    
    print(f"Command: {' '.join(cmd)}")
    
    # Output handling
    log_path = Path("/tmp/claude_simple_test.log")
    
    start_time = time.time()
    
    with open(log_path, 'wb') as f:
        print("Starting process...")
        try:
            # Using subprocess.run for blocking execution
            result = subprocess.run(
                cmd,
                env=env,
                cwd="/tmp",
                stdout=f,
                stderr=f,
                stdin=subprocess.DEVNULL,
                check=False
            )
            duration = time.time() - start_time
            
            print(f"Process finished in {duration:.1f}s")
            print(f"Exit Code: {result.returncode}")
            
            # Analyze Log
            log_content = log_path.read_text(errors='replace')
            if result.returncode == 0:
                print("\n✅ SUCCESS: Claude CLI exited cleaner.")
            elif result.returncode == 124:
                print("\n⚠️ TIMEOUT: Process took longer than 60s.")
            else:
                print(f"\n❌ FAILURE: Exit code {result.returncode}")
                
            print(f"Logs saved to: {log_path}")
            
        except Exception as e:
            print(f"\n❌ EXCEPTION: {e}")

if __name__ == "__main__":
    run_simple_test()
