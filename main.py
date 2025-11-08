#!/usr/bin/env python3
"""
Project Zomboid Discord Bot
AI-powered bot for managing Project Zomboid servers
"""

import os
from dotenv import load_dotenv
from bot.discord_client import PZDiscordBot


def main():
    """Main entry point"""
    # Load environment variables
    load_dotenv()

    # Get required configuration
    discord_token = os.getenv('DISCORD_BOT_TOKEN')
    claude_api_key = os.getenv('ANTHROPIC_API_KEY')

    # FTP configuration
    ftp_host = os.getenv('FTP_HOST')
    ftp_port = int(os.getenv('FTP_PORT', 21))
    ftp_user = os.getenv('FTP_USER')
    ftp_password = os.getenv('FTP_PASSWORD')

    # Validate configuration
    if not discord_token:
        print("ERROR: DISCORD_BOT_TOKEN not set in .env file")
        return

    if not claude_api_key:
        print("ERROR: ANTHROPIC_API_KEY not set in .env file")
        return

    if not all([ftp_host, ftp_user, ftp_password]):
        print("ERROR: FTP credentials not properly configured in .env file")
        return

    # Create and run bot
    print("Starting Project Zomboid Discord Bot...")
    print(f"FTP Host: {ftp_host}:{ftp_port}")
    print(f"FTP User: {ftp_user}")
    print("-" * 50)

    bot = PZDiscordBot(
        claude_api_key=claude_api_key,
        ftp_host=ftp_host,
        ftp_port=ftp_port,
        ftp_user=ftp_user,
        ftp_password=ftp_password
    )

    try:
        bot.run_bot(discord_token)
    except KeyboardInterrupt:
        print("\nShutting down bot...")
    except Exception as e:
        print(f"Error running bot: {e}")


if __name__ == "__main__":
    main()
