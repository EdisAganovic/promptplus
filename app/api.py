"""
app/api.py - FastAPI Web Server
================================
Routes:
- GET  /                  -> Home page (list prompts)
- POST /add               -> Add new prompt (keyword, content)
- POST /update/{keyword}  -> Update existing prompt
- GET  /delete/{keyword}  -> Delete prompt
"""
import os
from fastapi import FastAPI, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import shutil

from .utils import load_prompts, save_prompts, get_current_date, count_tokens

app = FastAPI()

# Static files
static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Templates
templates_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")
if not os.path.exists(templates_dir):
    os.makedirs(templates_dir)
templates = Jinja2Templates(directory=templates_dir)


@app.get("/favicon.ico")
async def favicon():
    icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "icon.ico")
    if os.path.exists(icon_path):
        return FileResponse(icon_path)
    return {"error": "File not found"}


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
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
    return templates.TemplateResponse("index.html", {
        "request": request,
        "prompts": processed_prompts,
        "count_tokens": count_tokens,
        "all_tags": sorted(list(set(tag for p in processed_prompts.values() for tag in p.get('tags', []))))
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
    prompts = load_prompts()
    if old_keyword in prompts:
        del prompts[old_keyword]
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


@app.get("/export")
async def export_prompts():
    from .utils import PROMPTS_FILE
    if os.path.exists(PROMPTS_FILE):
        return FileResponse(PROMPTS_FILE, media_type='application/json', filename="textflow_prompts.json")
    return {"error": "File not found"}


@app.post("/import")
async def import_prompts(file: UploadFile = File(...)):
    from .utils import PROMPTS_FILE
    try:
        content = await file.read()
        # Validate JSON
        json.loads(content)
        with open(PROMPTS_FILE, "wb") as f:
            f.write(content)
    except Exception as e:
        return {"error": f"Invalid JSON: {str(e)}"}
    return RedirectResponse("/", status_code=303)


@app.get("/delete/{keyword}")
async def delete_prompt(keyword: str):
    prompts = load_prompts()
    if keyword in prompts:
        del prompts[keyword]
        save_prompts(prompts)
    return RedirectResponse("/", status_code=303)
