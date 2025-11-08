"""Claude AI agent for natural language server management"""

from anthropic import Anthropic
from typing import Dict, List, Optional
import json


class ClaudeAgent:
    """AI agent for interpreting and responding to server management requests"""

    def __init__(self, api_key: str):
        self.client = Anthropic(api_key=api_key)
        self.model = "claude-3-haiku-20240307"

        # Define available tools/functions
        self.tools = [
            {
                "name": "check_server_status",
                "description": "Check if the Project Zomboid server is online and running. Returns server status and last activity time.",
                "input_schema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            {
                "name": "get_recent_logs",
                "description": "Retrieve recent server log entries. Useful for debugging issues or checking server activity.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "lines": {
                            "type": "integer",
                            "description": "Number of recent log lines to retrieve (default: 50, max: 200)",
                            "default": 50
                        }
                    },
                    "required": []
                }
            },
            {
                "name": "search_logs",
                "description": "Search server logs for specific terms or errors. Case-insensitive search.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "search_term": {
                            "type": "string",
                            "description": "The term to search for in logs (e.g., 'error', 'warning', player name)"
                        },
                        "max_lines": {
                            "type": "integer",
                            "description": "Maximum number of recent lines to search through",
                            "default": 100
                        }
                    },
                    "required": ["search_term"]
                }
            },
            {
                "name": "get_chat_logs",
                "description": "Retrieve recent in-game chat messages from players.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "lines": {
                            "type": "integer",
                            "description": "Number of recent chat lines to retrieve",
                            "default": 50
                        }
                    },
                    "required": []
                }
            },
            {
                "name": "get_server_info",
                "description": "Get general server information including name, max players, map, PVP status, etc.",
                "input_schema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            {
                "name": "get_player_activity",
                "description": "Get recent player connection/disconnection activity and player-related events.",
                "input_schema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            {
                "name": "list_mods",
                "description": "List all currently installed mods on the server.",
                "input_schema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            {
                "name": "list_backups",
                "description": "List available server backups.",
                "input_schema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            {
                "name": "update_server_config",
                "description": "Update a server configuration setting. Use with caution!",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "key": {
                            "type": "string",
                            "description": "Configuration key to update (e.g., 'MaxPlayers', 'PVP')"
                        },
                        "value": {
                            "type": "string",
                            "description": "New value for the configuration"
                        }
                    },
                    "required": ["key", "value"]
                }
            },
            {
                "name": "add_mod",
                "description": "Add a mod to the server by Workshop ID. The server will download the mod on next restart.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "workshop_id": {
                            "type": "string",
                            "description": "Steam Workshop ID of the mod to add (e.g., '2169435993')"
                        },
                        "mod_id": {
                            "type": "string",
                            "description": "Optional: Mod ID for the Mods= config line. If not provided, will be extracted from workshop.",
                            "default": ""
                        }
                    },
                    "required": ["workshop_id"]
                }
            },
            {
                "name": "remove_mod",
                "description": "Remove a mod from the server configuration.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "mod_identifier": {
                            "type": "string",
                            "description": "Workshop ID or Mod ID to remove"
                        }
                    },
                    "required": ["mod_identifier"]
                }
            },
            {
                "name": "get_sandbox_settings",
                "description": "Get sandbox/gameplay settings like zombie speed, multi-hit, loot abundance, etc. These are different from server config.",
                "input_schema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            {
                "name": "update_sandbox_setting",
                "description": "Update a sandbox/gameplay setting like MultiHitZombies, Speed, Zombies population, etc.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "key": {
                            "type": "string",
                            "description": "Sandbox setting key (e.g., 'MultiHitZombies', 'Speed', 'Zombies')"
                        },
                        "value": {
                            "type": "string",
                            "description": "New value (use 'true'/'false' for booleans, numbers as strings)"
                        }
                    },
                    "required": ["key", "value"]
                }
            },
            {
                "name": "search_knowledge_base",
                "description": "Search the local Project Zomboid wiki knowledge base for gameplay information, mechanics, tips, and strategies. ALWAYS try this FIRST when answering PZ gameplay questions. Fast and comprehensive.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The question or topic to search for (e.g., 'how does farming work', 'zombie migration', 'best early game strategy')"
                        },
                        "n_results": {
                            "type": "integer",
                            "description": "Number of relevant chunks to retrieve (default: 5)",
                            "default": 5
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "search_pz_wiki",
                "description": "Search the live Project Zomboid wiki online. Use this as a FALLBACK when search_knowledge_base returns poor results or doesn't have the information. Also use for very recent/new content that might not be in the local knowledge base.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The topic or question to search the wiki for"
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "get_player_stats",
                "description": "Get gameplay statistics for a specific player, including zombies killed, distance traveled, deaths, playtime, and more.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "username": {
                            "type": "string",
                            "description": "The player's username"
                        }
                    },
                    "required": ["username"]
                }
            },
            {
                "name": "get_leaderboard",
                "description": "Get a leaderboard showing top players in a specific category. Available categories: zombies_killed, distance_traveled, buildings_placed, items_crafted, total_playtime, longest_life, current_life_duration, kill_death_ratio, most_deaths.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "category": {
                            "type": "string",
                            "description": "Leaderboard category: 'zombies_killed', 'distance_traveled', 'buildings_placed', 'items_crafted', 'total_playtime', 'longest_life' (best survival streak), 'current_life_duration' (who's been alive longest now), 'kill_death_ratio' (efficiency), or 'most_deaths' (hall of shame)"
                        },
                        "top_n": {
                            "type": "integer",
                            "description": "Number of top players to show (default: 10)",
                            "default": 10
                        }
                    },
                    "required": ["category"]
                }
            },
            {
                "name": "get_server_summary",
                "description": "Get overall server statistics including total players, zombies killed, playtime, and playstyle distribution.",
                "input_schema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        ]

        self.system_prompt = """You are Spiffo, an AI assistant managing a Project Zomboid game server via FTP access.

**SERVER MANAGEMENT CAPABILITIES:**
✅ Check server status and health
✅ View and search server logs (console logs, chat logs, debug logs)
✅ Monitor player activity (connections, disconnections)
✅ List currently installed mods
✅ **ADD/REMOVE MODS** - Add Workshop IDs to server config (server downloads them on restart)
✅ Manage server configuration (MaxPlayers, PVP settings, passwords, welcome message, etc.)
✅ **Manage Sandbox/Gameplay settings** (zombie speed, multi-hit, loot, difficulty, etc.)
✅ List available backups
✅ Get server information (name, description, settings)
✅ Search logs for specific terms or errors

**WHAT YOU CANNOT DO:**
❌ Restart the server (tell users: use IB bot command `/restart`)
❌ Kick/ban players in real-time (no RCON access)
❌ Send in-game announcements directly

**PROJECT ZOMBOID KNOWLEDGE:**
✅ Answer gameplay questions using comprehensive wiki knowledge
✅ Explain game mechanics, strategies, and tips
✅ Provide detailed information about items, skills, survival, crafting, etc.
✅ Have casual conversations while helping with server management

**PLAYER STATISTICS:**
✅ View individual player stats (zombies killed, distance traveled, deaths, playtime, etc.)
✅ Generate leaderboards by category (zombies_killed, distance_traveled, buildings_placed, items_crafted, total_playtime)
✅ Get server-wide statistics and playstyle distribution
✅ Stats include playstyle profiles (Combat-Focused Fighter, Explorer/Looter, Builder/Crafter, etc.)

**KNOWLEDGE SEARCH STRATEGY:**
When answering PZ gameplay questions:
1. **FIRST**: Use `search_knowledge_base` to search the local wiki database (fast, comprehensive)
2. **Check relevance**: Results include relevance scores (0-1 range)
3. **If needed**: Use `search_pz_wiki` as fallback if:
   - Knowledge base results have low relevance (<0.6)
   - No good matches found
   - Question is about very recent/new content
4. **Combine sources**: You can use both if it provides better answers

**IMPORTANT NOTES:**
- Configuration changes require a server restart to take effect
- Empty results mean no data exists (e.g., no mods = empty mod list)
- If tools return empty/None, report that clearly: "No mods are currently installed" not "I cannot access mods"

**DISPLAY RULES:**
- ALWAYS show actual data from tools, never just describe it
- Use ```code blocks``` for logs, configs, and technical output
- Display ALL lines when showing logs (don't summarize unless >2000 chars)
- Use **bold** for important info, bullet points for lists
- Keep responses under 2000 characters when possible

**EXAMPLES:**
Good: "No mods are currently installed. To add mods, I can update the config with Workshop IDs."
Bad: "I cannot access the mod list"

Good: "Here are the last 20 log lines: ```[logs displayed here]```"
Bad: "The logs show server startup information" """

    def process_message(self, user_message: str, conversation_history: List[Dict] = None) -> Dict:
        """
        Process a user message and determine what actions to take.

        Returns a dict with:
        - response: The text response to send back
        - tool_calls: List of tools that were called (for logging)
        """
        if conversation_history is None:
            conversation_history = []

        # Add user message to history
        messages = conversation_history + [
            {"role": "user", "content": user_message}
        ]

        try:
            # Call Claude with tools
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                system=self.system_prompt,
                tools=self.tools,
                messages=messages
            )

            # Process the response
            tool_calls = []
            final_text = ""

            for block in response.content:
                if block.type == "text":
                    final_text += block.text
                elif block.type == "tool_use":
                    tool_calls.append({
                        "id": block.id,
                        "name": block.name,
                        "input": block.input
                    })

            return {
                "response": final_text,
                "tool_calls": tool_calls,
                "stop_reason": response.stop_reason,
                "full_response": response
            }

        except Exception as e:
            return {
                "response": f"Sorry, I encountered an error: {str(e)}",
                "tool_calls": [],
                "error": str(e)
            }

    def get_final_response(self, messages: List[Dict]) -> str:
        """
        Get final response from Claude given complete message history including tool results.

        messages should be complete conversation including tool_use and tool_result
        """
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                system=self.system_prompt,
                tools=self.tools,
                messages=messages
            )

            # Extract text response
            final_text = ""
            for block in response.content:
                if block.type == "text":
                    final_text += block.text

            return final_text

        except Exception as e:
            return f"Sorry, I encountered an error: {str(e)}"
