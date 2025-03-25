import subprocess
import os
import paramiko
import serial
import logging
from pathlib import Path
from typing import Tuple, Optional, Dict, List
import traceback
from ..utils.command import run_command

class DeploymentService:
    _instance = None
    _initialized = False

    def __new__(cls, workspace_root: Path):
        if cls._instance is None:
            cls._instance = super(DeploymentService, cls).__new__(cls)
        return cls._instance

    def __init__(self, workspace_root: Path):
        if not self._initialized:
            self.workspace_root = workspace_root
            self.serial_connection = None
            self.ssh_connection = None
            self.logger = logging.getLogger(__name__)
            self._initialized = True
        
    def connect_serial(self, port: str, baudrate: int = 115200) -> Tuple[bool, str]:
        """Connect to a device via serial port."""
        try:
            self.logger.info(f"Connecting to serial port {port} at {baudrate} baud")
            
            # Check if already connected
            if self.serial_connection and self.serial_connection.is_open:
                self.serial_connection.close()
                self.logger.info("Closed existing serial connection")
                
            # Open new connection
            self.serial_connection = serial.Serial(port, baudrate)
            self.logger.info(f"Successfully connected to {port}")
            
            return True, f"Connected to {port} at {baudrate} baud"
            
        except Exception as e:
            self.logger.error(f"Error connecting to serial port: {str(e)}")
            self.logger.error(traceback.format_exc())
            return False, f"Error connecting to serial port: {str(e)}"
            
    def connect_ssh(self, hostname: str, username: str, password: Optional[str] = None, key_filename: Optional[str] = None, port: int = 22) -> Tuple[bool, str]:
        """Connect to a device via SSH."""
        try:
            self.logger.info(f"Connecting to {hostname} via SSH")
            
            # Check if already connected
            if self.ssh_connection and self.ssh_connection.get_transport() and self.ssh_connection.get_transport().is_active():
                self.ssh_connection.close()
                self.logger.info("Closed existing SSH connection")
                
            # Open new connection
            self.ssh_connection = paramiko.SSHClient()
            self.ssh_connection.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            if key_filename:
                self.ssh_connection.connect(hostname, port, username, key_filename=key_filename)
            else:
                self.ssh_connection.connect(hostname, port, username, password=password)
                
            self.logger.info(f"Successfully connected to {hostname}")
            
            return True, f"Connected to {hostname} via SSH"
            
        except Exception as e:
            self.logger.error(f"Error connecting via SSH: {str(e)}")
            self.logger.error(traceback.format_exc())
            return False, f"Error connecting via SSH: {str(e)}"
            
    def deploy_model(self, model_path: str, remote_path: str, device_type: str = 'serial') -> Tuple[bool, str]:
        """Deploy a model to a connected device."""
        try:
            model_file = Path(model_path)
            if not model_file.exists():
                self.logger.error(f"Model file not found: {model_path}")
                return False, f"Model file not found: {model_path}"
                
            if device_type == 'serial':
                return self.deploy_model_serial(model_path)
            else:
                return self.deploy_model_ssh(model_path, remote_path)
                
        except Exception as e:
            self.logger.error(f"Error deploying model: {str(e)}")
            self.logger.error(traceback.format_exc())
            return False, f"Error deploying model: {str(e)}"
            
    def deploy_model_serial(self, model_path: str) -> Tuple[bool, str]:
        """Deploy a model via serial connection."""
        try:
            if not self.serial_connection or not self.serial_connection.is_open:
                self.logger.error("Serial connection not established")
                return False, "Serial connection not established"
                
            self.logger.info(f"Deploying model {model_path} via serial")
            
            # TODO: Implement protocol for sending model over serial
            # This is a placeholder - actual implementation will depend on the device protocol
            model_data = Path(model_path).read_bytes()
            self.serial_connection.write(model_data)
            
            self.logger.info(f"Model {model_path} deployed successfully via serial")
            
            return True, f"Model {model_path} deployed successfully via serial"
            
        except Exception as e:
            self.logger.error(f"Error deploying model via serial: {str(e)}")
            self.logger.error(traceback.format_exc())
            return False, f"Error deploying model via serial: {str(e)}"
            
    def deploy_model_ssh(self, model_path: str, remote_path: str) -> Tuple[bool, str]:
        """Deploy a model via SSH connection."""
        try:
            if not self.ssh_connection or not self.ssh_connection.get_transport() or not self.ssh_connection.get_transport().is_active():
                self.logger.error("SSH connection not established")
                return False, "SSH connection not established"
                
            self.logger.info(f"Deploying model {model_path} via SSH to {remote_path}")
            
            # Get SFTP client
            sftp = self.ssh_connection.open_sftp()
            
            # Create remote directory if it doesn't exist
            remote_dir = os.path.dirname(remote_path)
            try:
                sftp.stat(remote_dir)
            except IOError:
                self.logger.info(f"Creating remote directory: {remote_dir}")
                self.ssh_connection.exec_command(f"mkdir -p {remote_dir}")
                
            # Upload file
            sftp.put(model_path, remote_path)
            
            # Close SFTP
            sftp.close()
            
            self.logger.info(f"Model {model_path} deployed successfully to {remote_path}")
            
            return True, f"Model {model_path} deployed successfully to {remote_path}"
            
        except Exception as e:
            self.logger.error(f"Error deploying model via SSH: {str(e)}")
            self.logger.error(traceback.format_exc())
            return False, f"Error deploying model via SSH: {str(e)}"
            
    def get_device_status(self, device_type: str = 'serial') -> Tuple[bool, str, Dict]:
        """Get status of the connected device."""
        try:
            if device_type == 'serial':
                if not self.serial_connection:
                    return False, "Serial connection not established", {'connected': False}
                    
                return True, "Serial device connected", {
                    'connected': self.serial_connection.is_open,
                    'port': self.serial_connection.port,
                    'baudrate': self.serial_connection.baudrate
                }
                
            else:  # SSH
                if not self.ssh_connection:
                    return False, "SSH connection not established", {'connected': False}
                    
                transport = self.ssh_connection.get_transport()
                return True, "SSH device connected", {
                    'connected': transport and transport.is_active(),
                    'hostname': transport.getpeername()[0] if transport else None,
                    'username': transport.get_username() if transport else None
                }
                
        except Exception as e:
            self.logger.error(f"Error getting device status: {str(e)}")
            self.logger.error(traceback.format_exc())
            return False, f"Error getting device status: {str(e)}", {'connected': False, 'error': str(e)} 