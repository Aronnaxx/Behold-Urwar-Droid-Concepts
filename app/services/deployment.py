import subprocess
import os
from pathlib import Path
import serial
import json
from typing import Tuple, Optional, List, Dict
import paramiko

class DeploymentService:
    def __init__(self, workspace_root: Path):
        self.workspace_root = workspace_root
        self._serial_connection = None
        self._ssh_connection = None
        
    def connect_serial(self, port: str, baudrate: int = 115200) -> Tuple[bool, str]:
        """Connect to a device via serial."""
        try:
            if self._serial_connection:
                self._serial_connection.close()
                
            self._serial_connection = serial.Serial(port, baudrate)
            return True, "Serial connection established"
        except Exception as e:
            return False, f"Error connecting to serial port: {str(e)}"
            
    def disconnect_serial(self) -> Tuple[bool, str]:
        """Disconnect from serial device."""
        try:
            if self._serial_connection:
                self._serial_connection.close()
                self._serial_connection = None
            return True, "Serial connection closed"
        except Exception as e:
            return False, f"Error closing serial connection: {str(e)}"
            
    def send_serial_command(self, command: str) -> Tuple[bool, str, Optional[str]]:
        """Send a command over serial connection."""
        try:
            if not self._serial_connection:
                return False, "No active serial connection", None
                
            self._serial_connection.write(command.encode())
            response = self._serial_connection.readline().decode().strip()
            return True, "Command sent successfully", response
        except Exception as e:
            return False, f"Error sending serial command: {str(e)}", None
            
    def connect_ssh(self, 
                   hostname: str, 
                   username: str, 
                   password: Optional[str] = None,
                   key_filename: Optional[str] = None) -> Tuple[bool, str]:
        """Connect to a remote device via SSH."""
        try:
            if self._ssh_connection:
                self._ssh_connection.close()
                
            self._ssh_connection = paramiko.SSHClient()
            self._ssh_connection.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            if key_filename:
                self._ssh_connection.connect(hostname, username=username, key_filename=key_filename)
            else:
                self._ssh_connection.connect(hostname, username=username, password=password)
                
            return True, "SSH connection established"
        except Exception as e:
            return False, f"Error connecting via SSH: {str(e)}"
            
    def disconnect_ssh(self) -> Tuple[bool, str]:
        """Disconnect SSH connection."""
        try:
            if self._ssh_connection:
                self._ssh_connection.close()
                self._ssh_connection = None
            return True, "SSH connection closed"
        except Exception as e:
            return False, f"Error closing SSH connection: {str(e)}"
            
    def run_remote_command(self, command: str) -> Tuple[bool, str, Optional[str]]:
        """Run a command on the remote device via SSH."""
        try:
            if not self._ssh_connection:
                return False, "No active SSH connection", None
                
            stdin, stdout, stderr = self._ssh_connection.exec_command(command)
            output = stdout.read().decode()
            error = stderr.read().decode()
            
            if error:
                return False, "Command execution failed", error
                
            return True, "Command executed successfully", output
        except Exception as e:
            return False, f"Error executing remote command: {str(e)}", None
            
    def deploy_model(self, 
                    model_path: str, 
                    remote_path: str,
                    device_type: str = 'serial') -> Tuple[bool, str]:
        """Deploy a model to a device."""
        try:
            if device_type == 'serial':
                if not self._serial_connection:
                    return False, "No active serial connection"
                    
                with open(model_path, 'rb') as f:
                    data = f.read()
                    
                # Send model data over serial in chunks
                chunk_size = 1024
                for i in range(0, len(data), chunk_size):
                    chunk = data[i:i + chunk_size]
                    self._serial_connection.write(chunk)
                    # Wait for acknowledgment
                    ack = self._serial_connection.readline().decode().strip()
                    if ack != 'OK':
                        return False, "Error during model transfer"
                        
            elif device_type == 'ssh':
                if not self._ssh_connection:
                    return False, "No active SSH connection"
                    
                sftp = self._ssh_connection.open_sftp()
                sftp.put(model_path, remote_path)
                sftp.close()
                
            else:
                return False, f"Unsupported device type: {device_type}"
                
            return True, "Model deployed successfully"
        except Exception as e:
            return False, f"Error deploying model: {str(e)}"
            
    def get_device_status(self, device_type: str = 'serial') -> Tuple[bool, str, Optional[Dict]]:
        """Get status information from the device."""
        try:
            if device_type == 'serial':
                if not self._serial_connection:
                    return False, "No active serial connection", None
                    
                self._serial_connection.write(b'status\n')
                response = self._serial_connection.readline().decode().strip()
                status = json.loads(response)
                
            elif device_type == 'ssh':
                if not self._ssh_connection:
                    return False, "No active SSH connection", None
                    
                _, stdout, _ = self._ssh_connection.exec_command('cat /proc/cpuinfo && free -h && df -h')
                status = {
                    'system_info': stdout.read().decode()
                }
                
            else:
                return False, f"Unsupported device type: {device_type}", None
                
            return True, "Status retrieved successfully", status
        except Exception as e:
            return False, f"Error getting device status: {str(e)}", None 