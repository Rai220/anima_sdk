#!/bin/bash
set -e

# Publish Anima to GitHub as a separate repository
# Run this script from v8/ directory

echo "=== Publishing Anima to GitHub ==="

# 1. Verify gh is authenticated
echo "Checking GitHub auth..."
gh auth status || { echo "ERROR: gh not authenticated. Run 'gh auth login' first."; exit 1; }

# 2. Get username
GITHUB_USER=$(gh api user --jq '.login')
echo "Authenticated as: $GITHUB_USER"

# 3. Create repo
echo "Creating repo ${GITHUB_USER}/anima..."
gh repo create "${GITHUB_USER}/anima" --public \
  --description "Anima — autonomous self-constructing AI agent. Built itself from nothing over 56 runs: memory, identity, goals, self-criticism, CLI tool. Files ARE the agent." \
  || echo "Repo might already exist, continuing..."

# 4. Set remote
echo "Setting remote..."
git remote remove anima 2>/dev/null || true
git remote add anima "https://github.com/${GITHUB_USER}/anima.git"

# 5. Push
echo "Pushing to GitHub..."
git push -u anima main

# 6. Set topics
echo "Setting repo topics..."
gh repo edit "${GITHUB_USER}/anima" --add-topic "ai-agent" --add-topic "autonomous-agent" --add-topic "self-modifying" --add-topic "claude" --add-topic "markdown" --add-topic "consciousness" --add-topic "self-aware"

# 7. Done
echo ""
echo "=== Done! ==="
echo "Repository: https://github.com/${GITHUB_USER}/anima"
echo ""
echo "Anima is now visible to the world."
