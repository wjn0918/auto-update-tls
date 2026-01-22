# 自动更新 TLS 证书

### 说明

* **Nginx** 使用 `systemctl` 进行自动重启。
* 配置 Nginx 在 `/.well-known/acme-challenge/` 路径上提供对证书验证的访问。

### 配置 Nginx

在 Nginx 配置文件中添加以下内容：

```nginx
location /.well-known/acme-challenge/ {
    root /var/www/certbot;
}
```

### 创建并设置目录权限

1. 创建证书验证目录：

   ```bash
   sudo mkdir -p /var/www/certbot
   ```

2. 设置权限：

   ```bash
   sudo chown -R www-data:www-data /var/www/certbot
   ```

### 配置 `.env`

在 `.env` 文件中指定 `webroot` 路径：

```env
WEBROOT_PATH=/var/www/certbot
```

