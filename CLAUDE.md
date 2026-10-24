# 本仓库写作与 SEO 规范（所有会话必须遵守）

仓库：`suduwuxiantop/vpn-guide`。站点：WordPress `https://main.suduwuxian.top`。品牌：速度无限VPN。
GitHub 上放**摘要版**，完整版发在网站；两边内容必须一致。和用户沟通一律用中文。

## 一、每篇文章的硬性要求

写新文章或改旧文章，发布前逐条自查，缺一条不发：

1. **按搜索意图选题和起标题**
   - 先想清楚用户会搜什么：问题句（"怎么装""打不开怎么办""提示 XX 不可用"）、报错原文（`0x80131500`、`Unsupported country`）、设备和场景（"国内""Windows""安卓"）、年份（2026）。
   - 标题 = 核心关键词 + 痛点/问题 + 年份，核心词放前面，尽量控制在 30 个汉字左右（搜索结果超过会被截断）。
   - H2/H3 用用户的原话写，报错原文要出现在小标题或正文里。
   - URL slug 用英文短横线小写（如 `v2rayn-subscription-beginner-tutorial`），不用中文 slug。
   - H1 下一行写 `<!-- description: ... -->`：SEO 描述，中文 70～80 字，包含核心关键词和文章能解决的问题；GitHub 不显示，发布脚本会写入摘要和 SEO 插件。
2. **开头先给答案**：第一段 2～3 句话直接回答"为什么/怎么办"，方便 Google 摘要、ChatGPT 和 Claude 引用；然后是"本文要点"列表。
3. **配图**：每篇至少 3 张图——1 张封面图 + 至少 2 张正文图（流程图、对比图、步骤示意、真实截图）。
   - 图片放 `images/<slug>/`，WebP 格式，宽 1200px 左右，单张尽量 < 150KB，英文文件名。
   - 每张图写准确的中文 alt（描述图里画的是什么，不堆关键词），图下加一行说明。
   - 只用自己生成的图、自己截的图或明确可商用的图；不盗图、不热链别人的图片。
4. **引用来源**：文末 `## 参考资料` 至少 3 条外部权威来源（官方帮助中心、官方文档、GitHub 仓库/Wiki、标准文档），正文涉及的事实就近加链接。
   - 每个链接必须查证存在（WebSearch/WebFetch），**不许编造 URL**；查不到就不写这条。
   - 涉及版本号、菜单名、系统要求、支持地区这类会变的信息，以官方页面为准，写明"截至 2026 年 X 月"。
5. **站内互链**：正文至少 3 处链到本站相关文章，锚文本要有描述性（不要用"点这里"）；文末保留"相关阅读"。
6. **常见问题（FAQ）**：`## 常见问题` 3～5 个问答，问题用用户会搜的原话，答案 1～3 句直接说结论（便于 FAQ 结构化数据和 AI 摘录）。
7. **速查表**：排错类文章必须有"现象 / 原因 / 解决"表格。
8. **作者与时间（E-E-A-T）**：文章开头注明 `作者：速度无限技术团队 ｜ 最后更新：YYYY-MM-DD`；内容有实测就写清楚测试环境。
9. **结尾 CTA**：保留统一推广语（见现有文章末尾），不夸大、不承诺"永不失联"之类。
10. **禁止**：堆砌关键词、编造数据或用户评价、推荐接码平台/共享账号/破解版等违反服务条款的做法、写过时的模型名或版本号。

## 二、GitHub 摘要版格式

网站发布后，GitHub 上的同名文件改成摘要版：H1 标题 → 作者与更新时间 → 1 段导语 → `## 本文要点` → 封面图 → 速查表（如有）→ `> 📖 **完整内容请阅读原文**：[标题](网站链接)` → 推广语。
参考 `articles/node-timeout-troubleshooting.md`。README 文章合集按分类同步新增条目。

## 三、网站技术 SEO 标准（体检与修复都按这份）

参照用户提供的 maglau.com 体检报告标准，WordPress 站点逐项检查：

| 类别 | 标准 |
|---|---|
| 元数据 | 每页独立 title、meta description（中文 70～80 字）、canonical；首页 title 含品牌 + 核心词 |
| 抓取 | `/robots.txt` 返回 text/plain 且声明 sitemap；sitemap 返回 XML 并提交 Google Search Console 和 Bing 网站管理员工具 |
| AI 搜索 | robots.txt 不屏蔽 Googlebot、Bingbot、OAI-SearchBot、GPTBot、ChatGPT-User、ClaudeBot、Claude-SearchBot、Claude-User、PerplexityBot；可加 `/llms.txt`；开启 IndexNow（Bing / ChatGPT 搜索依赖 Bing 索引） |
| 结构化数据 | 全站 Organization + WebSite；文章页 Article（含 author、datePublished、dateModified、image）+ BreadcrumbList；有 FAQ 的文章加 FAQPage |
| 社交分享 | og:title / og:description / og:image / twitter:card 齐全 |
| 状态码 | 不存在的页面返回真 404，不能 200 软 404；http→https、www→裸域（或反之）统一 301 |
| 语言 | `<html lang="zh-CN">`；如有多语言要 hreflang 互指 + x-default |
| 性能 | 静态资源长缓存（Cache-Control）、图片 WebP + 宽高属性 + 懒加载、移动端无横向溢出、海外 CDN |
| 安全头 | HSTS、X-Content-Type-Options、X-Frame-Options、Referrer-Policy |
| 内容 | 无空壳/过薄文章；图片 alt 与图片一致；URL 无空格/括号/超长中文编码 |

改网站任何设置前先告诉用户要改什么、为什么，得到同意再动手；每项修改都要用实测结果验证（curl 输出、页面源码），不接受"已修改"的口头结论。

## 四、工具（依赖：`pip install markdown requests beautifulsoup4 playwright pillow`）

- `tools/check_article.py articles/x.md`：按第一节逐条检查文章，**发布前必须全部 ✅**。
- `tools/make_images.py images/<slug>/images.json`：按配置生成封面图（1200×630）、步骤图、对比表、决策图（WebP）。新文章先写 `images.json` 再运行；有真实截图时一并放进同一目录。
- `tools/wp_publish.py --status publish --category 分类 slug ...`：把完整版发布到 WordPress，上传配图到媒体库并设特色图片、改写站内互链、写 SEO 描述；先 `--dry-run` 预览。凭据读取环境变量 `WP_URL`、`WP_USER`、`WP_APP_PASSWORD`，**不得打印或提交凭据**。摘要版会被拒绝发布。
- `tools/seo_audit.py --render > report.md`：按第三节标准做只读体检，输出按 P0/P1/P2 排序的问题清单。

## 五、发布流程

写完整版 → `make_images.py` 生成配图 → `check_article.py` 全部通过 → `wp_publish.py --dry-run` → 正式发布并逐篇打开确认 200 → GitHub 改摘要版并链接网站原文 → README 更新 → 提交推送。

## 六、提交规范

提交作者：`速度无限 | 高可用架构VPN | Claude/Gpt/Gemini可用VPN | 流媒体VPN <107822428+suduwuxiantop@users.noreply.github.com>`；提交信息 `docs: ...` 中文；用户已同意直接推送 main。
