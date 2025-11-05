from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import json
import os

# File to store prompts
PROMPTS_FILE = "prompts.json"

def load_prompts():
    """Load prompts from a JSON file."""
    if os.path.exists(PROMPTS_FILE):
        with open(PROMPTS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Convert old format to new format if needed
            prompts = {}
            for key, value in data.items():
                if isinstance(value, str):
                    # Old format: {keyword: content}
                    prompts[key] = {
                        'content': value,
                        'last_updated': get_current_date()
                    }
                elif isinstance(value, dict) and 'content' in value:
                    # New format: {keyword: {'content': content, 'last_updated': date}}
                    # Ensure last updated date exists, if not add current date
                    if 'last_updated' not in value:
                        value['last_updated'] = get_current_date()
                    prompts[key] = value
                else:
                    # Some other format
                    prompts[key] = {
                        'content': value,
                        'last_updated': get_current_date()
                    }
            return prompts
    return {}

def save_prompts(prompts):
    """Save prompts to a JSON file."""
    with open(PROMPTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(prompts, f, ensure_ascii=False, indent=2)

def get_current_date():
    """Get current date in m.d.Y format."""
    from datetime import datetime
    return datetime.now().strftime("%m.%d.%Y")

def count_tokens(text):
    """Count tokens in text using tiktoken for accurate OpenAI token counting"""
    try:
        import tiktoken
        # Use the cl100k_base encoding which is used by most recent OpenAI models
        encoding = tiktoken.get_encoding("cl100k_base")
        token_count = len(encoding.encode(text))
        return token_count
    except ImportError:
        # Fallback if tiktoken is not available - simple approximation
        import re
        tokens = re.findall(r'\b\w+\b|[^\w\s]', text)
        return max(len(tokens), 1)  # Return at least 1 token

app = FastAPI()

# Mount static files directory if it exists, otherwise create it
static_dir = os.path.join(os.path.dirname(__file__), "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Create templates directory if it doesn't exist
templates_dir = os.path.join(os.path.dirname(__file__), "templates")
if not os.path.exists(templates_dir):
    os.makedirs(templates_dir)

templates = Jinja2Templates(directory=templates_dir)

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    prompts = load_prompts()
    # Convert to a format that template can handle easily
    processed_prompts = {}
    for keyword, data in prompts.items():
        if isinstance(data, dict):
            processed_prompts[keyword] = {
                'content': data['content'],
                'last_updated': data['last_updated']
            }
        else:
            # Fallback for old format
            processed_prompts[keyword] = {
                'content': data,
                'last_updated': get_current_date()
            }
    return templates.TemplateResponse("index.html", {"request": request, "prompts": processed_prompts, "count_tokens": count_tokens})

@app.post("/add")
async def add_prompt(keyword: str = Form(...), content: str = Form(...)):
    prompts = load_prompts()
    # Automatically prepend ":" if not already present
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
    # Remove old keyword and add new one
    if old_keyword in prompts:
        del prompts[old_keyword]
    # Automatically prepend ":" if not already present
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
    uvicorn.run(app, host="127.0.0.1", port=8000)