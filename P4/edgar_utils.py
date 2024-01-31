import re
import pandas as pd
from bisect import bisect
import netaddr

ips = pd.read_csv("ip2location.csv")
ip = ips['high'].tolist()

def lookup_region(region):
    region = int(netaddr.IPAddress(re.sub(r"[A-Za-z]", "0", region)))
    idx = bisect(ip, region)
    return ips.loc[idx, 'region']

class Filing:
    def __init__(self, html):
        self.dates = self.extract_date(html)
        self.sic = self.extract_sic(html)
        self.addresses = self.extract_addr(html)

    def extract_date(self, html):
        tmp = re.findall(r"((19|20)\d{2}-[0-1][0-9]-[0-3][0-9])", html)
        date = []
        for i in range(0,len(tmp)):
            date.append(tmp[i][0])
        return date
    
    def extract_sic(self,html):
        if(re.findall(r"SIC=(\d{4})", html)):
            return int(re.findall(r"SIC=(\d{4})", html)[0])
        return None
    
    def extract_addr(self,html):
        result = []
        for addr_html in re.findall(r'<div class="mailer">([\s\S]+?)</div>', html):
            lines = []
            for line in re.findall(r'<span class="mailerAddress">([\s\S]+?)</span>', addr_html):
                lines.append(line.strip())
            if(lines):
                result.append("\n".join(lines))
        return result
                
    def state(self):
        for address in self.addresses:
            result = re.findall(r'\s([A-Z]{2})\s\d{5}', address)
            if(result):
                return result[0]
        return None