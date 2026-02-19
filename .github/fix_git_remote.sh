#!/bin/bash
# fix_git_remote.sh
# 用途：修復 origin 網址 + 正確推送 feat-financial-dashboard-api

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}🔧 修復 Git 遠端網址${NC}"

# 1. 顯示當前遠端
echo "當前遠端："
git remote -v

# 2. 移除壞掉的 origin
echo -e "${YELLOW}移除錯誤的 origin...${NC}"
git remote remove origin 2>/dev/null

# 3. 重新加入正確的 origin（請確認您的正確網址）
# 這裡用 608304.jpg 中看到的 universe-temp 網址為例
CORRECT_URL="https://github.com/AnonymousTalent/-init_universe_page---repo-lightning-empire-universe2025--git"

echo -e "${GREEN}加入正確的 origin: $CORRECT_URL${NC}"
git remote add origin "$CORRECT_URL"

# 4. 確認目前分支
CURRENT_BRANCH=$(git branch --show-current)
echo -e "目前分支：${YELLOW}$CURRENT_BRANCH${NC}"

# 5. 如果是 feat-financial-dashboard-api，就直接推送
if [ "$CURRENT_BRANCH" == "feat-financial-dashboard-api" ]; then
    echo -e "${GREEN}推送分支到 origin...${NC}"
    git push -u origin feat-financial-dashboard-api
else
    echo -e "${YELLOW}不在 feat-financial-dashboard-api 分支，先切換${NC}"
    git checkout -b feat-financial-dashboard-api 2>/dev/null || git checkout feat-financial-dashboard-api
    git push -u origin feat-financial-dashboard-api
fi

# 6. 驗證
echo -e "${GREEN}✅ 修復完成，遠端狀態：${NC}"
git remote -v