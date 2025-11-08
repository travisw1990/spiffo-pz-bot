"""Player statistics tracker with persistence"""

import json
import os
from typing import Dict, List, Optional
from datetime import datetime
from .log_parser import LogParser


class PlayerStatsTracker:
    """Track and persist player statistics over time"""

    def __init__(self, stats_file: str = "./player_stats.json"):
        """
        Initialize player stats tracker

        Args:
            stats_file: Path to JSON file for persisting stats
        """
        self.stats_file = stats_file
        self.log_parser = LogParser()
        self.stats = self._load_stats()

    def _load_stats(self) -> Dict:
        """Load stats from file"""
        if os.path.exists(self.stats_file):
            try:
                with open(self.stats_file, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def _save_stats(self):
        """Save stats to file"""
        # Convert datetime objects to strings for JSON serialization
        stats_copy = {}
        for username, data in self.stats.items():
            stats_copy[username] = data.copy()
            if 'first_seen' in stats_copy[username] and stats_copy[username]['first_seen']:
                if isinstance(stats_copy[username]['first_seen'], datetime):
                    stats_copy[username]['first_seen'] = stats_copy[username]['first_seen'].isoformat()
            if 'last_seen' in stats_copy[username] and stats_copy[username]['last_seen']:
                if isinstance(stats_copy[username]['last_seen'], datetime):
                    stats_copy[username]['last_seen'] = stats_copy[username]['last_seen'].isoformat()

            # Convert level_up timestamps
            if 'level_ups' in stats_copy[username]:
                for level_up in stats_copy[username]['level_ups']:
                    if 'timestamp' in level_up and isinstance(level_up['timestamp'], datetime):
                        level_up['timestamp'] = level_up['timestamp'].isoformat()

        with open(self.stats_file, 'w') as f:
            json.dump(stats_copy, f, indent=2)

    def update_from_logs(self, log_lines: List[str]):
        """
        Update player stats from log lines

        Args:
            log_lines: List of log lines to parse
        """
        # Parse new stats from logs
        parsed_stats = self.log_parser.parse_logs(log_lines)

        # Merge with existing stats
        for username, new_stats in parsed_stats.items():
            if username not in self.stats:
                self.stats[username] = new_stats
            else:
                # Merge stats (accumulate counts, append lists)
                existing = self.stats[username]

                existing['connections'] += new_stats['connections']
                existing['disconnections'] += new_stats['disconnections']
                existing['zombies_killed'] += new_stats['zombies_killed']
                existing['deaths'] += new_stats['deaths']
                existing['distance_traveled'] += new_stats['distance_traveled']
                existing['vehicles_entered'] += new_stats['vehicles_entered']

                existing['death_causes'].extend(new_stats['death_causes'])
                existing['level_ups'].extend(new_stats['level_ups'])
                existing['items_crafted'].extend(new_stats['items_crafted'])
                existing['buildings_placed'].extend(new_stats['buildings_placed'])
                existing['session_times'].extend(new_stats['session_times'])

                # Update first/last seen
                if new_stats['first_seen']:
                    if not existing['first_seen'] or new_stats['first_seen'] < existing['first_seen']:
                        existing['first_seen'] = new_stats['first_seen']
                if new_stats['last_seen']:
                    if not existing['last_seen'] or new_stats['last_seen'] > existing['last_seen']:
                        existing['last_seen'] = new_stats['last_seen']

        # Save updated stats
        self._save_stats()

    def get_player_stats(self, username: str) -> Optional[Dict]:
        """
        Get statistics for a specific player

        Args:
            username: Player username

        Returns:
            Player statistics dictionary or None if not found
        """
        return self.stats.get(username)

    def get_all_stats(self) -> Dict:
        """Get statistics for all players"""
        return self.stats

    def get_leaderboards(self) -> Dict[str, List]:
        """Get leaderboards across all categories"""
        return self.log_parser.get_leaderboards(self.stats)

    def get_playstyle_profiles(self) -> Dict[str, str]:
        """Get playstyle profiles for all players"""
        return self.log_parser.calculate_playstyle_profile(self.stats)

    def format_player_stats(self, username: str) -> Optional[str]:
        """
        Format player statistics for display

        Args:
            username: Player username

        Returns:
            Formatted statistics string or None if player not found
        """
        stats = self.get_player_stats(username)
        if not stats:
            return None

        return self.log_parser.format_player_stats(username, stats)

    def format_leaderboard(self, category: str, top_n: int = 10) -> str:
        """
        Format a leaderboard for display

        Args:
            category: Leaderboard category (e.g., 'zombies_killed', 'distance_traveled')
            top_n: Number of top players to show

        Returns:
            Formatted leaderboard string
        """
        leaderboards = self.get_leaderboards()

        if category not in leaderboards:
            return f"Unknown leaderboard category: {category}"

        board = leaderboards[category][:top_n]

        # Format category name
        category_names = {
            'zombies_killed': '🧟 Zombie Slayers',
            'distance_traveled': '🚶 Top Explorers',
            'buildings_placed': '🏗️ Master Builders',
            'items_crafted': '🔨 Expert Crafters',
            'total_playtime': '⏱️ Most Dedicated Players'
        }

        title = category_names.get(category, category.replace('_', ' ').title())

        lines = [f"**{title}**", ""]

        for i, (username, value) in enumerate(board, 1):
            # Format value based on category
            if category == 'total_playtime':
                hours = value / 3600
                value_str = f"{hours:.1f} hours"
            elif category == 'distance_traveled':
                value_str = f"{value} tiles"
            else:
                value_str = str(value)

            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            lines.append(f"{medal} **{username}**: {value_str}")

        return "\n".join(lines)

    def get_server_summary(self) -> str:
        """
        Get overall server statistics summary

        Returns:
            Formatted summary string
        """
        if not self.stats:
            return "No player statistics available yet."

        total_players = len(self.stats)
        total_zombies = sum(s['zombies_killed'] for s in self.stats.values())
        total_deaths = sum(s['deaths'] for s in self.stats.values())
        total_distance = sum(s['distance_traveled'] for s in self.stats.values())
        total_playtime = sum(sum(s['session_times']) for s in self.stats.values() if s['session_times'])

        # Get playstyle distribution
        profiles = self.get_playstyle_profiles()
        from collections import Counter
        profile_counts = Counter(profiles.values())

        lines = [
            "**Server Statistics Summary**",
            "",
            f"👥 Total Players: {total_players}",
            f"🧟 Total Zombies Killed: {total_zombies}",
            f"💀 Total Deaths: {total_deaths}",
            f"🚶 Total Distance Traveled: {total_distance} tiles",
            f"⏱️ Total Playtime: {total_playtime / 3600:.1f} hours",
            "",
            "**Playstyle Distribution:**"
        ]

        for profile, count in profile_counts.most_common():
            lines.append(f"  • {profile}: {count} player(s)")

        return "\n".join(lines)

    def analyze_for_mod_recommendations(self) -> Dict[str, float]:
        """
        Analyze player behavior to generate mod recommendation scores

        Returns:
            Dictionary of mod categories with confidence scores (0-1)
        """
        if not self.stats:
            return {}

        # Calculate aggregate metrics
        total_zombies = sum(s['zombies_killed'] for s in self.stats.values())
        total_buildings = sum(len(s['buildings_placed']) for s in self.stats.values())
        total_crafts = sum(len(s['items_crafted']) for s in self.stats.values())
        total_distance = sum(s['distance_traveled'] for s in self.stats.values())
        total_vehicles = sum(s['vehicles_entered'] for s in self.stats.values())
        total_deaths = sum(s['deaths'] for s in self.stats.values())

        num_players = len(self.stats)
        avg_zombies = total_zombies / num_players if num_players > 0 else 0
        avg_buildings = total_buildings / num_players if num_players > 0 else 0
        avg_crafts = total_crafts / num_players if num_players > 0 else 0

        # Calculate mod category scores (0-1 scale)
        recommendations = {}

        # Combat/Zombie mods - high if lots of zombie kills
        recommendations['combat'] = min(1.0, avg_zombies / 100)

        # Building/Construction mods - high if lots of building activity
        recommendations['building'] = min(1.0, avg_buildings / 50)

        # Crafting/Recipe mods - high if lots of crafting
        recommendations['crafting'] = min(1.0, avg_crafts / 100)

        # Vehicle mods - high if lots of vehicle usage
        recommendations['vehicles'] = min(1.0, total_vehicles / (num_players * 10))

        # Exploration/Map mods - high if lots of travel
        recommendations['exploration'] = min(1.0, total_distance / (num_players * 1000))

        # Difficulty/Hardcore mods - high if players dying frequently (experienced players)
        recommendations['difficulty'] = min(1.0, total_deaths / (num_players * 3))

        return recommendations
