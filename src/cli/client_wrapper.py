#!/usr/bin/env python3
"""
Client Wrapper (Python Version)
Wraps the Claude Code client to handle 401 errors and auto-heal.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
from src.cli.fix_keys import main as fix_keys_main

# Colors
RED = "\033[0;31m"
YELLOW = "\033[1;33m"
CYAN = "\033[0;36m"
NC = "\033[0m"

def main(args=None):
    if args is None:
        args = sys.argv[1:]
        
    if not args:
        print("Usage: python start_proxy.py --client -- <command>")
        sys.exit(1)

    # 1. Check Mode (Proxy vs Direct)
    # We check ANTHROPIC_BASE_URL or PROVIDER_BASE_URL
    base_url = os.environ.get("ANTHROPIC_BASE_URL", "") or os.environ.get("PROVIDER_BASE_URL", "")
    is_proxy_mode = "localhost" in base_url or "127.0.0.1" in base_url

    # 2. Prepare Environment
    env = os.environ.copy()
    if is_proxy_mode:
        # Force 'pass' as the API key for the client
        env["ANTHROPIC_API_KEY"] = "pass"
        env["PROXY_AUTH_KEY"] = "pass" # Ensure this is set too just in case

    # 3. Run Command
    # We need to run it and capture output while preserving TTY
    # This is tricky in Python. subprocess.run with capture_output=True hides TTY.
    # We can use pexpect or just run it and let it print to stdout/stderr, 
    # but then we can't easily grep the output unless we pipe it.
    # 
    # The shell script used `2> >(tee temp)`.
    # In Python, we can try to pipe stderr to a pipe, read it in a thread, and print it?
    # Or simpler: just run it. If it fails with a specific exit code, we assume it might be auth.
    # But Claude Code exit codes might not be specific enough.
    #
    # Let's try the pipe approach for stderr.
    
    print(f"{CYAN}🚀 Starting Client Wrapper...{NC}")
    
    while True:
        process = subprocess.Popen(
            args,
            env=env,
            stderr=subprocess.PIPE,
            stdout=sys.stdout, # Pass stdout directly
            stdin=sys.stdin,   # Pass stdin directly
            bufsize=0,         # Unbuffered
            universal_newlines=True
        )
        
        # We need to read stderr to check for errors, but also print it to user
        stderr_output = []
        
        while True:
            char = process.stderr.read(1)
            if not char and process.poll() is not None:
                break
            if char:
                sys.stderr.write(char)
                sys.stderr.flush()
                stderr_output.append(char)
                
        stderr_str = "".join(stderr_output)
        return_code = process.poll()
        
        if return_code != 0:
            # Check for auth errors
            if "401" in stderr_str or "Unauthorized" in stderr_str or "Invalid API key" in stderr_str:
                print(f"\n{RED}🛑 Authentication Error Detected!{NC}")
                print(f"{YELLOW}🚀 Launching Auto-Healing Wizard...{NC}\n")
                
                try:
                    fix_keys_main()
                except SystemExit as e:
                    if e.code != 0:
                        print(f"{RED}Wizard cancelled. Exiting.{NC}")
                        sys.exit(return_code)
                    # If 0, wizard succeeded
                
                print(f"\n{CYAN}🔄 Restarting command...{NC}\n")
                
                if is_proxy_mode:
                     print(f"{RED}⚠️  ACTION REQUIRED ⚠️{NC}")
                     print(f"{YELLOW}You are running in PROXY MODE.{NC}")
                     print("The proxy server should auto-detect the key change within 5 minutes.")
                     print("If it doesn't, restart the proxy terminal.")
                     input("Press Enter to retry the client command...")
                
                # We need to reload env vars from profile for the NEXT run?
                # Actually, if we are in proxy mode, we just need to send 'pass' again.
                # The PROXY server needs the new key (which it gets via file polling).
                # So we don't need to update OUR env here if we are just sending 'pass'.
                #
                # If we are in DIRECT mode, we DO need to update our env.
                if not is_proxy_mode:
                    # Reload key from profile
                    from src.utils.key_reloader import key_reloader
                    # Force a check
                    key_reloader.check_for_updates()
                    # Update env
                    # This is tricky because key_reloader updates os.environ of THIS process
                    # but we constructed `env` dict earlier.
                    # Let's refresh `env` from `os.environ`
                    env = os.environ.copy()
                
                continue # Retry loop
            
        # If we get here, it wasn't an auth error or it succeeded
        sys.exit(return_code)

if __name__ == "__main__":
    main()
