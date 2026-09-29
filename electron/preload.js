const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('promptplus', {
  listPrompts: () => ipcRenderer.invoke('list-prompts'),
  pastePrompt: item => ipcRenderer.invoke('paste-prompt', item),
  closeSearch: () => ipcRenderer.send('close-search'),
  setShortcut: shortcut => ipcRenderer.invoke('set-shortcut', shortcut),
  onReset: callback => ipcRenderer.on('reset-search', () => callback()),
  onShowPicker: callback => ipcRenderer.on('show-picker', (_event, data) => callback(data)),
});
