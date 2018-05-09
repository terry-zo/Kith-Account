# KithAccountGenerator
## Run using python 2.7

Creates kith accounts with captcha requests from 2captcha.

## Instructions

  * First, you must enter all appropriate information in **config.json**.
    * **email** is the email you want all your kith accounts under.
    * **firstname** is the first name of every kith account generated.
    * **lastname** is the last name of every kith account generated.
    * **password** is the password of every kith account generated.
    * **captchakey** is the api key for your [2captcha](https://goo.gl/T1c75n) account.
    * **sitekey** is the captcha identifier for [kith](https://kith.com/). The sitekey is pre-filled, and should only be changed if [kith](https://kith.com/) renewed their sitekey.
    * **interval** is the amount of time the script waits _(in seconds)_ before creating the next account.
    * **numofaccounts** is the amount of accounts you want the script the create.
    * **proxyfile** is the name of the file your proxies are in.
    * **logconsole** can only be **True** or **False**, where the user can determine if they want a log.txt for debugging purposes.
  * Secondly, you must install the modules required for the script to work. Please refer to **Required modules**.

**_Note_** If you don't have a 2captcha account, you can create one [here](https://goo.gl/T1c75n).

## Proxies
_Proxies implemented 5-8-18_

  * Every proxy must be on its own line.
  * Every proxy must be the following format:

    * Supports IP Authentication proxies:
    ```ip:host```

    * Supports user:pass Authentication proxies:
    ```ip:host:user:pass```


  * **Example**:
  ```
  123.123.123.123:12345:hello:bye
  123.123.123.123:12345:hello:bye
  123.123.123.123:12345:hello:bye
  123.123.123.123:12345:hello:bye
  123.123.123.123:12345
  123.123.123.123:12345
  123.123.123.123:12345
  123.123.123.123:12345
  ```

## Required modules

Before running the script, the following modules are required:
```requests bs4```

This can be accomplished by running the following command in a command prompt:

```
pip install requests bs4
```

## Other scripts

I _might or might not_ release more scripts on my [twitter](https://twitter.com/zoegodterry).

Follow to be the **first ones to know**!
