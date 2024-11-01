# Cloudflare Integration

The following procedure will enable Cloudflare integration, so that when the server boots
it automatically registers its IP address with Cloudflare:

Create /home/cms/cloudflare.config:

```
cloudflare_auth_email=(Cloudflare login email address)
cloudflare_auth_key=(Cloudflare Global API Key)
```

Install cloudflare service and enable:

```
sudo cp cloudflare.service /etc/systemd/system
cd /etc/systemd/system
sudo systemctl enable cloudflare
sudo systemctl start cloudflare
sudo systemctl status cloudflare
```

The status output should look something like this:

```
cms@cms-server:/etc/systemd/system$ sudo systemctl status cloudflare
○ cloudflare.service - Cloudflare IP update
     Loaded: loaded (/etc/systemd/system/cloudflare.service; enabled; vendor preset: enabled)
     Active: inactive (dead) since Wed 2024-10-30 13:01:40 UTC; 29min ago
    Process: 8528 ExecStart=/bin/bash /home/cms/open-contest/cloudflare.sh (code=exited, status=0/SUCCESS)
   Main PID: 8528 (code=exited, status=0/SUCCESS)
        CPU: 744ms
```

When the system reboots, it should register its IP with
CloudFlare.
