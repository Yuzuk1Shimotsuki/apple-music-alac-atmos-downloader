#!/usr/bin/env python3
import os
import sys
import time
import subprocess
import threading
import getpass
from datetime import datetime
import multiprocessing
import signal

def get_instance_info():
    try:
        # Get detailed process information with more specific filtering
        result = subprocess.run(
            ['ps', 'aux'], 
            stdout=subprocess.PIPE, 
            stderr=subprocess.DEVNULL,
            text=True
        )
        
        # More strict filtering to avoid false positives
        wrapper_processes = []
        for line in result.stdout.splitlines():
            # Only match exact wrapper process pattern
            if './wrapper -D 10020 -M 20020' in line and not ('python' in line or 'wrapper.py' in line):
                parts = line.split()
                pid = parts[1]
                start_time = ' '.join(parts[8:9])
                wrapper_processes.append({
                    'pid': pid,
                    'time': start_time
                })
        
        return wrapper_processes
    except:
        return []

def is_running():
    processes = get_instance_info()
    # Add debug logging
    if processes:
        print(f"Debug: Found running processes: {processes}")
    return len(processes) > 0

def logout():
    processes = get_instance_info()
    
    if not processes:
        print(f'''
{"-" * 120}

No running instances found.
To start a new instance:
    python3 wrapper.py


{"-" * 120}
''')
        return False

    killed_count = 0
    failed_count = 0
    
    print(f"\n{'-' * 120}\n\nTerminating instances...")
    for proc in processes:
        try:
            pid = int(proc['pid'])
            # First try SIGTERM for graceful shutdown
            os.kill(pid, signal.SIGTERM)
            time.sleep(0.5)  # Give process time to terminate gracefully
            
            # If process still exists, force kill
            try:
                os.kill(pid, 0)  # Check if process still exists
                os.kill(pid, signal.SIGKILL)  # Force kill if still running
            except ProcessLookupError:
                pass  # Process already terminated
                
            killed_count += 1
            print(f"Terminated PID: {pid}")
        except ProcessLookupError:
            continue
        except PermissionError:
            failed_count += 1
            print(f"Permission denied for PID: {pid}")
        except Exception as e:
            failed_count += 1
            print(f"Failed to terminate PID {pid}: {str(e)}")

    # Force cleanup any remaining processes
    cleanup_cmd = f"pkill -f './wrapper -D'"
    try:
        subprocess.run(cleanup_cmd, shell=True, stderr=subprocess.DEVNULL)
    except:
        pass

    if failed_count > 0:
        print(f'''
Some processes could not be terminated due to permission issues.
Try running with sudo:
    sudo python3 wrapper.py logout
''')
        return False

    if killed_count > 0:
        print(f"\nSuccessfully terminated {killed_count} instance{'s' if killed_count > 1 else ''}.")
    
    print(f"\n{'-' * 120}\n")
    return killed_count > 0

def show_status():
    processes = get_instance_info()
    if not processes:
        print(f'''
{"-" * 120}

Status: Not running

To start a new instance:
    python3 wrapper.py

    
{"-" * 120}
''')
        return False
    
    status_message = f'''
{"-" * 120}

Status: Running
Instance{"s" if len(processes) > 1 else ""}:'''
    
    for proc in processes:
        status_message += f'''
    PID: {proc['pid']}
    Started at: {proc['time']}'''
    
    status_message += f'''

To terminate, run:
    python3 wrapper.py logout

    
{"-" * 120}
'''
    print(status_message)
    return True

def get_credentials():
    login_message =f'''
{"-" * 120}

Login with Your Apple Music / iCloud or Apple ID
To continue, please log in with your Apple ID credentials (email or phone number).

Note: 
If you have Two-Factor Authentication (2FA) enabled, a verification code will be sent to your trusted device.
Enter the code to complete the login process.

Forgot Your Password? 
Visit Reset your password (https://iforgot.apple.com/password/verify/appleid) to reset it.

Need Further Help?
For any login issues, please visit Apple Support (https://support.apple.com/) for assistance.


Username (add +86 prefix for Chinese mainland accounts): '''
    username = input(login_message)
    password = getpass.getpass("Password: ")
    print("\n")
    return f"{username}:{password}"

def log_output(timestamp, message):
    with open("wrapper_log.txt", "a") as log:
        log.write(f"[{timestamp}] {message}\n")

def handle_2fa():
    code = input(f"\n\nEnter the 2FA code: ")
    print("\n")
    if code == "" or len(code) != 6:
        return "000000" + "\n"  # Assume a wrong code to stop
    return code + "\n"

def background_process(log_file):
    with open(os.devnull, 'r') as devnull:
        os.dup2(devnull.fileno(), sys.stdin.fileno())
    with open(log_file, 'a') as log:
        os.dup2(log.fileno(), sys.stdout.fileno())
        os.dup2(log.fileno(), sys.stderr.fileno())

