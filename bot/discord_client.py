"""Discord bot client for Project Zomboid server management"""

import discord
from discord.ext import commands
import os
from typing import Optional
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai.claude_agent import ClaudeAgent
from server.controller import PZServerController
from knowledge.rag_manager import RAGManager
from knowledge.wiki_scraper import WikiScraper
from analytics.player_stats import PlayerStatsTracker


class PZDiscordBot(commands.Bot):
    """Discord bot for PZ server management with AI integration"""

    def __init__(self,
                 claude_api_key: str,
                 ftp_host: str,
                 ftp_port: int,
                 ftp_user: str,
                 ftp_password: str,
                 game_port: int = 27325,
                 command_prefix: str = "!pz"):

        # Set up intents
        intents = discord.Intents.default()
        intents.message_content = True
        intents.messages = True

        super().__init__(command_prefix=command_prefix, intents=intents)

        # Initialize components
        self.claude_agent = ClaudeAgent(claude_api_key)
        self.server_controller = PZServerController(ftp_host, ftp_port, ftp_user, ftp_password, game_port)

        # Initialize knowledge base
        print("Initializing knowledge base...")
        self.rag_manager = RAGManager(persist_directory="./knowledge_base")
        self.wiki_scraper = WikiScraper(delay=1.0)

        # Check knowledge base status
        stats = self.rag_manager.get_stats()
        if stats['total_chunks'] > 0:
            print(f"Knowledge base loaded: {stats['total_chunks']} chunks from ~{stats['sampled_unique_pages']} pages")
        else:
            print("⚠️  Knowledge base is empty. Run 'python build_knowledge_base.py' to populate it.")

        # Initialize player stats tracker
        print("Initializing player statistics tracker...")
        self.player_stats = PlayerStatsTracker(stats_file="./player_stats.json")

        # Conversation history per channel (limited to prevent token overflow)
        self.conversations = {}
        self.MAX_HISTORY = 10  # Keep last 10 messages per channel

    async def on_ready(self):
        """Called when bot is ready"""
        print(f'Bot logged in as {self.user}')
        print(f'Bot is in {len(self.guilds)} guilds')
        await self.change_presence(activity=discord.Game(name="Managing PZ Server"))

    async def on_message(self, message: discord.Message):
        """Process incoming messages"""
        # Ignore bot's own messages
        if message.author == self.user:
            return

        # Only respond if bot is mentioned or in DM
        if not (self.user.mentioned_in(message) or isinstance(message.channel, discord.DMChannel)):
            return

        # Remove bot mention from message
        content = message.content.replace(f'<@{self.user.id}>', '').strip()

        if not content:
            return

        # Show typing indicator
        async with message.channel.typing():
            # Get conversation history for this channel
            channel_id = str(message.channel.id)
            if channel_id not in self.conversations:
                self.conversations[channel_id] = []

            # Process message with Claude
            result = self.claude_agent.process_message(content, self.conversations[channel_id])

            # Execute any tool calls
            if result.get('tool_calls'):
                tool_results = await self.execute_tools(result['tool_calls'])

                # Build tool results for Claude
                claude_tool_results = []
                for i, tool_call in enumerate(result['tool_calls']):
                    claude_tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_call['id'],
                        "content": str(tool_results[i])
                    })

                # Build the message sequence correctly:
                # 1. User message
                # 2. Assistant with tool_use
                # 3. User with tool_results

                # Format assistant content properly
                assistant_content = []
                for block in result['full_response'].content:
                    if block.type == "text":
                        assistant_content.append({"type": "text", "text": block.text})
                    elif block.type == "tool_use":
                        assistant_content.append({
                            "type": "tool_use",
                            "id": block.id,
                            "name": block.name,
                            "input": block.input
                        })

                # Build complete message sequence for this turn
                messages_with_tools = self.conversations[channel_id] + [
                    {"role": "user", "content": content},
                    {"role": "assistant", "content": assistant_content},
                    {"role": "user", "content": claude_tool_results}
                ]

                # Get final response with complete conversation
                final_response = self.claude_agent.get_final_response(messages_with_tools)

                # Now save to history: user message, assistant with tools, user with results, assistant final
                self.conversations[channel_id].append({"role": "user", "content": content})
                self.conversations[channel_id].append({"role": "assistant", "content": assistant_content})
                self.conversations[channel_id].append({"role": "user", "content": claude_tool_results})
                self.conversations[channel_id].append({"role": "assistant", "content": final_response})

                # Trim conversation history
                if len(self.conversations[channel_id]) > self.MAX_HISTORY * 2:
                    self.conversations[channel_id] = self.conversations[channel_id][-self.MAX_HISTORY * 2:]

                await self.send_long_message(message.channel, final_response)
            else:
                # No tools needed, just send the response
                response_text = result.get('response', 'Sorry, I could not process that request.')

                # Update conversation history
                self.conversations[channel_id].append({"role": "user", "content": content})
                self.conversations[channel_id].append({"role": "assistant", "content": response_text})

                # Trim history
                if len(self.conversations[channel_id]) > self.MAX_HISTORY * 2:
                    self.conversations[channel_id] = self.conversations[channel_id][-self.MAX_HISTORY * 2:]

                await self.send_long_message(message.channel, response_text)

    async def execute_tools(self, tool_calls):
        """Execute tool calls and return results"""
        results = []

        for tool_call in tool_calls:
            tool_name = tool_call['name']
            tool_input = tool_call['input']

            try:
                if tool_name == "check_server_status":
                    is_online, message = self.server_controller.is_server_online()
                    results.append({"online": is_online, "message": message})

                elif tool_name == "get_recent_logs":
                    lines = tool_input.get('lines', 50)
                    logs = self.server_controller.get_recent_logs(lines)
                    if logs:
                        results.append("\n".join(logs[-lines:]))
                    else:
                        results.append("Could not retrieve logs")

                elif tool_name == "search_logs":
                    search_term = tool_input['search_term']
                    max_lines = tool_input.get('max_lines', 100)
                    matches = self.server_controller.search_logs(search_term, max_lines)
                    if matches:
                        results.append(f"Found {len(matches)} matches:\n" + "\n".join(matches))
                    else:
                        results.append(f"No matches found for '{search_term}'")

                elif tool_name == "get_chat_logs":
                    lines = tool_input.get('lines', 50)
                    chat = self.server_controller.get_chat_logs(lines)
                    if chat:
                        results.append("\n".join(chat[-lines:]))
                    else:
                        results.append("Could not retrieve chat logs")

                elif tool_name == "get_server_info":
                    info = self.server_controller.get_server_info()
                    if info:
                        results.append(info)
                    else:
                        results.append("Could not retrieve server info")

                elif tool_name == "get_player_activity":
                    activity = self.server_controller.get_player_activity()
                    if activity:
                        results.append("\n".join(activity))
                    else:
                        results.append("No recent player activity found")

                elif tool_name == "list_mods":
                    mods = self.server_controller.list_mods()
                    if mods:
                        results.append(f"Installed mods: {', '.join(mods)}" if mods else "No mods installed")
                    else:
                        results.append("Could not retrieve mod list")

                elif tool_name == "list_backups":
                    backups = self.server_controller.list_backups()
                    if backups:
                        results.append(f"Available backups:\n" + "\n".join(backups))
                    else:
                        results.append("No backups found or could not retrieve backup list")

                elif tool_name == "update_server_config":
                    key = tool_input['key']
                    value = tool_input['value']
                    success = self.server_controller.update_server_config(key, value)
                    if success:
                        results.append(f"Successfully updated {key} to {value}. Restart server for changes to take effect.")
                    else:
                        results.append(f"Failed to update configuration")

                elif tool_name == "add_mod":
                    workshop_id = tool_input['workshop_id']
                    mod_id = tool_input.get('mod_id', '')
                    success, message = self.server_controller.add_mod(workshop_id, mod_id)
                    results.append(message)

                elif tool_name == "remove_mod":
                    mod_identifier = tool_input['mod_identifier']
                    success, message = self.server_controller.remove_mod(mod_identifier)
                    results.append(message)

                elif tool_name == "get_sandbox_settings":
                    settings = self.server_controller.get_sandbox_settings()
                    if settings:
                        results.append(settings)
                    else:
                        results.append("Could not retrieve sandbox settings")

                elif tool_name == "update_sandbox_setting":
                    key = tool_input['key']
                    value = tool_input['value']
                    success, message = self.server_controller.update_sandbox_setting(key, value)
                    results.append(message)

                elif tool_name == "search_knowledge_base":
                    query = tool_input['query']
                    n_results = tool_input.get('n_results', 5)

                    search_results = self.rag_manager.search(query, n_results=n_results)

                    if search_results:
                        # Format results with relevance scores
                        formatted = f"Found {len(search_results)} results from knowledge base:\n\n"

                        for i, result in enumerate(search_results, 1):
                            formatted += f"**Result {i}** (relevance: {result['relevance']:.2f})\n"
                            formatted += f"Source: {result['metadata']['title']}\n"
                            formatted += f"{result['content']}\n\n"

                        results.append(formatted)
                    else:
                        results.append("No results found in knowledge base. Consider using search_pz_wiki as fallback.")

                elif tool_name == "search_pz_wiki":
                    query = tool_input['query']

                    wiki_content = self.wiki_scraper.search_wiki_live(query)

                    if wiki_content:
                        results.append(f"Wiki search results:\n\n{wiki_content}")
                    else:
                        results.append(f"No wiki results found for '{query}'")

                elif tool_name == "get_player_stats":
                    username = tool_input['username']

                    # Update stats from recent logs first
                    recent_logs = self.server_controller.get_recent_logs(500)
                    if recent_logs:
                        self.player_stats.update_from_logs(recent_logs)

                    # Get formatted player stats
                    stats_text = self.player_stats.format_player_stats(username)

                    if stats_text:
                        results.append(stats_text)
                    else:
                        # Check if we have ANY player data at all
                        all_stats = self.player_stats.get_all_stats()
                        if not all_stats or len(all_stats) == 0:
                            results.append(f"No player statistics available yet. No players have connected to the server or left activity in the logs.")
                        else:
                            results.append(f"No statistics found for player '{username}'. Available players: {', '.join(all_stats.keys())}")

                elif tool_name == "get_leaderboard":
                    category = tool_input['category']
                    top_n = tool_input.get('top_n', 10)

                    # Update stats from recent logs first
                    recent_logs = self.server_controller.get_recent_logs(500)
                    if recent_logs:
                        self.player_stats.update_from_logs(recent_logs)

                    # Get all leaderboards
                    leaderboards = self.player_stats.get_leaderboards()

                    if category in leaderboards:
                        # Get top N entries
                        top_entries = leaderboards[category][:top_n]

                        # Check if leaderboard is empty
                        if not top_entries or len(top_entries) == 0:
                            results.append(f"No player data available for {category.replace('_', ' ')} leaderboard. No players have connected to the server or left activity in the logs.")
                        else:
                            formatted = f"**{category.replace('_', ' ').title()} Leaderboard (Top {top_n})**\n\n"

                            for i, (player, value) in enumerate(top_entries, 1):
                                if category == 'total_playtime':
                                    # Format hours
                                    hours = value
                                    formatted += f"{i}. {player}: {hours:.1f} hours\n"
                                elif category == 'distance_traveled':
                                    # Format distance
                                    formatted += f"{i}. {player}: {value:.1f} tiles\n"
                                elif category == 'longest_life' or category == 'current_life_duration':
                                    # Format time (seconds to hours/days)
                                    hours = value / 3600
                                    if hours >= 24:
                                        days = hours / 24
                                        formatted += f"{i}. {player}: {days:.1f} days\n"
                                    else:
                                        formatted += f"{i}. {player}: {hours:.1f} hours\n"
                                elif category == 'kill_death_ratio':
                                    # Format ratio with 2 decimal places
                                    formatted += f"{i}. {player}: {value:.2f} K/D ratio\n"
                                else:
                                    formatted += f"{i}. {player}: {value}\n"

                            results.append(formatted)
                    else:
                        results.append(f"Invalid leaderboard category: {category}. Valid categories: zombies_killed, distance_traveled, buildings_placed, items_crafted, total_playtime, longest_life, current_life_duration, kill_death_ratio, most_deaths")

                elif tool_name == "get_server_summary":
                    # Update stats from recent logs first
                    recent_logs = self.server_controller.get_recent_logs(500)
                    if recent_logs:
                        self.player_stats.update_from_logs(recent_logs)

                    # Check if we have any player data at all
                    all_stats = self.player_stats.get_all_stats()

                    if not all_stats or len(all_stats) == 0:
                        results.append("No player activity data available yet. The server has no recorded player connections or activity in the logs.")
                    else:
                        # Get server summary
                        summary = self.player_stats.get_server_summary()
                        results.append(summary)

                else:
                    results.append(f"Unknown tool: {tool_name}")

            except Exception as e:
                results.append(f"Error executing {tool_name}: {str(e)}")

        return results

    async def send_long_message(self, channel, content: str):
        """Send a message, splitting it if it exceeds Discord's limit"""
        MAX_LENGTH = 2000

        if len(content) <= MAX_LENGTH:
            await channel.send(content)
        else:
            # Split into chunks
            chunks = [content[i:i+MAX_LENGTH] for i in range(0, len(content), MAX_LENGTH)]
            for chunk in chunks:
                await channel.send(chunk)

    def run_bot(self, token: str):
        """Run the Discord bot"""
        self.run(token)
