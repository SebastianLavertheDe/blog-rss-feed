# TODO

## gwern.net RSS 源失效

- 当前配置使用 `gwern.substack.com/feed`，该 newsletter 自 2021年6月起停更
- gwern.net 主站仍在活跃更新内容，但没有提供 RSS/Atom feed
- `gwern.net/feed` 重定向到已停更的 substack feed
- 已在 config.yaml 中设为 `enabled: false`

**解决方案：** 需要写一个 scraping 脚本（参考 anthropic_engineering_rss.py）抓取 gwern.net 页面生成 RSS feed。

## NVIDIA AI Blog 分类 feed 不活跃（已修复）

- 已将 RSS URL 从 `/blog/category/deep-learning/feed/` 换为主 feed `/feed/`
- 主 feed 包含所有分类内容，不仅限于 AI/deep-learning

## Substack 源在 GitHub Actions 中抓取失败

**现象：** 以下 Substack 源本地落后于上游，自 5月17日手动刷新后再没被 Actions 更新：

| 源 | 本地最新 | 上游最新 | 落后 |
|---|---|---|---|
| Import AI (`importai.substack.com/feed`) | 5月11日 | 5月26日 | ~15天 |
| garymarcus.substack.com | 5月17日 | 5月26日 | ~9天 |
| worksonmymachine.substack.com | 5月17日 | 5月24日 | ~7天 |
| The Batch (`charonhub.deeplearning.ai/rss/`) | 5月15日 | 5月22日 | ~7天 |

**排查进度：**

1. GitHub Actions 每小时正常运行，最近提交频繁（每天多次），状态均为 success
2. 非 Substack 源（如 danieldelaney.net、arstechnica、bensbites、ahead_of_ai）在最新提交中正常更新
3. 所有 Substack 源（包括 lcamtuf 等与上游一致的）自 5月17日后都没被 Actions 更新过
4. 本地测试抓取这 4 个 feed 全部成功，ElementTree 解析正常
5. `external_rss_importer.py` 每次成功运行会写入新的 `lastBuildDate`，如果文件没变说明脚本没成功执行
6. 脚本配置正确（enabled: true），无超时限制
7. GitHub Actions 日志获取失败（EOF），无法直接查看运行时错误

**可能原因：**

- Substack 对 GitHub Actions IP 段做了限流/封禁（所有 Substack 源同时失败）
- `requests` 库在 Actions 环境中请求 Substack 时被 403/429 拒绝
- 脚本失败但 `run_all.py` 默认 `stop_on_error: false`，静默跳过继续执行

**待验证：**

- [ ] 获取 Actions 运行日志确认具体报错信息
- [ ] 在 Actions 中添加 Substack 专用 User-Agent 或重试逻辑
- [ ] 考虑为 Substack 源添加 `--use-feedparser` 参数（Import AI 已有此配置但仍失败）
- [ ] worksonmymachine.substack.com 已迁移到 worksonmymachine.ai，更新 rssUrl

## danieldelaney.net 短暂落后（已自愈）

- 在排查时发现本地落后上游 8 天，但最新 Actions 提交已包含更新
- 属于正常延迟，无需处理
