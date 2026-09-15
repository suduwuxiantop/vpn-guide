# AnyTLS从零搭建到Clash Verge连接：一份能直接跑通的实战教程

> 同步发布于 [速度无限VPN官方博客](https://main.suduwuxian.top/anytls%e4%bb%8e%e9%9b%b6%e6%90%ad%e5%bb%ba%e5%88%b0clash-verge%e8%bf%9e%e6%8e%a5%e6%95%99%e7%a8%8b/)

> 前面两篇分别写了Hysteria2（抗丢包速度快）和VLESS+REALITY（伪装成真实网站）。这篇要讲的AnyTLS走的是第三条路：不追求花哨的伪装技巧，而是把"减少连接特征、降低握手开销"这件事做到极致，用最朴素的方式让流量更难被基于连接行为的检测手段盯上。同样按"协议是什么→服务端怎么搭→客户端怎么连"的顺序，命令和配置都能直接抄。

## AnyTLS到底是什么

AnyTLS是sing-box内核从1.12.0版本开始原生支持的一个代理协议，出发点是解决Trojan、VMess+TLS这类"裸TLS"协议长期存在的一个问题：这类协议每开一条新连接都要重新走一次完整的TLS握手，在网络质量差、需要频繁开新连接的场景下，握手本身的时延和特征就成了破绽——审查系统统计连接频率、握手时长这些行为特征，也能大致画出代理流量的轮廓，不需要看清包内容。

**核心思路是连接复用（session pooling）**：AnyTLS客户端会维护一个"闲置连接池"，新的请求优先复用池子里已经建立好TLS的连接，而不是每次都重新握手。`idle_session_check_interval`、`idle_session_timeout`、`min_idle_session`这几个参数就是用来控制这个连接池怎么维护的——池子里保留几条闲置连接、多久检查一次、闲置多久回收，本质上是用连接复用换取"握手行为"的隐蔽性。

**padding_scheme（填充方案）**：AnyTLS在数据包外面加了一层长度混淆，通过`padding_scheme`定义的规则给包体添加随机长度的填充，让基于包长度序列做流量分析的检测手段更难提取特征。不填的话，sing-box会用一套内置的默认规则。

**协议设计足够"朴素"**：和REALITY比，AnyTLS不去借用第三方网站的证书做伪装，它更依赖标准TLS（可以是ACME签发的真证书，也可以自签）加上连接复用和填充混淆的组合拳，配置复杂度介于Hysteria2和REALITY之间，属于"新协议里相对好懂、好排障"的一档。

*协议解决的是"减少可被观察的连接行为特征"，线路（直连/中转/专线）解决的是"数据包走哪条路"，两者同样可以叠加使用*

## 部署流程一览

整个搭建过程可以拆成六步：

```mermaid
flowchart LR
    A[准备VPS<br/>+域名解析] --> B[官方仓库<br/>安装sing-box]
    B --> C[准备TLS证书<br/>ACME/自签]
    C --> D[编辑<br/>config.json]
    D --> E[防火墙放行<br/>TCP端口]
    E --> F[Clash Verge<br/>导入配置连接]
```

## 第一步：准备一台全新的VPS和域名

AnyTLS用的是标准TLS，最省心的方式是配一个能自动签发证书的域名：

- 一台全新的VPS（Ubuntu 22.04/24.04或Debian 11/12都可以，1核1G起步够用）
- 一个域名，并把一条A记录解析到这台VPS的IP上（如果用Cloudflare做DNS，记得把橙色云朵关掉改成"仅DNS"，否则证书申请会失败）
- 确认服务器安全组/防火墙面板里放行了你打算用的端口（比如443）的TCP

## 第二步：通过官方APT仓库安装sing-box

sing-box官方维护了APT源，比脚本一键安装更透明、也方便后续升级。SSH登录服务器后依次执行：

```bash
sudo mkdir -p /etc/apt/keyrings && \
sudo curl -fsSL https://sing-box.app/gpg.key -o /etc/apt/keyrings/sagernet.asc && \
sudo chmod a+r /etc/apt/keyrings/sagernet.asc && \
echo 'Types: deb
URIs: https://deb.sagernet.org/
Suites: *
Components: *
Enabled: yes
Signed-By: /etc/apt/keyrings/sagernet.asc' | sudo tee /etc/apt/sources.list.d/sagernet.sources && \
sudo apt-get update && \
sudo apt-get install sing-box
```

装完之后，配置文件路径是`/etc/sing-box/config.json`，systemd服务名是`sing-box`。

## 第三步：生成密码

AnyTLS的认证用的是密码字符串，随便用一串足够长的随机字符即可，也可以用`openssl`生成：

```bash
openssl rand -base64 16
```

把输出的字符串记下来，服务端和客户端配置里都要填这个值。

## 第四步：编辑服务端配置

打开（或新建）配置文件：

```bash
sudo nano /etc/sing-box/config.json
```

写入下面这份最小可用配置（把`your.domain.com`、`your-email@example.com`、`your-password-here`换成你自己的）：

```json
{
  "inbounds": [
    {
      "type": "anytls",
      "tag": "anytls-in",
      "listen": "0.0.0.0",
      "listen_port": 443,
      "users": [
        {
          "name": "user1",
          "password": "your-password-here"
        }
      ],
      "tls": {
        "enabled": true,
        "server_name": "your.domain.com",
        "acme": {
          "domain": ["your.domain.com"],
          "email": "your-email@example.com",
          "provider": "letsencrypt"
        }
      }
    }
  ],
  "outbounds": [
    {
      "type": "direct"
    }
  ]
}
```

几个字段说明一下：`users`里可以填多个`name`/`password`对，支持多用户共用一个端口；`tls.acme`这一段是让sing-box自动向Let's Encrypt申请并续期证书，只需要域名和邮箱；`padding_scheme`没写就是用内置默认规则，一般不需要手动改。

如果你的服务器已经有自己签发的证书，不想用ACME自动签，可以把`tls`换成手动指定证书路径：

```json
"tls": {
  "enabled": true,
  "server_name": "your.domain.com",
  "certificate_path": "/etc/sing-box/cert.pem",
  "key_path": "/etc/sing-box/key.pem"
}
```

配置写完保存后，建议先测试一下语法是否正确：

```bash
sing-box check -c /etc/sing-box/config.json
```

## 第五步：放行防火墙端口

AnyTLS走标准TLS，也就是TCP。如果服务器本身开了ufw，记得放行：

```bash
sudo ufw allow 443/tcp
```

如果是云厂商的安全组（阿里云、腾讯云、AWS等），同样要去控制台面板里把443端口的TCP协议加到入站规则里。

## 第六步：启动服务并检查运行状态

启动并设置开机自启：

```bash
sudo systemctl enable sing-box
sudo systemctl start sing-box
```

改完配置需要重启时用：

```bash
sudo systemctl restart sing-box
```

检查服务是否正常运行：

```bash
sudo systemctl status sing-box
```

如果显示`active (running)`就说明启动成功了。要是启动失败或者想确认证书有没有签发成功，看详细日志：

```bash
sudo journalctl -u sing-box --output cat -e
```

## 第七步：在Clash Verge里配置连接

服务端跑起来之后，回到本地电脑打开Clash Verge，在配置文件里加一段代理节点。可以直接编辑现有订阅配置文件，在`proxies`列表下加入：

```yaml
proxies:
  - name: my-anytls
    type: anytls
    server: your.domain.com
    port: 443
    password: your-password-here
    sni: your.domain.com
    udp: true
    idle-session-check-interval: 30
    idle-session-timeout: 30
    min-idle-session: 0
```

字段和服务端一一对应：`server`填你解析的域名（用ACME签的证书就必须填域名，不能填IP）；`port`和服务端`listen_port`保持一致；`password`就是服务端`users`里对应的密码；`sni`一般也填同一个域名；如果服务端用的是自签证书，需要额外加一行`skip-cert-verify: true`跳过证书校验（用ACME签的正规证书则不需要）；连接池相关的几个参数保持默认即可，一般不需要手动调。

改完保存，在Clash Verge界面里把这个节点加进代理组、切换过去，右下角测一下延迟，能测出数值基本就说明连通了。

## 常见问题排查

连不上的时候，按这个顺序排查效率比较高：先用`sing-box check`确认配置文件语法没问题；再看`journalctl -u sing-box`日志有没有报错（尤其是ACME证书相关的，域名没解析对、Cloudflare橙色云朵没关都会导致签证书失败）；然后确认服务器安全组和本地防火墙的TCP规则都放行了443端口；接着检查客户端的`password`、`sni`是不是和服务端完全一致；最后如果用的是自签证书，别忘了客户端加上`skip-cert-verify: true`，否则TLS握手会因为证书校验失败而连不上。

## 写在最后

AnyTLS解决的是连接层面的行为特征问题——通过连接复用减少握手频率，通过填充混淆包长度特征，思路上比追求"完美伪装"的REALITY更朴素，配置也相对简单，适合作为除Hysteria2、VLESS+REALITY之外的第三种协议做多协议部署，分散单一协议被针对性识别的风险。协议本身同样不解决线路拥堵问题，落地IP的线路质量依然决定最终体验。

## 参考资料

1. [AnyTLS Inbound - sing-box 官方文档：服务端配置](https://sing-box.sagernet.org/configuration/inbound/anytls/)
2. [AnyTLS Outbound - sing-box 官方文档：客户端配置](https://sing-box.sagernet.org/configuration/outbound/anytls/)
3. [Package Manager - sing-box 官方文档：APT仓库安装方式](https://sing-box.sagernet.org/installation/package-manager/)
4. [TLS - sing-box 官方文档：ACME证书配置](https://sing-box.sagernet.org/configuration/shared/tls/)
5. [AnyTLS — mihomo Core Tutorial：客户端字段详解](https://core-tutorial.argsment.com/singbox/anytls)
