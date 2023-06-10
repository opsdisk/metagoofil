# Metagoofil

## Introduction

metagoofil searches Google for specific types of files being publicly hosted on a web site and optionally downloads them
to your local box.  This is useful for Open Source Intelligence gathering, penetration tests, or determining what files
your organization is leaking to search indexers like Google.  As an example, it uses the Google query below to find all
the `.pdf` files being hosted on `example.com` and optionally downloads a local copy.

```none
site:example.com filetype:pdf
```

This is a maintained fork of the original <https://github.com/laramies/metagoofil> and is currently installed by default
on the Kali Operating System <https://gitlab.com/kalilinux/packages/metagoofil>.  Unlike the original, a design decision
was made to not do metadata analysis and instead defer to other tools like `exiftool`.

```bash
exiftool -r *.doc | egrep -i "Author|Creator|Email|Producer|Template" | sort -u
```

Comments, suggestions, and improvements are always welcome.  Be sure to follow [@opsdisk](https://twitter.com/opsdisk)
on Twitter for the latest updates.

## Installation

Clone the git repository and install the requirements

```bash
git clone https://github.com/opsdisk/metagoofil
cd metagoofil
virtualenv -p python3 .venv  # If using a virtual environment.
source .venv/bin/activate  # If using a virtual environment.
pip install -r requirements.txt
```

## Docker Installation & Usage

```bash
git clone https://github.com/opsdisk/metagoofil
cd metagoofil
docker build -t metagoofil .

# This will save the files in the host ./data directory.
docker run -v $PWD/data:/data metagoofil -d github.com -f -n 10 -r 4 -t pdf -w
```

## Google is blocking me!

If you start getting HTTP 429 errors, Google has rightfully detected you as a bot and will block your IP for a set
period of time.  One solution is to use proxychains and a bank of proxies to round robin the lookups.

Install proxychains4

```bash
apt install proxychains4 -y
```

Edit the `/etc/proxychains4.conf` configuration file to round robin the look ups through different proxy servers.  In
the example below, 2 different dynamic SOCKS proxies have been set up with different local listening ports (9050 and
9051).  Don't know how to utilize SSH and dynamic SOCKS proxies?  Do yourself a favor and pick up a copy of [Cyber
Plumber's Handbook and interactive lab](https://gumroad.com/l/cph_book_and_lab) to learn all about Secure Shell (SSH)
tunneling, port redirection, and bending traffic like a boss.

```bash
vim /etc/proxychains4.conf
```

```bash
round_robin
chain_len = 1
proxy_dns
remote_dns_subnet 224
tcp_read_time_out 15000
tcp_connect_time_out 8000
[ProxyList]
socks4 127.0.0.1 9050
socks4 127.0.0.1 9051
```

Throw `proxychains4` in front of the Python script and each lookup will go through a different proxy (and thus source
from a different IP).  You could even tune down the `-e` delay time because you will be leveraging different proxy
boxes.

```bash
proxychains4 python metagoofil.py -d https://github.com -f -t pdf,doc,xls
```
