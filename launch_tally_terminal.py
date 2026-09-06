"""Launch Tally's local OpenClaw terminal with the key from approved .env."""
import os
import subprocess
from pathlib import Path

ENV = Path.home() / '.hermes' / '.env'
for line in ENV.read_text(encoding='utf-8-sig').splitlines():
    if line.startswith('OPENROUTER_API_KEY='):
        os.environ['OPENROUTER_API_KEY'] = line.split('=', 1)[1]
        break
else:
    raise SystemExit('OPENROUTER_API_KEY is not configured')

subprocess.run(['openclaw', '--profile', 'avengers-free', 'terminal', '--local'], check=False)
