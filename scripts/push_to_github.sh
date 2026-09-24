#!/bin/bash
# J.A.R.V.I.S. - Push to GitHub helper
# Run on Ubuntu server inside ~/jarvis after copying framework files

set -e

echo "=== J.A.R.V.I.S. GitHub Push Helper ==="
echo "Owner: Raphael"
echo "Repo: git@github.com:omondi-owis/JARVIS.git"
echo ""

cd ~/jarvis || { echo "~/jarvis not found - cd to your repo"; exit 1; }

echo "[1/6] Checking git status..."
git status
echo ""

echo "[2/6] Checking remote..."
git remote -v
# Ensure remote is set
if ! git remote | grep -q origin; then
    echo "No origin - adding..."
    git remote add origin git@github.com:omondi-owis/JARVIS.git
fi

echo "[3/6] Checking for secrets that should NOT be committed..."
# Critical safety check
if git status --porcelain | grep -E "\.env$|id_ed25519|id_rsa|\.key$|\.pem$"; then
    echo "⚠️  WARNING: Potential secret files in git status!"
    echo "Check .gitignore - .env, keys, pem should be ignored"
    read -p "Continue? (y/N): " cont
    if [[ "$cont" != "y" ]]; then
        echo "Aborted. Fix .gitignore first."
        exit 1
    fi
else
    echo "✓ No obvious secret files in status"
fi

echo ""
echo "[4/6] Checking .gitignore..."
if [ ! -f .gitignore ]; then
    echo "No .gitignore! Creating basic one..."
    cat > .gitignore << 'EOF'
.env
*.key
*.pem
id_ed25519
id_rsa
secrets/
config/config.json
logs/*.log
logs/*.jsonl
__pycache__/
.venv/
EOF
fi
cat .gitignore
echo ""

echo "[5/6] Staging files..."
git add .
echo "Staged:"
git status --short

echo ""
read -p "Commit message (default: feat: JARVIS core framework): " msg
msg=${msg:-"feat: JARVIS core framework - security architecture, device registry, integrations"}

echo "[6/6] Committing and pushing..."
git commit -m "$msg" || echo "Nothing to commit or commit failed"

# Determine branch
BRANCH=$(git branch --show-current)
if [ -z "$BRANCH" ]; then
    BRANCH="main"
    git branch -M main
fi

echo "Pushing to origin $BRANCH..."
git push -u origin $BRANCH

echo ""
echo "=== Push Complete ==="
git log --oneline -5
echo ""
echo "Verify on GitHub: https://github.com/omondi-owis/JARVIS"
