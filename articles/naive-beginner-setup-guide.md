# NaiveProxy 小白搭建教程：从买服务器到能用，照着做就行

前面写过一篇 NaiveProxy 的技术向教程，这篇是给完全没搭过服务器的人准备的简化操作版——不讲原理，只讲每一步手指头该按什么、该看到什么结果。跟着做就行，不需要你懂任何网络知识。

**先提醒一件事**：NaiveProxy 用的客户端跟其他协议不一样，**Clash Verge 用不了**，后面第七步会详细说该装什么软件，别提前下错App。

## 开始之前，你需要准备好这3样东西

1. **一台海外服务器（VPS）**——1核1GB内存、系统选 **Ubuntu 22.04**。买完你会拿到IP地址、用户名（通常是`root`）、密码这三样东西，先存好备用。

2. **一个域名**——NaiveProxy 这个协议**必须**要有真实域名和真实证书才能用，不像有的协议可以先不买域名凑合跑。域名很便宜，随便找个域名注册商买一个就行。

3. **一个能连SSH的软件**——Windows用Xshell或者系统自带的"终端"（Windows Terminal）；Mac用自带的"终端"App。

---

## 第一步：登录你的服务器

打开SSH软件，输入（把IP换成你自己的）：

```bash
ssh root@你的服务器IP
```

第一次连接会问你要不要继续，输入 `yes` 回车。接着输入密码——**密码框不会显示任何字符，也不会有星号，这是正常的**，打完直接回车。

**你应该看到什么**：屏幕前面变成 `root@一串字符:~#` 的样子，说明登录成功了。

**卡住了怎么办**：多半是IP/用户名/密码打错了，回邮箱翻商家发的信息，逐字对照，注意别多打空格。

---

## 第二步：把域名解析到服务器

登录你买域名那个网站的后台，找到"域名解析"或"DNS解析"，添加一条：

- 记录类型：`A`
- 主机记录：`@` 或者你想要的前缀（比如 `naive`）
- 记录值：你服务器的IP地址
- 保存

等几分钟到半小时生效。在自己电脑上打开命令行，输入 `ping 你的域名`，如果返回的IP跟服务器IP一致，说明解析好了。

---

## 第三步：安装 sing-box（NaiveProxy靠它运行）

回到SSH窗口，复制粘贴下面这行，回车：

```bash
bash <(curl -fsSL https://sing-box.app/install.sh)
```

**你应该看到什么**：滚动一堆安装信息，最后停下来，光标恢复到 `root@...#`。输入下面这行确认装好了：

```bash
sing-box version
```

能看到一行版本号（类似 `sing-box version 1.x.x`）就说明装成功了。

---

## 第四步：申请免费证书

依次输入下面几行（一行一行来，等上一行执行完再输下一行）：

```bash
curl https://get.acme.sh | sh -s email=你的邮箱地址
```

（换成你自己真实能收邮件的邮箱）

```bash
source ~/.bashrc
```

```bash
~/.acme.sh/acme.sh --issue -d 你的域名 --standalone
```

（换成你第二步解析好的域名）

**你应该看到什么**：最后一行出现 "Cert success" 之类的绿色提示。

**卡住了怎么办**：多半是域名还没解析生效，回第二步用 `ping` 再确认一次。

接着把证书放到指定位置：

```bash
mkdir -p /etc/sing-box/cert
~/.acme.sh/acme.sh --install-cert -d 你的域名 \
  --key-file /etc/sing-box/cert/private.key \
  --fullchain-file /etc/sing-box/cert/cert.pem
```

同样把"你的域名"换成自己的，没有报错就是成功了。

---

## 第五步：写配置文件

输入打开编辑器：

```bash
mkdir -p /etc/sing-box
nano /etc/sing-box/config.json
```

把下面这一整段复制粘贴进去：

