#!/usr/local/bin/python
# -*- coding: utf-8 -*-

# Kith Account Generator
# Twitter @zoegodterry

import os
import requests
import time
import random
import sys
import json
import bs4
import names
import Queue
import threading
from bs4 import BeautifulSoup as soup
from threading import Thread, Lock
from random import randint, choice


def readconfig(filename):
    with open(filename, 'r') as config_json:
        config_data = config_json.read()
    return json.loads(config_data)


def genemail(rawemail):
    if rawemail[0] != "@":
        splitstuff = rawemail.split("@")
        for item in splitstuff:
            if item.strip() == "":
                splitstuff.remove(item)
        front = splitstuff[0]
        provider = splitstuff[1]
        bignum = str(randint(1, 1000000))
        return front + "+" + bignum + '@' + provider
    else:
        front = names.get_first_name() + names.get_last_name()
        splitstuff = rawemail.split("@")
        for item in splitstuff:
            if item.strip() == "":
                splitstuff.remove(item)
        provider = splitstuff[0]
        bignum = str(randint(1, 1000000))
        return front + bignum + "@" + provider


def verifydata(config):
    for data in config:
        if config[data] == "":
            print("{} is not filled out in config.json! Exiting...".format(data))
            sys.exit()


def readproxyfile(proxyfile):
    with open(proxyfile, "a+") as raw_proxies:
        proxies = raw_proxies.read().split("\n")
        proxies_list = []
        for individual_proxies in proxies:
            if individual_proxies.strip() != "":
                p_splitted = individual_proxies.split(":")
                if len(p_splitted) == 2:
                    proxies_list.append("http://" + individual_proxies)
                if len(p_splitted) == 4:
                    # ip0:port1:user2:pass3
                    # -> username:password@ip:port
                    p_formatted = "http://{}:{}@{}:{}".format(p_splitted[2], p_splitted[3], p_splitted[0], p_splitted[1])
                    proxies_list.append(p_formatted)
        proxies_list.append(None)
    return proxies_list


def request_recaptcha(service_key, google_site_key, pageurl):
    url = "http://2captcha.com/in.php?key=" + service_key + "&method=userrecaptcha&googlekey=" + google_site_key + "&pageurl=" + pageurl
    resp = requests.get(url)
    if resp.text[0:2] != 'OK':
        print("Error: {} Exiting...".format(resp.text))
        raise
    captcha_id = resp.text[3:]
    return captcha_id


def receive_token(captcha_id, service_key):
    global queue_, lock_
    fetch_url = "http://2captcha.com/res.php?key=" + service_key + "&action=get&id=" + captcha_id
    for count in range(1, 26):
        resp = requests.get(fetch_url)
        if resp.text[0:2] == 'OK':
            grt = resp.text.split('|')[1]  # g-recaptcha-token
            return grt
        time.sleep(5)
    print("No tokens received.")
    raise


def submit_recaptcha(grt, at, session, rand_proxy):
    payload = {
        "authenticity_token": at,
        "g-recaptcha-response": grt
    }
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "en-US,en;q=0.9",
        "Cache-Control": "max-age=0",
        "Connection": "close",
        "Content-Length": "614",
        "Content-Type": "application/x-www-form-urlencoded",
        "Host": "kith.com",
        "Referer": "https://kith.com/challenge",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.139 Safari/537.36"
    }
    resp = session.post('https://kith.com/account', headers=headers, data=payload, allow_redirects=False, proxies={"https": rand_proxy}, timeout=30)
    if resp.status_code == 200:
        return resp
    else:
        raise


def grabauthkey(page_html):
    global queue_, lock_
    page_soup = soup(page_html, 'html.parser')
    authtokenvar = page_soup.findAll("input", {"name": "authenticity_token"})
    if authtokenvar:
        authtoken = authtokenvar[0]["value"]
        return authtoken
    else:
        print("No authenticity token found. Restarting...")
        raise


def genaccs(config):
    global queue_, lock_, p_list, p_list_lock, p_lock, a_lock
    while queue_.qsize() > 0:
        try:
            with lock_:
                queue_.get()
            rand_proxy = choice(p_list)
            if not rand_proxy in p_list_lock:
                if rand_proxy != None:
                    with p_lock:
                        p_list_lock.append(rand_proxy)
                fn = config['firstname']
                ln = config['lastname']
                pw = config['password']
                interval = config['interval']
                email = genemail(config['email'])
                payload = {
                    'form_type': 'create_customer',
                    "customer[first_name]": fn,
                    "customer[last_name]": ln,
                    "customer[email]": email,
                    "customer[password]": pw
                }
                headers = {
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Cache-Control': 'max-age=0',
                    'Connection': 'close',
                    'Content-Length': '205',
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'Host': 'kith.com',
                    'Referer': 'https://kith.com/account/register',
                    'Upgrade-Insecure-Requests': '1',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.139 Safari/537.36'
                }
                with requests.Session() as s:
                    b = s.post('https://kith.com/account', headers=headers, data=payload, proxies={"https": rand_proxy}, timeout=30)
                    if b.status_code == 200:
                        if (b.url == "https://kith.com/challenge") or (b.url == "https://kith.com/challenge/"):
                            print("Waiting for captcha.")
                            captcha_id = request_recaptcha(config['captchakey'], config['sitekey'], 'https://kith.com/challenge')
                            grt = receive_token(captcha_id, config['captchakey'])
                            challenge = s.get('https://kith.com/challenge')
                            challenge_html = challenge.content
                            authtoken = grabauthkey(challenge_html)
                            submit_recaptcha(grt, authtoken, s, rand_proxy)
                            print('Successfully registered.')
                            with a_lock:
                                with open('Accounts.txt', 'a+') as txtfile:
                                    txtfile.write(email + ':' + pw + "\n")
                        elif (b.url == "https://kith.com/account/") or (b.url == "https://kith.com/account"):
                            print('Successfully registered.')
                            with a_lock:
                                with open('Accounts.txt', 'a+') as txtfile:
                                    txtfile.write(email + ':' + pw + "\n")
                        else:
                            raise
                    else:
                        raise
                unlock_p(rand_proxy)
                time.sleep(interval)
            else:
                raise
        except Exception as e:
            with lock_:
                queue_.put(1)
            excepName = type(e).__name__


def unlock_p(rand_proxy):
    global p_list_lock, p_lock
    if (rand_proxy in p_list_lock) and (rand_proxy != None):
        with p_lock:
            p_list_lock.remove(rand_proxy)


def main(numofaccs, config):
    global queue_, lock_, t_list, t_lock
    for _ in range(numofaccs):
        with lock_:
            queue_.put(1)
    st_ = time.time()
    threads = []
    for _ in range(10):
        t = Thread(target=genaccs, args=(config,))
        threads.append(t)
    [t.start() for t in threads]
    [t.join() for t in threads]
    print("Finished {} in {}".format(str(numofaccs), (time.time() - st_)))


if __name__ == "__main__":
    config = readconfig('config.json')
    verifydata(config)
    queue_ = Queue.Queue()
    lock_ = Lock()
    p_list = readproxyfile(config["proxyfile"])
    p_lock = Lock()
    p_list_lock = []
    a_lock = Lock()
    l_lock = Lock()
    t_list = []
    t_lock = Lock()
    numofaccs = config["numofaccounts"]
    main(numofaccs, config)
