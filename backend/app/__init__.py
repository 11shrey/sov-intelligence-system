"""SOV Intelligence System Backend Application Package."""

from pathlib import Path

try:
    from dotenv import load_dotenv, find_dotenv

    _env_file = find_dotenv(usecwd=True)
    if _env_file:
        load_dotenv(_env_file)
    else:
        _root_env = Path(__file__).resolve().parent.parent.parent / ".env"
        if _root_env.exists():
            load_dotenv(_root_env)
except ImportError:
    pass

