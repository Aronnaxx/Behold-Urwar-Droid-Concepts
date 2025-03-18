import subprocess
import os

def run_command(command, cwd=None):
    """Run a shell command and return its output."""
    print(f"Running command: {command}")
    print(f"Working directory: {cwd or os.getcwd()}")
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True
        )
        print(f"Command output: {result.stdout}")
        if result.stderr:
            print(f"Command error: {result.stderr}")
        return result.stdout, result.stderr
    except Exception as e:
        print(f"Command error: {str(e)}")
        return None, str(e)

def run_background_process(command, cwd=None):
    """Run a command in the background and return the process object."""
    process = subprocess.Popen(
        command,
        shell=True,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    return process 
