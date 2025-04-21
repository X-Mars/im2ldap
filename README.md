# IM LDAP 账号同步助手 im2ldap

## 项目介绍

1. 基于vue3 + django rest framework
2. 由**cursor、trae**协助开发
3. 当前为测试版本，欢迎提意见和需求
4. 近期将进行频繁更新，欢迎star、watch

## 功能定位

1. 将企业微信、飞书、钉钉等用户账号同步到LDAP
2. 支持企业微信、飞书、钉钉、

## demo

<https://im2ldap.huoxingxiaoliu.com/login?username=admin&password=huoxingxiaoliu>  
用户名：admin  
密码：huoxingxiaoliu


## 跟着火星小刘学运维开发

<https://space.bilibili.com/439068477>

## qq群

[![QQ群](https://pub.idqqimg.com/wpa/images/group.png)](https://qm.qq.com/cgi-bin/qm/qr?k=a_y5qjuIfBYZHkhGg4JTZqGjTk3KUI5T&jump_from=webapi&authKey=qJpb8UQWFJcxKBdT/zq9kGBqiMxOm9k3TkfYeAtaVtHAbKbIfxMiGBolmP+aWa5b)

[![QQ群二维码](https://github.com/X-Mars/im2ldap/blob/master/images/qrcode.jpg?raw=true)](https://qm.qq.com/cgi-bin/qm/qr?k=a_y5qjuIfBYZHkhGg4JTZqGjTk3KUI5T&jump_from=webapi&authKey=qJpb8UQWFJcxKBdT/zq9kGBqiMxOm9k3TkfYeAtaVtHAbKbIfxMiGBolmP+aWa5b)

[![B站火星小刘](https://github.com/X-Mars/Zabbix-Alert-WeChat/blob/master/images/5.jpg?raw=true)](https://space.bilibili.com/439068477)

## 截图展示

![登录页](https://raw.githubusercontent.com/X-Mars/im2ldap/refs/heads/master/images/1.png)
![仪表盘](https://raw.githubusercontent.com/X-Mars/im2ldap/refs/heads/master/images/2.png)
![笔记管理](https://raw.githubusercontent.com/X-Mars/im2ldap/refs/heads/master/images/3.png)
![笔记授权](https://raw.githubusercontent.com/X-Mars/im2ldap/refs/heads/master/images/4.png)
![三方登录](https://raw.githubusercontent.com/X-Mars/im2ldap/refs/heads/master/images/5.png)

## 开发环境

```shell
python 3.12
sqlite 3
django 5.2
node v22.14.0
```

## 部署安装

1. 拉取代码

```shell
git clone https://github.com/X-Mars/im2ldap.git
```

2. 初始化后端

```shell
cd im2ldap/server
pip3 install -r requirements.txt
python3 manage.py makemigrations
python3 manage.py migrate
```

3. 启动项目

```shell
python3 manage.py runserver
```

4. nginx 反向代理

```conf
location / {
  root /im2ldap/web/dist;
  index  index.html index.htm;
}

location /api {
  proxy_pass  http://localhost:8000;
  proxy_redirect     off;
  proxy_set_header   Host             $host;
  proxy_set_header   X-Real-IP        $remote_addr;
  proxy_set_header   X-Forwarded-For  $proxy_add_x_forwarded_for;
  proxy_next_upstream error timeout invalid_header http_500 http_502 http_503 http_504;
  proxy_max_temp_file_size 0;
  proxy_connect_timeout      90;
  proxy_send_timeout         900;
  proxy_read_timeout         900;
  proxy_buffer_size          34k;
  proxy_buffers              4 32k;
  proxy_busy_buffers_size    64k;
  proxy_temp_file_write_size 64k;
}
```

## 后台地址

```url
<http://ip:8000/admin>
```

## 默认用户名密码

```conf
用户名：admin 
密码： huoxingxiaoliu
```

## License

[996ICU License](LICENSE)  
