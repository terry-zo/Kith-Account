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
import Queue
import threading
from bs4 import BeautifulSoup as soup
from threading import Thread, Lock
from random import randint, choice


def log(phrase):
    global l_lock, logconsole
    if logconsole == "True":
        with l_lock:
            with open('log.txt', 'a+') as logfile:
                logfile.write(phrase + "\n")
    print phrase


def readconfig(filename):
    with open(filename, 'r') as config_json:
        config_data = config_json.read()
    return json.loads(config_data)


def genemail(rawemail):
    front = rawemail.split("@")[0]
    provider = rawemail.split("@")[1]
    bignum = str(randint(1, 1000000))
    return front + "+" + bignum + '@' + provider


def verifydata(config):
    for data in config:
        if config[data] == "":
            log("{} is not filled out in config.json! Exiting...".format(data))
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


def request_recaptcha(service_key, google_site_key, pageurl, index):
    url = "http://2captcha.com/in.php?key=" + service_key + "&method=userrecaptcha&googlekey=" + google_site_key + "&pageurl=" + pageurl
    resp = requests.get(url)
    if resp.text[0:2] != 'OK':
        log("#{} - Error: {} Exiting...".format(index, resp.text))
    captcha_id = resp.text[3:]
    log("#{} - Successfully requested for captcha.".format(index))
    return captcha_id


def receive_token(captcha_id, service_key, index):
    global queue_, lock_
    fetch_url = "http://2captcha.com/res.php?key=" + service_key + "&action=get&id=" + captcha_id
    for count in range(1, 26):
        log("#{} - Attempting to fetch token. {}/25".format(index, count))
        resp = requests.get(fetch_url)
        if resp.text[0:2] == 'OK':
            grt = resp.text.split('|')[1]  # g-recaptcha-token
            log("#{} - Captcha token received.".format(index))
            return grt
        time.sleep(5)
    log("#{} - No tokens received. Restarting...".format(index))
    with lock_:
        queue_.put(1)


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
    return resp


def grabauthkey(page_html, index):
    global queue_, lock_
    page_soup = soup(page_html, 'html.parser')
    authtokenvar = page_soup.findAll("input", {"name": "authenticity_token"})
    if authtokenvar:
        authtoken = authtokenvar[0]["value"]
        log("#{} - Authenticity token found.".format(index))
        return authtoken
    else:
        log("#{} - No authenticity token found. Restarting...".format(index))
        with lock_:
            queue_.put(1)


def genaccs(config, index):
    global queue_, lock_, p_list, p_list_lock, p_lock, a_lock
    while queue_.qsize() > 0:
        with lock_:
            queue_.get()
        rand_proxy = choice(p_list)
        if not rand_proxy in p_list_lock:
            with p_lock:
                p_list_lock.append(rand_proxy)
                log("Using proxy: " + str(rand_proxy))
            s = requests.Session()
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
                'Accept-Encoding': 'gzip, deflat    e, br',
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
            b = s.post('https://kith.com/account', headers=headers, data=payload, allow_redirects=False, proxies={"https": rand_proxy}, timeout=30)
            if b.status_code == 302:
                log('#{} - Requesting Captcha...'.format(index))
                captcha_id = request_recaptcha(config['captchakey'], config['sitekey'], 'https://kith.com/challenge', index)
                grt = receive_token(captcha_id, config['captchakey'], index)
                challenge = s.get('https://kith.com/challenge')
                challenge_html = challenge.content
                authtoken = grabauthkey(challenge_html, index)
                submit_recaptcha(grt, authtoken, s, rand_proxy)
            else:
                log('#{} - An unexpected ' + str(b.status_code) + ' error has occurred.'.format(index))
            log('#{} - Successfully registered.'.format(index))
            with a_lock:
                with open('Accounts.txt', 'a+') as txtfile:
                    txtfile.write(email + ':' + pw + "\n")
            s.close()
            unlock_p(rand_proxy)
            time.sleep(interval)
        else:
            log("Proxy in use: " + str(rand_proxy))
            with lock_:
                queue_.put(1)


def unlock_p(rand_proxy):
    global p_list_lock, p_lock
    if rand_proxy in p_list_lock:
        with p_lock:
            p_list_lock.remove(rand_proxy)
            log("Released proxy: " + rand_proxy)


def main(numofaccs, config):
    global queue_, lock_, t_list, t_lock
    for index in range(numofaccs):
        with lock_:
            queue_.put(index)
    st_ = time.time()
    with t_lock:
        for index in range(10):
            thread_ = Thread(target=genaccs, args=(config, index))
            t_list.append(thread_)
            thread_.start()
    for t_ in t_list:
        t_.join()
    log("Finished {} in {}".format(numofaccs, (time.time() - st_)))


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
    logconsole = config["logconsole"]
    numofaccs = config["numofaccounts"]
    main(numofaccs, config)
