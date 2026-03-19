# git-scrub

清理洩密步驟紀錄

- 產生備份分支：pre-scrub-backup-*
- 使用 git filter-branch 刪除 .openclaw/ 下的 token 檔
- 強制推送（force push）到遠端

警告：改寫歷史會變動 commit hashes，協作者需重新 clone 或重設分支
