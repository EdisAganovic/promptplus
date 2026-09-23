const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('promptplus', {
  listPrompts: () => ipcRenderer.invoke('list-prompts'),
  pastePrompt: keyword => ipcRenderer.invoke('paste-prompt', keyword),
  closeSearch: () => ipcRenderer.send('close-search'),
  setShortcut: shortcut => ipcRenderer.invoke('set-shortcut', shortcut),
  onReset: callback => ipcRenderer.on('reset-search', () => callback()),
});
