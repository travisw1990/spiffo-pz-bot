"""Server controller for Project Zomboid server operations"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from .ftp_client import PZFTPClient
import os


class PZServerController:
    """High-level controller for PZ server management"""

    def __init__(self, ftp_host: str, ftp_port: int, ftp_user: str, ftp_password: str):
        self.ftp_client = PZFTPClient(ftp_host, ftp_port, ftp_user, ftp_password)

        # Server paths
        self.LOGS_PATH = "/server-data/Logs"
        self.SERVER_PATH = "/server-data/Server"
        self.CONFIG_FILE = "/server-data/Server/pzserver.ini"
        self.SANDBOX_FILE = "/server-data/Server/pzserver_SandboxVars.lua"
        self.CONSOLE_LOG = "/server-data/server-console.txt"
        self.SAVES_PATH = "/server-data/Saves/Multiplayer"
        self.BACKUPS_PATH = "/server-data/backups"

    def is_server_online(self) -> Tuple[bool, str]:
        """Check if server is online by examining recent logs"""
        try:
            with self.ftp_client:
                # Check console log modification time
                mod_time = self.ftp_client.get_file_modified_time(self.CONSOLE_LOG)

                if not mod_time:
                    return False, "Could not read server console log"

                # If log was modified in last 5 minutes, server is likely running
                time_diff = datetime.utcnow() - mod_time
                if time_diff < timedelta(minutes=5):
                    # Read last few lines to confirm
                    lines = self.ftp_client.read_file_tail(self.CONSOLE_LOG, 10)
                    if lines and any("SERVER STARTED" in line for line in lines):
                        return True, f"Server online (last activity: {time_diff.seconds // 60} minutes ago)"
                    return True, f"Server appears online (log updated {time_diff.seconds // 60} minutes ago)"
                else:
                    return False, f"Server appears offline (last log update: {time_diff.seconds // 60} minutes ago)"

        except Exception as e:
            return False, f"Error checking server status: {e}"

    def get_recent_logs(self, lines: int = 50) -> Optional[List[str]]:
        """Get recent server log lines"""
        try:
            with self.ftp_client:
                return self.ftp_client.read_file_tail(self.CONSOLE_LOG, lines)
        except Exception as e:
            print(f"Error getting logs: {e}")
            return None

    def search_logs(self, search_term: str, max_lines: int = 100) -> Optional[List[str]]:
        """Search for specific term in recent logs"""
        try:
            with self.ftp_client:
                all_lines = self.ftp_client.read_file_tail(self.CONSOLE_LOG, max_lines)
                if not all_lines:
                    return None

                # Case-insensitive search
                matching_lines = [
                    line for line in all_lines
                    if search_term.lower() in line.lower()
                ]
                return matching_lines
        except Exception as e:
            print(f"Error searching logs: {e}")
            return None

    def get_chat_logs(self, lines: int = 50) -> Optional[List[str]]:
        """Get recent chat logs"""
        try:
            with self.ftp_client:
                # Find most recent chat log file
                log_files = self.ftp_client.list_directory(self.LOGS_PATH)
                chat_files = [f for f in log_files if 'chat.txt' in f]

                if not chat_files:
                    return None

                # Sort by name (contains timestamp) and get most recent
                chat_files.sort(reverse=True)
                recent_chat = f"{self.LOGS_PATH}/{chat_files[0]}"

                return self.ftp_client.read_file_tail(recent_chat, lines)
        except Exception as e:
            print(f"Error getting chat logs: {e}")
            return None

    def get_server_config(self) -> Optional[Dict[str, str]]:
        """Read server configuration"""
        try:
            with self.ftp_client:
                content = self.ftp_client.read_file(self.CONFIG_FILE)
                if not content:
                    return None

                # Parse INI file into dict
                config = {}
                for line in content.split('\n'):
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        config[key.strip()] = value.strip()

                return config
        except Exception as e:
            print(f"Error reading config: {e}")
            return None

    def update_server_config(self, key: str, value: str) -> bool:
        """Update a single config value"""
        try:
            with self.ftp_client:
                content = self.ftp_client.read_file(self.CONFIG_FILE)
                if not content:
                    return False

                # Update the config line
                lines = content.split('\n')
                updated = False

                for i, line in enumerate(lines):
                    if line.strip().startswith(key + '='):
                        lines[i] = f"{key}={value}"
                        updated = True
                        break

                if not updated:
                    # Key not found, add it
                    lines.append(f"{key}={value}")

                new_content = '\n'.join(lines)
                return self.ftp_client.write_file(self.CONFIG_FILE, new_content)
        except Exception as e:
            print(f"Error updating config: {e}")
            return False

    def get_player_activity(self) -> Optional[List[str]]:
        """Get recent player activity from logs"""
        try:
            with self.ftp_client:
                logs = self.ftp_client.read_file_tail(self.CONSOLE_LOG, 200)
                if not logs:
                    return None

                # Look for player-related log entries
                player_lines = []
                keywords = ['player', 'connected', 'disconnected', 'login', 'logout']

                for line in logs:
                    if any(keyword in line.lower() for keyword in keywords):
                        player_lines.append(line)

                return player_lines
        except Exception as e:
            print(f"Error getting player activity: {e}")
            return None

    def list_mods(self) -> Optional[List[str]]:
        """List installed mods"""
        try:
            with self.ftp_client:
                config = self.get_server_config()
                if not config:
                    return None

                # Get mods from config
                mods_str = config.get('Mods', '')
                workshop_items = config.get('WorkshopItems', '')

                mods = []
                if mods_str:
                    mods.extend([m.strip() for m in mods_str.split(';') if m.strip()])

                return mods if mods else []
        except Exception as e:
            print(f"Error listing mods: {e}")
            return None

    def get_server_info(self) -> Optional[Dict[str, str]]:
        """Get general server information"""
        try:
            config = self.get_server_config()
            if not config:
                return None

            info = {
                'Server Name': config.get('PublicName', 'Unknown'),
                'Description': config.get('PublicDescription', 'N/A'),
                'Max Players': config.get('MaxPlayers', 'Unknown'),
                'Map': config.get('Map', 'Unknown'),
                'PVP': config.get('PVP', 'Unknown'),
                'Public': config.get('Public', 'Unknown'),
                'Password Protected': 'Yes' if config.get('Password') else 'No',
            }

            return info
        except Exception as e:
            print(f"Error getting server info: {e}")
            return None

    def list_backups(self) -> Optional[List[str]]:
        """List available backups"""
        try:
            with self.ftp_client:
                backups = []
                # Check startup backups
                startup_backups = self.ftp_client.list_directory(f"{self.BACKUPS_PATH}/startup")
                backups.extend([f"startup/{b}" for b in startup_backups if b.endswith('.zip')])

                # Check version backups
                version_backups = self.ftp_client.list_directory(f"{self.BACKUPS_PATH}/version")
                backups.extend([f"version/{v}" for v in version_backups if v.endswith('.zip')])

                return backups
        except Exception as e:
            print(f"Error listing backups: {e}")
            return None

    def add_mod(self, workshop_id: str, mod_id: str = "") -> Tuple[bool, str]:
        """Add a mod to the server configuration"""
        try:
            config = self.get_server_config()
            if not config:
                return False, "Could not read server configuration"

            # Get current mods and workshop items
            current_mods = config.get('Mods', '').split(';') if config.get('Mods') else []
            current_workshop = config.get('WorkshopItems', '').split(';') if config.get('WorkshopItems') else []

            # Clean empty strings
            current_mods = [m.strip() for m in current_mods if m.strip()]
            current_workshop = [w.strip() for w in current_workshop if w.strip()]

            # Check if already added
            if workshop_id in current_workshop:
                return False, f"Workshop ID {workshop_id} is already in the mod list"

            # Add workshop ID
            current_workshop.append(workshop_id)

            # Add mod ID if provided
            if mod_id and mod_id not in current_mods:
                current_mods.append(mod_id)

            # Update config
            workshop_success = self.update_server_config('WorkshopItems', ';'.join(current_workshop))

            if mod_id:
                mods_success = self.update_server_config('Mods', ';'.join(current_mods))
                if not (workshop_success and mods_success):
                    return False, "Failed to update configuration"
            else:
                if not workshop_success:
                    return False, "Failed to update WorkshopItems"

            return True, f"Successfully added Workshop ID {workshop_id}. Server restart required for mod to download."

        except Exception as e:
            return False, f"Error adding mod: {e}"

    def remove_mod(self, mod_identifier: str) -> Tuple[bool, str]:
        """Remove a mod from the server configuration"""
        try:
            config = self.get_server_config()
            if not config:
                return False, "Could not read server configuration"

            # Get current mods and workshop items
            current_mods = config.get('Mods', '').split(';') if config.get('Mods') else []
            current_workshop = config.get('WorkshopItems', '').split(';') if config.get('WorkshopItems') else []

            # Clean empty strings
            current_mods = [m.strip() for m in current_mods if m.strip()]
            current_workshop = [w.strip() for w in current_workshop if w.strip()]

            removed_something = False

            # Try to remove from workshop items
            if mod_identifier in current_workshop:
                current_workshop.remove(mod_identifier)
                removed_something = True

            # Try to remove from mods
            if mod_identifier in current_mods:
                current_mods.remove(mod_identifier)
                removed_something = True

            if not removed_something:
                return False, f"Could not find mod identifier '{mod_identifier}' in config"

            # Update config
            self.update_server_config('WorkshopItems', ';'.join(current_workshop))
            self.update_server_config('Mods', ';'.join(current_mods))

            return True, f"Successfully removed mod '{mod_identifier}'. Server restart required."

        except Exception as e:
            return False, f"Error removing mod: {e}"

    def get_sandbox_settings(self) -> Optional[Dict[str, str]]:
        """Read sandbox settings from Lua file"""
        try:
            with self.ftp_client:
                content = self.ftp_client.read_file(self.SANDBOX_FILE)
                if not content:
                    return None

                # Parse Lua sandbox vars (simple key = value extraction)
                settings = {}
                for line in content.split('\n'):
                    line = line.strip()
                    # Look for lines like: SomeVariable = value,
                    if '=' in line and not line.startswith('--') and not line.startswith('SandboxVars'):
                        # Remove trailing comma
                        line = line.rstrip(',')
                        parts = line.split('=', 1)
                        if len(parts) == 2:
                            key = parts[0].strip()
                            value = parts[1].strip()
                            settings[key] = value

                return settings
        except Exception as e:
            print(f"Error reading sandbox settings: {e}")
            return None

    def update_sandbox_setting(self, key: str, value: str) -> Tuple[bool, str]:
        """Update a sandbox setting in the Lua file"""
        try:
            with self.ftp_client:
                content = self.ftp_client.read_file(self.SANDBOX_FILE)
                if not content:
                    return False, "Could not read sandbox file"

                lines = content.split('\n')
                updated = False

                # Find and update the line
                for i, line in enumerate(lines):
                    stripped = line.strip()
                    if stripped.startswith(key + ' =') or stripped.startswith(key + '='):
                        # Preserve indentation
                        indent = line[:len(line) - len(line.lstrip())]
                        lines[i] = f"{indent}{key} = {value},"
                        updated = True
                        break

                if not updated:
                    return False, f"Setting '{key}' not found in sandbox file"

                new_content = '\n'.join(lines)
                success = self.ftp_client.write_file(self.SANDBOX_FILE, new_content)

                if success:
                    return True, f"Successfully updated {key} to {value}. Server restart required."
                else:
                    return False, "Failed to write sandbox file"

        except Exception as e:
            return False, f"Error updating sandbox setting: {e}"
