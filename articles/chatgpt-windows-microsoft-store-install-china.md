# 国内 Windows 微软商店安装 ChatGPT：搜不到、0x80131500 怎么办（2026）
<!-- description: 国内 Windows 微软商店搜不到 ChatGPT、报错 0x80131500 或提示地区不可用？开 TUN、改系统地区、运行 wsreset 后安装，附新版与 ChatGPT Classic 区别和排错表。 -->

作者：速度无限技术团队 ｜ 最后更新：2026-10-24

**简短回答**：国内 Windows 电脑在微软商店搜不到 ChatGPT，是因为 ChatGPT 没有在中国区商店上架；开了代理商店还是打不开，是因为微软商店属于 UWP 应用，默认不走系统代理。解决办法是：选美国等支持地区的节点并开启 **TUN 模式** → 把 Windows 的"国家或地区"改成美国 → 运行 `wsreset.exe` 重置商店 → 搜索并安装发布者为 OpenAI 的 ChatGPT。整个过程 10 分钟左右。

## 本文要点

- **为什么搜不到**：ChatGPT 没有在中国大陆区的微软商店上架，商店按"Windows 设置里的国家或地区"决定显示哪些应用，跟 IP 无关。
- **为什么开了代理商店还打不开**：UWP 应用默认不能访问本机 `127.0.0.1`，系统代理对它无效，要用 TUN 模式。
- **新版和旧版**：2026 年 7 月起，OpenAI 推出整合了 Chat、Work 和 Codex 的新版 ChatGPT 桌面应用，旧版改名为 **ChatGPT Classic**，两个都在商店里，都能用。
- **节点**：美国、日本、新加坡、台湾都可以，**不要用香港**，香港不在 OpenAI 支持的地区里。
- **装完之后**：地区可以改回中国，但 ChatGPT 联网仍然需要代理，建议一直开着 TUN。

![国内 Windows 从微软商店安装 ChatGPT 教程封面：搜不到、0x80131500、地区不可用、登录转圈一篇解决](../images/chatgpt-windows-microsoft-store-install-china/cover.webp)

## 常见问题速查表

| 现象 | 最可能的原因 | 怎么解决 |
|---|---|---|
| 商店里搜不到 ChatGPT | 地区还是中国，或缓存没刷新 | 地区改美国 → `wsreset.exe` → 或从 chatgpt.com/download 进入 |
| 提示"此应用在你所在的国家或地区不可用" | 商店按系统地区判断 | 同上 |
| 商店打不开，错误 `0x80131500` 或"出了点问题" | UWP 回环限制，商店进不了代理 | 开 TUN，或用 CheckNetIsolation 解除限制 |
| 一直卡在"正在下载" | 下载队列卡住或节点慢 | 暂停后继续；换速度快的节点；重启电脑 |
| 打开 ChatGPT 白屏、转圈 | 应用流量没走代理 | 开 TUN，完全关闭应用后重开 |
| 提示 `Unsupported country, region, or territory` | 节点在香港或不支持的地区 | 换美国 / 日本 / 新加坡节点 |
| 登录时人机验证一直循环 | 节点 IP 被大量共用、被风控 | 换节点，优先"原生 IP"节点 |
| 对话中途断开、Network Error | 节点不稳或自动切换 | 固定一个节点，参考[节点全部超时怎么办](node-timeout-troubleshooting.md) |

> 📖 **完整内容请阅读原文**：[国内 Windows 微软商店安装 ChatGPT：搜不到、0x80131500 怎么办（2026）](https://main.suduwuxian.top/chatgpt-windows-microsoft-store-install-china/)

原文包含分步骤操作说明、示意图、常见问题解答和官方参考资料。

---

> 速度无限：Hysteria2 / VLESS+Reality / AnyTLS 多协议节点，基础套餐 19 元/月起，[qaz.suduwuxian.top](https://qaz.suduwuxian.top)。节点公告和更新请关注 Telegram 频道：[t.me/suduwuxiantop](https://t.me/suduwuxiantop)
