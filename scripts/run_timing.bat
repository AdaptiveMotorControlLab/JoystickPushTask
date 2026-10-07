@echo off
rem Usage: run_timing.bat "<full path to EVENTS_<name>>"
rem Called by the push VI (System Exec) after the session files are closed.
rem Output is also saved to timing_log.txt next to the EVENTS file.
set "PY=C:\Users\Mathis_Lab_1\AppData\Local\Programs\Python\Python36-32\python.exe"
set "SCRIPT=%~dp0make_labview_timing.py"
set "LOG=%~dp1timing_log.txt"
"%PY%" "%SCRIPT%" %1 > "%LOG%" 2>&1
set "RC=%ERRORLEVEL%"
type "%LOG%"
exit /b %RC%
