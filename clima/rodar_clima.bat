@echo off
rem Coleta uma leitura de clima e guarda em clima.db (nesta mesma pasta).
rem Use com o Agendador de Tarefas do Windows para rodar de hora em hora.
cd /d "%~dp0"
python clima.py >> log.txt 2>&1
