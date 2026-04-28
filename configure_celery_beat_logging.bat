@echo off
setlocal

set NSSM=C:\nssm\nssm.exe
set PROJECT_DIR=C:\DjangoApps\ims_fleet
set VENV_DIR=C:\DjangoApps\venv
set PYTHONPATH=C:\DjangoApps\ims_fleet
set DJANGO_SETTINGS_MODULE=ims_fleet.settings.production
set BEAT_SERVICE=IMS_Fleet_Celery_Beat
set LOG_DIR=C:\DjangoApps\logs

if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

echo Configuring Celery beat service logging...
"%NSSM%" set %BEAT_SERVICE% Application "%VENV_DIR%\Scripts\celery.exe"
"%NSSM%" set %BEAT_SERVICE% AppDirectory "%PROJECT_DIR%"
"%NSSM%" set %BEAT_SERVICE% AppParameters -A ims_fleet beat --scheduler django_celery_beat.schedulers:DatabaseScheduler -l info
"%NSSM%" set %BEAT_SERVICE% AppEnvironmentExtra DJANGO_SETTINGS_MODULE=%DJANGO_SETTINGS_MODULE% PYTHONPATH=%PYTHONPATH%
"%NSSM%" set %BEAT_SERVICE% AppStdout "%LOG_DIR%\celery-beat.stdout.log"
"%NSSM%" set %BEAT_SERVICE% AppStderr "%LOG_DIR%\celery-beat.stderr.log"
"%NSSM%" set %BEAT_SERVICE% AppRotateFiles 1
"%NSSM%" set %BEAT_SERVICE% AppRotateOnline 1
"%NSSM%" set %BEAT_SERVICE% AppRotateBytes 10485760
"%NSSM%" set %BEAT_SERVICE% AppRestartDelay 5000
"%NSSM%" set %BEAT_SERVICE% Start SERVICE_AUTO_START

echo Restarting Celery beat service...
net stop %BEAT_SERVICE%
net start %BEAT_SERVICE%

echo Done. Check:
echo   %LOG_DIR%\celery-beat.stdout.log
echo   %LOG_DIR%\celery-beat.stderr.log

endlocal
