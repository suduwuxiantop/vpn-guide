# Trojan协议从0到1完整部署：真证书、双客户端接入与避坑指南

Trojan是这几年流传最广的代理协议之一，思路简单粗暴——把代理流量伪装成再普通不过的HTTPS流量，让审查系统没法从"这是不是TLS"这个层面把你区分出来。它的配置门槛低、客户端支持面极广，到今天仍然是很多人自建节点的第一选择。

这篇从一台刚开好的空VPS讲起，用sing-box做服务端，申请真实的Let's Encrypt证书并配好自动续期，最后分别接入Clash Verge和Shadowrocket。每条命令都能直接复制执行。文章最后也会老实讲一下Trojan在2026年的处境——它哪些场景还很能打，哪些场景已经不是最优解了。

## Trojan的设计思路，以及它的软肋

Trojan的核心假设是：审查系统不可能封锁所有HTTPS流量。

所以它不去发明什么新的加密方式，而是直接用标准TLS把自己包起来。客户端连上服务器，完成一次再正常不过的TLS握手，然后在这条加密隧道里传输代理数据。从流量特征上看，这就是一次访问HTTPS网站的连接。

和它常被拿来比较的几个协议，差别在于：

**Shadowsocks**加密后的流量没有TLS外壳，是一段"看不懂的随机数据"，早年就是靠这个特征被主动探测识别出来的。Trojan有完整的TLS外壳，这一层过不了。

**VLESS+REALITY**更进一步——它不但是TLS，用的还是真实大厂网站（比如微软、苹果）的证书，审查方去探测的时候会被转发到那个真网站，看起来毫无破绽。Trojan用的是你自己域名的证书，一个访问量为零的陌生域名。

**Hysteria2**走的是QUIC/UDP路线，主打抗丢包和高带宽利用率，和Trojan不是一个赛道。

所以Trojan的软肋也很清楚：**它的伪装只到"这是TLS"这一层为止**。一个从没有人访问过的域名，突然有固定几个IP在长时间保持TLS连接，这个行为模式本身就不太自然。历史上Trojan也确实经历过被主动探测的阶段——审查方直接去连你的443端口，发现响应不像一个正常网站，就把你标记了。

这也是为什么传统Trojan教程都会教你配一个nginx假网站做fallback。不过这一点现在有不同看法，后面"进阶"那节会专门讲。

## 整体流程

```
准备VPS和域名 → 解析生效 → 校时 → 装sing-box → 申请证书 → 写服务端配置
      → 放行端口 → 启动并验证 → Clash Verge接入 → Shadowrocket接入 → 验证出口IP
```

下面用到的示例值，操作时全部换成你自己的：

| 占位符 | 含义 |
|---|---|
| `trojan.example.com` | 你解析到VPS的域名 |
| `443` | Trojan监听端口 |
| `YOUR_PASSWORD` | 连接密码，第五步会生成 |

## 第一步：准备VPS和域名解析

系统建议Debian 12或Ubuntu 22.04/24.04，1核512M足够。

在DNS服务商处加一条A记录，把`trojan.example.com`指向VPS的IPv4地址。用Cloudflare的话，**一定要把小云朵关掉（DNS only，灰色）**——开着代理Cloudflare会截走80和443的流量，证书申请和节点连接都会失败。

解析加完后在VPS上验证：

```bash
apt update && apt install -y dnsutils curl
dig +short trojan.example.com
```

输出应该正好是你VPS的IP。不对的话等几分钟让解析传播，别急着往下走——后面证书申请会卡在这里。

## 第二步：校时

TLS对系统时间敏感，偏差几分钟客户端就会报证书错误，而且报出来的信息很有迷惑性，看着像证书本身坏了。先同步好：

```bash
timedatectl set-timezone UTC
apt install -y systemd-timesyncd
systemctl enable --now systemd-timesyncd
timedatectl status
```

看到`System clock synchronized: yes`就行了。

## 第三步：安装sing-box

用官方APT仓库装，以后`apt upgrade`就能直接升级：

```bash
sudo mkdir -p /etc/apt/keyrings
sudo curl -fsSL https://sing-box.app/gpg.key -o /etc/apt/keyrings/sagernet.asc
sudo chmod a+r /etc/apt/keyrings/sagernet.asc
echo '
Types: deb
URIs: https://deb.sagernet.org/
Suites: *
Components: *
Enabled: yes
Signed-By: /etc/apt/keyrings/sagernet.asc
' | sudo tee /etc/apt/sources.list.d/sagernet.sources
sudo apt-get update
sudo apt-get install -y sing-box
```

确认装上了：

```bash
sing-box version
```

如果VPS访问不了这个仓库，用官方脚本：

```bash
curl -fsSL https://sing-box.app/install.sh | sh
```

