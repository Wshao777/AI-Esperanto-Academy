#!/bin/bash
# continue_merge_after_fix.sh
# 用途：修復遠端 + 繼續合併到 Ai-main

echo "⚡ 繼續合併程序"

# 1. 先修復遠端
bash fix_git_remote.sh

# 2. 確認遠端正常
if git ls-remote origin > /dev/null 2>&1; then
    echo -e "${GREEN}✅ 遠端可存取${NC}"
    
    # 3. 抓取最新內容
    git fetch origin
    
    # 4. 合併到本地 feat-financial-dashboard-api
    git checkout -b feat-financial-dashboard-api origin/feat-financial-dashboard-api 2>/dev/null || git checkout feat-financial-dashboard-api
    
    # 5. 複製到 Ai-main
    mkdir -p Ai-main/imports/init_universe_page
    
    # 複製所有檔案（排除 .git）
    find . -path './.git' -prune -o -type f -print | while read file; do
        if [ -f "$file" ]; then
            cp --parents "$file" Ai-main/imports/init_universe_page/ 2>/dev/null
        fi
    done
    
    echo -e "${GREEN}✅ 已合併到 Ai-main/imports/init_universe_page/${NC}"
else
    echo -e "${RED}❌ 遠端仍無法存取，請檢查：${NC}"
    echo "1. 網址是否正確"
    echo "2. 是否有存取權限"
    echo "3. 是否需要 GitHub 帳號密碼/Token"
fi

# 6. 回到 Ai-main
git checkout Ai-main 2>/dev/null || git checkout -b Ai-main

echo -e "${GREEN}✅ 繼續完成${NC}"