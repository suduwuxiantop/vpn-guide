# 节点和协议怎么选？Hysteria2、VLESS+Reality、AnyTLS 对比与宽带适配指南

导入订阅以后，同一个地区经常能看到好几个节点，分别是 Hysteria2（hy2）、VLESS+Reality、AnyTLS 三种协议。不少朋友会问：到底点哪个？这篇先给结论，再把原因讲清楚，看完就知道自己该怎么选。

## 先说结论

- **电信 / 联通宽带**：直接选 Hysteria2，速度最快。
- **移动宽带**：先试 Hysteria2，能连上就用；连不上或者经常超时，换 VLESS+Reality 或 AnyTLS。
- **最看重稳定**（比如开会、长时间挂着不想断）：选 VLESS+Reality。
- **Hysteria2 突然连接超时**：先重启光猫，再换节点。

## 线路：哪些节点做了 BGP

除了**盐湖城节点**和**其中一个单独的香港节点**之外，本站其他所有节点都接入了 BGP 多线方案。

简单说，BGP 多线就是同一个节点同时接入多家运营商的线路，电信、联通、移动用户连过来时，会各自走适合自己运营商的那条路，不容易绕远路。所以晚高峰的时候，BGP 节点通常会更稳一些。

盐湖城和那个单独的香港节点是普通线路，平时一样能用。如果你在晚高峰觉得某个香港节点明显比别的香港节点慢，换一个香港节点就好。

## 三种协议对比

| 协议 | 速度 | 稳定性 | 底层传输 | 更适合 |
|---|---|---|---|---|
| Hysteria2（hy2） | ★★★ 最快 | 受运营商对 UDP 的策略影响 | UDP（QUIC） | 电信、联通宽带 |
| VLESS+Reality | ★★ 第二 | ★★★ 最稳 | TCP | 各种网络，移动宽带首选备用 |
| AnyTLS | ★ 第三 | ★★ 第二 | TCP | 备用选择 |

### Hysteria2：速度最快

Hysteria2 基于 QUIC 协议，走的是 UDP，并且用了自己的拥塞控制方式。网络有一点丢包的时候，它依然能把带宽跑起来，所以在本站三种协议里速度最快，看 4K/8K 视频、下载大文件体验最好。

它的问题也在 UDP 上：有些网络环境会对 UDP 流量限速或者干扰，这时候 Hysteria2 就可能连不上或者时断时续。

### VLESS+Reality：最稳定

VLESS+Reality 走 TCP，握手阶段看起来和访问一个普通 HTTPS 网站一样，兼容性好，几乎所有网络环境下都能正常工作。速度排第二，稳定性是三种里最好的，适合需要长时间稳定连接的场景。

### AnyTLS：稳定的备用选择

AnyTLS 同样走 TCP + TLS，是比较新的协议。稳定性排第二，速度在本站三种协议里排第三。当你想换个协议试试，或者 VLESS+Reality 用着不顺手的时候，它是很好的备用。

## 移动宽带用户请注意

Hysteria2 是**纯 UDP 协议**，而移动宽带对 UDP 流量通常不太友好，常见的表现有：

- 白天能连，到了晚上开始卡顿、超时；
- 测速正常，但实际打开网页很慢；
- 直接连不上 Hysteria2 节点。

所以移动宽带的建议是：**能连上 Hysteria2 就优先用，速度最快；连不上或者不稳定，就换 VLESS+Reality 或 AnyTLS**，不用在 Hysteria2 上反复折腾。

电信、联通宽带一般没有这个问题，直接选 Hysteria2 就行。

## Hysteria2 连接超时怎么办

按这个顺序排查，大部分情况都能解决：

1. **重启光猫**：把光猫断电，等 30 秒左右再插上，等网络恢复后重新连接。光猫长时间不重启，UDP 连接很容易出问题，移动宽带用户尤其要先试这一步。
2. **换同地区的另一个 Hysteria2 节点**：排除单个节点的问题。
3. **换协议**：还是不行，就切到 VLESS+Reality 或 AnyTLS，先保证能用。

## 一张图看懂怎么选

```
你的宽带是？
├─ 电信 / 联通 ──→ 选 Hysteria2
│                     └─ 超时？→ 重启光猫 → 仍不行换 VLESS+Reality
└─ 移动 ────────→ 先试 Hysteria2
                      ├─ 能连上 → 继续用 Hysteria2
                      └─ 连不上 / 不稳 → VLESS+Reality（最稳）或 AnyTLS
```

## 在客户端里怎么切换

不管用的是 Clash Verge、Clash Mi 还是其他 Mihomo 内核的客户端，切换方法都一样：在节点列表里选中对应协议的节点即可。节点的协议类型可以在节点名称或节点详情里看到。

如果你设置了自动选择（自动测速选最快节点），客户端可能会把你切到 Hysteria2 节点上。移动宽带用户如果发现自动选择后经常断，可以改成手动选择 VLESS+Reality 节点。

## 参考资料

- [Hysteria 2 官方文档](https://v2.hysteria.network/zh/docs/)
- [XTLS/REALITY（GitHub）](https://github.com/XTLS/REALITY)
- [anytls/anytls-go（GitHub）](https://github.com/anytls/anytls-go)

---

> 本文同步发布于 [速度无限博客](https://main.suduwuxian.top/节点和协议怎么选/)。
>
> 速度无限的套餐里 Hysteria2、VLESS+Reality、AnyTLS 三种协议都有，可以随时切换，基础套餐 19 元/月起：[qaz.suduwuxian.top](https://qaz.suduwuxian.top)。邀请好友可拿 30% 返佣并提现。节点公告和更新通知请关注 Telegram 频道：[t.me/suduwuxiantop](https://t.me/suduwuxiantop)
