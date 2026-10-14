"""
src/ui/server.py - Servidor Web Backend FastAPI para a interface gráfica do Docu-Vibe Studio.
Permite criar projetos, disparar a produção em tempo real, gerenciar mídias locais e monitorar a VRAM.
"""

import asyncio
from pathlib import Path
from typing import Optional, List
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
import logging

from src.core.manifest import ProjectManifest
from src.core.vram_guard import get_vram_status
import main as orchestrator

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("DocuVibeServer")

app = FastAPI(title="Docu-Vibe Studio API", version="2.0.0")

# Monta arquivos estáticos do frontend
STATIC_DIR = Path("src/ui/static")
STATIC_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Monta diretório workspace para servir vídeos e assets gerados
WORKSPACE_DIR = Path("workspace")
WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/workspace", StaticFiles(directory=str(WORKSPACE_DIR)), name="workspace")


class GenerationRequest(BaseModel):
    topic: str
    project_id: Optional[str] = None
    tone: Optional[str] = "investigative"
    voice: Optional[str] = "pt-BR-ThalitaMultilingualNeural"
    remove_silence: bool = True
    local_assets_folder: Optional[str] = None
    export_kdenlive: bool = True


# Estado em memória do progresso da geração
generation_state = {
    "status": "idle",
    "project_id": None,
    "current_stage": None,
    "progress_percent": 0,
    "log_message": "Pronto para criar novo documentário.",
    "final_video_url": None,
    "otio_url": None,
}


class ApiKeysRequest(BaseModel):
    gemini_key: Optional[str] = None
    groq_key: Optional[str] = None


def run_pipeline_task(req: GenerationRequest):
    global generation_state
    try:
        generation_state["status"] = "processing"
        generation_state["progress_percent"] = 10
        generation_state["log_message"] = "Escrevendo roteiro investigativo..."

        # Executa o pipeline orquestrado com todas as preferências do usuário
        orchestrator.run_pipeline(
            topic=req.topic,
            project_id=req.project_id,
            voice=req.voice,
            tone=req.tone,
            local_assets_folder=req.local_assets_folder
        )

        project_slug = req.project_id or f"doc_{abs(hash(req.topic)) % 100000}"
        video_path = f"/workspace/{project_slug}/output/{project_slug}_MASTER.mp4"
        otio_path = f"/workspace/{project_slug}/output/{project_slug}_timeline.otio"

        generation_state["status"] = "completed"
        generation_state["progress_percent"] = 100
        generation_state["log_message"] = "Documentário masterizado com sucesso!"
        generation_state["final_video_url"] = video_path
        generation_state["otio_url"] = otio_path
        generation_state["project_id"] = project_slug
    except Exception as e:
        logger.error("Erro durante a geração: %s", str(e), exc_info=True)
        generation_state["status"] = "error"
        generation_state["log_message"] = f"Erro: {str(e)}"


@app.get("/api/settings/keys")
def get_api_keys_status():
    import os
    from dotenv import load_dotenv
    load_dotenv(override=True)
    return {
        "has_gemini": bool(os.getenv("GEMINI_API_KEY")),
        "has_groq": bool(os.getenv("GROQ_API_KEY")),
    }


@app.post("/api/settings/keys")
def save_api_keys(req: ApiKeysRequest):
    import os
    env_path = Path(".env")
    lines = []
    if env_path.exists():
        lines = env_path.read_text(encoding="utf-8").splitlines()
    
    env_dict = {}
    for line in lines:
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            env_dict[k.strip()] = v.strip().strip('"').strip("'")
            
    if req.gemini_key is not None:
        env_dict["GEMINI_API_KEY"] = req.gemini_key.strip()
        os.environ["GEMINI_API_KEY"] = req.gemini_key.strip()
    if req.groq_key is not None:
        env_dict["GROQ_API_KEY"] = req.groq_key.strip()
        os.environ["GROQ_API_KEY"] = req.groq_key.strip()

    new_content = [
        "# Docu-Vibe Studio Environment",
        f'GEMINI_API_KEY="{env_dict.get("GEMINI_API_KEY", "")}"',
        f'GROQ_API_KEY="{env_dict.get("GROQ_API_KEY", "")}"',
        f'PEXELS_API_KEY="{env_dict.get("PEXELS_API_KEY", "")}"',
        f'PIXABAY_API_KEY="{env_dict.get("PIXABAY_API_KEY", "")}"',
    ]
    env_path.write_text("\n".join(new_content) + "\n", encoding="utf-8")
    return {"message": "Chaves salvas com sucesso no .env"}


@app.get("/", response_class=HTMLResponse)
def get_index():
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return index_file.read_text(encoding="utf-8")
    return "<h1>Docu-Vibe Studio: Carregando frontend...</h1>"


@app.get("/api/status")
def get_status():
    vram = get_vram_status()
    return {
        "generation": generation_state,
        "hardware": {
            "vram": vram,
            "encoder": "NVENC H.264 Ativo"
        }
    }


@app.post("/api/generate")
def start_generation(req: GenerationRequest, background_tasks: BackgroundTasks):
    global generation_state
    if generation_state["status"] == "processing":
        raise HTTPException(status_code=400, detail="Já existe um documentário em processamento.")

    project_slug = req.project_id or f"doc_{abs(hash(req.topic)) % 100000}"
    generation_state["project_id"] = project_slug
    generation_state["status"] = "queued"
    generation_state["progress_percent"] = 5
    generation_state["log_message"] = "Iniciando esteira de produção..."
    generation_state["final_video_url"] = None

    background_tasks.add_task(run_pipeline_task, req)
    return {"message": "Produção iniciada em segundo plano", "project_id": project_slug}


@app.get("/api/projects")
def list_projects():
    projects = []
    if WORKSPACE_DIR.exists():
        for p in WORKSPACE_DIR.iterdir():
            if p.is_dir() and (p / "project_manifest.json").exists():
                try:
                    manifest = ProjectManifest.load(p / "project_manifest.json")
                    projects.append({
                        "project_id": manifest.project_id,
                        "title": manifest.title,
                        "scenes_count": len(manifest.scenes),
                        "has_final_video": bool(manifest.final_video_path and Path(manifest.final_video_path).exists()),
                        "video_url": f"/workspace/{manifest.project_id}/output/{manifest.project_id}_MASTER.mp4"
                    })
                except Exception:
                    pass
    return projects


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.ui.server:app", host="127.0.0.1", port=8000, reload=False)
