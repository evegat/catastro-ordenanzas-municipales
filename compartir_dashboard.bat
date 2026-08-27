@echo off
title Servidor y Tunel P090
echo ===================================================
echo   Iniciando Dashboard y Tunel Web Publico (P090)
echo ===================================================
echo.

start /B python -m http.server 8000 --directory "D:\Proyectos\P090 - Catastro Ordenanzas Municipales BCN\dashboard"

echo Servidor local iniciado en puerto 8000.
echo Generando enlace publico seguro HTTPS...
echo.

ssh -o StrictHostKeyChecking=no -p 443 -R0:localhost:8000 a.pinggy.io

pause
