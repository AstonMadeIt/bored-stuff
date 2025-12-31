#!/bin/bash
# Test Git Authentication and Push
# This script tests if we can push to GitHub

cd "$(dirname "$0")"

echo "🧪 TESTING GITHUB AUTHENTICATION"
echo "=================================="
echo ""

# Check git status
echo "📋 Git Status:"
git status --short
echo ""

# Check remote
echo "📋 Remote Configuration:"
git remote -v
echo ""

# Test SSH connection
echo "🔐 Testing SSH Authentication:"
if ssh -T git@github.com 2>&1 | grep -q "successfully authenticated"; then
    echo "   ✅ SSH authentication successful!"
    USE_SSH=true
elif ssh -T git@github.com 2>&1 | grep -q "Hi"; then
    echo "   ✅ SSH connection works (may show warning, that's OK)"
    USE_SSH=true
else
    echo "   ⚠️  SSH authentication failed or not configured"
    USE_SSH=false
fi
echo ""

# Create a test file
echo "📝 Creating test file..."
echo "Test commit $(date)" > test_git_push.txt
git add test_git_push.txt

# Try to commit
echo "💾 Committing test file..."
git commit -m "Test: GitHub authentication $(date '+%Y-%m-%d %H:%M:%S')" > /dev/null 2>&1

if [ $? -eq 0 ]; then
    echo "   ✅ Commit successful"
    echo ""
    
    # Try to push
    echo "📤 Testing push to GitHub..."
    
    # Check which branch we're on
    BRANCH=$(git branch --show-current 2>/dev/null || echo "main")
    echo "   Branch: $BRANCH"
    
    # Try push
    if git push -u origin $BRANCH 2>&1 | tee /tmp/git_push_test.log; then
        echo ""
        echo "   ✅ PUSH SUCCESSFUL!"
        echo ""
        echo "🎉 GitHub authentication is working!"
        echo ""
        
        # Clean up test file
        git rm test_git_push.txt > /dev/null 2>&1
        git commit -m "Remove test file" > /dev/null 2>&1
        git push > /dev/null 2>&1
        
    else
        echo ""
        echo "   ❌ Push failed"
        echo ""
        echo "📋 Troubleshooting:"
        echo ""
        
        if [ "$USE_SSH" = false ]; then
            echo "   Option 1: Set up SSH keys"
            echo "   - Check: https://docs.github.com/en/authentication/connecting-to-github-with-ssh"
            echo ""
            echo "   Option 2: Use HTTPS with Personal Access Token"
            echo "   - Change remote: git remote set-url origin https://github.com/AstonMadeIt/bored-stuff.git"
            echo "   - Create token: https://github.com/settings/tokens"
            echo "   - Use token as password when pushing"
        else
            echo "   SSH works but push failed. Possible issues:"
            echo "   - Repository permissions"
            echo "   - Branch protection"
            echo "   - Network issues"
        fi
        
        echo ""
        echo "   Full error log saved to: /tmp/git_push_test.log"
    fi
else
    echo "   ⚠️  Commit failed (may need git config)"
    echo ""
    echo "   Setting up git config..."
    git config user.name "Pro Sports Intel AI" 2>/dev/null
    git config user.email "a.fleming@example.com" 2>/dev/null
    echo "   ✅ Git config set"
fi

echo ""
echo "=================================="

