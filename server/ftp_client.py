"""FTP client for Project Zomboid server file operations"""

import ftplib
import io
from typing import List, Optional, Tuple
from datetime import datetime
import os


class PZFTPClient:
    """FTP client for managing Project Zomboid server files"""

    def __init__(self, host: str, port: int, username: str, password: str):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self._ftp = None

    def connect(self) -> bool:
        """Connect to FTP server"""
        try:
            self._ftp = ftplib.FTP()
            self._ftp.connect(self.host, self.port)
            self._ftp.login(self.username, self.password)
            return True
        except Exception as e:
            print(f"FTP connection error: {e}")
            return False

    def disconnect(self):
        """Disconnect from FTP server"""
        if self._ftp:
            try:
                self._ftp.quit()
            except:
                pass
            self._ftp = None

    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()

    def list_directory(self, path: str) -> List[str]:
        """List files and directories at path"""
        try:
            items = []
            self._ftp.cwd(path)
            self._ftp.retrlines('NLST', items.append)
            return items
        except Exception as e:
            print(f"Error listing directory {path}: {e}")
            return []

    def read_file(self, filepath: str) -> Optional[str]:
        """Read entire file content as string"""
        try:
            lines = []
            self._ftp.retrlines(f'RETR {filepath}', lines.append)
            return '\n'.join(lines)
        except Exception as e:
            print(f"Error reading file {filepath}: {e}")
            return None

    def read_file_lines(self, filepath: str, start: int = 0, count: int = None) -> Optional[List[str]]:
        """Read specific lines from a file"""
        try:
            lines = []
            self._ftp.retrlines(f'RETR {filepath}', lines.append)

            if count is None:
                return lines[start:]
            else:
                return lines[start:start + count]
        except Exception as e:
            print(f"Error reading file lines {filepath}: {e}")
            return None

    def read_file_tail(self, filepath: str, lines: int = 50) -> Optional[List[str]]:
        """Read last N lines from a file"""
        try:
            all_lines = []
            self._ftp.retrlines(f'RETR {filepath}', all_lines.append)
            return all_lines[-lines:] if len(all_lines) > lines else all_lines
        except Exception as e:
            print(f"Error reading file tail {filepath}: {e}")
            return None

    def write_file(self, filepath: str, content: str) -> bool:
        """Write content to file"""
        try:
            bio = io.BytesIO(content.encode('utf-8'))
            self._ftp.storbinary(f'STOR {filepath}', bio)
            return True
        except Exception as e:
            print(f"Error writing file {filepath}: {e}")
            return False

    def file_exists(self, filepath: str) -> bool:
        """Check if file exists"""
        try:
            self._ftp.size(filepath)
            return True
        except:
            return False

    def get_file_modified_time(self, filepath: str) -> Optional[datetime]:
        """Get file modification time"""
        try:
            response = self._ftp.sendcmd(f'MDTM {filepath}')
            # Response format: '213 YYYYMMDDHHMMSS'
            time_str = response.split()[1]
            return datetime.strptime(time_str, '%Y%m%d%H%M%S')
        except Exception as e:
            print(f"Error getting file time {filepath}: {e}")
            return None

    def download_file(self, remote_path: str, local_path: str) -> bool:
        """Download file from server"""
        try:
            with open(local_path, 'wb') as f:
                self._ftp.retrbinary(f'RETR {remote_path}', f.write)
            return True
        except Exception as e:
            print(f"Error downloading file {remote_path}: {e}")
            return False

    def upload_file(self, local_path: str, remote_path: str) -> bool:
        """Upload file to server"""
        try:
            with open(local_path, 'rb') as f:
                self._ftp.storbinary(f'STOR {remote_path}', f)
            return True
        except Exception as e:
            print(f"Error uploading file {local_path}: {e}")
            return False

    def delete_file(self, filepath: str) -> bool:
        """Delete file from server"""
        try:
            self._ftp.delete(filepath)
            return True
        except Exception as e:
            print(f"Error deleting file {filepath}: {e}")
            return False

    def create_directory(self, path: str) -> bool:
        """Create directory on server"""
        try:
            self._ftp.mkd(path)
            return True
        except Exception as e:
            print(f"Error creating directory {path}: {e}")
            return False
