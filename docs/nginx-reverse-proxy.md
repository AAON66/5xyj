# Nginx 反向代理配置

当系统部署在 nginx 反向代理后面时，需要配置以下 header 以确保审计日志记录真实客户端 IP。

## 推荐配置

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## 说明

- `X-Real-IP`: nginx 设置为客户端真实 IP（`$remote_addr`）
- `X-Forwarded-For`: 追加客户端 IP 到转发链
- 系统优先读取 `X-Forwarded-For`，备选 `X-Real-IP`
- 只有来自 `trusted_proxies` 配置中的 IP 发起的请求才会信任代理头

## 环境变量

在 `.env` 文件中可配置信任的代理 IP：

```
TRUSTED_PROXIES=["127.0.0.1", "::1", "10.0.0.1"]
```

默认值：`["127.0.0.1", "::1"]`

## 安全说明

系统对代理头采用严格的信任模型：
- 只有当请求直接来自 `trusted_proxies` 列表中的 IP 时，才会信任 `X-Forwarded-For` 和 `X-Real-IP` 头
- 这防止了来自公网的客户端通过伪造代理头来欺骗服务器获取虚假 IP
- 生产环境部署时，必须配置 nginx / 负载均衡器的内网 IP 到 `trusted_proxies`

## 验证

配置完成后，访问系统并检查审计日志页面中的 IP 地址列。
如果仍显示 127.0.0.1，请检查 nginx 配置是否正确加载并且 `trusted_proxies` 中包含了 nginx 所在主机的 IP。