```json
{
  "log": {
    "level": "info"
  },
  "inbounds": [
    {
      "type": "naive",
      "listen": "::",
      "listen_port": 443,
      "network": "tcp",
      "users": [
        {
          "username": "设置一个用户名",
          "password": "设置一个高强度密码"
        }
      ],
      "tls": {
        "enabled": true,
        "server_name": "你的域名",
        "certificate_path": "/etc/sing-box/cert/cert.pem",
        "key_path": "/etc/sing-box/cert/private.key",
        "alpn": ["h2", "http/1.1"]
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

粘贴完必须改三个地方：

1. `设置一个用户名` 换成你自己起的用户名（随便起，比如 `myuser`）
2. `设置一个高强度密码` 换成一串字母数字混合的密码，比如 `Xk9mP2vQ7Lw3`
3. `你的域名` 出现的这一处也要换成你自己的域名

改完保存退出：按 `Ctrl+X`，再按 `Y`，再按一次回车。

**特别提醒**：JSON格式对逗号和引号非常敏感，复制粘贴的时候不要手动改动其他符号，只改上面说的这三处文字内容，其他标点符号原样保留。

---

## 第六步：启动服务并检查

先检查配置文件写得对不对：

```bash
sing-box check -c /etc/sing-box/config.json
```

**没有任何输出**（也就是执行完直接回到 `root@...#`）就是配置没问题；如果出现红色报错文字，说明第五步哪里改错了，对照报错提示里提到的行号回去检查。

确认没问题后，设置成开机自启并启动：

```bash
cat > /etc/systemd/system/sing-box.service << 'EOF'
[Unit]
Description=sing-box service
After=network.target

[Service]
ExecStart=/usr/local/bin/sing-box run -c /etc/sing-box/config.json
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable --now sing-box
systemctl status sing-box
```

**你应该看到什么**：绿色的 `active (running)`，说明启动成功。按 `Q` 退出查看界面。

**如果是红色的 failed**：输入 `journalctl -u sing-box -n 50 --no-pager` 看具体报错，一般是配置文件里证书路径或者域名拼写有问题。

---

## 第七步：开放443端口

服务器里放行端口：

```bash
ufw allow 443/tcp
```

**关键的一步，很多人卡在这里**：如果服务器是阿里云、腾讯云、Vultr这类平台买的，还要登录**平台的网页控制台**，找到"安全组"设置，手动添加一条规则放行443端口（TCP）。服务器里配好了，但云平台控制台没放行，照样连不上，这是最容易漏掉的地方。

---

## 第八步：装客户端——注意，不能用Clash Verge

这是NaiveProxy跟其他协议最大的不同点：**Clash Verge目前不支持NaiveProxy这个协议**，装了也找不到对应的选项。要用下面这几个软件：

### Windows电脑：装 v2rayN

1. 去v2rayN的官方发布页面下载最新版（搜索"v2rayN github"能找到，下载 `.exe` 版本）
2. 打开软件，点"服务器"菜单 → 添加自定义配置
3. 把下面这段配置里的信息换成你自己的，粘贴进去：

```json
{
  "type": "naive",
  "server": "你的域名",
  "server_port": 443,
  "username": "第五步设置的用户名",
  "password": "第五步设置的密码",
  "network": "tcp",
  "tls": {
    "enabled": true,
    "server_name": "你的域名"
  }
}
```

4. 保存后，在节点列表里选中它，右键点"测试延迟"，出现数字就是通了

### 安卓手机：装 NekoBox for Android

1. 搜索"NekoBox for Android github"下载安装包安装
2. 打开App，右下角加号 → 手动添加，类型选跟上面一样的配置方式
3. 填入同样的域名、端口、用户名、密码
4. 保存后点击连接按钮

### 苹果手机/电脑：装 sing-box 官方客户端

iOS上叫 **SFI（sing-box for iOS）**，Mac上叫 **SFM（sing-box for Mac）**，可以在App Store里直接搜索"sing-box"找到官方App，配置方式跟上面类似，把域名、端口、用户名密码填进去就行。

---

## 全流程检查清单

卡住了从头对照这张表：

- [ ] 服务器能SSH登录
- [ ] 域名已经解析到服务器IP
- [ ] sing-box 装好了，`sing-box version` 能看到版本号
- [ ] 证书申请成功，出现过 "Cert success"
- [ ] 配置文件里的用户名、密码、域名三处都改成自己的了，其他符号没动过
- [ ] `sing-box check` 没有报错
- [ ] `systemctl status sing-box` 显示 `active (running)`
- [ ] 443端口在服务器里放行了
- [ ] 443端口在云平台控制台的安全组里也放行了
- [ ] 客户端用的是v2rayN/NekoBox/SFI/SFM这几个之一，不是Clash Verge
- [ ] 客户端填的域名、端口、用户名、密码跟服务端完全一致

九成问题顺着这张清单从上往下查都能自己找到。如果卡在某一步，把具体报错截图留着，方便定位问题。
