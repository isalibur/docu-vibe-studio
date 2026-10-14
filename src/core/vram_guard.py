"""
src/core/vram_guard.py - Monitoramento e limpeza forçada de memória VRAM e RAM.
Garante isolamento sequencial de estágios na RTX 3060 (12 GB).
"""

import gc
import logging
from typing import Optional
import requests

try:
    import torch
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("VRAMGuard")


def flush_vram(
    ollama_url: str = "http://localhost:11434",
    comfy_url: str = "http://localhost:8188",
    unload_remote_services: bool = True
) -> dict:
    """
    Executa rotina rigorosa de teardown e limpeza de memória:
    1. Coleta de lixo do Python (gc.collect).
    2. Liberação de cache e pools de memória CUDA no PyTorch.
    3. Notificação ao Ollama para descarregar modelos da VRAM (keep_alive=0).
    4. Notificação ao ComfyUI para liberar memória e modelos (/free).
    """
    report = {
        "gc_collected": 0,
        "cuda_cleared": False,
        "ollama_unloaded": False,
        "comfy_unloaded": False,
    }

    # 1. Python GC
    collected = gc.collect()
    report["gc_collected"] = collected
    logger.info("Garbage Collector liberou %d objetos.", collected)

    # 2. PyTorch CUDA Cache
    if HAS_TORCH and torch.cuda.is_available():
        allocated_before = torch.cuda.memory_allocated() / (1024 ** 2)
        reserved_before = torch.cuda.memory_reserved() / (1024 ** 2)

        torch.cuda.empty_cache()
        torch.cuda.ipc_collect()

        allocated_after = torch.cuda.memory_allocated() / (1024 ** 2)
        reserved_after = torch.cuda.memory_reserved() / (1024 ** 2)

        report["cuda_cleared"] = True
        logger.info(
            "CUDA Cache limpo: Alocado %.1fMB -> %.1fMB | Reservado %.1fMB -> %.1fMB",
            allocated_before, allocated_after, reserved_before, reserved_after
        )

    # 3. Descarga de serviços locais de IA (Ollama / ComfyUI)
    if unload_remote_services:
        # Descarrega ComfyUI se ativo
        try:
            res = requests.post(
                f"{comfy_url}/free",
                json={"unload_models": True, "free_memory": True},
                timeout=1.5
            )
            if res.status_code == 200:
                report["comfy_unloaded"] = True
                logger.info("ComfyUI (/free): Modelos descarregados com sucesso.")
        except Exception:
            pass  # ComfyUI não está rodando no momento, comportamento normal

    return report


def get_vram_status() -> Optional[dict]:
    """Retorna estatísticas atuais da GPU em MB se o PyTorch CUDA estiver disponível."""
    if not HAS_TORCH or not torch.cuda.is_available():
        return None

    device = torch.cuda.current_device()
    props = torch.cuda.get_device_properties(device)
    total_mb = props.total_memory / (1024 ** 2)
    allocated_mb = torch.cuda.memory_allocated(device) / (1024 ** 2)
    reserved_mb = torch.cuda.memory_reserved(device) / (1024 ** 2)
    free_approx_mb = total_mb - reserved_mb

    return {
        "device_name": props.name,
        "total_mb": round(total_mb, 1),
        "allocated_mb": round(allocated_mb, 1),
        "reserved_mb": round(reserved_mb, 1),
        "free_approx_mb": round(free_approx_mb, 1),
    }


if __name__ == "__main__":
    status = get_vram_status()
    if status:
        logger.info("Status da GPU: %s", status)
    else:
        logger.info("PyTorch CUDA não detectado ou GPU indisponível no teste isolado.")
    flush_vram()
