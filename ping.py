#!/usr/bin/env python3

## NOTE: requires pysocks

import requests, optparse, time
from threading import *
import re

maxConnections = 4
connection_lock = BoundedSemaphore(value=maxConnections)

#Global variables

Working = []
Tested = 0
To_test = 0
Force_quit = False

def get_tor_session():
    session = requests.session()
    # Tor uses the 9050 port as the default socks port
    session.proxies = {'http':  'socks5h://127.0.0.1:9050',
                       'https': 'socks5h://127.0.0.1:9050'}
    return session


def print_result():
    global Working

    print("[=] {} working URL".format(len(Working)))

    for w in Working:
        print("[+]  {} for {}".format(w['status'], w['url']))


def connect(url, session, thr=False):
    global Working
    global Tested
    global Force_quit

    if not Force_quit:
        time.sleep(1)
        try:
            resp = session.get(url, timeout=10)
            Working.append({'url': url, 'status': resp.status_code})

        except Exception as e:
            if "Missing dependencies for SOCKS support." in str(e) and not Force_quit:
                print("[!] Please that pysocks is installed (pip install pysocks)")
                Force_quit = True
            # elif "SOCKSHTTPConnectionPool" in str(e) and not Force_quit:
                # print("[!] Please check that tor is running")
                # Force_quit = True
            else:
                pass
            #        print(" -  Error on {}".format(url))
        finally:
            if thr:
                Tested = Tested + 1
                connection_lock.release()
                if (Tested == To_test): print_result()

def main():
    global To_test
    global Tested
    global Force_quit

    parser = optparse.OptionParser('usage%prog -f <hosts list>')
    parser.add_option('-f', dest='hostFile', type='string', help='specify the file containing the list of urls to ping')
    (options, args) = parser.parse_args()

    hostFile = options.hostFile

    if hostFile == None:
        print(parser.usage)
        exit(0)


    fn = open(hostFile, 'r')
    schemas = ['http']
    session = get_tor_session()

    checktor_resp = session.get("https://check.torproject.org").text
    if "Congratulations. This browser is configured to use Tor." not in checktor_resp:
        print("[!] Please make sure that TOR is running")
        exit(0)

    print("[i] Using a tor connection")
    ip = re.search(r'<p>Your IP address appears to be:  <strong>(\d+.\d+.\d+.\d+)</strong></p>', checktor_resp).group(1)
    print("[i] Your IP address appears to be {}".format(ip))

    lines = []
    for line in fn.readlines():
        lines.append(line.strip('\r').strip('\n'))

    uniqueLines = set(lines)
    To_test = len(uniqueLines)
    print("[i] {} URL to test".format(To_test))
    for ul in uniqueLines:
        for s in schemas:
            if Force_quit:
                exit(0)
            else:
                url = "{}://{}".format(s, ul)
                connection_lock.acquire()
                print("[*] Testing: {}".format(url))
                t = Thread(target=connect, args=(url, session, True))
                child = t.start()


if __name__ == '__main__': main()
