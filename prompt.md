**根据以下未完成需求更新项目，必须遵循操作条件中的内容**

# 未完成需求

* 使用prettytable库绘制 --list 返回的Let’s Encrypt 证书信息


# 已完成需求

* 使用python创建一个使用certbot自动申请Let’s Encrypt 证书
* 提供查询指定域名的证书是否存在，如果存在，到期时间还有多少
* 需要打包成可执行文件
* GitHub Actions 自动打包
* 创建.env 配置文件
* 通过配置文件配置1、需要监控的域名列表 2、到期剩余多少需要更新
* 添加一个配置判断是否要certbot 是否要更新nginx
* 增加 --list 用来展示目前certbot已经申请的Let’s Encrypt 证书信息


# 操作条件

* 使用 write_to_file 编辑文件
* 不需要更新README.md