这里多说一句为什么用sing-box而不是老牌的trojan-go：trojan-go已经很久没有维护了，而sing-box在持续更新，同一套程序还能跑Hysteria2、VLESS、AnyTLS等协议。以后想换协议或者同时开几个，不用再装一堆东西。

## 第四步：申请Let's Encrypt证书

用acme.sh的standalone模式，临时占用80端口做验证。先确认80是空的：

```bash
ss -tlnp | grep ':80 ' || echo "80端口空闲"
```

被nginx之类占着的话先`systemctl stop nginx`，签完再启回来。

安装acme.sh并申请（邮箱换成你自己的）：

```bash
curl https://get.acme.sh | sh -s email=you@example.com
source ~/.bashrc
~/.acme.sh/acme.sh --set-default-ca --server letsencrypt
~/.acme.sh/acme.sh --issue -d trojan.example.com --standalone --keylength ec-256
```

看到`Cert success`就成了。

接着把证书装到固定路径，并挂上续期后的重启钩子——**这一步经常被教程漏掉，结果三个月后证书过期、节点毫无征兆地全挂**：

```bash
mkdir -p /etc/sing-box/cert
~/.acme.sh/acme.sh --install-cert -d trojan.example.com --ecc \
  --fullchain-file /etc/sing-box/cert/fullchain.pem \
  --key-file /etc/sing-box/cert/private.key \
  --reloadcmd "systemctl restart sing-box"
```

两个细节：`--keylength ec-256`签出来的是ECC证书，所以`--install-cert`必须带`--ecc`，不然会提示找不到证书；另外必须用`fullchain.pem`而不是`cert.pem`，少了中间证书的话部分客户端会报"certificate signed by unknown authority"。

acme.sh安装时会自动往crontab写每日检查任务，确认一下：

```bash
crontab -l | grep acme
```

## 第五步：生成密码

```bash
openssl rand -base64 24 | tr -dc 'A-Za-z0-9' | head -c 24; echo
```

这条会生成一个24位、只含字母数字的密码。之所以不用带符号的base64原始输出，是因为后面Shadowrocket的分享链接里如果密码含`@`、`:`、`/`、`#`这些字符，必须做百分号编码，很容易出错。**把生成的结果复制保存好**，服务端和客户端要填一致。

## 第六步：写服务端配置

```bash
nano /etc/sing-box/config.json
```

贴进去，替换域名和密码：

```json
{
  "log": {
    "level": "info",
    "timestamp": true
  },
  "inbounds": [
    {
      "type": "trojan",
      "tag": "trojan-in",
      "listen": "::",
      "listen_port": 443,
      "users": [
        {
          "name": "user1",
          "password": "YOUR_PASSWORD"
        }
      ],
      "tls": {
        "enabled": true,
        "server_name": "trojan.example.com",
        "alpn": [
          "h2",
          "http/1.1"
        ],
        "certificate_path": "/etc/sing-box/cert/fullchain.pem",
        "key_path": "/etc/sing-box/cert/private.key"
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

几个字段说明：

`"listen": "::"`同时监听IPv4和IPv6。只有IPv4的机器写`"0.0.0.0"`也行。

`"listen_port": 443`——Trojan用443是有意义的，整个协议的前提就是"看起来像正常HTTPS"，跑在一个奇怪的高位端口上这个前提就塌了一半。如果443被别的服务占用，看后面"进阶"那节的共存方案。

`"users"`是数组，可以配多组账号。给朋友分一个的话，加一个对象、换name和password即可，不用改动其他地方。

`"alpn"`填`h2`和`http/1.1`，和真实HTTPS站点协商的协议一致。这个要和客户端保持一致。

写完先做语法检查，别直接启动：

```bash
sing-box check -c /etc/sing-box/config.json
```

没有任何输出就是通过了。

## 第七步：证书权限

确认sing-box以什么用户运行：

```bash
systemctl cat sing-box | grep -i '^User='
```

没有输出（默认root运行）就跳过这步。如果显示了非root用户，给证书授权：

```bash
chown -R sing-box:sing-box /etc/sing-box/cert
chmod 600 /etc/sing-box/cert/private.key
```

## 第八步：放行端口

系统防火墙：

```bash
ufw allow 443/tcp
ufw allow 80/tcp
ufw reload
ufw status
```

80端口留着给证书续期，别关。

另外——这条经常被忽略——**云厂商控制台的安全组是独立的一层**。阿里云、腾讯云、AWS、Oracle这些都要在网页控制台的安全组规则里单独放行443和80，只在系统里`ufw allow`是不够的。很多"配置全对就是连不上"最后都查到这里。

## 第九步：启动并验证

```bash
systemctl enable --now sing-box
systemctl status sing-box
```

看到`active (running)`就起来了。起不来就看日志：

```bash
journalctl -u sing-box -n 50 --no-pager
```

确认端口在监听：

```bash
ss -tlnp | grep 443
```

最关键的一步，验证TLS证书真的生效、证书链完整：

```bash
openssl s_client -connect trojan.example.com:443 \
  -servername trojan.example.com </dev/null 2>/dev/null \
  | openssl x509 -noout -subject -issuer -dates
