# PhishXplain

PhishXplain is a Chrome extension that automatically explains detected phishing websites. It integrates with your browser's anti-phishing tool (Google Safe Browsing) to identify suspicious sites and provides detailed visual explanations of why a site might be phishing.

## Features

- Visual analysis of suspicious elements on the page
- Detailed explanations of potential phishing indicators
- Interactive screenshot with highlighted areas of concern

## Prerequisites

- Python 3.8 or higher
- Chrome browser
- Node.js and npm (for building the extension)
- Ollama (for running the Llama model)

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd phishxplain
```

### 2. Install Ollama and Llama Model

#### On macOS:
```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Install Llama 3.2:3b model
ollama pull llama3.2:3b
```

#### On Linux:
```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Install Llama 3.2:3b model
ollama pull llama3.2:3b
```

#### On Windows:
1. Download and install Ollama from https://ollama.com/download
2. Open PowerShell and run:
```powershell
ollama pull llama3.2:3b
```

### 3. Set Up Python Environment

```bash
# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install required Python packages
pip install -r requirements.txt
```

### 4. Install Chrome Extension

1. Open Chrome (or any Chromium based browser) and go to `chrome://extensions/`
2. Enable "Developer mode" in the top right corner
3. Click "Load unpacked" and select the `extension` directory from the project

## Running the Application

### 1. Start Ollama Service

Make sure Ollama is running in the background:

```bash
# On macOS/Linux:
ollama serve

# On Windows:
# Ollama service should start automatically after installation
```

### 2. Start the Flask Server

```bash
# Make sure you're in the virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Start the Flask server
python extension/server.py
```

The server will start on `http://127.0.0.1:5000`

### 2. Using the Extension

1. The extension will automatically activate when Google Safe Browsing detects a phishing site
2. When a phishing site is detected, the extension will:
   - Take a screenshot of the suspicious page
   - Analyze the page content
   - Generate a detailed report
   - Show a warning page with visual explanations

## Project Structure

```
phishxplain/
├── extension/              # Chrome extension files
│   ├── background.js       # Extension background script
│   ├── server.py          # Flask server for analysis
│   ├── landing.html       # Loading page
│   ├── warning.html       # Warning page template
│   └── images/            # Extension images
├── artifacts/             # Generated analysis files
├── annotate.py           # Screenshot annotation script
├── get.py               # Website screenshot capture
├── generate.py          # Analysis generation
└── requirements.txt     # Python dependencies
```

## How It Works

1. When Google Safe Browsing detects a phishing site, the extension automatically triggers
2. The extension captures the screenshot and source code of the suspicious page
3. The source code of the website is analyzed for suspicious elements
4. A detailed report is generated with highlighted areas of concern
5. The user is shown a warning page with visual explanations

## License

This project is licensed for **non-commercial use only**.

Copyright (c) 2025 Sayak Saha Roy.

You are permitted to use, copy, modify, and share the code for **personal, academic, or research purposes**.  
**Commercial use—including use in proprietary software, paid services, or enterprise deployments—is strictly prohibited** without explicit, written permission from the author.

See the LICENSE.md file for full terms.  


## Attribution 

PhishXplain is based on the research presented in:

**"Explain, Don’t Just Warn!: A Real-Time Framework for Generating Phishing Warnings with Contextual Cues"**  
Sayak Saha Roy, Cesar Torres, Shirin Nilizadeh - https://arxiv.org/abs/2505.06836
