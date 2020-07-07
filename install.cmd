set echo off
set ENV_PATH=.\venv
if not exist "%ENV_PATH%" (
    mkdir "%ENV_PATH%"
    py -3  -m venv "%ENV_PATH%"
	if not exist  "%ENV_PATH%\Scripts\python3.exe" (
	    copy  "%ENV_PATH%\Scripts\python.exe"  "%ENV_PATH%\Scripts\python3.exe"
	    )
    )

call "%ENV_PATH%\Scripts\activate.bat"
pip  install -r requirements.txt
python3 init.py
pause
