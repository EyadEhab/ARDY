@echo off
title ARDY - Training Models (Phase 2)
cd /d "%~dp0.."

echo ========================================
echo   ARDY Smart Agriculture
echo   Training Phase 2 Models
echo ========================================
echo.

docker-compose run --rm model-trainer python retrain_models.py

echo.
echo ========================================
echo   Done!
echo ========================================

pause
