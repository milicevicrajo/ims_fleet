@echo off
setlocal

set NSSM=C:\nssm\nssm.exe
set PROJECT_DIR=C:\DjangoApps\ims_erp
set VENV_DIR=C:\DjangoApps\venv
set PYTHONPATH=C:\DjangoApps\ims_erp
set DJANGO_SETTINGS_MODULE=ims_erp.settings.production

set REDIS_EXE=C:\Redis\redis-server.exe
set REDIS_CONF=C:\Redis\redis.windows.conf

set WORKER_SERVICE=IMS_Fleet_Celery_Worker
set BEAT_SERVICE=IMS_Fleet_Celery_Beat
set REDIS_SERVICE=IMS_Fleet_Redis

set LOG_DIR=C:\DjangoApps\logs

if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

echo Installing Redis service...
"%NSSM%" install %REDIS_SERVICE% "%REDIS_EXE%" "%REDIS_CONF%"
"%NSSM%" set %REDIS_SERVICE% AppDirectory C:\Redis
"%NSSM%" set %REDIS_SERVICE% AppStdout "%LOG_DIR%\redis.stdout.log"
"%NSSM%" set %REDIS_SERVICE% AppStderr "%LOG_DIR%\redis.stderr.log"
"%NSSM%" set %REDIS_SERVICE% Start SERVICE_AUTO_START

echo Installing Celery worker service...
"%NSSM%" install %WORKER_SERVICE% "%VENV_DIR%\Scripts\celery.exe"
"%NSSM%" set %WORKER_SERVICE% AppDirectory "%PROJECT_DIR%"
"%NSSM%" set %WORKER_SERVICE% AppParameters -A ims_erp worker -l info -P solo -Q default,sync,selenium
"%NSSM%" set %WORKER_SERVICE% AppEnvironmentExtra DJANGO_SETTINGS_MODULE=%DJANGO_SETTINGS_MODULE% PYTHONPATH=%PYTHONPATH%
"%NSSM%" set %WORKER_SERVICE% AppStdout "%LOG_DIR%\celery-worker.stdout.log"
"%NSSM%" set %WORKER_SERVICE% AppStderr "%LOG_DIR%\celery-worker.stderr.log"
"%NSSM%" set %WORKER_SERVICE% AppRotateFiles 1
"%NSSM%" set %WORKER_SERVICE% AppRotateOnline 1
"%NSSM%" set %WORKER_SERVICE% AppRotateBytes 10485760
"%NSSM%" set %WORKER_SERVICE% Start SERVICE_AUTO_START
"%NSSM%" set %WORKER_SERVICE% AppRestartDelay 5000

echo Installing Celery beat service...
"%NSSM%" install %BEAT_SERVICE% "%VENV_DIR%\Scripts\celery.exe"
"%NSSM%" set %BEAT_SERVICE% AppDirectory "%PROJECT_DIR%"
"%NSSM%" set %BEAT_SERVICE% AppParameters -A ims_erp beat --scheduler django_celery_beat.schedulers:DatabaseScheduler -l info
"%NSSM%" set %BEAT_SERVICE% AppEnvironmentExtra DJANGO_SETTINGS_MODULE=%DJANGO_SETTINGS_MODULE% PYTHONPATH=%PYTHONPATH%
"%NSSM%" set %BEAT_SERVICE% AppStdout "%LOG_DIR%\celery-beat.stdout.log"
"%NSSM%" set %BEAT_SERVICE% AppStderr "%LOG_DIR%\celery-beat.stderr.log"
"%NSSM%" set %BEAT_SERVICE% AppRotateFiles 1
"%NSSM%" set %BEAT_SERVICE% AppRotateOnline 1
"%NSSM%" set %BEAT_SERVICE% AppRotateBytes 10485760
"%NSSM%" set %BEAT_SERVICE% Start SERVICE_AUTO_START
"%NSSM%" set %BEAT_SERVICE% AppRestartDelay 5000

echo Starting services...
net start %REDIS_SERVICE%
net start %WORKER_SERVICE%
net start %BEAT_SERVICE%

echo Done.
endlocal
