#!/bin/bash
# Quick GitHub Authentication Test
# Tests if git push will work for scheduled scripts

cd "$(dirname "$0")"

echo "🧪 QUICK GITHUB AUTH TEST"
echo "========================="
echo ""

# Test SSH
echo "🔐 Testing SSH connection..."
if ssh -T git@github.com 2>&1 | grep -qE "(successfully authenticated|Hi AstonMadeIt)"; then
    echo "   ✅ SSH authentication: WORKING"
    SSH_OK=true
else
    echo "   ❌ SSH authentication: FAILED"
    SSH_OK=false
fi
echo ""

# Test git fetch
echo "📥 Testing git fetch..."
FETCH_OUTPUT=$(git fetch origin 2>&1)
if echo "$FETCH_OUTPUT" | grep -qE "(From|Already up to date|fatal)" && ! echo "$FETCH_OUTPUT" | grep -q "fatal.*permission"; then
    echo "   ✅ Git fetch: WORKING"
    FETCH_OK=true
else
    echo "   ⚠️  Git fetch: May have issues"
    FETCH_OK=false
fi
echo ""

# Test actual push capability
echo "🧪 Testing push capability..."
BRANCH=$(git branch --show-current 2>/dev/null || echo "main")
if git push origin "$BRANCH" --dry-run 2>&1 | grep -qE "(Everything up-to-date|To|Would push)"; then
    echo "   ✅ Git push: READY"
    PUSH_OK=true
else
    echo "   ⚠️  Git push: May need attention"
    PUSH_OK=false
fi
echo ""

# Summary
echo "========================="
if [ "$SSH_OK" = true ]; then
    echo "✅ GitHub authentication is CONFIGURED and WORKING!"
    echo ""
    echo "Your scheduled scripts should be able to push to GitHub."
    echo "The scripts will automatically:"
    echo "  - Fetch latest changes"
    echo "  - Merge remote changes if needed"
    echo "  - Commit HTML files"
    echo "  - Push to origin"
    echo ""
    if [ "$PUSH_OK" = true ]; then
        echo "✅ Push capability confirmed!"
    fi
else
    echo "⚠️  SSH authentication needs setup"
    echo ""
    echo "Check: https://docs.github.com/en/authentication/connecting-to-github-with-ssh"
fi
echo ""

