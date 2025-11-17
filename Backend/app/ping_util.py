import platform
import subprocess
from typing import Tuple


# PUBLIC_INTERFACE
def ping_host(ip: str, timeout_seconds: int = 2) -> Tuple[bool, str]:
    """Ping a host in a platform-aware way with timeout.

    Args:
        ip: IPv4 address to ping.
        timeout_seconds: Timeout in seconds.

    Returns:
        (reachable, note): reachable True/False and a note string (possibly 'unknown').
    """
    system = platform.system().lower()
    # Construct ping command
    count_flag = "-n" if system == "windows" else "-c"
    timeout_flag = "-w" if system == "windows" else "-W"
    cmd = ["ping", count_flag, "1", timeout_flag, str(timeout_seconds), ip]

    try:
        proc = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout_seconds + 1
        )
        success = proc.returncode == 0
        return success, "ok" if success else "timeout" if "timed out" in (proc.stderr or "").lower() else "unreachable"
    except FileNotFoundError:
        # ping binary not available in environment
        return False, "ping-not-available"
    except subprocess.TimeoutExpired:
        return False, "timeout"
    except Exception as exc:
        # Any unexpected error - report unknown
        return False, f"error:{type(exc).__name__}"
