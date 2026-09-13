# Hysteria2协议的特点：为什么越来越多机场开始用它替代Shadowsocks和VMess

> "这机场怎么又更新协议了？"——如果你留意机场的节点更新公告，会发现最近一两年一个很明显的趋势：老牌的Shadowsocks、VMess节点在慢慢减少，取而代之的是Hysteria2。这篇文章讲清楚Hysteria2到底强在哪，值不值得作为主力协议。

Shadowsocks和VMess是陪伏很多人多年的"老朋友"，简单、稳定、生态成熟。但网络环境这几年变化很大：一边是审查手段在升级，另一边是国内outbound高峰期的丢包、拥堵越来越常见。Hysteria2就是在这样的背景下，专门针对"弱网络环境"设计出来的新一代协议。这篇文章把它的核心机制和实际优势讲清楚。

## 先说结论：Hysteria2到底是什么

Hysteria2是基于QUIC（一种跑在UDP之上的传输协议，HTTP/3也用它）构建的代理协议，由开源项目apernet/hysteria开发和维护。和走TCP的Shadowsocks、VMess不同，Hysteria2从底层传输层就换了一条路，这也是它大部分优势的根源。

## 优势一：拥塞控制更激进，弱网下更抗造

TCP协议有一个老毛病：一旦检测到丢包，就会大幅度降低发送速率来"避让"，在国内到海外的高峰期拥堵路段，这种保守策略会让网速断崖式下跌。

Hysteria2基于QUIC实现了名为Brutal的拥塞控制算法，思路完全不同：不再像TCP那样"一丢包就退让"，而是允许客户端主动声明自己的带宽上限，服务端按照这个上限尽量维持发送速率，即使出现一定比例的丢包也不会像TCP那样保守收缩。实际体验上，这意味着在晚高峰、丢包率较高的线路上，Hysteria2通常比走TCP的Shadowsocks、VMess更抗造，卡顿和掉速的情况明显更少。

## 优势二：一次握手就能建连，延迟更低

传统TCP建立连接需要经过"三次握手"，再加上TLS握手，实际连接建立往往要经过好几个来回。QUIC协议本身支持0-RTT/1-RTT握手，Hysteria2在此基础上进一步简化，连接建立速度比TCP+TLS的组合更快。这对于看视频、打游戏这种对首次连接延迟敏感的场景，体验提升是能明显感觉到的。

## 优势三：伪装成HTTP/3流量，隐蔽性更强

Hysteria2在设计上会让服务端表现得像一个标准的HTTP/3网站：外部探测者访问时，看到的是正常的Web服务响应；只有携带正确身份信息的客户端请求，才会被服务端识别并建立代理隧道。加上协议自带的Salamander混淆机制（对QUIC握手包做加密和填充处理），让流量特征更难被精确识别为"代理流量"。相比之下，Shadowsocks虽然数据本身也加密，但流量的包长分布、握手特征等更容易被针对性识别；VMess虽然做了一些改进，但底层依然是TCP，遇到精细化的流量分析时隐蔽性上限不如Hysteria2。

![Hysteria2与Shadowsocks、VMess在传输层、拥塞控制、隐蔽性、连接迁移四个维度的对比](images/diagram1_protocol_table.png)
*四个核心维度的直观对比：Hysteria2的优势集中在传输层选型带来的连锁反应*

## 优势四：连接迁移，切换网络不断线

QUIC协议原生支持"连接迁移"——当你的设备从WiFi切换到蜂窝网络，或者IP地址发生变化时，连接可以无缝延续，不需要重新握手。这对于手机用户来说是个实打实的体验提升：出门时WiFi切4G，代理连接不会因此断掉重连。Shadowsocks和VMess跑在TCP之上，天然不具备这个能力，网络一变就得重新建立连接。

![弱网环境下Hysteria2与TCP类协议的速度表现趋势示意](images/diagram2_weak_network_curve.png)
*丢包率上升时，Hysteria2的Brutal拥塞控制让速度下降曲线更平缓*

## 那Hysteria2是不是完美无缺？

当然不是。UDP流量在部分运营商的网络里会被更严格地限速或QoS降级，高峰期UDP协议被限速的情况比TCP更常见；另外QUIC类协议目前在"证书级别伪装"这个维度上还不如REALITY那样彻底（REALITY能做到连TLS证书都是真实网站的），Hysteria2更多依赖流量混淆而不是身份分流。所以严谨地说，Hysteria2的优势主要体现在弱网抗造、延迟和连接稳定性上，而不是"绝对不会被针对"。

## 普通用户该怎么选

如果你所在的网络环境经常在晚高峰卡顿、丢包，或者你是手机用户经常切换WiFi和移动网络，Hysteria2通常会带来更明显的体验提升；如果只是日常网页浏览、对延迟不敏感，用哪个协议差别可能不大，更值得关注的还是机场本身的线路质量和运维稳定性。

像[速度无限VPN](https://qaz.suduwuxian.top)这样的服务，会持续跟进主流协议的更新和优化，把这些底层技术选型和调优留给自己去处理，用户端不需要自己折腾配置，专注在"连得上、够稳定"这件事本身就够了。

## 写在最后

协议这件事说到底没有绝对的"谁比谁强"，只有"哪种场景下更合适"。Hysteria2能在这两年迅速普及，核心原因是它精准解决了当下网络环境里最常见的痛点——弱网丢包和网络切换。了解这些概念不是为了自己动手折腾配置，而是下次看到机场的协议更新公告时，能看懂它到底在解决什么问题。

## 参考资料

1. [apernet/hysteria 官方项目仓库](https://github.com/apernet/hysteria)
2. [Hysteria 2 官方协议文档](https://v2.hysteria.network/docs/developers/Protocol/)
3. [Shadowsocks/VMess/Trojan/Hysteria2 技术原理与性能对比](https://ygjc.cc/guide/proxy-protocol-deep-dive-2026)
4. [Geek关于Shadowrocket更新支持Hysteria2 Brutal拥塞控制的推文](https://x.com/geekbb/status/1725866047717425582)
5. [Hysteria2 协议是什么？原理、UDP被限速怎么办与机场清单](https://jichangtuijian1.com/hysteria2)
