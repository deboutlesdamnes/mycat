# executor.py
import subprocess
import tempfile
import os


def run_code(code: str, timeout: int = 30) -> dict:
    """Run code in a subprocess and capture output. Not a real sandbox — fine for trusted code."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(code)
        path = f.name
    try:
        result = subprocess.run(
            ['python', path],
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return {
            'stdout': result.stdout,
            'stderr': result.stderr,
            'returncode': result.returncode,
            'timed_out': False
        }
    except subprocess.TimeoutExpired:
        return {'stdout': '', 'stderr': 'TIMEOUT', 'returncode': -1, 'timed_out': True}
    finally:
        os.unlink(path)