```

正常会输出证书域名、签发者（Let's Encrypt）和有效期。这一步过不了的话客户端一定连不上，先在这里解决，别急着去调客户端。

## 第十步：Clash Verge接入（桌面端）

Clash Verge底层是mihomo内核。在Clash Verge里新建本地配置（订阅 → 新建 → 本地文件），贴入：

```yaml
mixed-port: 7890
allow-lan: false
mode: rule
log-level: info

proxies:
  - name: "Trojan-节点1"
    type: trojan
    server: trojan.example.com
    port: 443
    password: "YOUR_PASSWORD"
    sni: trojan.example.com
    udp: true
    alpn:
      - h2
      - http/1.1
    client-fingerprint: chrome
    skip-cert-verify: false
    network: tcp

proxy-groups:
  - name: "节点选择"
    type: select
    proxies:
      - "Trojan-节点1"
      - DIRECT

rules:
  - GEOIP,CN,DIRECT
  - MATCH,节点选择
```

参数解释：

`sni`填真实域名，必须和证书上的域名一致。

`skip-cert-verify`一定要填`false`。用了真证书还设成`true`，等于主动放弃证书校验，中间人就能伪造连接——这是自签证书教程留下的坏习惯，换真证书后务必改回来。

`client-fingerprint: chrome`是uTLS指纹伪装，让ClientHello看起来像Chrome发出来的。对Trojan来说这个参数价值不小：默认的Go TLS指纹是相当明显的特征，加上它能让握手更像真实浏览器。

`alpn`要和服务端配置的保持一致。

`udp: true`开启UDP转发，游戏和语音通话需要。

## 第十一步：Shadowrocket接入（iOS端）

Trojan是Shadowrocket支持最早、最成熟的协议之一，任何版本都能用，不像新协议那样有版本门槛。

**方式一：分享链接导入（推荐）**

Trojan的URI格式：

```
trojan://密码@域名:端口?security=tls&sni=域名&alpn=h2,http/1.1&fp=chrome&type=tcp#节点名称
```

按上面的配置拼出来是：

```
trojan://YOUR_PASSWORD@trojan.example.com:443?security=tls&sni=trojan.example.com&alpn=h2,http/1.1&fp=chrome&type=tcp#Trojan-节点1
```

几个细节：

- 端口是443时可以省略，但写上更保险
- `fp=chrome`对应上面说的uTLS指纹伪装
- `#`后面是节点显示名称，中文需要URL编码，嫌麻烦用英文
- 用真证书时**不要**加`allowInsecure=1`，那个参数是给自签证书用的
- 密码含特殊字符必须做百分号编码，这也是第五步建议生成纯字母数字密码的原因

把链接复制到剪贴板，切回Shadowrocket，App会自动弹窗提示添加。

**方式二：手动填写**

首页右上角`+`，类型选`Trojan`，填：

| 字段 | 填什么 |
|---|---|
| 地址 | trojan.example.com |
| 端口 | 443 |
| 密码 | 你的密码 |
| SNI / Peer名称 | trojan.example.com |
| 允许不安全 | 关闭 |

保存后回首页点选节点，右上角开关打开。

## 第十二步：验证流量真的走了代理

显示"已连接"不代表流量真的走了代理，一定要实测。

桌面端，Clash Verge开启代理后在终端跑：

```bash
curl -x socks5h://127.0.0.1:7890 https://ipinfo.io/ip
```

输出应该是VPS的IP，不是你本地的。

手机端直接用Safari打开`ipinfo.io`看IP。

同时在服务器上盯日志，看连接有没有真打进来：

```bash
journalctl -u sing-box -f
```

这招在排查"显示连上了但打不开网页"时特别有用：服务端日志完全没动静，说明问题在客户端配置或者防火墙；日志有连接但网页出不去，说明问题在服务端出站或者VPS本身的网络。

## 进阶：和已有网站共用443端口

如果这台VPS上已经跑着一个网站，443被nginx占了，有两种处理方式。

**方案一：sing-box监听443，用fallback转发给nginx**

把nginx改成监听本地8080，然后在Trojan的inbound里加上fallback：

```json
"fallback": {
  "server": "127.0.0.1",
  "server_port": 8080
}
```

这样，带正确密码的Trojan流量被sing-box处理，其他所有流量（比如有人直接用浏览器访问你的域名）会被转发给nginx，返回一个真实的网页。

