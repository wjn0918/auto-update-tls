# 自动更新tls 证书

!!! note

    nginx 目前使用systemctl 进行自动重启


Nginx 配置里专门开一个 /\.well-known/acme-challenge/ 路径，指向一个空目录

```

    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }


```

```
sudo mkdir -p /var/www/certbot
sudo chown -R www-data:www-data /var/www/certbot
```

.env 配置文件中指定webroot path