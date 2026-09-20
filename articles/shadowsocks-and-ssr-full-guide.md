# Shadowsocks 从0到1完整部署指南：原理、搭建与2026年还值不值得用

Shadowsocks（简称 SS）是这个圈子里资历最老的协议之一，2012 年由个人开发者 clowwindy 发布，至今已经十四年。这篇文章分三部分：Shadowsocks 本身怎么从零搭建、2026 年还搭它图个什么、以及它的"变种"ShadowsocksR（SSR）怎么搭、原理跟 SS 差在哪。

## 目录

1. Shadowsocks 技术原理
2. 从0到1部署 Shadowsocks（sing-box 版）
3. 客户端接入：Clash Verge 与 Shadowrocket
4. 2026 年搭建 Shadowsocks 节点，意义到底在哪
5. ShadowsocksR（SSR）技术原理：它和 SS 的本质区别
6. 从0到1部署 ShadowsocksR
7. SS vs SSR vs 新协议，怎么选
8. 常见问题排错

---

## 一、Shadowsocks 技术原理

Shadowsocks 本质上是一个"加密的 SOCKS5 代理"。理解它，抓住三个层面就够了。

### 1. 基本工作方式

客户端（比如你手机上的 Shadowrocket）在本地起一个 SOCKS5 代理端口，你的浏览器、App 把流量交给这个本地端口。本地客户端把这些流量加密后，通过一个自定义的二进制协议发给远端服务器；服务器解密，还原出原始请求，代为访问目标网站，再把响应原路加密返回。

跟标准 SOCKS5 不同的是，标准 SOCKS5 是明文的（或者只有用户名密码认证，内容不加密），中间任何一个节点都能看到你在访问什么。Shadowsocks 在 SOCKS5 的基础上，给客户端到服务器这一段加上了对称加密，让链路上的观察者（比如运营商的 DPI 设备）看不到你实际请求的内容。

### 2. 加密方式：从流加密到 AEAD

Shadowsocks 的加密方式经历过一次重要的架构升级，理解这段历史对理解它现在的处境很关键。

**第一代：流加密（Stream Cipher）**，比如 `aes-256-cfb`、`rc4-md5`。这一代加密只保证机密性（内容看不懂），不保证完整性——攻击者虽然读不懂内容，但可以在密文流中做"主动探测"：往连接里注入几个字节，观察服务器的反应（报错、断连、超时的方式和时间是否有差异），借此判断这个端口是不是在跑 Shadowsocks。这个弱点在 2019 年前后被大规模利用，是很多"服务器很快就被墙/被封端口"现象的技术根源。

**第二代：AEAD 加密（Authenticated Encryption with Associated Data）**，比如现在标准配置的 `aes-256-gcm`、`chacha20-ietf-poly1305`。AEAD 在加密的同时生成一个认证标签（tag），服务器解密时会校验这个标签，篡改或猜测发来的数据会直接被拒绝，而不会给出任何可资利用的差异化反馈。这从根本上堵住了"主动探测"这条路。

**现在部署 Shadowsocks，只应该用 AEAD 加密（2022 版协议，即 AEAD-2022，代表算法是 `2022-blake3-aes-256-gcm`）。任何还在用流加密或者老式 AEAD 的教程，都是过时甚至危险的。**

### 3. 协议的先天局限：没有伪装

不管用哪种加密，Shadowsocks 的流量在"元数据"层面有一个改不掉的特征：它就是一坨看起来随机的二进制数据，握手不像 TLS，没有 SNI、没有证书链、没有看起来像 HTTPS 的痕迹。它的安全模型建立在"混进正常流量里泯然众人"这件事上，早期确实有效——但今天的 DPI 设备已经能通过流量的熵值分布、包长分布、握手模式等特征，把"看起来完全随机的二进制流"本身当作一个可疑特征来标记，即使猜不出具体协议也可能触发限速或阻断。

这是本文第四部分要展开聊的核心问题。

---

## 二、从0到1部署 Shadowsocks（sing-box 版）

跟本系列其他协议教程一样，这里用 sing-box 搭建，理由不变：一个二进制文件支持全部主流协议，配置格式统一，社区活跃，客户端兼容性好。

### 2.1 准备工作

