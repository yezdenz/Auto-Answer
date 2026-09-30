@echo off
REM Auto Answer Batch Launcher for Windows

where py >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    py -3 main.py %*
    goto end
)

where python >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    python main.py %*
    goto end
)

echo [ERROR] Python was not found on your system!
pause

:end
