import time

DEBUG_MODE = False


def set_debug(enabled: bool):
    global DEBUG_MODE
    DEBUG_MODE = bool(enabled)


def is_debug():
    return DEBUG_MODE


def debug_log(category: str, message: str):
    """
    Prints formatted debug event information only when --debug is enabled.
    Format: [HH:MM:SS.mmm] [Category] Message
    """
    if DEBUG_MODE:
        now = time.time()
        msec = int((now - int(now)) * 1000)
        time_str = time.strftime("%H:%M:%S", time.localtime(now))
        print(f"[{time_str}.{msec:03d}] [{category}] {message}", flush=True)
