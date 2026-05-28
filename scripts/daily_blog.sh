#!/bin/bash
# Daily Consulting24 Blogger pipeline:
#   1) publish today's batch of Blogger posts (consulting24_blog.py)
#   2) re-sync the site's /blog/ hub so EVERY Blogger guide is linked (link_blogger.py)
#   3) commit + push so the new links deploy live to www.consulting24.co
# Wired into the com.consulting24.blog LaunchAgent (runs daily).
set -u
REPO=/Users/master/panama-crypto-license
PY=/usr/bin/python3
cd "$REPO" || exit 1

mkdir -p logs
ts() { date "+%Y-%m-%d %H:%M:%S"; }
echo "[$(ts)] daily_blog: start" >> logs/daily_blog.log

# 1) publish today's Blogger batch (don't abort the rest on failure)
"$PY" scripts/consulting24_blog.py >> logs/daily_blog.log 2>&1 || echo "[$(ts)] poster nonzero" >> logs/daily_blog.log

# 2) link ALL published Blogger guides from the site blog hub
"$PY" scripts/link_blogger.py >> logs/daily_blog.log 2>&1 || echo "[$(ts)] linker nonzero" >> logs/daily_blog.log

# 3) deploy if anything changed
git add blog/index.html config/blog_posted.json 2>/dev/null
if ! git diff --cached --quiet 2>/dev/null; then
  git commit -q -m "daily: publish Blogger batch + sync site blog links" >> logs/daily_blog.log 2>&1
  git push -q origin main >> logs/daily_blog.log 2>&1 && echo "[$(ts)] pushed" >> logs/daily_blog.log
else
  echo "[$(ts)] no changes to deploy" >> logs/daily_blog.log
fi
echo "[$(ts)] daily_blog: done" >> logs/daily_blog.log
