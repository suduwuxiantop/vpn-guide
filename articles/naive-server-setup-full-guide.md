# NaiveProxy（Naive协议）从0到1完整部署：伪装成真实Chrome流量的代理协议

本系列已经写过 Trojan、AnyTLS、Hysteria2、VLESS+REALITY、Shadowsocks 这几个协议，这次补上一个思路完全不同的选项——**NaiveProxy（在 sing-box 里的协议名是 `naive`）**。它不是又一个"套壳TLS"的协议，而是直接把 Chromium 浏览器的网络栈搬过来当客户端用，流量在协议层面就是一次真实的 Chrome 请求，而不是"模仿得像"的Chrome请求。这个区别很关键，下面会讲清楚。

## 目录

1. NaiveProxy 是什么，它解决的是什么问题
2. 技术原理：为什么说它是"真Chrome流量"而不是伪装
3. 从0到1部署 NaiveProxy（sing-box 版）
4. 客户端接入：为什么不能用 Clash Verge，该用什么
5. 2026年该怎么给它定位
6. 常见问题排错

---

## 一、NaiveProxy 是什么，它解决的是什么问题

NaiveProxy 最早是 Chromium 项目的贡献者从 Chromium 源码里剥离出来的一个独立项目（作者 klzgrad，项目名 `naiveproxy`），核心思路很朴素：与其自己写一套TLS握手、自己实现HTTP/2协议栈去"模仿"浏览器，不如**直接用 Chromium 的网络栈本身**——同一份代码、同一套TLS指纹、同一套HTTP/2帧结构。sing-box、Xray 等项目后来把这套协议标准化，作为一种内置的代理类型实现（sing-box 里的 inbound/outbound 类型是 `naive`），不再需要专门编译 naiveproxy 的 Chromium 定制版二进制，用 sing-box 一个程序就能跑。

它要解决的问题，跟 Trojan、AnyTLS 是同一个大方向——**让代理流量在网络观察者眼里长得和普通HTTPS网页访问没有区别**——但实现思路不同：Trojan/AnyTLS 是"自己实现TLS，尽量让特征贴近真实浏览器"；NaiveProxy 是"直接复用真实浏览器的实现"，天然没有"这套TLS库跟Chrome实际用的不完全一样"这种细微特征差异的问题。

## 二、技术原理：为什么说它是"真Chrome流量"而不是伪装

理解 NaiveProxy，抓住两个层面：

### 1. 传输层：HTTP/2 CONNECT 隧道

NaiveProxy 服务端本质上是一个标准的、支持 `CONNECT` 方法的 HTTP/2（或 HTTP/3/QUIC）代理服务器，客户端通过 Chromium 网络栈原生支持的HTTP代理协议——HTTP/2 CONNECT——向服务端发起隧道请求，请求本身用标准用户名密码做 Basic 认证。这和你在企业网络里配置一个"公司代理服务器"用的是完全相同的机制，唯一区别是这个"公司代理"套了一层TLS，而且服务端和客户端都是拿真实 Chromium 代码实现的。

### 2. TLS指纹：不是模仿，是复用

绝大多数DPI设备识别"伪装成HTTPS的代理流量"，靠的是TLS ClientHello里的一系列细节特征（支持的加密套件顺序、扩展字段顺序、椭圆曲线列表等，业内统称"JA3/JA4指纹"）——自己实现的TLS库，哪怕拼命模仿Chrome的参数，也很难做到每一个字节顺序都跟真实Chrome版本完全一致，尤其是Chrome版本更新后这些细节还会变。NaiveProxy因为直接用的是Chromium网络栈的代码，它的TLS ClientHello**就是**某个真实Chrome版本发出的样子，不存在"模仿得够不够像"这个问题——因为它压根不是模仿，是同一份代码跑出来的结果。

这也是为什么 NaiveProxy 在设计理念上，被很多人认为是当前"传输层伪装"这条技术路线里做得最彻底的实现之一。

### 3. 认证与多路复用

客户端到服务端认证走标准 HTTP Basic Auth（用户名+密码），一个 TLS 连接上可以承载多路 HTTP/2 stream，也就是多路复用——这跟 Trojan、Hysteria2 依赖的多路复用机制目标一致：减少频繁建立新连接带来的握手开销和可被观察的"连接建立模式"特征。

---

## 三、从0到1部署 NaiveProxy（sing-box 版）

### 3.1 准备工作

