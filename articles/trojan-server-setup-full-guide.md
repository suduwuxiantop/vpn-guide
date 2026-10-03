# Trojan协议从0到1完整部署：真证书、双客户端接入与避坑指南

Trojan是这几年流传最广的代理协议之一，思路简单粗暴——把代理流量伪装成再普通不过的HTTPS流量，让审查系统没法从"这是不是TLS"这个层面把你区分出来。它的配置门槛低、客户端支持面极广，到今天仍然是很多人自建节点的第一选择。

这篇从一台刚开好的空VPS讲起，用sing-box做服务端，申请真实的Let's Encrypt证书并配好自动续期，最后分别接入Clash Verge和Shadowrocket。每条命令都能直接复制执行。文章最后也会老实讲一下Trojan在2026年的处境——它哪些场景还很能打，哪些场景已经不是最优解了。

## 本文要点

- Trojan的设计思路，以及它的软肋
- 整体流程
- 第一步：准备VPS和域名解析
- 第二步：校时
- 第三步：安装sing-box
- 第四步：申请Let's Encrypt证书
- 第五步：生成密码
- 第六步：写服务端配置
- 第七步：证书权限
- 第八步：放行端口

> 📖 **完整内容请阅读原文**：[Trojan协议从0到1完整部署：真证书、双客户端接入与避坑指南](https://main.suduwuxian.top/trojan%E5%8D%8F%E8%AE%AE%E4%BB%8E0%E5%88%B01%E5%AE%8C%E6%95%B4%E9%83%A8%E7%BD%B2%EF%BC%9A%E7%9C%9F%E8%AF%81%E4%B9%A6%E3%80%81%E5%8F%8C%E5%AE%A2%E6%88%B7%E7%AB%AF%E6%8E%A5%E5%85%A5%E4%B8%8E%E9%81%BF/)

---

> 速度无限：Hysteria2 / VLESS+Reality / AnyTLS 多协议节点，基础套餐 19 元/月起，[qaz.suduwuxian.top](https://qaz.suduwuxian.top)。节点公告和更新请关注 Telegram 频道：[t.me/suduwuxiantop](https://t.me/suduwuxiantop)
