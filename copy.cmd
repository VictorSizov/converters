echo on
set ROOT_PATH=F:\place\ruscorpora\test
if not exist "%ROOT_PATH%" (
    echo "root path not exists"
    exit/b 1
    )
set COPY_PATH=%ROOT_PATH%\validator
if not exist "%COPY_PATH%" (
    mkdir %COPY_PATH%
    )

xcopy converter_basic.py %COPY_PATH%\ /Y
xcopy converter_spoken.py %COPY_PATH%\ /Y
xcopy error_processor.py %COPY_PATH%\ /Y
xcopy init.py %COPY_PATH%\ /Y
xcopy lxml_ext.py %COPY_PATH%\ /Y
xcopy processor_basic.py %COPY_PATH%\ /Y
xcopy validator_basic.py %COPY_PATH%\ /Y
xcopy validator_spoken.py %COPY_PATH%\ /Y
xcopy validator_spoken.py %COPY_PATH%\ /Y
xcopy install.cmd %COPY_PATH%\ /Y
xcopy converter_spoken.cmd %COPY_PATH%\ /Y
xcopy requirements.txt %COPY_PATH%\ /Y
xcopy templates %COPY_PATH%\templates\ /Y
xcopy validation %COPY_PATH%\validation\ /Y