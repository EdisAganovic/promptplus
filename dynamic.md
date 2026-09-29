# Dynamic Tags & Variables Specification for PromptPlus

This document outlines proposed designs and concepts for implementing **Dynamic Tags** and **Dynamic Content Placeholders** in PromptPlus.

---

## 1. Dynamic Content Placeholders (Expansion Tags)

These placeholders are written directly inside prompt text and are automatically resolved and replaced with real-time values at the moment of expansion/pasting.

### 📅 Time & Date Placeholders
* `{{date}}` — Inserts the current date (e.g. `30.09.2026`).
* `{{time}}` — Inserts the current local time (e.g. `14:35`).
* `{{datetime}}` — Inserts formatted date and timestamp.
* `{{day}}` — Inserts current day of the week (e.g. `Wednesday` / `Srijeda`).
* `{{year}}` — Inserts current year (e.g. `2026`).

### 📋 System & Clipboard Placeholders
* `{{clipboard}}` — Automatically embeds current clipboard contents into the prompt.
  * *Example prompt:* `Proofread the following text for grammar and clarity:\n\n{{clipboard}}`
* `{{cursor}}` — Positions the active text cursor at this spot after pasting so the user can begin typing immediately.

### ✍️ Interactive Variable Inputs
* `{{input:Topic}}` or `[topic]` — Triggers a lightweight popup/modal asking for variable values before pasting.
* `{{select:Language|Python|JavaScript|Go}}` — Shows a small dropdown or quick-picker to choose an option for the placeholder.

---

## 2. Smart / Computed Filter Tags (Library UI)

Dynamic tags that the system computes automatically to enhance search and filtering in the library interface:

### 📊 Usage & History Tags
* **`⭐ Most Used / Favorites`** — Prompts with highest usage count.
* **`🕒 Recently Used`** — Prompts pasted within the last 24–48 hours.
* **`🆕 Recently Added`** — Prompts created in the current week.

### 🏷️ Property & Structure Tags
* **`🔀 Multi-Choice Keywords`** — Prompts that share a keyword with other prompts (triggering the Quick Picker popup).
* **`⚠️ Untagged`** — Quickly identify prompts without assigned categories.
* **`📏 Short (< 50 words)`** vs **`📜 Long (> 200 words)`** — Content-length filters.

### 🤖 Auto-Detected Content Tags
* **Detected Code Languages:** `Python`, `SQL`, `HTML/CSS`, `JavaScript`.
* **Language Detection:** `Bosanski`, `English`, `German`, etc.
* **Tone Detection:** `Formal`, `Casual`, `Technical`.

---

## 3. Context-Aware Dynamic Tags (Application-Smart)

PromptPlus can detect the currently focused desktop application and surface relevant tags/prompts first:

* **Coding Environments** (VS Code, PyCharm, Cursor, Terminal) $\rightarrow$ Boost prompts tagged `#Coding`, `#Debug`, `#Refactor`.
* **Email Clients** (Outlook, Gmail, Thunderbird) $\rightarrow$ Boost prompts tagged `#Email`, `#Formal`, `#Communication`.
* **Web Browsers / LLM UIs** (ChatGPT, Claude, Perplexity) $\rightarrow$ Boost prompts tagged `#AI`, `#Research`, `#Writing`.

---

## 4. Suggested Implementation Roadmap

1. **Phase 1 (Core Placeholders):**
   - Implement `{{clipboard}}`, `{{date}}`, and `{{time}}` parsing in `app/replacer.py`.
2. **Phase 2 (Dynamic UI Filter Chips):**
   - Add computed filter chips (`Recently Used`, `Multi-Match`, `Untagged`) to the sidebar in `templates/index.html`.
3. **Phase 3 (Interactive Prompts):**
   - Add mini variable input modal in Electron for prompts with `{{input:Field}}`.