- 一台海外 VPS（KVM 架构，1核1G 起步够用），系统建议 Debian 12 或 Ubuntu 22.04
- 一个能正常解析到服务器 IP 的域名（Shadowsocks 本身不强制要求域名和证书，但为了和本系列其他协议保持一致的运维习惯，以及方便未来叠加 TLS 类协议，建议还是留一个域名）
- SSH root 权限

### 2.2 安装 sing-box

```bash
bash <(curl -fsSL https://sing-box.app/install.sh)
```

安装完检查版本，1.9 以上都支持 AEAD-2022：

```bash
sing-box version
```

### 2.3 生成密钥

AEAD-2022 系列加密需要用 sing-box 自带的工具生成对应长度的密钥，不能自己随便写一串字符：

```bash
# 2022-blake3-aes-256-gcm 需要 32 字节密钥
sing-box generate rand --base64 32
```

记下输出的这一串，下一步要用。

### 2.4 编写配置文件

```bash
mkdir -p /etc/sing-box
nano /etc/sing-box/config.json
```

写入以下内容（把 `YOUR_GENERATED_KEY` 换成上一步生成的密钥，端口自己定一个 10000-65535 之间不常用的）：

```json
{
  "log": {
    "level": "info",
    "timestamp": true
  },
  "inbounds": [
    {
      "type": "shadowsocks",
      "tag": "ss-in",
      "listen": "::",
      "listen_port": 8443,
      "method": "2022-blake3-aes-256-gcm",
      "password": "YOUR_GENERATED_KEY",
      "multiplex": {
        "enabled": true
      }
    }
  ],
  "outbounds": [
    {
      "type": "direct",
      "tag": "direct"
    }
  ]
}
```

要点说明：

- `method` 一定用 `2022-blake3-aes-256-gcm`（或流量更大时用 `2022-blake3-chacha20-poly1305`，移动设备省电），不要用旧版 AEAD 或流加密
- `multiplex` 开启多路复用，能缓解一部分连接数暴露的问题，客户端要配套开启才有效
- 这里没有配置 TLS，是 Shadowsocks 的常规形态；如果想进一步伪装，可以把 SS 套在 `shadowtls` 协议内层（sing-box 原生支持这种组合，本文不展开，后续会单独写 ShadowTLS 的教程）

### 2.5 校验配置并启动

```bash
sing-box check -c /etc/sing-box/config.json
```

没有报错，再配置成 systemd 服务：

```bash
cat > /etc/systemd/system/sing-box.service << 'EOF'
[Unit]
Description=sing-box service
After=network.target nss-lookup.target

[Service]
ExecStart=/usr/local/bin/sing-box run -c /etc/sing-box/config.json
Restart=on-failure
RestartSec=5
LimitNOFILE=infinity

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable --now sing-box
systemctl status sing-box
```

看到 `active (running)` 就是启动成功了。

### 2.6 防火墙放行端口

```bash
# 以 ufw 为例
ufw allow 8443/tcp
ufw allow 8443/udp
```

阿里云/腾讯云/AWS 等云服务商，记得同时在控制台的安全组里放行这个端口，光改本机防火墙没用。

---

## 三、客户端接入：Clash Verge 与 Shadowrocket

### 3.1 Clash Verge（Windows / macOS）

Clash Verge 的 Mihomo 内核原生支持 Shadowsocks 2022 系列加密，YAML 配置示例：

```yaml
proxies:
  - name: "SS-2022-测试节点"
    type: ss
    server: 你的服务器IP或域名
    port: 8443
    cipher: 2022-blake3-aes-256-gcm
    password: "YOUR_GENERATED_KEY"
    udp: true
    smux:
      enabled: true
```

导入方式：设置里"导入配置" → 粘贴或上传含有以上 proxies 字段的 YAML，或者直接把这段追加到你现有订阅配置的 `proxies` 列表里。

### 3.2 Shadowrocket（iOS）

Shadowrocket 对 Shadowsocks 的支持是最原生、历史最悠久的（毕竟协议名字里都带 Shadow），两种方式都可以：

**方式一：SS 链接直接导入**

Shadowsocks 有标准的 URI 格式：

```
ss://BASE64(method:password)@server:port#备注名
```

比如把 `2022-blake3-aes-256-gcm:YOUR_GENERATED_KEY` 做 base64 编码后拼进去，生成的链接可以直接在 Shadowrocket 里"添加订阅" → "扫描二维码"或"手动粘贴"导入。

