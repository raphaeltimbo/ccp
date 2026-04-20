const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("ccpElectron", {
  saveFile: (payload) => ipcRenderer.invoke("ccp:saveFile", payload),
  openFile: () => ipcRenderer.invoke("ccp:openFile"),
});
