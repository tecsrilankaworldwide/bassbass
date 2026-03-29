const { app, BrowserWindow, Menu, shell, dialog, session } = require('electron');
const path = require('path');

const SERVER_URL = 'https://grade5exam.com';
const APP_TITLE = 'Grade 5 Scholarship Exam Platform';

let mainWindow;
let isConnected = false;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1366,
    height: 868,
    minWidth: 1024,
    minHeight: 700,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      nodeIntegration: false,
      contextIsolation: true,
      webviewTag: false
    },
    icon: path.join(__dirname, 'assets', 'icon.png'),
    title: APP_TITLE,
    show: false,
    backgroundColor: '#FFFBF0',
    autoHideMenuBar: false
  });

  // Build application menu
  const menuTemplate = [
    {
      label: 'File',
      submenu: [
        {
          label: 'Refresh',
          accelerator: 'F5',
          click: () => { mainWindow.webContents.reload(); }
        },
        {
          label: 'Go to Login',
          click: () => { mainWindow.loadURL(SERVER_URL + '/login'); }
        },
        { type: 'separator' },
        {
          label: 'Exit',
          accelerator: 'Alt+F4',
          click: () => { app.quit(); }
        }
      ]
    },
    {
      label: 'View',
      submenu: [
        {
          label: 'Zoom In',
          accelerator: 'CmdOrCtrl+=',
          click: () => { mainWindow.webContents.setZoomLevel(mainWindow.webContents.getZoomLevel() + 0.5); }
        },
        {
          label: 'Zoom Out',
          accelerator: 'CmdOrCtrl+-',
          click: () => { mainWindow.webContents.setZoomLevel(mainWindow.webContents.getZoomLevel() - 0.5); }
        },
        {
          label: 'Reset Zoom',
          accelerator: 'CmdOrCtrl+0',
          click: () => { mainWindow.webContents.setZoomLevel(0); }
        },
        { type: 'separator' },
        {
          label: 'Full Screen',
          accelerator: 'F11',
          click: () => { mainWindow.setFullScreen(!mainWindow.isFullScreen()); }
        }
      ]
    },
    {
      label: 'Help',
      submenu: [
        {
          label: 'About',
          click: () => {
            dialog.showMessageBox(mainWindow, {
              type: 'info',
              title: 'About',
              message: APP_TITLE,
              detail: `Version ${app.getVersion()}\n\nExamination Evaluation Bureau\nTEC Sri Lanka Worldwide (Pvt.) Ltd\n\nServer: ${SERVER_URL}`,
              buttons: ['OK']
            });
          }
        },
        {
          label: 'Check Connection',
          click: () => { checkConnection(); }
        }
      ]
    }
  ];

  Menu.setApplicationMenu(Menu.buildFromTemplate(menuTemplate));

  // Show loading screen first
  mainWindow.loadFile(path.join(__dirname, 'loading.html'));

  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
    connectToServer();
  });

  // Handle external links — open in default browser
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    if (url.startsWith('http') && !url.includes('grade5exam.com')) {
      shell.openExternal(url);
      return { action: 'deny' };
    }
    return { action: 'allow' };
  });

  // Handle navigation errors
  mainWindow.webContents.on('did-fail-load', (event, errorCode, errorDescription) => {
    console.error(`Failed to load: ${errorDescription} (${errorCode})`);
    if (!isConnected) {
      mainWindow.loadFile(path.join(__dirname, 'loading.html'));
      setTimeout(() => connectToServer(), 5000);
    }
  });

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

async function connectToServer() {
  try {
    const response = await fetch(`${SERVER_URL}/api/`);
    if (response.ok) {
      isConnected = true;
      mainWindow.loadURL(`${SERVER_URL}/login`);
      console.log('Connected to server successfully');
    } else {
      throw new Error(`Server returned ${response.status}`);
    }
  } catch (error) {
    console.error('Connection failed:', error.message);
    isConnected = false;
    // Retry after 5 seconds
    setTimeout(() => {
      if (mainWindow && !isConnected) {
        connectToServer();
      }
    }, 5000);
  }
}

async function checkConnection() {
  try {
    const response = await fetch(`${SERVER_URL}/api/`);
    const data = await response.json();
    dialog.showMessageBox(mainWindow, {
      type: 'info',
      title: 'Connection Status',
      message: 'Connected to Server',
      detail: `Server: ${SERVER_URL}\nStatus: ${data.status || 'OK'}\nVersion: ${data.version || 'Unknown'}`,
      buttons: ['OK']
    });
  } catch (error) {
    dialog.showMessageBox(mainWindow, {
      type: 'error',
      title: 'Connection Status',
      message: 'Cannot Connect to Server',
      detail: `Server: ${SERVER_URL}\nError: ${error.message}\n\nPlease check your internet connection.`,
      buttons: ['Retry', 'OK']
    }).then(result => {
      if (result.response === 0) {
        connectToServer();
      }
    });
  }
}

// Single instance lock — prevent multiple app windows
const gotTheLock = app.requestSingleInstanceLock();
if (!gotTheLock) {
  app.quit();
} else {
  app.on('second-instance', () => {
    if (mainWindow) {
      if (mainWindow.isMinimized()) mainWindow.restore();
      mainWindow.focus();
    }
  });
}

app.on('ready', createWindow);

app.on('window-all-closed', () => {
  app.quit();
});

app.on('activate', () => {
  if (mainWindow === null) {
    createWindow();
  }
});
