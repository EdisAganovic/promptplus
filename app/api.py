"""
app/api.py - FastAPI Web Server
================================
Routes:
- GET  /                  -> Home page (list prompts)
- POST /add               -> Add new prompt (keyword, content)
- POST /update/{keyword}  -> Update existing prompt
- GET  /delete/{keyword}  -> Delete prompt
- POST /update_theme      -> Update UI theme
- POST /update_language   -> Update UI language
- POST /update_settings   -> Update Windows autostart & settings
"""
import os
import sys
import json
import traceback
import logging
import hashlib
from fastapi import FastAPI, Request, Form, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from .utils import (
    load_prompts,
    save_prompts,
    get_prompts_file,
    DEMO_FILE,
    get_current_date,
    count_tokens,
    load_settings,
    save_settings,
    set_start_on_boot,
    VERSION,
)

app = FastAPI()

CATEGORY_COLORS = {
    "writing": "#0f766e", "editing": "#4338ca", "email": "#1d4ed8",
    "marketing": "#b45309", "social media": "#be185d", "learning": "#6d28d9",
    "research": "#0e7490", "coding": "#475569", "data": "#15803d",
    "planning": "#a16207", "productivity": "#4d7c0f", "business": "#b91c1c",
    "creative": "#a21caf", "translation": "#0369a1", "personal": "#be123c",
}


def category_color(tag: str) -> str:
    """Stable palette for demo and user-defined categories alike."""
    name = tag.strip().casefold()
    if not name:
        return "#64748b"
    if name in CATEGORY_COLORS:
        return CATEGORY_COLORS[name]
    palette = tuple(CATEGORY_COLORS.values())
    index = int.from_bytes(hashlib.blake2b(name.encode("utf-8"), digest_size=2).digest(), "big") % len(palette)
    return palette[index]


@app.get("/api/prompts")
async def quick_search_prompts(request: Request):
    """Contract: Electron main fetches keyword/content pairs with its private token."""
    token = getattr(app.state, "desktop_token", None)
    if not token or request.headers.get("X-PromptPlus-Token") != token:
        raise HTTPException(status_code=403, detail="Desktop access required")
    prompts = load_prompts()
    return [{"keyword": key, "content": data["content"]}
            for key, data in prompts.items() if isinstance(data.get("content"), str)]


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global error handler caught: {exc}")
    logger.error(traceback.format_exc())
    return HTMLResponse(content=f"Internal Server Error: {str(exc)}", status_code=500)


# Determine base path for resources
if getattr(sys, 'frozen', False):
    base_dir = sys._MEIPASS if hasattr(sys, '_MEIPASS') else os.path.dirname(sys.executable)
