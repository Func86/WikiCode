#!/usr/bin/python3

import re
import requests

WORKSPACE = {
    'ZHWIKI': {
        'URL': "https://zh.wikipedia.org/w/api.php",
        'PROXY': {'http': 'http://localhost:1087', 'https': 'http://localhost:1087'},
        'SESSION': requests.Session(),
        'lgname': "YOUR-BOT-NAME",
        "lgpassword": "YOUR-BOT-PASSWORD",
        "csrftoken": ""
        }
    }


def login(spaceid = 'ZH'):
    workspace = WORKSPACE[spaceid]
    # Step 1: GET request to fetch login token
    PARAMS_0 = {
        "action": "query",
        "meta": "tokens",
        "type": "login",
        "format": "json"
    }

    R = workspace['SESSION'].get(url=workspace['URL'], params=PARAMS_0)
    DATA = R.json()
    print(DATA)

    LOGIN_TOKEN = DATA['query']['tokens']['logintoken']

    # Step 2: POST request to log in. Use of main account for login is not
    # supported. Obtain credentials via Special:BotPasswords
    # (https://www.mediawiki.org/wiki/Special:BotPasswords) for lgname & lgpassword
    PARAMS_1 = {
        "action": "login",
        "lgname": workspace['lgname'],
        "lgpassword": workspace['lgpassword'],
        "lgtoken": LOGIN_TOKEN,
        "format": "json"
    }

    R = workspace['SESSION'].post(workspace['URL'], data=PARAMS_1)
    DATA = R.json()
    print(DATA)

    # Step 3: GET request to fetch CSRF token
    PARAMS_2 = {
        "action": "query",
        "meta": "tokens",
        "format": "json"
    }

    R = workspace['SESSION'].get(url=workspace['URL'], params=PARAMS_2)
    DATA = R.json()
    print(DATA)
    workspace['csrftoken'] = DATA['query']['tokens']['csrftoken']
    return workspace['csrftoken']


def deal_convert(cat_from, cat_to, spaceid = 'ZH'):
    workspace = WORKSPACE[spaceid]
    PARAMS = {
        "action": "query",
        "format": "json",
        "list": "categorymembers",
        "formatversion": "2",
        "cmtitle": cat_from,
        "cmlimit": "max"
    }
    res = workspace['SESSION'].get(url=workspace['URL'], params=PARAMS, proxies = workspace['PROXY'])
    data = res.json()
    members = data["query"]["categorymembers"]
    cat_from = re.sub('^Category:', '', cat_from)
    cat_to = re.sub('^Category:', '', cat_to)
    for item in members:
        pageid = item["pageid"]
        print(pageid, item["title"], cat_from, cat_to)


def main():
    site = 'ZHWIKI'
    # login(site) # If you have a heigher API limit

    PARAMS = {
        "action": "query",
        "format": "json",
        "generator": "allcategories",
        "redirects": 1,
        "converttitles": 1,
        "formatversion": "2",
        "gaclimit": "max"
    }

    while True:
        res = WORKSPACE[site]['SESSION'].get(url=WORKSPACE[site]['URL'], params=PARAMS, proxies = WORKSPACE[site]['PROXY'])
        data = res.json()

        if not 'converted' in data['query']:
            if 'continue' in data:
                PARAMS['continue'] = data['continue']['continue']
                PARAMS['gaccontinue'] = data['continue']['gaccontinue']
                continue
            else:
                break

        redirect = {}
        if 'redirects' in data['query']:
            for redir in data["query"]['redirects']:
                cat_from = redir['from']
                cat_to = redir['to']
                print('#Redirect:', cat_from, cat_to)
                redirect[cat_from] = cat_to

        for conv in data['query']['converted']:
            cat_from = conv['from']
            cat_to = conv['to']
            print("* [[" + cat_from + "]]->[[" + cat_to + "]]")
            if cat_from in redirect:
                deal_convert(cat_from, redirect[cat_from], site)
            if cat_to in redirect:
                deal_convert(cat_to, redirect[cat_to], site)
            if cat_from in redirect or cat_to in redirect:
                continue

            deal_convert(cat_from, cat_to, site)

        if 'continue' in data:
            PARAMS['continue'] = data['continue']['continue']
            PARAMS['gaccontinue'] = data['continue']['gaccontinue']
        else:
            break


if __name__ == '__main__':
    main()
