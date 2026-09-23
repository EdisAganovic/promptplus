const query = document.getElementById('query');
const results = document.getElementById('results');
let prompts = [];
let visible = [];
let selected = 0;

function render() {
  const term = query.value.toLowerCase();
  visible = prompts.filter(prompt => prompt.keyword.toLowerCase().includes(term) || prompt.content.toLowerCase().includes(term));
  selected = Math.min(selected, Math.max(visible.length - 1, 0));
  results.replaceChildren();
  if (!visible.length) {
    const empty = document.createElement('div');
    empty.className = 'empty';
    empty.textContent = 'No matching prompts';
    results.append(empty);
    return;
  }
  visible.forEach((prompt, index) => {
    const button = document.createElement('button');
    button.className = 'result';
    button.setAttribute('role', 'option');
    button.setAttribute('aria-selected', String(index === selected));
    const keyword = document.createElement('span');
    keyword.className = 'keyword';
    keyword.textContent = prompt.keyword;
    const preview = document.createElement('span');
    preview.className = 'preview';
    preview.textContent = prompt.content.replace(/[\r\n]+/g, ' ').slice(0, 120);
    button.append(keyword, preview);
    button.addEventListener('click', () => window.promptplus.pastePrompt(prompt.keyword));
    results.append(button);
  });
  results.children[selected]?.scrollIntoView({ block: 'nearest' });
}

window.promptplus.onReset(async () => {
  query.value = '';
  selected = 0;
  try { prompts = await window.promptplus.listPrompts(); }
  catch { prompts = []; }
  render();
  query.focus();
});
query.addEventListener('input', () => { selected = 0; render(); });
query.addEventListener('keydown', event => {
  if (event.key === 'Escape') window.promptplus.closeSearch();
  if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
    event.preventDefault();
    selected = Math.max(0, Math.min(visible.length - 1, selected + (event.key === 'ArrowDown' ? 1 : -1)));
    render();
  }
  if (event.key === 'Enter' && visible[selected]) {
    event.preventDefault();
    window.promptplus.pastePrompt(visible[selected].keyword);
  }
});
document.getElementById('close').addEventListener('click', () => window.promptplus.closeSearch());
