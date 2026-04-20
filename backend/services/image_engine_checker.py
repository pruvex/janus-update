import asyncio
import aiohttp
import os
import subprocess
import time
import logging

GPU_PATH = r"C:\KI\Janus-Image-Engine\main.py"
CPU_PATH = r"C:\KI\Janus-Image-Engine-CPU"

logger = logging.getLogger("janus_backend")

_engine_process = None
_last_used_time = 0.0


def has_nvidia_gpu() -> bool:
    try:
        subprocess.check_output(["nvidia-smi"], stderr=subprocess.DEVNULL)
        return True
    except Exception:
        return False


async def get_engine_type_and_status():
    is_gpu_installed = os.path.exists(GPU_PATH) and has_nvidia_gpu()
    is_cpu_installed = os.path.exists(CPU_PATH)
    engine_type = "none"
    if is_gpu_installed:
        engine_type = "gpu"
    elif is_cpu_installed:
        engine_type = "cpu"

    is_running = False
    if engine_type != "none":
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get("http://127.0.0.1:8188/", timeout=2) as resp:
                    is_running = resp.status == 200
        except Exception:
            is_running = False

    return {"engine_type": engine_type, "is_running": is_running}


def _touch_last_used() -> None:
    global _last_used_time
    _last_used_time = time.time()


async def is_local_engine_ready() -> bool:
    status = await get_engine_type_and_status()
    ready = status.get("engine_type") != "none" and status.get("is_running")
    if ready:
        _touch_last_used()
    return ready


def start_engine_process(script_path: str):
    global _engine_process
    abs_path = os.path.abspath(script_path)
    logger.info("start_engine_process: %s", abs_path)
    cwd = os.path.dirname(abs_path)
    _engine_process = subprocess.Popen(
        ["cmd.exe", "/c", abs_path],
        cwd=cwd,
        shell=False,
    )
    _touch_last_used()
    return _engine_process


def stop_engine_process() -> None:
    global _engine_process, _last_used_time
    if _engine_process:
        logger.info("stop_engine_process: Terminating engine")
        try:
            subprocess.run(
                ["taskkill", "/PID", str(_engine_process.pid), "/T", "/F"],
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except Exception:
            _engine_process.terminate()
        _engine_process = None
        _last_used_time = 0.0


async def idle_shutdown_worker():
    global _last_used_time
    while True:
        await asyncio.sleep(60)
        if _last_used_time == 0.0:
            continue
        if time.time() - _last_used_time > 300:
            if await is_local_engine_ready():
                logger.info("IDLE-SHUTDOWN: Stoppe inaktive Bild-Engine.")
                stop_engine_process()
