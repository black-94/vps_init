import binascii
import hashlib
import json
import os
import subprocess
import time

import requests
from Crypto.Cipher import AES

root_ip = os.getenv("ROOT_IP")
root_passwd = os.getenv("ROOT_PASSWD")

role = os.getenv("V2RAY_ROLE")

url = os.getenv("V2RAY_URL")

key = os.getenv("V2RAY_KEY")
iv = os.getenv("V2RAY_IV")
password = os.getenv("SS_PASSWD")

configCache = ""
ack = ""
md5 = ""

# Padding
BS = len("" if key is None else key)
pad = lambda s: s + (BS - len(s) % BS) * chr(BS - len(s) % BS)
unpad = lambda s: s[0:-ord(s[-1:])]


def poll():
    global md5, ack
    log("poll,", "role:" + role + ",md5:" + md5 + ",ack:" + ack)
    resp = requests.post(url, encrypt("|".join([role, md5, ack])))
    http_code = resp.status_code
    content = resp.text
    log("poll,http code", str(http_code))
    log("poll,http content", content)
    if http_code != 200 or content is None or content.isspace():
        return None
    ack = ""
    content = decrypt(content)
    data = fromJson(content)
    log("poll,content", content)
    if (data['message'] == 'repeat'):
        return None
    return data['config']


def encrypt(text):
    cryptor = AES.new(key.encode(), AES.MODE_CBC, iv.encode())
    ciphertext = cryptor.encrypt(bytes(pad(text), encoding="utf8"))
    return binascii.hexlify(ciphertext)


def decrypt(text):
    ciphertext = bytes.fromhex(text)
    cryptor = AES.new(key.encode(), AES.MODE_CBC, iv.encode())
    plaintext = cryptor.decrypt(ciphertext)
    return str(unpad(plaintext), encoding='utf-8')


def toJson(text):
    return json.dumps(text)


def fromJson(text):
    return json.loads(text)


def update(data):
    global configCache, md5, ack
    config = toJson(data)
    if not configCache.isspace() and config == configCache:
        return False
    updated = write(config)
    if updated:
        configCache = config
        md5 = hashlib.md5(configCache.replace(" ", "").encode('utf8')).hexdigest()
        ack = "true"
    return updated


def write(config):
    v2rayCheck()
    file = open("/root/v2ray/config.cfg", 'w', encoding="utf-8")
    file.write(config)
    file.close()
    return True


def restartV2ray():
    if role == 'end':
        os.system("nohup ss-server -s 0.0.0.0 -p 80 -k '" + password + "' -m aes-256-gcm -t 300 --fast-open &")
    v2rayCheck()
    pids = procExist("v2ray")
    for pid in pids:
        subprocess.getstatusoutput("kill -9 " + pid)
    os.system("nohup /root/v2ray/v2ray -config /root/v2ray/config.cfg &")
    time.sleep(1)
    pids = procExist("v2ray")
    if len(pids) < 1:
        log("v2ray restart", "not success")
        return
    log("v2ray restart ,", "pids : " + " ".join(pids))


def procExist(command):
    status, output = subprocess.getstatusoutput("ps -ef | grep " + command)
    if status != 0:
        raise Exception("ps run error")
    lines = output.splitlines()
    pids = []
    for line in lines:
        if line.find("grep " + command) < 0:
            pid = line.split()[1]
            pids.append(pid)
    return pids


def v2rayCheck():
    if not os.path.exists("/root/v2ray"):
        log("v2rayCheck", "mkdir")
        os.mkdir("/root/v2ray")
    if not os.path.exists("/root/v2ray/v2ray.zip"):
        log("v2rayCheck", "download")
        downloadV2ray()
    if not os.path.exists("/root/v2ray/v2ray"):
        log("v2rayCheck", "unzip")
        os.system("unzip /root/v2ray/v2ray.zip -d /root/v2ray/")


def downloadV2ray():
    if role == 'end':
        os.system(
            "wget -O /root/v2ray/v2ray.zip https://github.com/v2ray/v2ray-core/releases/download/v4.27.5/v2ray-linux-64.zip")
    else:
        os.system(
            "expect ./scp.ex " + "scp" + " root@" + root_ip + ":/root/v2ray/v2ray.zip" + " /root/v2ray/ " + " '" + root_passwd + "' >> /tmp/loop.log")


def log(pre, msg):
    exist = os.path.exists("/tmp")
    if not exist:
        return
    exist = os.path.exists("/tmp/loop.log")
    mode = "a" if exist else "w"
    file = open("/tmp/loop.log", mode, encoding="utf-8")
    t = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    file.write(t + " , " + pre + " : " + msg + "\n")
    print(t + " , " + pre + " : " + msg + "\n")
    file.close()


def main():
    """
    拉取配置
        拉取失败，返回
    更新配置
        缓存比对，无需更新，返回
    重启v2ray
    """
    try:
        log("main", "start")
        config = poll()
        if config is None:
            log("main", "after poll")
            restartV2ray()
            return
        updated = update(config)
        if not updated:
            log("main", "after update")
            return
        restartV2ray()
        log("main", "end")
    except Exception as e:
        print(e)
        log("main", "exception")
        pass


if __name__ == '__main__':
    """
    实例唯一
    轮询：拉取->更新->重启
    注意：客户端缓存
    """
    pids = procExist("loop.py")
    if len(pids) > 1:
        log("main", "process already run")
        exit()
    while True:
        main()
        time.sleep(1)
