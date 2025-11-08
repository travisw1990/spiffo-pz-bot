#!/usr/bin/env python3
"""Test network connectivity from inside Docker container"""

import socket
import os

host = os.getenv('FTP_HOST', '172.240.71.175')
game_port = int(os.getenv('PZ_GAME_PORT', 27325))

print('Testing connectivity from Docker container')
print('=' * 60)
print(f'Target host: {host}')
print(f'Game port: {game_port}')
print('=' * 60)

# Test game port
print(f'\n[Test 1] Game port {host}:{game_port}')
try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(5)
    result = sock.connect_ex((host, game_port))
    sock.close()
    if result == 0:
        print(f'  ✓ Game port {game_port} is OPEN (can connect)')
    else:
        print(f'  ✗ Game port {game_port} is CLOSED/UNREACHABLE')
        print(f'    Error code: {result}')
        if result == 111:
            print(f'    (111 = Connection refused - port not listening)')
        elif result == 110:
            print(f'    (110 = Connection timed out - firewall/network issue)')
except Exception as e:
    print(f'  ✗ Exception: {e}')

# Test FTP port for comparison
print(f'\n[Test 2] FTP port {host}:21')
try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(5)
    result = sock.connect_ex((host, 21))
    sock.close()
    if result == 0:
        print(f'  ✓ FTP port 21 is OPEN (can connect)')
    else:
        print(f'  ✗ FTP port 21 is CLOSED/UNREACHABLE')
        print(f'    Error code: {result}')
except Exception as e:
    print(f'  ✗ Exception: {e}')

# Test DNS resolution
print(f'\n[Test 3] DNS resolution for {host}')
try:
    result = socket.gethostbyname(host)
    print(f'  ✓ Resolved to: {result}')
except Exception as e:
    print(f'  ✗ DNS error: {e}')

# Show container's network info
print(f'\n[Test 4] Container network information')
try:
    hostname = socket.gethostname()
    print(f'  Container hostname: {hostname}')

    # Get container's IP
    import subprocess
    result = subprocess.run(['hostname', '-I'], capture_output=True, text=True)
    if result.returncode == 0:
        print(f'  Container IP(s): {result.stdout.strip()}')
except Exception as e:
    print(f'  Could not get network info: {e}')

# Test alternate port check method
print(f'\n[Test 5] Alternative connection test (with actual connect)')
try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(5)
    sock.connect((host, game_port))
    print(f'  ✓ Successfully connected to game port!')
    sock.close()
except socket.timeout:
    print(f'  ✗ Connection timed out (firewall or network filtering)')
except ConnectionRefusedError:
    print(f'  ✗ Connection refused (port not listening or server offline)')
except Exception as e:
    print(f'  ✗ Error: {type(e).__name__}: {e}')

print('\n' + '=' * 60)
print('Summary:')
print('  - If game port shows "Connection refused": Server is likely offline')
print('  - If game port shows "Connection timed out": Network/firewall issue')
print('  - If FTP works but game port doesn\'t: Different issue with game server')
print('=' * 60)
