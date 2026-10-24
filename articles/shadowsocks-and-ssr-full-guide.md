# Shadowsocks 从0到1完整部署指南：原理、搭建与2026年还值不值得用

Shadowsocks（简称 SS）是这个圈子里资历最老的协议之一，2012 年由个人开发者 clowwindy 发布，至今已经十四年。这篇文章分三部分：Shadowsocks 本身怎么从零搭建、2026 年还搭它图个什么、以及它的"变种"ShadowsocksR（SSR）怎么搭、原理跟 SS 差在哪。

## 本文要点

- 目录
- 一、Shadowsocks 技术原理
- 二、从0到1部署 Shadowsocks（sing-box 版）
- 三、客户端接入：Clash Verge 与 Shadowrocket
- 四、2026 年搭建 Shadowsocks 节点，意义到底在哪
- 五、ShadowsocksR（SSR）技术原理：它和 SS 的本质区别
- 六、从0到1部署 ShadowsocksR
- 七、SS vs SSR vs 新协议，怎么选
- 八、常见问题排错

> 📖 **完整内容请阅读原文**：[Shadowsocks 从0到1完整部署指南：原理、搭建与2026年还值不值得用](https://main.suduwuxian.top/shadowsocks-ssr-setup-guide/)

---

> 速度无限：Hysteria2 / VLESS+Reality / AnyTLS 多协议节点，基础套餐 19 元/月起，[qaz.suduwuxian.top](https://qaz.suduwuxian.top)。节点公告和更新请关注 Telegram 频道：[t.me/suduwuxiantop](https://t.me/suduwuxiantop)
