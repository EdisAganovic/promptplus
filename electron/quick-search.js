const query = document.getElementById('query');
const results = document.getElementById('results');
const title = document.getElementById('title');
const modeBadge = document.getElementById('mode-badge');
let prompts = [];
let visible = [];
let selected = 0;
let isPickerMode = false;

function render() {
  const term = query.value.toLowerCase().trim();
  if (isPickerMode && !term) {
    visible = prompts;
  } else {
    visible = prompts.filter(prompt => {
      const kw = (prompt.keyword || '').toLowerCase();
      const ct = (prompt.content || '').toLowerCase();
      const tg = (prompt.tags || []).join(' ').toLowerCase();
      return kw.includes(term) || ct.includes(term) || tg.includes(term);
    });
  }
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
    const isCurSelected = index === selected;
    const button = document.createElement('button');
    button.className = 'result' + (isCurSelected ? ' selected' : '');
    button.setAttribute('role', 'option');
    button.setAttribute('aria-selected', String(isCurSelected));
    
    const topRow = document.createElement('div');
    topRow.className = 'result-top';

    if (index < 9) {
      const numBadge = document.createElement('span');
      numBadge.className = 'key-badge';
      numBadge.title = `Press ${index + 1} to paste`;
      numBadge.textContent = `${index + 1}`;
      topRow.append(numBadge);
    }

    const keyword = document.createElement('span');
    keyword.className = 'keyword';
    keyword.textContent = prompt.keyword;
    topRow.append(keyword);

    if (prompt.tags && prompt.tags.length > 0) {
      const tagsContainer = document.createElement('span');
      tagsContainer.className = 'tags';
      prompt.tags.forEach(t => {
        const tag = document.createElement('span');
        tag.className = 'tag';
        tag.textContent = t;
        tagsContainer.append(tag);
      });
      topRow.append(tagsContainer);
    }

    if (isCurSelected) {
      const enterHint = document.createElement('span');
      enterHint.className = 'enter-badge';
      enterHint.textContent = '↵ Enter';
      topRow.append(enterHint);
    }

    const preview = document.createElement('div');
    preview.className = 'preview';
    preview.textContent = prompt.content.replace(/[\r\n]+/g, ' ').slice(0, 150);

    button.append(topRow, preview);

    button.addEventListener('mouseenter', () => {
      if (selected !== index) {
        selected = index;
        renderSelected();
      }
    });

    button.addEventListener('click', () => {
      window.promptplus.pastePrompt({ id: prompt.id, content: prompt.content, keyword: prompt.keyword });
    });
    results.append(button);
  });
  results.children[selected]?.scrollIntoView({ block: 'nearest' });
}

function renderSelected() {
  Array.from(results.children).forEach((child, index) => {
    const isCur = index === selected;
    child.classList.toggle('selected', isCur);
    child.setAttribute('aria-selected', String(isCur));
    const topRow = child.querySelector('.result-top');
    let enterHint = child.querySelector('.enter-badge');
    if (isCur) {
      if (!enterHint && topRow) {
        enterHint = document.createElement('span');
        enterHint.className = 'enter-badge';
        enterHint.textContent = '↵ Enter';
        topRow.append(enterHint);
      }
    } else if (enterHint) {
      enterHint.remove();
    }
  });
  results.children[selected]?.scrollIntoView({ block: 'nearest' });
}

function handleKeyNav(event) {
  if (event.key === 'Escape') {
    event.preventDefault();
    window.promptplus.closeSearch();
    return;
  }
  if (/^[1-9]$/.test(event.key) && (!query.value || isPickerMode)) {
    const num = parseInt(event.key, 10) - 1;
    if (visible[num]) {
      event.preventDefault();
      window.promptplus.pastePrompt({ id: visible[num].id, content: visible[num].content, keyword: visible[num].keyword });
      return;
    }
  }
  if (event.key === 'ArrowDown') {
    event.preventDefault();
    if (visible.length > 0) {
      selected = (selected + 1) % visible.length;
      renderSelected();
    }
    return;
  }
  if (event.key === 'ArrowUp') {
    event.preventDefault();
    if (visible.length > 0) {
      selected = (selected - 1 + visible.length) % visible.length;
      renderSelected();
    }
    return;
  }
  if (event.key === 'Enter') {
    event.preventDefault();
    if (visible[selected]) {
      window.promptplus.pastePrompt({ id: visible[selected].id, content: visible[selected].content, keyword: visible[selected].keyword });
    }
  }
}

window.addEventListener('keydown', handleKeyNav);

window.promptplus.onReset(async () => {
  isPickerMode = false;
  if (title) title.textContent = 'Quick Search';
  if (modeBadge) modeBadge.hidden = true;
  query.value = '';
  query.placeholder = 'Search prompts…';
  selected = 0;
  try { prompts = await window.promptplus.listPrompts(); }
  catch { prompts = []; }
  render();
  query.focus();
});

window.promptplus.onShowPicker(data => {
  isPickerMode = true;
  if (title) title.textContent = `Choose prompt: ${data.keyword}`;
  if (modeBadge) {
    modeBadge.textContent = `${data.prompts.length} options`;
    modeBadge.hidden = false;
  }
  query.value = '';
  query.placeholder = 'Filter options or use ↑/↓ to choose…';
  selected = 0;
  prompts = data.prompts || [];
  render();
  query.focus();
});

query.addEventListener('input', () => { selected = 0; render(); });
document.getElementById('close').addEventListener('click', () => window.promptplus.closeSearch());
