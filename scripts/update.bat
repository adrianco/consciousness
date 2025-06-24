@echo off
REM House Consciousness System Update Script for Windows
REM This script updates the system with the latest changes from GitHub

echo 🔄 Updating House Consciousness System...
echo ==========================================

REM Check if we're in the right directory
if not exist "consciousness\main.py" (
    echo ❌ Error: Please run this script from the consciousness project root directory
    echo    Current directory: %CD%
    echo    Expected files: consciousness\main.py should exist
    pause
    exit /b 1
)

REM Check if git repository
if not exist ".git" (
    echo ❌ Error: This doesn't appear to be a git repository
    echo    Please ensure you cloned the project with: git clone https://github.com/adrianco/consciousness.git
    pause
    exit /b 1
)

REM Get current branch
for /f %%i in ('git branch --show-current') do set CURRENT_BRANCH=%%i
echo 📍 Current branch: %CURRENT_BRANCH%

REM Check for uncommitted changes
git diff-index --quiet HEAD --
if %errorlevel% neq 0 (
    echo ⚠️  Warning: You have uncommitted changes
    echo    Stashing changes before update...
    git stash push -m "Auto-stash before update %date% %time%"
    set STASHED=true
) else (
    set STASHED=false
)

REM Pull latest changes
echo ⬇️  Pulling latest changes from GitHub...
git pull origin %CURRENT_BRANCH%
if %errorlevel% neq 0 (
    echo ❌ Error: Failed to pull changes from GitHub
    echo    Please check your internet connection and try again
    pause
    exit /b 1
)

REM Check if virtual environment exists
if exist "consciousness-env" (
    echo 🐍 Activating virtual environment...
    call consciousness-env\Scripts\activate.bat

    echo 📦 Updating Python dependencies...
    pip install -e . --upgrade
    if %errorlevel% neq 0 (
        echo ❌ Error: Failed to update dependencies
        echo    Try running: pip install -e . --force-reinstall
        pause
        exit /b 1
    )

    echo ✅ Dependencies updated successfully
) else (
    echo ⚠️  Warning: Virtual environment not found at 'consciousness-env'
    echo    If you're using a different environment, please activate it manually and run:
    echo    pip install -e . --upgrade
)

REM Check for Docker setup
if exist "docker-compose.yml" (
    echo.
    echo 🐳 Docker detected. If you're using Docker, also run:
    echo    docker-compose down
    echo    docker-compose up -d --build
)

REM Restore stashed changes if any
if "%STASHED%"=="true" (
    echo 📋 Restoring your stashed changes...
    git stash pop
    if %errorlevel% equ 0 (
        echo ✅ Stashed changes restored
    ) else (
        echo ⚠️  Could not automatically restore stashed changes
        echo    Your changes are saved in: git stash list
    )
)

echo.
echo 🎉 Update completed successfully!
echo ==========================================
echo.
echo 📋 Next steps:
echo 1. Restart your consciousness system:
if exist "consciousness-env" (
    echo    python -m consciousness.main
) else (
    echo    Activate your environment and run: python -m consciousness.main
)
echo.
echo 2. Or if using Docker:
echo    docker-compose restart consciousness
echo.
echo 3. Verify the update worked:
echo    curl http://localhost:8000/health
echo.
echo ✨ Your consciousness system is now up to date!
echo.
pause
