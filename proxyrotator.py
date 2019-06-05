#https://github.com/lakam99/ProxyRotator
## ##

import requests
import re
from bs4 import BeautifulSoup as bs
import numpy as np
from threading import Thread
import random
import socket
import time

class ProxyAgent:

    def __init__(self, IP, user_agent):
        self.IP, self.user_agent = IP, user_agent

    def reassign(self, IP, user_agent):
        self.IP, self.user_agent = IP, user_agent

    def get_credentials(self):
        return {"user-agent": self.user_agent}, {"http": "http://" + self.IP, "https": "https://" + self.IP}

class ProxyBuilder:

    def __init__(self):
        r = requests.get("https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list.txt")
        self.IPs = r.text.split("\n")
        self.IPs = self.IPs[4:-2]
        self._l = len(self.IPs)
        self.IPs = [re.compile("[a-zA-Z\s]*[-+!]*").sub("", _data) for _data in self.IPs]

        z = requests.get("https://developers.whatismybrowser.com/useragents/explore/software_name/chrome/1")
        page = bs(z.text, 'lxml')
        z = page.find_all("td", attrs={"class":"useragent"})
        self.user_agents = np.array([tag.text for tag in z])
        if len(self.user_agents) < len(self.IPs):
            z = requests.get("https://developers.whatismybrowser.com/useragents/explore/software_name/chrome/2")
            page = bs(z.text, 'lxml')
            z = page.find_all("td", attrs={"class": "useragent"})
            new_agents = [tag.text for tag in z]
            l = abs(len(self.user_agents) - len(self.IPs))
            self.user_agents = np.append(self.user_agents, new_agents[:l])

        self._i = 0

        self.spy = ProxyAgent(self.IPs[0], self.user_agents[0])

        random.shuffle(self.IPs)
        random.shuffle(self.user_agents)

        #print("When using a proxy, your spy's credentials are:\n" + str(self.spy.get_credentials()))

    def next_ip(self, loop=False):
        if not loop:
            if self._i < len(self.IPs):
                self.spy.reassign(self.IPs[self._i], self.user_agents[self._i % (len(self.user_agents))])
                self._i += 1
                #print("\nYour spy's new credentials are:\n" + str(self.spy.get_credentials()))
                print("Generated " + str(self._i) + ' IPs / ' + str(len(self.IPs)) + ' total  ----  ' + str(self._i) + ' UAs / ' + str(len(self.user_agents)) + ' total')
                return self.spy
            else:
                return False

        self.spy.reassign(self.IPs[self._i % len(self.IPs)], self.user_agents[self._i % len(self.user_agents)])
        self._i += 1
        return self.spy


class ProxyRotator(Thread):
    rotator = ProxyBuilder()
    testers = []
    working_spies = []

    def __init__(self, idt=0, spies=None, url='http://icanhazip.com', master=False, size=20, testing=False, req=False, parent=None):
        Thread.__init__(self)
        self.spies = spies
        self.url = url
        self.master = master
        self.idt = idt
        self.size = size
        self.testing = testing
        self.req = req
        if self.master:
            self.rotator = ProxyBuilder()
            self.testers = []
            self.working_spies = []
        else:
            self.parent = parent

    def run(self):
        if self.testing:
            if self.master:
                self.test_all()
                return
            else:
                self.test()

        elif self.req:
            return self.req(self.url)

    def req(self, url):
        if not self.req:
            th = ProxyRotator(url=url, req=True, Testing=True)
            th.start()
            th.join()

        spie = self.parent.rotator.next_ip(loop=True).get_credentials()
        agent, proxy = spie

        try:
            time.sleep(0.01)
            proxy_req = requests.get(url, headers=agent, proxies=proxy)
            resp = proxy_req
            if not self.testing:
                return resp
            else:
                print('#' + str(self.idt) + ' IP : ' + str(resp.text).strip() + ' ---> Proxy: ' + str(proxy['http']))
        except Exception as e:
            if not self.testing:
                return False
            else:
                print(str(e))
                print('### ---> Proxy not working: ' + str(proxy['http']))


    def test(self):
        for spie in self.spies:
            agent, proxy = spie

            try:
                time.sleep(0.1)
                proxy_req = requests.get(self.url, headers=agent, proxies=proxy)
                if proxy_req.status_code == '200':
                    resp = proxy_req.text
                    self.parent.working_spies.append(spie)
                    print('Tester-#' + str(self.idt) + ' -- IP : ' + str(resp).strip() + ' ---> Proxy: ' + str(proxy['http']) + '   [' + str(len(self.parent.working_spies)) + ' / ' + str(len(ProxyTester.rotator.IPs)) + '] working')
            except Exception as e:
                print(str(e))
                print('Tester-#' + str(self.idt) + '---> Proxy not working: ' + str(proxy['http']))
                continue 

    def test_all(self):
        spies = []
        counter = 0
        tcounter = 0
        testers = []

        while True:
            spie = self.rotator.next_ip()
            counter += 1
            if not spie: 
                if len(spies) > 0:
                    tester = ProxyRotator(idt=tcounter, spies=spies, url=self.url, testing=True, parent=self)
                    tester.start()  
                    self.testers.append(tester)
                break

            spie = spie.get_credentials()
            spies.append(spie)

            if counter == self.size:
                tester = ProxyRotator(idt=tcounter, spies=spies, url=self.url, testing=True, parent=self)
                tester.start()
                self.testers.append(tester)
                print('Thread ' + str(tcounter) + ' Started !')
                testers.append(tester)
                tcounter += 1
                spies = []
                counter = 0
            continue

        for th in testers:
            th.join()

        print('\n----------------\nTest done: [' +  str(len(self.working_spies)) + '/' + str(len(self.rotator.IPs)) + '] working' + '\n----------------\n')

    def get_working_spies(self):
        return self.working_spies

def main():
    url = 'http://icanhazip.com'
    size = 1

    master = ProxyRotator(idt='r00t', url=url, master=True, size=size, testing=True)
    
    master.start()
    
    #resp = master.req(url)

    #if (resp):
    #    print(resp)
    #else:
    #    print('Request failed')

    master.join()

if __name__ == '__main__':
  main()