**不过这里有个值得知道的反直觉观点**：sing-box官方文档在fallback这个字段的说明里明确写着，没有证据表明GFW会依据HTTP响应来检测和封锁Trojan服务器，而在服务器上开放标准的http/s端口反而是一个大得多的特征。

换句话说，"配个假网站防主动探测"这套流传已久的做法，在sing-box维护者看来收益存疑、甚至可能适得其反。我的建议是：如果你本来就有一个真实在运营的网站，用fallback共用443完全合理；但如果你只是为了"防探测"专门去搭一个没人访问的空壳网站，性价比不高，不如把精力花在别的地方。

**方案二：换一台VPS或换个端口**

最省事的做法。如果这台机器的网站很重要，不如单独开一台小鸡跑代理，两边互不影响，出问题时排查也简单。

## 常见问题排查

**证书申请失败或卡住**

依次检查：80端口是否被占用（`ss -tlnp | grep ':80 '`）、域名解析是否真指向这台机器（`dig +short 你的域名`）、云厂商安全组是否放行80、Cloudflare小云朵是否关闭。

**客户端报 certificate signed by unknown authority**

证书链不完整。检查配置里`certificate_path`指向的是`fullchain.pem`而不是`cert.pem`。

**客户端报证书过期或尚未生效**

服务器或手机时间不对。服务器跑`timedatectl status`确认已同步；手机检查"设置-通用-日期与时间-自动设置"。

**握手成功但立刻断开**

九成是密码不一致。服务端和客户端的密码必须完全相同，注意复制时有没有带上多余的空格或换行。也检查一下两边的`alpn`是否一致。

**连上了但网页打不开**

按第十二步看服务端日志。日志没动静多半是云厂商安全组没放行443。

**sing-box启动失败**

`journalctl -u sing-box -n 50 --no-pager`看报错。最常见是JSON语法错误（多了或少了逗号，`sing-box check`能提前发现）和证书路径不存在/无读取权限。

**443端口启动报 permission denied**

1024以下端口需要特权。确认sing-box是以root运行，或者给二进制加上`CAP_NET_BIND_SERVICE`能力。

**用了一段时间突然全挂**

先想想是不是快三个月了——证书到期没续上。`~/.acme.sh/acme.sh --list`看有效期，`~/.acme.sh/acme.sh --renew -d 你的域名 --ecc --force`手动续一次。如果确实是这个原因，回头检查第四步的`--reloadcmd`有没有挂上。

## Trojan在2026年还值得用吗

老实说，如果你是从零开始、追求最强的抗封锁能力，今天大概率不会首选Trojan——VLESS+REALITY在伪装维度上确实更高一档，Hysteria2在弱网环境下的体感也更好。

但Trojan有它的位置，而且这个位置还挺稳：

**客户端兼容性是它最大的优势**。从Shadowrocket、Clash系列到各种路由器固件、老版本客户端，几乎没有不支持Trojan的。你配一个Trojan节点，可以确信任何设备上都能连；换成比较新的协议，就得挨个确认客户端版本。

**配置简单、出问题好查**。整个协议就是"TLS+密码"，排查链路短。新协议的参数多，出问题时要排除的变量也多。

**在没有被重点针对的网络环境下，它够用**。海外常驻、企业网络绕行、日常科学上网这些场景，Trojan的稳定性完全不成问题。真正需要担心伪装强度的，主要是国内网络管控严格时期的特定场景。

所以比较合理的用法是：**Trojan当作兼容性最好的保底节点，配合一个REALITY或Hysteria2节点做主力**。sing-box一套程序就能同时开几个inbound，成本几乎为零。

## 写在最后

自建节点的价值在于完全可控，而且走一遍能把TLS、证书、DNS这些东西真正搞明白，这些知识在别的地方也用得上。但也要算清楚长期成本：VPS月费、IP被墙后换机器的时间、证书续期、内核升级，这些都是需要你持续照看的。

如果你的目标只是稳定地用，那这些维护成本是否值得，取决于你的时间怎么定价。两条路都合理，按自己的情况选。

顺带一提，我们的订阅同时支持Clash/Mihomo和Shadowrocket格式，节点里包含Trojan、Hysteria2、VLESS+REALITY等多种协议，导入订阅链接就能用，不用自己折腾服务端和证书续期。

## 参考资料

- [sing-box Trojan Inbound 配置文档](https://sing-box.sagernet.org/configuration/inbound/trojan/)
- [sing-box 安装文档](https://sing-box.sagernet.org/installation/package-manager/)
- [mihomo（Clash.Meta）Trojan 配置文档](https://wiki.metacubex.one/config/proxies/trojan/)
- [acme.sh 项目主页](https://github.com/acmesh-official/acme.sh)