**方式二：手动填写**

打开 Shadowrocket，点右上角 + 号：

- 类型：Shadowsocks
- 地址：你的服务器 IP 或域名
- 端口：8443
- 加密方式：下拉选择 `2022-blake3-aes-256-gcm`
- 密码：填入生成的密钥

保存后点节点测速，能看到延迟数值即为连接成功。

---

## 四、2026 年搭建 Shadowsocks 节点，意义到底在哪

这是很多人问过我的问题：都 2026 年了，Hysteria2、AnyTLS、VLESS+REALITY 这些新协议在抗封锁能力上明显更强，为什么还要花时间学 Shadowsocks 这种"上古协议"？我的看法分几层。

### 1. 它依然是理解这整套技术演化的起点

不管是 VMess、VLESS 还是后来的 Trojan、Hysteria2，本质上都是在回答同一个问题：Shadowsocks 暴露出来的弱点，怎么补。VMess 加了时间戳和动态端口来对抗重放；Trojan 直接套壳标准 TLS 来对抗流量特征识别；Hysteria2 基于 QUIC 从传输层重新设计来对抗封锁和提升弱网表现。不理解 SS 的原理和它被针对的具体原因，后面这些协议的设计动机你只能死记硬背，理解不了"为什么这么设计"。这是我在这个系列里一直把 SS 放在早期位置来讲的原因。

### 2. 中转/落地场景里，它依然被大量使用

单纯"面向审查者"这一个维度，SS 确实不是当前最优选。但机场行业里大量的中转（relay）到落地（landing）这一段内网/专线链路，走的仍然是 SS 或者其变种——因为这段链路本身通常不直接暴露在需要对抗 DPI 的公网审查环境里（走的是 IEPL/IPLC 专线，或者 relay 到 landing 之间本身就有其他协议在做外层封装），这时候 SS 极低的握手开销、极简的实现、几乎可以忽略不计的 CPU 占用，反而是优点。换句话说：SS 现在更适合"信任链路内部"的场景，而不是"直接暴露给审查者"的第一落点。

### 3. 极低资源占用，适合特定补充场景

一个 sing-box 跑纯 SS 入站，内存占用可以做到几 MB 级别，这对于跑在低配 VPS、路由器固件（OpenWrt）、甚至某些 IoT 设备上的场景是有意义的。如果你要在一台配置很差的老机器上顺手加一个代理出口，SS 依然是启动成本最低的选择之一。

### 4. 但作为"主力对抗审查"的协议，它已经过时

必须说清楚：如果你的目标是搭一个直接给国内用户连接、且要长期稳定不被墙的节点，2026 年不建议把 Shadowsocks（哪怕是 AEAD-2022）作为唯一或主力协议。原因在本文第一部分已经讲过——它没有真实的传输层伪装，纯二进制流的特征在长期、大规模的 DPI 扫描下依然有被针对的风险。现实中的最佳实践是"分层"：面向审查者暴露的那一跳，用 Hysteria2 或 VLESS+REALITY 这类有真实 TLS/QUIC 握手伪装的协议；SS 放在信任边界内部，或者作为多协议节点里"順手加一个、成本几乎为零"的备选项，而不是唯一依赖。

一句话总结：**学 SS 是为了理解，部署 SS 更多是为了内部链路和资源受限场景的实用性，而不是指望它单独扛住 2026 年的审查强度。**

---

## 五、ShadowsocksR（SSR）技术原理：它和 SS 的本质区别

讲完 SS，很多人会问起 SSR——这是十年前很多人的启蒙协议，但它现在的处境跟 SS 又不一样，需要单独说清楚。

### 1. SSR 的来历

2015 年，一位化名 breakwa11 的开发者在 Shadowsocks 的基础上 fork 出了 ShadowsocksR，加入了两类 SS 原生没有的能力：**protocol（协议插件）**和 **obfs（混淆插件）**。这次 fork 一度让 SSR 比原版 SS 更流行，因为它在当年确实明显提升了抗探测能力。但 2017 年前后原作者停止维护，社区分裂、审计缺失，加上后续的 AEAD 加密普及，SSR 逐渐被 SS+AEAD 以及更新的协议取代。

### 2. SSR 到底比 SS 多了什么

