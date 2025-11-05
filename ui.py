from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import json
import os

PROMPTS_FILE = "prompts.json"

def load_prompts():
    if os.path.exists(PROMPTS_FILE):
        with open(PROMPTS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            prompts = {}
            for key, value in data.items():
                if isinstance(value, str):
                    prompts[key] = {
                        'content': value,
                        'last_updated': get_current_date()
                    }
                elif isinstance(value, dict) and 'content' in value:
                    if 'last_updated' not in value:
                        value['last_updated'] = get_current_date()
                    prompts[key] = value
                else:
                    prompts[key] = {
                        'content': value,
                        'last_updated': get_current_date()
                    }
            return prompts
    return {}

def save_prompts(prompts):
    with open(PROMPTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(prompts, f, ensure_ascii=False, indent=2)

def get_current_date():
    from datetime import datetime
    return datetime.now().strftime("%m.%d.%Y")

def count_tokens(text):
    try:
        import tiktoken
        encoding = tiktoken.get_encoding("cl100k_base")
        token_count = len(encoding.encode(text))
        return token_count
    except (ImportError, ValueError):
        # Fallback if tiktoken is not available or encoding not found
        import re
        tokens = re.findall(r'\b\w+\b|[^\w\s]', text)
        return max(len(tokens), 1)

app = FastAPI()

static_dir = os.path.join(os.path.dirname(__file__), "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

templates_dir = os.path.join(os.path.dirname(__file__), "templates")
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
    return templates.TemplateResponse("index.html", {"request": request, "prompts": processed_prompts, "count_tokens": count_tokens})

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

if __name__ == "__main__":
    import uvicorn
    # This is used when running ui.py directly, not when imported by run.py
    uvicorn.run(app, host="127.0.0.1", port=8000)