- 一台海外 VPS（KVM架构，1核1G起步）
- 一个域名，已经解析到服务器IP（NaiveProxy必须用真实域名+真实证书，这点和 Trojan、AnyTLS 一样，不支持类似 REALITY 那种"借用别人证书"的无域名方案）
- SSH root 权限

### 3.2 安装 sing-box

```bash
bash <(curl -fsSL https://sing-box.app/install.sh)
sing-box version
```

### 3.3 申请真实证书

用 acme.sh，流程和本系列 Trojan、AnyTLS 教程完全一致：

```bash
curl https://get.acme.sh | sh -s email=your@email.com
source ~/.bashrc

# standalone模式申请前先停掉占用80端口的服务
~/.acme.sh/acme.sh --issue -d yourdomain.com --standalone

mkdir -p /etc/sing-box/cert
~/.acme.sh/acme.sh --install-cert -d yourdomain.com \
  --key-file /etc/sing-box/cert/private.key \
  --fullchain-file /etc/sing-box/cert/cert.pem \
  --reloadcmd "systemctl restart sing-box"
```

### 3.4 编写配置文件

```bash
mkdir -p /etc/sing-box
nano /etc/sing-box/config.json
```

```json
{
  "log": {
    "level": "info",
    "timestamp": true
  },
  "inbounds": [
    {
      "type": "naive",
      "tag": "naive-in",
      "listen": "::",
      "listen_port": 443,
      "network": "tcp",
      "users": [
        {
          "username": "your_username",
          "password": "your_strong_password"
        }
      ],
      "tls": {
        "enabled": true,
        "server_name": "yourdomain.com",
        "certificate_path": "/etc/sing-box/cert/cert.pem",
        "key_path": "/etc/sing-box/cert/private.key",
        "alpn": ["h2", "http/1.1"],
        "min_version": "1.2"
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

- `network` 设为 `tcp`：NaiveProxy 走 HTTP/2 over TLS，走标准TCP即可；如果客户端和sing-box版本都支持QUIC传输的HTTP/3，也可以把这里改成同时监听UDP，本文用最通用的TCP方案
- `alpn` 一定要包含 `h2`：这是HTTP/2协商的关键字段，缺了这个客户端连不上
- `username`/`password` 就是HTTP Basic Auth的凭据，密码建议用高强度随机字符串，避免被弱密码爆破
- 监听端口用443是有意为之——因为NaiveProxy的流量特征就是"一次正常的HTTPS请求"，用标准443端口更符合这个人设，用高位端口反而显得突兀

### 3.5 校验并启动

```bash
sing-box check -c /etc/sing-box/config.json
```

配置成systemd服务：

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

### 3.6 防火墙放行443端口

```bash
ufw allow 443/tcp
```

别忘了云服务商控制台的安全组同步放行，这是本系列反复强调但也反复有人漏掉的一步。

---

## 四、客户端接入：为什么不能用 Clash Verge，该用什么

这里必须提前说清楚一件事：**Clash Verge（Mihomo内核）目前不支持 NaiveProxy 协议**。查了 Mihomo 官方仓库的issue记录，"支持Naive Proxy"这个功能请求截至目前仍然是待开发状态，没有排期。如果你直接照搬前面几篇教程"把节点加进Clash Verge的YAML"的思路，会发现根本没有 `naive` 这个type可用——这不是配置写错了，是内核层面真的不支持。

NaiveProxy 能用的客户端，目前主要是**基于 sing-box 内核本身**的那一批客户端：

### 4.1 Windows：v2rayN

v2rayN 内置了 sing-box 核心，支持直接添加 NaiveProxy 节点。添加方式：

1. 打开v2rayN，服务器 → 添加自定义配置（或者直接选"sing-box"类型节点）
2. 手动填入或粘贴以下JSON片段作为outbound配置：

```json
{
  "type": "naive",
  "tag": "naive-out",
  "server": "yourdomain.com",
  "server_port": 443,
  "username": "your_username",
  "password": "your_strong_password",
  "network": "tcp",
  "tls": {
    "enabled": true,
    "server_name": "yourdomain.com"
  }
}
```

3. 保存后选中该节点，右键测试连接延迟

### 4.2 Android：NekoBox for Android

NekoBox 同样基于 sing-box 内核，原生支持 naive 协议：

1. 添加节点 → 手动输入
2. 类型选择 sing-box 自定义配置，或者直接用上面outbound的JSON粘贴导入
3. 保存后点击连接

### 4.3 iOS / macOS：sing-box 官方客户端（SFI / SFM）

苹果生态下，Shadowrocket 目前对 NaiveProxy 的原生支持并不稳定（不同版本表现不一致），更可靠的选择是 sing-box 官方出的客户端：iOS上是 **SFI（sing-box for iOS）**，macOS上是 **SFM（sing-box for Mac）**，两者都是官方sing-box团队维护，配置文件格式和服务端完全一致，把上面的outbound JSON包进标准sing-box客户端配置模板（补上 `inbounds` 里的本地SOCKS/HTTP监听、`route` 规则）即可直接导入使用。

### 4.4 命令行验证（跨平台通用）

如果只是想先验证服务端配好了没有，最快的方式是直接用 sing-box 客户端模式在本地起一个测试实例，或者用支持HTTP Basic Auth的curl直接测试HTTP/2 CONNECT隧道是否握手成功：

```bash
curl -v --proxy-insecure -x https://your_username:your_strong_password@yourdomain.com:443 https://ip.sb
```

能返回你服务器的出口IP，说明服务端配置完全正确。

---

## 五、2026年该怎么给它定位

NaiveProxy 不是一个"万金油"选择，它有自己明确的适用边界：

**优势非常突出的地方**：如果你评估的核心风险是"主动或被动的TLS指纹识别"，NaiveProxy 目前是市面上在这一点上做得最彻底的方案之一——因为它根本不需要"伪装得像"，它用的就是真Chromium的网络栈。相比之下，Trojan、AnyTLS虽然也追求"看起来像真实TLS"，但终究是各自的TLS库实现，理论上仍存在被更精细指纹识别技术揪出细微差异的可能性（哪怕目前实践中很难被利用）。

**明显的短板**：客户端生态是它最大的现实问题。前面第四部分已经说得很清楚——主流的Clash系客户端完全不支持，只能依赖v2rayN、NekoBox、sing-box官方客户端这几个相对小众的选择，对于已经习惯Clash Verge多协议节点统一管理的用户，接入成本明显更高，也没法把NaiveProxy节点和你现有的Trojan/Hysteria2/VLESS节点放进同一个Clash订阅里统一切换。

**实际建议**：如果你的用户群体本身就是技术能力较强、愿意折腾客户端配置的人（比如你自己的自用节点，或者面向技术向社群），NaiveProxy 值得作为传输层伪装能力最强的备选项之一；但如果你是给普通用户批量分发订阅、需要"一个订阅链接、Clash Verge一键导入"这种傻瓜式体验，目前阶段 NaiveProxy 还不合适作为主力协议大规模铺开，Trojan/AnyTLS/Hysteria2 在客户端兼容性上仍然更实用。

---

## 六、常见问题排错

**1. 服务端启动正常，但客户端一直提示连接失败**

先确认客户端类型选对了——Clash Verge/Mihomo系客户端不支持naive，这是本文反复强调的点，如果你在用这类客户端却怎么都连不上，先确认是不是从一开始就选错了客户端。

**2. curl测试返回 "SSL certificate problem"**

检查证书链是否完整（`certificate_path`指向的应该是fullchain而不是单独的域名证书），acme.sh的 `--install-cert` 步骤如果用的是 `--fullchain-file` 参数，正常应该是完整链证书，如果这里出错大概率是证书文件路径填错或者证书过期没有自动续期成功。

**3. v2rayN/NekoBox显示节点已添加，但测速一直超时**

检查服务端`alpn`字段是否包含了`h2`，这是最容易漏掉的一个字段，没有它HTTP/2协商会失败，客户端表现为连接超时而不是明确的错误提示。

**4. 想同时支持QUIC(HTTP/3)传输**

sing-box的naive inbound在较新版本里支持QUIC拥塞控制算法的配置（`quic_congestion_control`字段），如果客户端和服务端版本都比较新，可以尝试在`network`字段同时开放udp监听来启用HTTP/3路径，但目前这个特性的客户端支持程度参差不齐，如果遇到兼容性问题，退回纯TCP的HTTP/2方案更稳妥。

**5. 想用443端口，但服务器上已经有别的网站占用了**

和Trojan、AnyTLS遇到的情况一样，如果443端口已经被一个真实网站占用，需要考虑用Nginx/Caddy做SNI分流转发，或者给NaiveProxy换一个独立的高位端口——但换端口会削弱"流量看起来完全正常"这个核心优势，需要根据实际情况权衡。

---

NaiveProxy 走的是一条和本系列其他协议都不一样的路——不是"更好地伪装"，而是"直接复用真实浏览器的实现"，这个思路本身值得理解，即便你最终因为客户端生态的限制选择别的协议作为主力。