**Protocol（协议层插件）** 解决的是"握手/包结构可被识别"的问题。原版 SS 的每个数据包结构相对固定，SSR 的 protocol 插件会在数据包前后加入伪造的头部、随机长度的填充、甚至模拟 HTTP 请求头的样式，让抓包分析时数据包结构看起来不那么"规整划一"。常见的 protocol 选项有 `origin`（不使用，等同原版 SS 行为）、`auth_sha1_v4`、`auth_aes128_md5`、`auth_chain_a` / `auth_chain_b`（用一个动态密钥链持续变化包结构，是 SSR 里对抗探测能力最强的一档）。

**Obfs（混淆层插件）** 解决的是"整体流量形态像不像正常 HTTPS/HTTP"的问题。常见选项有 `plain`（不混淆）、`http_simple` / `http_post`（把流量包装成看起来像 HTTP 请求）、`tls1.2_ticket_auth`（伪装出一个简化版的 TLS 1.2 握手外观）。`tls1.2_ticket_auth` 是当年最常用、伪装效果相对最好的一档，但它模拟的 TLS 握手非常粗糙，跟今天动辄要求"真实证书链、真实 SNI、能过主动探测"的标准（比如 Trojan、AnyTLS 的做法）完全不是一个量级。

用一句话概括 SS 和 SSR 的关系：**SSR = SS 的加密内核 + protocol 插件（包结构伪装）+ obfs 插件（流量形态伪装）**，它是在传输层之上打了两个"外挂式"的伪装补丁，而不是像 Trojan、AnyTLS 那样直接借用一个真实、完整、可被验证的 TLS 实现。这也是为什么 SSR 的伪装从今天的眼光看是"能看得出来是伪装"的伪装，而 Trojan/AnyTLS 是"直接就是真的"。

### 3. SSR 现在的真实处境

必须坦率地说：**ShadowsocksR 目前处于事实上的停止维护状态**，原版仓库早已停更，社区维护的分支（如 shadowsocksr-libev）也已多年没有安全审计和更新。它的 obfs/protocol 组合能提供的伪装强度，放在 2026 年的 DPI 技术水平面前已经相当有限——`http_simple` 这种直接在明文里塞一段假 HTTP 头的做法，现代 DPI 设备识别起来毫无难度；`tls1.2_ticket_auth` 模拟的握手也早已被针对性识别。选择 SSR，更多是出于兼容老客户端、教学演示、或者对接一些遗留系统的需要，而不应该是 2026 年新建节点的首选协议。

---

## 六、从0到1部署 ShadowsocksR

如果你确实需要（比如维护一个还在用 SSR 客户端的老用户群），部署方式如下。注意 SSR **没有被 sing-box、Xray 等现代内核收录**，必须用专门的 SSR 实现，这里用社区维护最久的 `shadowsocksr-libev`。

### 6.1 安装依赖并编译

```bash
apt update
apt install -y build-essential autoconf libtool libssl-dev \
  libpcre3-dev libev-dev asciidoc xmlto automake git

git clone https://github.com/shadowsocksrr/shadowsocksr-libev.git
cd shadowsocksr-libev
git submodule update --init --recursive
./autogen.sh
./configure
make -j$(nproc)
make install
```

编译过程可能因为系统较新、依赖版本冲突而报错（这个项目已经多年没更新，跟新版 OpenSSL 的兼容性问题不算少见），如果编译失败，建议直接用 Docker 跑现成镜像，能省去大量踩坑时间：

```bash
docker run -d --name ssr-server \
  --restart=always \
  -p 8989:8989 -p 8989:8989/udp \
  -e SERVER_PORT=8989 \
  -e PASSWORD=你的密码 \
  -e METHOD=aes-256-cfb \
  -e PROTOCOL=auth_aes128_md5 \
  -e OBFS=tls1.2_ticket_auth \
  breakwa11/shadowsocksr
```

（`breakwa11/shadowsocksr` 这类社区镜像久未更新，仅作为快速搭建演示，生产环境慎用。）

### 6.2 手动编译方式下的配置文件

```bash
mkdir -p /etc/shadowsocksr
nano /etc/shadowsocksr/config.json
```

```json
{
    "server": "0.0.0.0",
    "server_port": 8989,
    "password": "你的密码",
    "method": "aes-256-cfb",
    "protocol": "auth_aes128_md5",
    "protocol_param": "",
    "obfs": "tls1.2_ticket_auth",
    "obfs_param": "",
    "timeout": 300
}
```

