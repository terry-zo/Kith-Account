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
from bs4 import BeautifulSoup as soup
from random import randint

registered = 0


def log(phrase):
    if os.name == 'nt':
        os.system('cls')
    else:
        os.system('clear')
    print("Kith Account Generator")
    print("Twitter @zoegodterry\n")
    with open('log.txt', 'a+') as logfile:
        logfile.write(phrase + "\n")
        logfile.close()
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
            log(data + " is not filled out in config.json! Exiting...")
            sys.exit()


def request_recaptcha(service_key, google_site_key, pageurl):
    url = "http://2captcha.com/in.php?key=" + service_key + "&method=userrecaptcha&googlekey=" + google_site_key + "&pageurl=" + pageurl
    resp = requests.get(url)
    if resp.text[0:2] != 'OK':
        log('Error: ' + resp.text + "\nExiting...")
        sys.exit()
    captcha_id = resp.text[3:]
    log("Successfully Requested For Captcha!")
    time.sleep(0.1)
    return captcha_id


def receive_token(captcha_id, service_key):
    fetch_url = "http://2captcha.com/res.php?key=" + service_key + "&action=get&id=" + captcha_id
    for count, i in enumerate(range(1, 80)):
        log('Getting Captcha Token Attempt #' + str(count) + "/80")
        resp = requests.get(fetch_url)
        if resp.text[0:2] == 'OK':
            grt = resp.text.split('|')[1]  # g-recaptcha-token
            log("Captcha Token Received: " + grt)
            time.sleep(0.1)
            return grt
        time.sleep(1)
    log("No Tokens Received. Restarting...")
    time.sleep(1)
    global config
    genaccs(config)


def submit_recaptcha(grt, at, session):
    payload = {
        "utf8": "✓",
        "authenticity_token": at,
        "g-recaptcha-response": grt
    }
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "en-US,en;q=0.9",
        "Cache-Control": "max-age=0",
        "Connection": "keep-alive",
        "Content-Length": "614",
        "Content-Type": "application/x-www-form-urlencoded",
        "Host": " kith.com",
        "Referer": "https://kith.com/challenge",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.139 Safari/537.36"
    }
    resp = session.post('https://kith.com/account', headers=headers, data=payload, allow_redirects=False)
    return resp


def grabauthkey(page_html):
    page_soup = soup(page_html, 'html.parser')
    authtokenvar = page_soup.findAll("input", {"name": "authenticity_token"})
    if authtokenvar:
        authtoken = authtokenvar[0]["value"]
        log("Authenticity token found: " + authtoken)
        return authtoken
    else:
        log("No authenticity token found. Exiting...")
        sys.exit()


def genaccs(config):
    s = requests.Session()
    fn = config['firstname']
    ln = config['lastname']
    pw = config['password']
    interval = config['interval']
    email = genemail(config['email'])
    payload = {
        'form_type': 'create_customer',
        "utf8": "✓",
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
        'Connection': 'keep-alive',
        'Content-Length': '205',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Host': 'kith.com',
        'Referer': 'https://kith.com/account/register',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.139 Safari/537.36'
    }
    b = s.post('https://kith.com/account', headers=headers, data=payload, allow_redirects=False)
    if b.status_code == 302:
        log('Requesting Captcha...')
        captcha_id = request_recaptcha(config['captchakey'], config['sitekey'], 'https://kith.com/challenge')
        grt = receive_token(captcha_id, config['captchakey'])
        challenge = s.get('https://kith.com/challenge')
        challenge_html = challenge.content
        authtoken = grabauthkey(challenge_html)
        submit_recaptcha(grt, authtoken, s)
    else:
        log('An unexpected ' + str(b.status_code) + ' error has occurred. Exiting...')
        sys.exit()
    global registered
    registered += 1
    log('Returned Status Code: ' + str(b.status_code) + '\nFirst Name: ' + fn + '\nLast Name: ' + ln + '\nE-mail: ' + email + '\nPassword: ' + pw + '\nSuccessfully registered account #' + str(registered))
    with open('Accounts.txt', 'a+') as txtfile:
        txtfile.write(email + ':' + pw + "\n")
        txtfile.close()
    s.cookies.clear()
    time.sleep(interval)


config = readconfig('config.json')
verifydata(config)
numofaccs = config["numofaccounts"]
log("Creating " + str(numofaccs) + " accounts...")
for _ in range(numofaccs):
    genaccs(config)
log("Successfully created " + str(numofaccs) + " accounts!")
sys.exit()