def read_output(process):
    m3u8_seen = False
    is_type_6 = False
    waiting_for_2fa = False
    response_type = None

    while True:
        line = process.stdout.readline()
        if not line and process.poll() is not None:
            break
        if line:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            line = line.decode('utf-8', errors='replace').strip()

            if not m3u8_seen:
                print(f"[{timestamp}] {line}")

            log_output(timestamp, line)

            # Check for 2FA request
            if "2FA: true" in line:
                if not waiting_for_2fa:
                    waiting_for_2fa = True
                print(f"\n\nTwo-Factor Authentication (2FA) passcode required:\nA 2FA passcode has been sent to your devices using your preferred method.")
                code = handle_2fa()
                process.stdin.write(code.encode())
                process.stdin.flush()
                continue

            # Check for response type
            if "response type" in line.lower():
                try:
                    response_type = int(line.split("response type")[-1].strip())
                    if waiting_for_2fa and response_type == 0 or response_type == 4:
                        print("\n\n2FA verification failed.")
                        waiting_for_2fa = False
                    if response_type == 0:
                        login_failed_0 = f'''
Login failed. Please check your credentials and try again.
If the issue persist, please visit Apple Support (https://support.apple.com/) for further assistance.

Aborting...


{"-" * 120}
                        '''
                        print(login_failed_0)
                        sys.stdout.flush()
                        process.terminate()
                        sys.exit(1)
                    elif response_type == 4:
                        login_failed_4 = f'''
Your account has been disabled for security reasons.
If the issue persist, please visit Apple Support (https://support.apple.com/) for further assistance.

Aborting...


{"-" * 120}
                        '''
                        print(login_failed_4)
                        sys.stdout.flush()
                        process.terminate()
                        sys.exit(1)
                    elif response_type == 6:
                        is_type_6 = True
                except ValueError:
                    pass

            # Check for m3u8 message
            if "listening m3u8 request on" in line.lower():
                m3u8_seen = True

            # Check if both conditions are met
            if is_type_6 and m3u8_seen:
                if waiting_for_2fa:
                    print("\n\n2FA verified successfully.")
                    waiting_for_2fa = False
                print(f"\n\nLogin Succeed.\n\nInstance PID: {process.pid}\n\n{'-' * 120}")
                print("\nService is ready. Moving to background...\n")
                print("To check status: python3 wrapper.py status")
                print("To logout: python3 wrapper.py logout\n")
                sys.stdout.flush()
                time.sleep(0.5)  # Give time for messages to be printed

                # Start background process
                ctx = multiprocessing.get_context('spawn')
                p = ctx.Process(target=background_process, args=("wrapper_log.txt",))
                p.daemon = True
                p.start()

                # Clean up and exit
                process.stdin.close()
                process.stdout.close()
                process.terminate()
                os._exit(0)

            # Check for login failure explicitly
            if "login failed" in line.lower():
                if waiting_for_2fa:
                    print("\n\n2FA verification failed.")
                login_failed = f'''
Login failed. Please try again later.
If the issue persist, please visit Apple Support (https://support.apple.com/) for further assistance.

Aborting...

{"-" * 120}
                '''
                print(login_failed)
                sys.stdout.flush()
                process.terminate()
                sys.exit(1)

def main():
    # Move the set_start_method inside main()
    if sys.platform != 'darwin':  # If not on macOS
        try:
            multiprocessing.set_start_method('spawn')
        except RuntimeError:
            pass  # Context already set, ignore the error
    # Command line argument handling
    if len(sys.argv) == 2:
        if sys.argv[1] == "logout":
            logout()
            return
        elif sys.argv[1] == "status":
            show_status()
            return
        else:
            print("Error: Invaild argument")
            sys.exit(1)
    elif len(sys.argv) > 2:
        print("Error: Invaild arguments")
        sys.exit(1)
    else:
        pass

    # Check if already running
    if is_running():
        print(f'''
{"-" * 120}

Error: An instance is already running.
To check status:
    python3 wrapper.py status

To start a new instance, please logout first:
    python3 wrapper.py logout

{"-" * 120}
''')
        sys.exit(1)

    try:
        if not os.path.isdir("wrapper"):
            print("Error: 'wrapper' directory not found. Aborting...\n")
            sys.exit(1)

        os.chdir("wrapper")

        if not os.path.isfile("./wrapper"):
            print("Error: 'wrapper' executable not found. Aborting...\n")
            sys.exit(1)

        if not os.access("./wrapper", os.X_OK):
            print("Error: 'wrapper' is not executable. Aborting...\n")
            sys.exit(1)

        credentials = get_credentials()

        process = subprocess.Popen(
            ["./wrapper", "-D", "10020", "-M", "20020", "-L", credentials],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=0,
            universal_newlines=False
        )

        output_thread = threading.Thread(target=read_output, args=(process,))
        output_thread.daemon = True
        output_thread.start()

        # Wait for a short time to allow the thread to process initial output
        time.sleep(0.1)

        # Wait for the process to complete or be terminated
        process.wait()

    except FileNotFoundError as e:
        print(f"Error: {str(e)}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        if 'process' in locals() and process.poll() is None:
            process.terminate()
            process.wait(timeout=5)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()