else:
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Static files
static_dir = os.path.join(base_dir, "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Templates
templates_dir = os.path.join(base_dir, "templates")
if not os.path.exists(templates_dir):
    os.makedirs(templates_dir)
templates = Jinja2Templates(directory=templates_dir)


@app.get("/favicon.ico")
async def favicon():
    icon_path = os.path.join(base_dir, "icon.ico")
    if os.path.exists(icon_path):
        return FileResponse(icon_path)
    return {"error": "File not found"}


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    settings = load_settings()
    prompts = load_prompts()
    processed_prompts = {}
    for keyword, data in prompts.items():
        if isinstance(data, dict):
            processed_prompts[keyword] = {
                'content': data['content'],
                'last_updated': data['last_updated'],
                'tags': data.get('tags', [])
            }
        else:
            processed_prompts[keyword] = {
                'content': data,
                'last_updated': get_current_date(),
                'tags': []
            }
    return templates.TemplateResponse(request, "index.html", {
        "prompts": processed_prompts,
        "count_tokens": count_tokens,
        "theme": settings.get("theme", "dark"),
        "language": settings.get("language", "bs"),
        "start_with_windows": settings.get("start_with_windows", False),
        "demo_mode": get_prompts_file() == DEMO_FILE,
        "all_tags": sorted(list(set(tag for p in processed_prompts.values() for tag in p.get('tags', [])))),
        "category_color": category_color,
        "version": VERSION
    })


@app.post("/add")
async def add_prompt(keyword: str = Form(...), content: str = Form(...), tags: str = Form("")):
    prompts = load_prompts()
    if not keyword.startswith(':'):
        keyword = ':' + keyword
    
    tag_list = [t.strip() for t in tags.split(',') if t.strip()]
    
    prompts[keyword] = {
        'content': content,
        'last_updated': get_current_date(),
        'tags': tag_list
    }
    save_prompts(prompts)
    return RedirectResponse("/", status_code=303)


@app.post("/update/{old_keyword}")
async def update_prompt(old_keyword: str, keyword: str = Form(...), content: str = Form(...), tags: str = Form("")):
    try:
        prompts = load_prompts()

        # Process new keyword first
        if not keyword.startswith(':'):
            new_keyword = ':' + keyword
        else:
            new_keyword = keyword

        # Check for keyword collision - don't overwrite existing prompts
        if new_keyword in prompts and new_keyword != old_keyword:
            logger.warning(f"Cannot rename '{old_keyword}' to '{new_keyword}': target already exists")
            return HTMLResponse(
                content=f"Prompt '{new_keyword}' already exists. Please use a different keyword.",
                status_code=400
            )

        # Remove old keyword
        if old_keyword in prompts:
            del prompts[old_keyword]

        tag_list = [t.strip() for t in tags.split(',') if t.strip()]

        prompts[new_keyword] = {
            'content': content,
            'last_updated': get_current_date(),
            'tags': tag_list
        }
        save_prompts(prompts)
        logger.info(f"Updated prompt: {old_keyword} -> {new_keyword}")
        return RedirectResponse("/", status_code=303)
    except Exception as e:
        logger.error(f"Error updating prompt: {e}")
        logger.error(traceback.format_exc())
        raise e


@app.get("/export")
async def export_prompts():
    prompt_file = get_prompts_file()
    if os.path.exists(prompt_file):
        return FileResponse(prompt_file, media_type='application/json', filename=os.path.basename(prompt_file))
    return {"error": "File not found"}


@app.post("/import")
async def import_prompts(file: UploadFile = File(...)):
    try:
        content = await file.read()
        # Validate JSON first
        try:
            imported = json.loads(content)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in import: {e}")
            return HTMLResponse(content=f"Invalid JSON file: {str(e)}", status_code=400)

        if not isinstance(imported, dict):
            return HTMLResponse(content="Invalid JSON file: the root value must be an object.", status_code=400)
        for keyword, value in imported.items():
            if not isinstance(keyword, str) or not isinstance(value, (str, dict)):
                return HTMLResponse(content="Invalid prompt format.", status_code=400)
            if isinstance(value, dict) and not isinstance(value.get('content'), str):
                return HTMLResponse(content="Invalid prompt content.", status_code=400)
        
        save_prompts(imported)
    except Exception as e:
        logger.error(f"Error importing prompts: {e}")
        logger.error(traceback.format_exc())
        return HTMLResponse(content=f"Import failed: {str(e)}", status_code=500)
    return RedirectResponse("/", status_code=303)


@app.get("/delete/{keyword}")
async def delete_prompt(keyword: str):
    prompts = load_prompts()
    if keyword in prompts:
        del prompts[keyword]
        save_prompts(prompts)
    return RedirectResponse("/", status_code=303)


@app.post("/update_theme")
async def update_theme(theme: str = Form(...)):
    settings = load_settings()
    settings["theme"] = theme
    save_settings(settings)
    return {"status": "success", "theme": theme}


@app.post("/update_language")
async def update_language(language: str = Form(...)):
    if language not in ("bs", "en"):
        raise HTTPException(status_code=400, detail="Unsupported language")
    settings = load_settings()
    settings["language"] = language
    save_settings(settings)
    return {"status": "success", "language": language}


@app.get("/open_url")
async def open_url(url: str):
    import webbrowser
    webbrowser.open(url)
    return {"status": "success"}


@app.post("/update_settings")
async def update_settings(start_with_windows: bool = Form(...)):
    settings = load_settings()
    settings["start_with_windows"] = start_with_windows
    save_settings(settings)
    
    # Update Windows Registry
    set_start_on_boot(start_with_windows)
    
    return {"status": "success", "start_with_windows": start_with_windows}
