const path = require('path');
const { app, BrowserWindow } = require('electron');
const { startServer, stopServer } = require('./server');

let mainWindow;
let serverRef;

function createChildWindow(url) {
  const child = new BrowserWindow({
    width: 1050,
    height: 760,
    minWidth: 860,
    minHeight: 600,
    autoHideMenuBar: true,
    parent: mainWindow,
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
    },
  });

  child.loadURL(url);
}

function createWindow(port) {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 1000,
    minHeight: 700,
    autoHideMenuBar: true,
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
    },
  });

  const appOrigin = `http://127.0.0.1:${port}`;

  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    if (url.startsWith(appOrigin)) {
      createChildWindow(url);
      return { action: 'deny' };
    }

    return { action: 'allow' };
  });

  mainWindow.loadURL(appOrigin);
}

app.whenReady().then(async () => {
  const dataDir = path.join(app.getPath('userData'), 'politicagem');
  serverRef = await startServer({ dataDir });
  createWindow(serverRef.port);

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0 && serverRef) {
      createWindow(serverRef.port);
    }
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('before-quit', async () => {
  await stopServer(serverRef);
});
