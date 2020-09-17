import binascii
import json
import os
import subprocess
import time

import requests
from Crypto.Cipher import AES

role = os.getenv("V2RAY_ROLE")

url = os.getenv("V2RAY_URL")

key = os.getenv("V2RAY_KEY")
iv = os.getenv("V2RAY_IV")

path_bin = "/snap/v2ray/current/bin/"

configCache = ""

# Padding
BS = len("" if key is None else key)
pad = lambda s: s + (BS - len(s) % BS) * chr(BS - len(s) % BS)
unpad = lambda s: s[0:-ord(s[-1:])]


def poll():
    log("poll,role", role)
    resp = requests.post(url, encrypt(role))
    http_code = resp.status_code
    content = resp.text
    log("poll,http code", str(http_code))
    log("poll,http content", content)
    if http_code != 200 or content is None or content.isspace():
        return None
    content = decrypt(content)
    data = fromJson(content)
    log("poll,content", content)
    # if (data['code'] != '200' or data['message'] == 'repeat'):
    #     return None
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
    global configCache
    config = toJson(data)
    if not configCache.isspace() and config == configCache:
        return False
    updated = write(config)
    if updated:
        configCache = config
    return updated


def write(config):
    exist = os.path.exists(path_bin)
    if not exist:
        log("poll,write", "bin path not exist")
        return False
    fd = os.open(path_bin + "config.json", os.O_RDWR | os.O_CREAT)
    os.write(fd, config.encode())
    os.close(fd)
    return True


def restartV2ray():
    pids = procExist("v2ray")
    for pid in pids:
        subprocess.getstatusoutput("kill -9 " + pid)
    subprocess.getstatusoutput("/snap/v2ray/current/bin/v2ray")
    time.sleep(1000)
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


def log(pre, msg):
    exist = os.path.exists("/tmp")
    if not exist:
        return
    fd = os.open("/tmp/loop.log", os.O_RDWR | os.O_CREAT)
    os.write(fd, (pre + " : " + msg).encode())
    os.close(fd)


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
            return
        updated = update(config)
        if not updated:
            return
        restartV2ray()
        log("main", "end")
    except Exception as e:
        print(e)
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
        time.sleep(1000)
