# ISSUES

1. FFmpeg is missing
2. cudnn8dlops.dll or whatever is missing/not in PATH

Setting up Single-File executable:
    pyinstaller  --add-data "F:\Working\*.dll;." "./summarize.py" -n "tldw-windows"    
    https://github.com/Purfview/whisper-standalone-win/releases