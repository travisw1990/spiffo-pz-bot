"""Log parser for extracting player statistics from PZ server logs"""

import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from collections import defaultdict


class LogParser:
    """Parse Project Zomboid server logs to extract player statistics"""

    # Log patterns for different events (Indifferent Broccoli format)
    # Format: LOG  : Type, epoch> epoch> [YY-MM-DD HH:MM:SS.mmm] > message
    PATTERNS = {
        # Player connected: look for "fully-connected" event with username
        'player_connect': r'\[(?P<timestamp>[\d\-: \.]+)\].*?ConnectionManager:\s+\[fully-connected\].*?username="(?P<username>[^"]+)"',

        # Player disconnected: "Disconnected player "Name" steamid" (timestamp optional)
        'player_disconnect': r'Disconnected player "(?P<username>[^"]+)"',

        # Zombie killed - these may not be in logs, patterns kept for future
        'zombie_killed': r'\[(?P<timestamp>[\d\-: \.]+)\].*?(?P<username>\w+) killed a zombie',
        'player_death': r'\[(?P<timestamp>[\d\-: \.]+)\].*?(?P<username>\w+) died',
        'distance_traveled': r'\[(?P<timestamp>[\d\-: \.]+)\].*?(?P<username>\w+) traveled (?P<distance>\d+) tiles',
        'level_up': r'\[(?P<timestamp>[\d\-: \.]+)\].*?(?P<username>\w+) reached level (?P<level>\d+) in (?P<skill>\w+)',
        'item_crafted': r'\[(?P<timestamp>[\d\-: \.]+)\].*?(?P<username>\w+) crafted (?P<item>[\w\s]+)',
        'vehicle_entered': r'\[(?P<timestamp>[\d\-: \.]+)\].*?(?P<username>\w+) entered vehicle',
        'building_placed': r'\[(?P<timestamp>[\d\-: \.]+)\].*?(?P<username>\w+) placed (?P<building>[\w\s]+)',
    }

    def __init__(self):
        """Initialize log parser"""
        self.compiled_patterns = {
            name: re.compile(pattern, re.IGNORECASE)
            for name, pattern in self.PATTERNS.items()
        }

    def parse_logs(self, log_lines: List[str]) -> Dict[str, Dict]:
        """
        Parse log lines and extract player statistics

        Args:
            log_lines: List of log lines to parse

        Returns:
            Dict mapping username to their statistics
        """
        player_stats = defaultdict(lambda: {
            # Lifetime totals (never reset)
            'lifetime_zombies_killed': 0,
            'lifetime_distance_traveled': 0,
            'lifetime_items_crafted': [],
            'lifetime_buildings_placed': [],

            # Current life stats (reset on death)
            'current_life_zombies_killed': 0,
            'current_life_distance_traveled': 0,
            'current_life_items_crafted': [],
            'current_life_buildings_placed': [],
            'current_life_start': None,

            # Legacy/combined stats
            'connections': 0,
            'disconnections': 0,
            'zombies_killed': 0,  # For backward compatibility
            'deaths': 0,
            'death_causes': [],
            'death_timestamps': [],
            'distance_traveled': 0,  # For backward compatibility
            'level_ups': [],
            'items_crafted': [],  # For backward compatibility
            'vehicles_entered': 0,
            'buildings_placed': [],  # For backward compatibility
            'first_seen': None,
            'last_seen': None,
            'last_death': None,
            'session_times': [],

            # Survival streak tracking
            'lives': [],  # List of {start, end, duration, zombies_killed, etc.}
        })

        session_starts = {}  # Track session start times

        for line in log_lines:
            # Check each pattern
            for event_type, pattern in self.compiled_patterns.items():
                match = pattern.search(line)

                if match:
                    data = match.groupdict()
                    username = data.get('username')
                    timestamp_str = data.get('timestamp')

                    if not username:
                        continue

                    # Parse timestamp - try multiple formats
                    timestamp = None
                    if timestamp_str:
                        # Try DD-MM-YY HH:MM:SS.mmm format (Indifferent Broccoli)
                        try:
                            # Format: 15-11-25 21:50:40.485 (DD-MM-YY HH:MM:SS.mmm)
                            # Remove milliseconds and parse
                            timestamp = datetime.strptime(timestamp_str.split('.')[0], '%d-%m-%y %H:%M:%S')
                        except:
                            # Try YYYY-MM-DD HH:MM:SS format (standard)
                            try:
                                timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                            except:
                                timestamp = None

                    # Update first/last seen
                    if timestamp:
                        if player_stats[username]['first_seen'] is None:
                            player_stats[username]['first_seen'] = timestamp
                        player_stats[username]['last_seen'] = timestamp

                    # Handle specific events
                    if event_type == 'player_connect':
                        player_stats[username]['connections'] += 1
                        session_starts[username] = timestamp

                        # Initialize current life start if not set
                        if player_stats[username]['current_life_start'] is None:
                            player_stats[username]['current_life_start'] = timestamp

                    elif event_type == 'player_disconnect':
                        player_stats[username]['disconnections'] += 1
                        if username in session_starts and timestamp:
                            session_duration = (timestamp - session_starts[username]).total_seconds()
                            player_stats[username]['session_times'].append(session_duration)
                            del session_starts[username]

                    elif event_type == 'zombie_killed':
                        player_stats[username]['zombies_killed'] += 1
                        player_stats[username]['lifetime_zombies_killed'] += 1
                        player_stats[username]['current_life_zombies_killed'] += 1

                    elif event_type == 'player_death':
                        player_stats[username]['deaths'] += 1
                        player_stats[username]['death_timestamps'].append(timestamp)
                        player_stats[username]['last_death'] = timestamp

                        # Try to extract death cause from line
                        cause = self._extract_death_cause(line)
                        player_stats[username]['death_causes'].append(cause)

                        # Save current life to history
                        if player_stats[username]['current_life_start']:
                            life_duration = (timestamp - player_stats[username]['current_life_start']).total_seconds() if timestamp else 0
                            player_stats[username]['lives'].append({
                                'start': player_stats[username]['current_life_start'],
                                'end': timestamp,
                                'duration': life_duration,
                                'zombies_killed': player_stats[username]['current_life_zombies_killed'],
                                'distance_traveled': player_stats[username]['current_life_distance_traveled'],
                                'items_crafted': len(player_stats[username]['current_life_items_crafted']),
                                'buildings_placed': len(player_stats[username]['current_life_buildings_placed']),
                                'death_cause': cause,
                            })

                        # Reset current life stats
                        player_stats[username]['current_life_zombies_killed'] = 0
                        player_stats[username]['current_life_distance_traveled'] = 0
                        player_stats[username]['current_life_items_crafted'] = []
                        player_stats[username]['current_life_buildings_placed'] = []
                        player_stats[username]['current_life_start'] = timestamp

                    elif event_type == 'distance_traveled':
                        distance = int(data.get('distance', 0))
                        player_stats[username]['distance_traveled'] += distance
                        player_stats[username]['lifetime_distance_traveled'] += distance
                        player_stats[username]['current_life_distance_traveled'] += distance

                    elif event_type == 'level_up':
                        player_stats[username]['level_ups'].append({
                            'skill': data.get('skill'),
                            'level': int(data.get('level', 0)),
                            'timestamp': timestamp
                        })

                    elif event_type == 'item_crafted':
                        item = data.get('item')
                        player_stats[username]['items_crafted'].append(item)
                        player_stats[username]['lifetime_items_crafted'].append(item)
                        player_stats[username]['current_life_items_crafted'].append(item)

                    elif event_type == 'vehicle_entered':
                        player_stats[username]['vehicles_entered'] += 1

                    elif event_type == 'building_placed':
                        building = data.get('building')
                        player_stats[username]['buildings_placed'].append(building)
                        player_stats[username]['lifetime_buildings_placed'].append(building)
                        player_stats[username]['current_life_buildings_placed'].append(building)

        return dict(player_stats)

    def _extract_death_cause(self, log_line: str) -> str:
        """
        Extract death cause from log line

        Args:
            log_line: Log line containing death information

        Returns:
            Death cause string
        """
        # Common death causes
        causes = {
            'zombie': 'Zombie',
            'starvation': 'Starvation',
            'dehydration': 'Dehydration',
            'bleeding': 'Blood Loss',
            'infection': 'Infection',
            'fall': 'Fall Damage',
            'fire': 'Fire',
            'vehicle': 'Vehicle Accident',
        }

        log_lower = log_line.lower()
        for keyword, cause in causes.items():
            if keyword in log_lower:
                return cause

        return 'Unknown'

    def calculate_playstyle_profile(self, player_stats: Dict) -> Dict[str, str]:
        """
        Analyze player stats to determine playstyle profiles

        Args:
            player_stats: Dictionary of player statistics

        Returns:
            Dictionary mapping username to playstyle category
        """
        profiles = {}

        for username, stats in player_stats.items():
            # Calculate various metrics
            zombies_killed = stats['zombies_killed']
            distance = stats['distance_traveled']
            buildings = len(stats['buildings_placed'])
            crafts = len(stats['items_crafted'])
            deaths = stats['deaths']

            # Determine dominant playstyle
            if zombies_killed > 50 and zombies_killed > distance / 10:
                profile = 'Combat-Focused Fighter'
            elif distance > 1000 and distance > zombies_killed * 10:
                profile = 'Explorer/Looter'
            elif buildings > 20 or crafts > 50:
                profile = 'Builder/Crafter'
            elif deaths > 5:
                profile = 'High-Risk Player'
            elif stats['connections'] > 10:
                profile = 'Regular Player'
            else:
                profile = 'Casual Survivor'

            profiles[username] = profile

        return profiles

    def get_leaderboards(self, player_stats: Dict) -> Dict[str, List[Tuple[str, int]]]:
        """
        Generate leaderboards from player statistics

        Args:
            player_stats: Dictionary of player statistics

        Returns:
            Dictionary of leaderboards (category -> sorted player list)
        """
        leaderboards = {}

        # Zombies killed leaderboard
        leaderboards['zombies_killed'] = sorted(
            [(username, stats['zombies_killed']) for username, stats in player_stats.items()],
            key=lambda x: x[1],
            reverse=True
        )

        # Distance traveled leaderboard
        leaderboards['distance_traveled'] = sorted(
            [(username, stats['distance_traveled']) for username, stats in player_stats.items()],
            key=lambda x: x[1],
            reverse=True
        )

        # Buildings placed leaderboard
        leaderboards['buildings_placed'] = sorted(
            [(username, len(stats['buildings_placed'])) for username, stats in player_stats.items()],
            key=lambda x: x[1],
            reverse=True
        )

        # Items crafted leaderboard
        leaderboards['items_crafted'] = sorted(
            [(username, len(stats['items_crafted'])) for username, stats in player_stats.items()],
            key=lambda x: x[1],
            reverse=True
        )

        # Total playtime leaderboard (sum of session times)
        leaderboards['total_playtime'] = sorted(
            [(username, sum(stats['session_times'])) for username, stats in player_stats.items()],
            key=lambda x: x[1],
            reverse=True
        )

        # Longest life leaderboard (best survival streak)
        longest_lives = []
        for username, stats in player_stats.items():
            if stats['lives']:
                longest = max(stats['lives'], key=lambda x: x['duration'])
                longest_lives.append((username, longest['duration']))
            elif stats['current_life_start']:  # Current life might be longest
                from datetime import datetime
                current_duration = (datetime.now() - stats['current_life_start']).total_seconds() if stats['current_life_start'] else 0
                longest_lives.append((username, current_duration))

        leaderboards['longest_life'] = sorted(longest_lives, key=lambda x: x[1], reverse=True)

        # Current life duration leaderboard
        current_lives = []
        for username, stats in player_stats.items():
            if stats['current_life_start']:
                from datetime import datetime
                duration = (datetime.now() - stats['current_life_start']).total_seconds()
                current_lives.append((username, duration))

        leaderboards['current_life_duration'] = sorted(current_lives, key=lambda x: x[1], reverse=True)

        # Kill-to-death ratio leaderboard
        kd_ratios = []
        for username, stats in player_stats.items():
            deaths = stats['deaths'] if stats['deaths'] > 0 else 1  # Avoid division by zero
            ratio = stats['zombies_killed'] / deaths
            kd_ratios.append((username, ratio))

        leaderboards['kill_death_ratio'] = sorted(kd_ratios, key=lambda x: x[1], reverse=True)

        # Most deaths leaderboard (Hall of Shame)
        leaderboards['most_deaths'] = sorted(
            [(username, stats['deaths']) for username, stats in player_stats.items()],
            key=lambda x: x[1],
            reverse=True
        )

        return leaderboards

    def format_player_stats(self, username: str, stats: Dict) -> str:
        """
        Format player statistics for display

        Args:
            username: Player username
            stats: Player statistics dictionary

        Returns:
            Formatted string
        """
        # Calculate current life duration
        current_life_duration = ""
        if stats.get('current_life_start'):
            from datetime import datetime
            duration_seconds = (datetime.now() - stats['current_life_start']).total_seconds()
            hours = duration_seconds / 3600
            if hours >= 24:
                days = hours / 24
                current_life_duration = f" ({days:.1f} days)"
            else:
                current_life_duration = f" ({hours:.1f} hours)"

        # Calculate longest life
        longest_life_str = ""
        if stats.get('lives'):
            longest = max(stats['lives'], key=lambda x: x['duration'])
            longest_hours = longest['duration'] / 3600
            if longest_hours >= 24:
                longest_days = longest_hours / 24
                longest_life_str = f"{longest_days:.1f} days"
            else:
                longest_life_str = f"{longest_hours:.1f} hours"

        lines = [
            f"**{username}'s Statistics**",
            "",
            "**Current Life:**",
            f"🧟 Zombies Killed: {stats.get('current_life_zombies_killed', 0)}",
            f"🚶 Distance Traveled: {stats.get('current_life_distance_traveled', 0)} tiles",
            f"🔨 Items Crafted: {len(stats.get('current_life_items_crafted', []))}",
            f"🏗️ Buildings Placed: {len(stats.get('current_life_buildings_placed', []))}",
            f"⏱️  Survival Time: {current_life_duration.strip() if current_life_duration else '0 hours'}",
            "",
            "**Lifetime Totals:**",
            f"🧟 Zombies Killed: {stats.get('lifetime_zombies_killed', stats['zombies_killed'])}",
            f"🚶 Distance Traveled: {stats.get('lifetime_distance_traveled', stats['distance_traveled'])} tiles",
            f"💀 Deaths: {stats['deaths']}",
            f"🔨 Items Crafted: {len(stats.get('lifetime_items_crafted', stats['items_crafted']))}",
            f"🏗️ Buildings Placed: {len(stats.get('lifetime_buildings_placed', stats['buildings_placed']))}",
            f"🚗 Vehicles Used: {stats['vehicles_entered']}",
            f"🔄 Sessions: {stats['connections']}",
        ]

        # Add longest life if available
        if longest_life_str:
            lines.append(f"🏆 Longest Life: {longest_life_str}")

        # Add total playtime if available
        if stats['session_times']:
            total_hours = sum(stats['session_times']) / 3600
            lines.append(f"⏱️ Total Playtime: {total_hours:.1f} hours")

        # Add skill levels if available
        if stats['level_ups']:
            lines.append("\n**Skill Levels:**")
            skill_levels = {}
            for level_up in stats['level_ups']:
                skill = level_up['skill']
                level = level_up['level']
                if skill not in skill_levels or level > skill_levels[skill]:
                    skill_levels[skill] = level

            for skill, level in sorted(skill_levels.items(), key=lambda x: x[1], reverse=True)[:5]:
                lines.append(f"  • {skill}: Level {level}")

        # Add most common death cause
        if stats['death_causes']:
            from collections import Counter
            most_common = Counter(stats['death_causes']).most_common(1)[0]
            lines.append(f"\n⚠️ Most Common Death: {most_common[0]} ({most_common[1]}x)")

        return "\n".join(lines)
