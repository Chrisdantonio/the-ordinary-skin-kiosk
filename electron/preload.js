const { contextBridge, ipcRenderer } = require('electron')

contextBridge.exposeInMainWorld('kiosk', {
  getSavedKey: () => ipcRenderer.invoke('get-saved-key'),
  launch: (apiKey, save) => ipcRenderer.send('launch', { apiKey, save }),
  onStatus: (cb) => ipcRenderer.on('status', (_, msg) => cb(msg)),
})
