@echo off
rem Starts MCP server %1 only in a project that switched it on: a file
rem .claude\mcp-on\%1 in the session's folder or one of its parents.
rem Anywhere else it exits at once, so no server process is left running.
setlocal
set "MCP_NAME=%~1"
set "d=%CD%"
:up
if exist "%d%\.claude\mcp-on\%MCP_NAME%" goto run
for %%I in ("%d%\..") do set "p=%%~fI"
if /i "%p%"=="%d%" exit /b 0
set "d=%p%"
goto up
:run
set "MCP_PROJECT=%d%"
call "%~dp0servers\%MCP_NAME%.cmd"