字段说明：

- `method`：SSR 因为是 SS 的老分支，只支持流加密系列（`aes-256-cfb`、`chacha20` 等），不支持后来的 AEAD-2022 系列——这也是它在加密强度上已经落后于现代实现的原因之一
- `protocol` / `obfs`：见第五部分的说明，两者可以自由组合，`auth_chain_a` + `tls1.2_ticket_auth` 是当年公认伪装效果最好的组合

### 6.3 启动服务

```bash
ssserver-r -c /etc/shadowsocksr/config.json -d start
```

配合 systemd 常驻的做法跟第二部分类似，这里不重复贴 unit 文件模板。

### 6.4 客户端接入

Shadowrocket、Clash（部分内核）仍然保留对 SSR 的支持，手动添加时选择"ShadowsocksR"类型，把 server / port / password / method / protocol / obfs 对应字段填入即可。SSR 也有自己的 URI scheme（`ssr://` 开头），生成方式和标准 SS 链接类似，只是编码的字段更多（把 protocol、obfs 等参数一并 base64 编码进去）。

---

## 七、SS vs SSR vs 新协议，怎么选

| 维度 | Shadowsocks (AEAD-2022) | ShadowsocksR | Trojan / AnyTLS | Hysteria2 |
|---|---|---|---|---|
| 加密强度 | 高（AEAD，防篡改） | 中低（仅流加密，无篡改防护） | 高（真实 TLS） | 高（真实 TLS，基于 QUIC） |
| 传输层伪装 | 无（纯二进制流） | 弱（obfs 插件伪装，特征可识别） | 强（真实证书+SNI） | 强（真实证书，QUIC 协议本身也是常见流量） |
| 维护状态 | 活跃（sing-box/Xray 持续更新） | 事实停更多年 | 活跃 | 活跃 |
| 资源占用 | 极低 | 低 | 低 | 中（QUIC 有一定开销） |
| 2026 推荐场景 | 内网中转链路、资源受限设备 | 仅维护老用户，不建议新建 | 直接面向审查者的主力节点 | 直接面向审查者的主力节点，弱网表现更好 |

结论很直接：**新建节点，不建议把 SSR 作为选项；SS(AEAD-2022) 适合放在信任链路内部或资源受限场景；直接暴露给用户、需要扛审查的主力节点，交给 Trojan/AnyTLS/Hysteria2 这类有真实传输层伪装的协议。**

---

## 八、常见问题排错

**1. 服务起来了，客户端连不上**

先用 `ss -tlnp | grep 8443` 确认端口确实在监听；再检查云服务商控制台的安全组规则，本机防火墙放行了不代表云平台的安全组也放行了，这是最容易漏掉的一步。

**2. Clash Verge 报 "cipher not supported"**

Mihomo 内核对 2022 系列加密的支持需要相对新的版本，太旧的 Clash 客户端（尤其是 Clash Premium 停更版）不认识 `2022-blake3-*` 这几种方法，升级到最新版 Clash Verge / Mihomo 内核即可。

**3. Shadowrocket 提示 "服务器无响应"**

大概率是加密方式选错了（比如服务端配的是 `2022-blake3-aes-256-gcm`，客户端却选了旧版 `aes-256-gcm`），两边必须完全一致，一个字符都不能错。

**4. SSR 编译报 OpenSSL 相关错误**

这是这个项目多年未更新和新系统 OpenSSL 版本（1.1 之后的分支变动较大）不兼容导致的，最快的解决办法是换用一台预装 OpenSSL 1.0.x 的旧版系统做编译环境，或者直接用前文提到的 Docker 方案绕开编译。

**5. 延迟正常但网页打不开**

检查客户端的 UDP 支持有没有开启（如果访问的是走 UDP 的服务，比如某些视频/游戏），以及本地 DNS 解析规则是否配置正确，很多"能连上但用不了"的问题根源在 DNS 分流规则而不是代理本身。

---

至此，Shadowsocks 和 ShadowsocksR 的原理、部署、以及 2026 年该怎么给它们定位，应该都讲清楚了。如果你手上还有一批需要维护的 SSR 老用户，可以按第六部分的方式单独起一个 SSR 实例，跟你的 Trojan/Hysteria2 主力节点并存，互不影响。
