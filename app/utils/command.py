import subprocess
import os
import logging
import traceback
from typing import List, Tuple, Optional, Union

def run_command(
    command: Union[List[str], str], 
    cwd: str, 
    logger: Optional[logging.Logger] = None,
    env: Optional[dict] = None,
    timeout: Optional[int] = None
) -> Tuple[str, str, bool]:
    """
    Helper function to run a shell command in the given directory.
    
    Args:
        command: The command to run, either as a list of strings or a string
        cwd: Working directory to run the command in
        logger: Optional logger to log debug and error information
        env: Optional environment variables to set
        timeout: Optional timeout in seconds
        
    Returns:
        Tuple of (stdout, stderr, success)
    """
    try:
        if isinstance(command, list):
            command_str = ' '.join(command)
        else:
            command_str = command
            
        if logger:
            logger.debug(f"Running command: {command_str}")
            logger.debug(f"Working directory: {cwd}")
            
        result = subprocess.run(
            command_str,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True,
            env=env,
            timeout=timeout
        )
        return result.stdout, result.stderr, True
    except subprocess.CalledProcessError as e:
        if logger:
            logger.error(f"Command failed with exit code {e.returncode}")
            logger.error(f"Command output: {e.stdout}")
            logger.error(f"Command error: {e.stderr}")
        return e.stdout, e.stderr, False
    except subprocess.TimeoutExpired as e:
        if logger:
            logger.error(f"Command timed out after {timeout} seconds")
        return "", f"Command timed out after {timeout} seconds", False
    except Exception as e:
        if logger:
            logger.error(f"Exception running command: {str(e)}")
            logger.error(traceback.format_exc())
        return "", str(e), False

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
