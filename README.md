Create Virtual Environment

    # macOS/Linux
    # You may need to run `sudo apt-get install python3-venv` first on Debian-based OSs
    python3 -m venv .venv

    # Windows
    # You can also use `py -3 -m venv .venv`
    python -m venv .venv

    #Activate Virtual Environment
    source .venv/bin/activate



Start the Backend
    
    cd Backend
    uvicorn main:app --reload


Start Webinterface
    
    cd kantine-web
    npm run dev


Start UI
    
    Just run it in VSCODE