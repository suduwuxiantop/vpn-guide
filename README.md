# VPN 科普知识库：科学上网中文教程合集（2026）

> 用大白话把 VPN、代理、机场、加密协议讲明白，不讲黑话。内容涵盖 **ChatGPT / Claude / Gemini 国内访问与安装**、**Clash Verge / v2rayN / 小火箭客户端教程**、**Hysteria2 / VLESS+Reality / AnyTLS 自建节点**和**节点超时等常见故障排查**。

🌐 **官网与完整版文章**：[main.suduwuxian.top](https://main.suduwuxian.top/) ｜ 📢 **Telegram 频道**：[t.me/suduwuxiantop](https://t.me/suduwuxiantop) ｜ ⭐ 觉得有用欢迎 Star

这是一个专注于 **网络加速与隐私保护科普** 的开源文档仓库，目标只有一个：让完全不懂技术的人，也能看懂"科学上网"这件事到底是怎么回事、该怎么挑、怎么避坑。

内容由 **速度无限VPN** 团队整理和原创撰写。我们长期做 VPN 相关的技术服务，写这些文档纯粹是因为：市面上大部分教程要么太"黑话"，要么就是变相的广告软文，真正把原理讲清楚的科普内容反而很少。

## 快速导航

- 🤖 [AI 工具访问与安装](#ai-工具访问与安装)：ChatGPT、Claude、Gemini、Cursor 国内怎么用、怎么装
- 💻 [客户端使用教程](#客户端使用教程)：Clash Verge、v2rayN、小火箭怎么导入订阅
- 🛠️ [故障排查](#故障排查)：节点超时、GitHub 打不开、WhatsApp / Discord 连不上
- 🖥️ [自建节点教程](#自建节点教程)：从买 VPS 到搭好 Hysteria2、VLESS+Reality、AnyTLS、Trojan
- 📡 [协议与线路科普](#协议与线路科普)：协议怎么选、中转和直连、CN2 GIA / IPLC
- ✈️ [机场选择与避坑](#机场选择与避坑)：机场是什么、怎么选、跑路了怎么办
- 🌏 [出海生活与网络安全](#出海生活与网络安全)：流媒体、公共 WiFi、海外双网生活
- 📚 [新手入门系列（docs）](#新手入门系列docs)：从零开始按顺序读

## AI 工具访问与安装

| 文章 | 说明 |
|---|---|
| [国内打不开 ChatGPT、Claude、Gemini？2026 年 AI 工具访问指南](articles/chatgpt-claude-gemini-access-china.md) | 为什么打不开、硬连会遇到什么问题、怎样才算稳定 |
| [国内 Windows 电脑怎么从微软商店安装 ChatGPT？](articles/chatgpt-windows-microsoft-store-install-china.md) | 商店搜不到、`0x80131500` 打不开、登录不支持地区：开 TUN → 改系统地区 → wsreset → 认准 OpenAI 发布者安装 |
| [国内 Windows 电脑怎么安装 Claude 桌面版？](articles/claude-windows-desktop-install-china.md) | 官网下载、TUN 模式、登录与 MCP 工具联网，附白屏 / 地区不可用 / 收不到验证码排查 |
| [Mac 上怎么安装 ChatGPT 和 Claude 桌面版？](articles/mac-chatgpt-claude-install-china.md) | 官网 dmg 免 Apple ID 安装，ChatGPT 需 Apple 芯片；以及自己注册美区 Apple ID 的正确方法 |
| [国内安卓手机怎么安装 ChatGPT？](articles/android-chatgpt-install-china.md) | 判断有无谷歌服务、Google Play 切换国家、APKMirror 下载正版 APK 并核对签名 |
| [Gemini 提示在你所在的国家/地区不可用？](articles/gemini-region-unavailable-fix.md) | 从节点 IP、Google 账号关联地区、浏览器缓存与定位三个方向排查 |
| [Claude Code、Codex 装完打不开？Clash Meta 网络设置与排查指南](articles/claude-code-codex-clash-meta-tun.md) | 浏览器能用、命令行连不上，多半是没开 TUN 模式 |
| [用了 VPN 还是被 Claude 封号？真正的雷区在这里](articles/claude-account-ban-vpn-myth.md) | 封号和 VPN 的关系，以及真正容易触发风控的行为 |
| [ChatGPT 国内稳定使用指南](articles/chatgpt-access-guide.md) | Network Error、Cloudflare 人机验证循环等报错的解决思路 |
| [Claude 稳定访问与防封号指南](articles/claude-access-guide.md) | 落地 IP 怎么选、怎样降低被封概率 |
| [Cursor 开发者网络优化手册](articles/cursor-access-guide.md) | Cursor 一直 Connecting、登录失败、补全延迟高的处理办法 |

## 客户端使用教程

| 文章 | 说明 |
|---|---|
| [Clash Verge 订阅怎么导入？从获取链接到 TUN 模式全教程](articles/clash-verge-subscription-tutorial.md) | Windows / Mac 上最常用的 Mihomo 内核客户端完整上手 |
| [v2rayN 新手订阅教程：从下载到导入订阅、选节点、开代理](articles/v2rayn-subscription-beginner-tutorial.md) | 下载 SelfContained 版、导入通用订阅、测速选节点、系统代理、绕过大陆路由与 TUN 模式 |
| [新晋的 Clash Mi 是什么来头？它会不会取代小火箭？](articles/clash-mi-vs-shadowrocket.md) | 从内核、协议支持、策略组、上手门槛对比 Clash Mi 和 Shadowrocket |

## 故障排查

| 文章 | 说明 |
|---|---|
| [节点全部超时怎么办？Clash Verge、v2rayN、小火箭通用的 8 步排查法](articles/node-timeout-troubleshooting.md) | 订阅状态、设备时间、客户端内核、软件冲突、UDP 限速、测速地址、重启顺序、交叉验证 |
| [为什么测速显示的延迟数字，跟实际用起来的感觉不一样](articles/latency-test-vs-real-experience.md) | Clash 测速忽高忽低，但日常使用完全不卡的原因 |
| [GitHub 在国内打不开、图裂、Raw 文件下载失败？开发者完整解决方案](articles/github-access-china-fix.md) | 网页、图片、git clone、Raw 下载分别怎么处理 |
| [WhatsApp 在国内总是连不上、消息发不出去？](articles/whatsapp-connection-troubleshoot.md) | 真正原因可能不是 VPN |
| [Discord 文字能发，语音却卡在"连接中"？](articles/discord-voice-connection-fix.md) | 语音走 UDP，国内玩家该怎么排查 |
| [独享 IP 连不上？SOCKS5 独享代理正确用法 + 云服务器中转转发完整指南](articles/dedicated-socks5-relay-setup-guide.md) | 独享 SOCKS5 超时排查、指纹浏览器与 Clash Verge 填写方法、中转转发实操 |

## 自建节点教程

| 文章 | 说明 |
|---|---|
| [Hysteria2 小白搭建教程：从买服务器到能用，照着做就行](articles/hysteria2-beginner-setup-guide.md) | 完全新手向操作版，每一步该看到什么结果、卡住了怎么办 |
| [Hysteria2 从零搭建到 Clash Verge 连接：一份能直接跑通的实战教程](articles/hysteria2-server-setup-clash-verge-tutorial.md) | 安装、编辑 config.yaml、放行防火墙、Clash Verge 导入连接 |
| [VLESS+REALITY 从零搭建到 Clash Verge 连接](articles/vless-reality-server-setup-clash-verge-tutorial.md) | 安装 Xray-core、生成密钥对、编辑 config.json、客户端连接 |
| [AnyTLS 从零搭建到 Clash Verge 连接](articles/anytls-server-setup-clash-verge-tutorial.md) | 通过官方 APT 仓库安装 sing-box、配置 AnyTLS 服务端 |
| [Trojan 协议从 0 到 1 完整部署：真证书、双客户端接入与避坑指南](articles/trojan-server-setup-full-guide.md) | 证书申请与自动续期、Clash Verge 和 Shadowrocket 双端接入、443 共存 |
| [Shadowsocks 从 0 到 1 完整部署：原理、搭建与 2026 年还值不值得用](articles/shadowsocks-and-ssr-full-guide.md) | SS 的 AEAD 加密原理、sing-box 搭建，以及 SSR 的原理与部署 |
| [NaiveProxy 从 0 到 1 完整部署：伪装成真实 Chrome 流量的代理协议](articles/naive-server-setup-full-guide.md) | 复用 Chromium 网络栈的原理、sing-box 部署，以及该用什么客户端 |
| [NaiveProxy 小白搭建教程：从买服务器到能用，照着做就行](articles/naive-beginner-setup-guide.md) | 完全新手向操作版，特别提醒 Clash Verge 不支持该协议 |

## 协议与线路科普

| 文章 | 说明 |
|---|---|
| [节点和协议怎么选？Hysteria2、VLESS+Reality、AnyTLS 对比与宽带适配指南](articles/protocol-choice-guide.md) | 电信联通用 Hysteria2，移动宽带连不上就换 VLESS+Reality / AnyTLS |
| [REALITY、Hysteria2、TUIC：现在的机场为什么都在换协议？](articles/reality-hysteria2-tuic-protocols.md) | 三种新协议的原理和适用场景对比 |
| [Hysteria2 协议的特点：为什么越来越多机场用它替代 Shadowsocks 和 VMess](articles/hysteria2-protocol-guide.md) | 基于 QUIC 的拥塞控制，为什么晚高峰更抗丢包 |
| [中转和直连到底有什么区别？搞懂这个再选机场不吃亏](articles/relay-vs-direct-hysteria2.md) | 为什么有的节点又稳又贵，有的又便宜又飘 |
| [CN2、GIA、CIA、IPLC、IEPL 都是什么？机场专线线路区别科普](articles/cn2-gia-iplc-iepl-guide.md) | 一次看懂机场介绍里的各种线路名词 |
| [什么是 VPN？一分钟看懂原理与作用（2026 新手指南）](articles/what-is-vpn-beginner-guide.md) | 零基础入门 |

## 机场选择与避坑

| 文章 | 说明 |
|---|---|
| [机场是什么？和 VPN 有什么区别？VPS 又是什么？一篇讲清楚](articles/airport-vpn-vps-guide.md) | 三个最容易混淆的概念 |
| [机场怎么选？6 个维度帮你避开新手坑](articles/airport-selection-guide.md) | 别只看价格和广告词 |
| [机场常见黑话大全：这些词看不懂，选机场基本靠蒙](articles/airport-slang-glossary.md) | 倍率、落地、专线、IEPL、解锁……一次看懂 |
| [机场跑路潮全解析：黑话、征兆与自保指南](articles/airport-runaway-survival-guide.md) | 跑路前有哪些征兆、怎么减少损失 |
| [从 2018 到现在：我的翻墙十年，和我为什么决定自己做机场](articles/my-vpn-history-and-why-i-started-an-airport.md) | 个人翻墙十年经历回顾，机场跑路原因复盘 |

## 出海生活与网络安全

| 文章 | 说明 |
|---|---|
| [Netflix、Disney+ 严打账号共享，普通用户该怎么应对？](articles/netflix-disney-account-sharing-crackdown.md) | 共享账号还能不能用、怎么避免被限制 |
| [出差旅行必看：公共 WiFi 到底有多危险？](articles/public-wifi-safety-guide.md) | 2026 年防泄露实用指南 |
| [海外留学生、远程工作者的"双网络"生活](articles/dual-network-life-abroad.md) | 怎样同时保留国内 App 和全球视野 |
| [2026 年跨境网络监管持续收紧，普通人还能怎样保持稳定的国际访问？](articles/cross-border-network-regulation-2026.md) | 监管趋势与应对思路 |
| [从"自由门"到 AI 流量指纹：翻墙工具二十多年演变史](articles/censorship-tools-history.md) | 网络工具发展历史 |

## 新手入门系列（docs）

| 文档 | 讲什么 | 适合谁看 |
|---|---|---|
| [01 · 什么是VPN](docs/01-什么是VPN.md) | VPN 到底在干什么，用买菜、寄快递类比讲清楚 | 完全零基础 |
| [02 · 中转与直连的区别](docs/02-中转与直连的区别.md) | 为什么有的节点又稳又贵，有的又便宜又飘 | 想搞懂"为什么我这个不稳定" |
| [03 · 路由器怎么装VPN](docs/03-路由器怎么装VPN.md) | 一次设置，全屋设备自动加密的实操思路 | 家里设备多、嫌一个个装麻烦的人 |
| [04 · 如何挑选靠谱的VPN服务](docs/04-如何挑选靠谱的VPN服务.md) | 别只看广告词，教你看懂真正该关注的几个指标 | 正在纠结选哪家的人 |
| [05 · 主流加密协议大白话详解](docs/05-主流加密协议大白话详解.md) | Shadowsocks / V2Ray / Trojan / Hysteria2 到底有什么不同 | 想再往下深入一点的人 |
| [06 · 外贸业务员必备工具网站合集](docs/06-外贸业务员必备工具网站合集.md) | 找客户、开发信、收款、物流追踪……外贸全流程常用网站导航 | 外贸从业者、想了解外贸工作流的人 |
| [07 · 科学上网新手值得逛的网站及理由](docs/07-科学上网新手值得逛的网站及理由.md) | 除了刷视频，翻墙之后还能去哪逛、为什么值得去 | 刚上手科学上网的新人 |
| [08 · 为什么我们要分协议部署节点](docs/08-为什么我们要分协议部署节点.md) | VLESS+REALITY、Hysteria2、AnyTLS 分别是什么、为什么要同时部署 | 想搞懂节点列表里协议差异的人 |
| [09 · 刚翻墙出来的新手要注意的几件事](docs/09-刚翻墙出来的新手要注意的几件事_1.md) | 连上之后容易踩的坑：账号安全、免费节点风险、常见故障自查 | 刚学会翻墙、还在磨合阶段的新人 |
| [10 · 这几天，我们把网站又打磨了一遍](docs/10-这几天我们做的一些改动.md) | 近期的内容SEO优化、登录页体验改进与邀请返佣机制更新 | 想了解产品最新进展的人 |

## 关于内容风格

我们尽量用类比而不是术语堆砌来解释技术概念——比如把"中转节点"类比成"快递中转仓"，把"加密协议"类比成"不同种类的包装方式"。如果你是完全的新手，从 docs 的 01 开始按顺序看就行；如果你已经懂一些基础，可以直接跳到你感兴趣的分类。

## 关于我们

**速度无限VPN** 专注全球加速节点与隐私保护服务，严格无日志。如果这些文档帮到了你，欢迎 star 这个仓库，也欢迎提 issue 补充你觉得该科普但没讲到的内容。

官网：[速度无限VPN](https://main.suduwuxian.top/)

## 许可

本仓库内容遵循 [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/deed.zh) 协议，欢迎转载科普内容，请注明来源为"速度无限VPN"，谢绝用于商业推广其他服务。

## 资源文件（resources）

| 文件 | 说明 |
|---|---|
| [default.clash.yaml](resources/default.clash.yaml) | Clash 默认配置文件 |
| [2022-suwayun-config-memento.yml](resources/2022-suwayun-config-memento.yml) | 速蛙云2022年的原始订阅配置文件（保留作纪念，节点均已失效） |
| [2022-suwayun-config-screenshot.png](resources/2022-suwayun-config-screenshot.png) | 速蛙云2022年订阅截图，节点已全部显示Timeout |


## 📢 Telegram 频道

新教程、节点公告和更新通知会第一时间发在 Telegram 频道，欢迎关注：[t.me/suduwuxiantop](https://t.me/suduwuxiantop)
