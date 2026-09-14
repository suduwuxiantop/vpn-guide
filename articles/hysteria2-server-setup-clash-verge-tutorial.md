# Hysteria2从零搭建到Clash Verge连接：一份能直接跑通的实战教程

> 同步发布于 [速度无限VPN官方博客](https://main.suduwuxian.top/hysteria2%e4%bb%8e%e9%9b%b6%e6%90%ad%e5%bb%ba%e5%88%b0clash-verge%e8%bf%9e%e6%8e%a5%e6%95%99%e7%a8%8b/)
>
> > 网上关于Hysteria2的教程不少，但很多要么只讲协议原理不讲怎么落地，要么给了一堆命令却不解释每一步在干什么，照着敲完出了问题也不知道从哪排查。这篇文章按"协议是什么→服务端怎么搭→客户端怎么连"的顺序走一遍完整流程，命令和配置都是可以直接抄的，出问题也知道去哪看日志。
> >
> > ## Hysteria2到底是什么
> >
> > Hysteria2是一个基于QUIC（也就是HTTP/3底层用的那套协议）的代理协议，跑在UDP上，自带TLS 1.3加密、多路复用和0-RTT握手。理解它，抓住三个关键词就够了。
> >
> > **拥塞控制用的是"Brutal"**：传统TCP协议在丢包时会保守地降速，Hysteria2的Brutal算法反过来，会主动探测链路的可用带宽并尽量把它占满，所以在丢包率较高、网络质量不稳定的链路上，Hysteria2通常比Shadowsocks、VMess这类老协议更抗造，速度也更稳。
> >
> > **混淆用的是"salamander"**：这是Hysteria2内置的流量混淆机制，会把数据包内容打散重排，用来干扰深度包检测（DPI）对特征的识别，让代理流量更难被针对性识别和限速。
> >
> > **伪装（masquerade）**：服务端可以配置成对外表现得像一个普通的HTTP/3网站——用一张合法的TLS证书，把非认证流量伪装成访问某个正常网站的样子，即便被探测或人工检查，看起来也只是"有人在浏览网页"。
> >
> > 这三者叠加起来，Hysteria2在弱网、高丢包、审查严格的环境下，综合表现通常明显好于基于TCP的老一代协议。
> >
> > *协议解决的是"怎么把数据包稳定送到对面"，线路（直连/中转/专线）解决的是"数据包走哪条路"，两者是相互独立又能叠加增益的维度*
> >
> > ## 部署流程一览
> >
> > 整个搭建过程可以拆成六步，先看一眼全貌，再逐步展开：
> >
> > ```mermaid
> > flowchart LR
> >     A[准备VPS<br/>+域名解析] --> B[执行官方<br/>一键安装脚本]
> >     B --> C[编辑<br/>config.yaml]
> >     C --> D[防火墙放行<br/>UDP端口]
> >     D --> E[启动并检查<br/>systemd服务]
> >     E --> F[Clash Verge<br/>导入配置连接]
> > ```
> >
> > ## 第一步：准备一台全新的VPS和域名
> >
> > Hysteria2的ACME自动签证书功能需要一个能正常解析的域名，所以开始之前先准备好：
> >
> > - 一台全新的VPS（Ubuntu 22.04/24.04或Debian 11/12都可以，1核1G起步够用）
> > - - 一个域名，并把一条A记录解析到这台VPS的IP上（如果用Cloudflare做DNS，记得先把这条记录的橙色云朵关掉，改成"仅DNS"，否则ACME签证书会失败）
> >   - - 确认服务器安全组/防火墙面板里放行了你打算用的端口（比如443）的UDP和TCP
> >    
> >     - ## 第二步：执行官方一键安装脚本
> >    
> >     - SSH登录进服务器后，执行Hysteria2官方维护的安装脚本：
> >    
> >     - ```bash
> > bash <(curl -fsSL https://get.hy2.sh/)
> > ```
> >
> > 这个脚本会自动识别系统架构、下载对应的Hysteria2二进制文件、注册成systemd服务，并在`/etc/hysteria/config.yaml`生成一份示例配置——但这份示例配置还不能直接用，需要手动改成你自己的参数，这是下一步的内容。
> >
> > 如果想装指定版本，可以加版本号参数：
> >
> > ```bash
> > bash <(curl -fsSL https://get.hy2.sh/) --version v2.6.1
> > ```
> >
> > ## 第三步：编辑服务端配置
> >
> > 用编辑器打开配置文件：
> >
> > ```bash
> > nano /etc/hysteria/config.yaml
> > ```
> >
> > 把内容替换成下面这份最小可用配置（记得把域名、邮箱、密码换成你自己的）：
> >
> > ```yaml
> > listen: :443
> >
> > acme:
> >   domains:
> >     - your.domain.com
> >   email: your-email@example.com
> >
> > auth:
> >   type: password
> >   password: 设置一个足够复杂的密码
> >
> > masquerade:
> >   type: proxy
> >   proxy:
> >     url: https://news.ycombinator.com/
> >     rewriteHost: true
> > ```
> >
> > 几个字段说明一下：
> >
> > `listen`写`:443`表示同时监听IPv4和IPv6的443端口；`acme`这一段是让Hysteria2自动向Let's Encrypt申请并续期TLS证书，只需要填域名和邮箱，不用自己折腾certbot；`auth`是客户端连接时要提供的密码，随便用密码生成器生成一串长一点的字符串就行；`masquerade`是前面提到的伪装功能，配置成`proxy`模式后，服务器对未认证的HTTP请求会原样转发一份`news.ycombinator.com`的内容回去，看起来就是个普通网站，这段如果不需要伪装效果也可以整段删掉。
> >
> > 如果你的服务器已经有自己签发的证书，不想用ACME自动签，可以把`acme`那一段换成：
> >
> > ```yaml
> > tls:
> >   cert: /path/to/your_cert.crt
> >   key: /path/to/your_key.key
> > ```
> >
> > ## 第四步：放行防火墙端口
> >
> > 配置里监听的是443端口的UDP（Hysteria2的核心流量走UDP），如果服务器本身开了ufw，记得放行：
> >
> > ```bash
> > ufw allow 443/udp
> > ufw allow 443/tcp
> > ```
> >
> > 如果是云厂商的安全组（阿里云、腾讯云、AWS等），还要去控制台面板里把443端口的UDP协议也加到入站规则里——这一步经常被漏掉，是"服务启动了但客户端连不上"最常见的原因之一。
> >
> > ## 第五步：启动服务并检查运行状态
> >
> > 保存配置后，启动并设置开机自启：
> >
> > ```bash
> > systemctl enable --now hysteria-server.service
> > ```
> >
> > 改完配置需要重启时用：
> >
> > ```bash
> > systemctl restart hysteria-server.service
> > ```
> >
> > 检查服务是否正常运行：
> >
> > ```bash
> > systemctl status hysteria-server.service
> > ```
> >
> > 如果显示`active (running)`就说明启动成功了。要是启动失败或者想看更详细的运行日志（比如证书有没有签发成功），可以看：
> >
> > ```bash
> > journalctl --no-pager -e -u hysteria-server.service
> > ```
> >
> > ACME签证书失败大部分是因为域名没解析对、DNS还没生效，或者Cloudflare的代理（橙色云朵）没关掉导致验证请求走了CDN——把这几项排查一遍基本都能解决。
> >
> > ## 第六步：在Clash Verge里配置连接
> >
> > 服务端跑起来之后，回到本地电脑打开Clash Verge，在配置文件里加一段代理节点。可以直接编辑现有订阅配置文件，在`proxies`列表下加入：
> >
> > ```yaml
> > proxies:
> >   - name: my-hysteria2
> >     type: hysteria2
> >     server: your.domain.com
> >     port: 443
> >     password: 你在服务端设置的那串密码
> >     sni: your.domain.com
> >     skip-cert-verify: false
> >     alpn: [h3]
> >     up: 50 Mbps
> >     down: 200 Mbps
> > ```
> >
> > 字段和服务端一一对应：`server`填你解析的域名（不是IP，因为证书是签给域名的）；`port`和服务端`listen`保持一致；`password`就是服务端`auth.password`；`sni`一般也填同一个域名；`skip-cert-verify`用ACME签的正规证书时保持`false`就行，只有用自签证书测试时才需要改成`true`；`up`/`down`是你本地上传下载带宽的粗略估计值，帮助Hysteria2的拥塞控制更快收敛到合适的速率，不需要特别精确。
> >
> > 改完保存，在Clash Verge界面里把这个节点加进代理组、切换过去，右下角测一下延迟，能测出数值基本就说明连通了。如果服务端加了`masquerade`伪装，用浏览器直接访问`https://your.domain.com`，应该能看到伪装网站的内容，这也是确认证书和监听没问题的一个简单办法。
> >
> > ## 常见问题排查
> >
> > 连不上的时候，按这个顺序排查效率比较高：先看服务端`journalctl`日志有没有报错（尤其是证书相关的）；再确认云厂商安全组和服务器本地防火墙的UDP规则都放行了；然后检查客户端配置里的域名、端口、密码是不是跟服务端完全一致（哪怕多一个空格都连不上）；最后如果前面都没问题还是慢或者卡，可以试着调整一下`up`/`down`的估计值，或者检查一下本地网络本身是不是对UDP流量有限速。
> >
> > ## 写在最后
> >
> > Hysteria2相比传统协议的优势主要体现在弱网环境下的抗丢包能力和更快的握手速度，但协议本身解决不了线路层面的拥堵问题——如果你的国际出口本身就严重拥堵，换协议也没法把烂线路变成好线路。搭建这一套流程走完，剩下能不能长期稳定运行，还要看服务器所在的机房线路质量和后续的证书续期、日志监控这些运维细节。
> >
> > ## 参考资料
> >
> > 1. [Server Installation Script - Hysteria 2 官方文档](https://v2.hysteria.network/docs/getting-started/Server-Installation-Script/)
> > 2. 2. [Server - Hysteria 2 官方文档：服务端配置](https://v2.hysteria.network/docs/getting-started/Server/)
> >    3. 3. [Hysteria2 — mihomo Core Tutorial：客户端字段详解](https://core-tutorial.argsment.com/mihomo/hysteria2/)
> >       4. 4. [Hysteria / Hysteria2 · Project Atlas：协议技术特性总结](https://project-atlas-dbb.pages.dev/docs/02-protocols/03-hysteria2/)
> >          5. 5. [GitHub - apernet/hysteria：Hysteria2官方源码仓库](https://github.com/apernet/hysteria)
> >             6. 
