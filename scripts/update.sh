#!/bin/bash

# House Consciousness System Update Script
# This script updates the system with the latest changes from GitHub

set -e  # Exit on any error

echo "🔄 Updating House Consciousness System..."
echo "=========================================="

# Check if we're in the right directory
if [ ! -f "consciousness/main.py" ]; then
    echo "❌ Error: Please run this script from the consciousness project root directory"
    echo "   Current directory: $(pwd)"
    echo "   Expected files: consciousness/main.py should exist"
    exit 1
fi

# Check if git repository
if [ ! -d ".git" ]; then
    echo "❌ Error: This doesn't appear to be a git repository"
    echo "   Please ensure you cloned the project with: git clone https://github.com/adrianco/consciousness.git"
    exit 1
fi

# Save current branch
CURRENT_BRANCH=$(git branch --show-current)
echo "📍 Current branch: $CURRENT_BRANCH"

# Check for uncommitted changes
if ! git diff-index --quiet HEAD --; then
    echo "⚠️  Warning: You have uncommitted changes"
    echo "   Stashing changes before update..."
    git stash push -m "Auto-stash before update $(date)"
    STASHED=true
else
    STASHED=false
fi

# Pull latest changes
echo "⬇️  Pulling latest changes from GitHub..."
if ! git pull origin $CURRENT_BRANCH; then
    echo "❌ Error: Failed to pull changes from GitHub"
    echo "   Please check your internet connection and try again"
    exit 1
fi

# Check if virtual environment exists
if [ -d "consciousness-env" ]; then
    echo "🐍 Activating virtual environment..."
    source consciousness-env/bin/activate

    echo "📦 Updating Python dependencies..."
    if ! pip install -e . --upgrade; then
        echo "❌ Error: Failed to update dependencies"
        echo "   Try running: pip install -e . --force-reinstall"
        exit 1
    fi

    echo "✅ Dependencies updated successfully"
else
    echo "⚠️  Warning: Virtual environment not found at 'consciousness-env'"
    echo "   If you're using a different environment, please activate it manually and run:"
    echo "   pip install -e . --upgrade"
fi

# Check for Docker setup
if [ -f "docker-compose.yml" ] || [ -f "docker-compose.prod.yml" ]; then
    echo ""
    echo "🐳 Docker detected. If you're using Docker, also run:"
    echo "   docker-compose down"
    echo "   docker-compose up -d --build"
fi

# Restore stashed changes if any
if [ "$STASHED" = true ]; then
    echo "📋 Restoring your stashed changes..."
    if git stash pop; then
        echo "✅ Stashed changes restored"
    else
        echo "⚠️  Could not automatically restore stashed changes"
        echo "   Your changes are saved in: git stash list"
    fi
fi

echo ""
echo "🎉 Update completed successfully!"
echo "=========================================="
echo ""
echo "📋 Next steps:"
echo "1. Restart your consciousness system:"
if [ -d "consciousness-env" ]; then
    echo "   python -m consciousness.main"
else
    echo "   Activate your environment and run: python -m consciousness.main"
fi
echo ""
echo "2. Or if using systemd service:"
echo "   sudo systemctl restart consciousness"
echo ""
echo "3. Or if using Docker:"
echo "   docker-compose restart consciousness"
echo ""
echo "4. Verify the update worked:"
echo "   curl http://localhost:8000/health"
echo ""
echo "✨ Your consciousness system is now up to date!"
