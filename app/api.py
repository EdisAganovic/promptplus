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
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

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


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    prompts = load_prompts()
    processed_prompts = {}
    for keyword, data in prompts.items():
        if isinstance(data, dict):
            processed_prompts[keyword] = {
                'content': data['content'],
                'last_updated': data['last_updated']
            }
        else:
            processed_prompts[keyword] = {
                'content': data,
                'last_updated': get_current_date()
            }
    return templates.TemplateResponse("index.html", {
        "request": request,
        "prompts": processed_prompts,
        "count_tokens": count_tokens
    })


@app.post("/add")
async def add_prompt(keyword: str = Form(...), content: str = Form(...)):
    prompts = load_prompts()
    if not keyword.startswith(':'):
        keyword = ':' + keyword
    prompts[keyword] = {
        'content': content,
        'last_updated': get_current_date()
    }
    save_prompts(prompts)
    return RedirectResponse("/", status_code=303)


@app.post("/update/{old_keyword}")
async def update_prompt(old_keyword: str, keyword: str = Form(...), content: str = Form(...)):
    prompts = load_prompts()
    if old_keyword in prompts:
        del prompts[old_keyword]
    if not keyword.startswith(':'):
        keyword = ':' + keyword
    prompts[keyword] = {
        'content': content,
        'last_updated': get_current_date()
    }
    save_prompts(prompts)
    return RedirectResponse("/", status_code=303)


@app.get("/delete/{keyword}")
async def delete_prompt(keyword: str):
    prompts = load_prompts()
    if keyword in prompts:
        del prompts[keyword]
        save_prompts(prompts)
    return RedirectResponse("/", status_code=303)
