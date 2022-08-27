import requests, json, re, time, csv
from bs4 import BeautifulSoup

class smallcase:
    def __init__(self):
        self.cases = []
        headers = ['Title', 'URL', 'Managed By', 'Small Description', 'CAGR time period', 'CAGR rate', 'Volatility',
                   'Overview', 'Minimum investment amount', 'Launch Date', 'Past performance: Small Case',
                   'Past performance: Equity',
                   'Past performance: FD', 'Past performance: Inflation', 'CAGR: Small Case', 'CAGR: Equity',
                   'CAGR: FD', 'CAGR: Inflation', 'Number of Smallcases managed by Manager', 'About manager'
                   ]
        self.openFile = open('output.csv', 'a', newline="")
        self.output = csv.DictWriter(self.openFile, fieldnames=headers)
        # self.output.writeheader()

    def getSCID(self, count, readLink):
        # initially count is 1 and readLink is False
        # if readLink is True then script will directly read scid from links.txt else it'll first write scids in text file.
        if not readLink:

            # writing all the small-cases' scid in one file and reading data from that file so,
            # whenever any error occurs then there's no need to start from start and we can start from the point where, we stopped.

            discover = BeautifulSoup(requests.get('https://www.smallcase.com/discover/all?count=290').content, 'lxml')
            with open('links.txt', 'w') as file:
                file.write(('\n').join([re.search(r"[^-?][A-Z]+_\d+", a['href'][-12:])[0] for a in discover.find_all('a', {'class': 'AllSmallcases__smallcasecard-link__2A7p_'})]) )

        with open('links.txt', 'r') as file:
            for a in file.readlines()[count:]:
                scid = a.replace('\n', '')
                # printing scid & count together to solve errors quickly
                # scid will be printed first to get an idea about where to search if any errors occur
                print(scid, end='\t')
                heads = {
                    'URL': f"https://www.smallcase.com/smallcase/{a}"
                }
                heads.update(self.getCaseData(scid))
                self.output.writerow(heads)
                print(count)
                # sleeping for 10 secs to avoid from getting banned from the servers
                time.sleep(10)
                count += 1
        return count

    def getCaseData(self, scid):

        # this dictionary will store all of the remaining values
        heads = {}

        # getting page data through api
        api = requests.get(f'https://api.smallcase.com/smallcases/smallcase?scid={scid}')
        inside_page = json.loads(api.content)

        # the following details are avaiable using the api
        heads['Title'] = inside_page['data']['info']['name']
        heads['Managed By'] = inside_page['data']['info']['publisherName']
        heads['Small Description'] = inside_page['data']['info']['shortDescription']
        heads['Overview'] = re.sub(r'</?[A-Za-z]*>', '', inside_page['data']['rationale'])
        heads['Launch Date'] = ('/').join(inside_page['data']['info']['created'][:10].split('-')[::-1])
        heads['Volatility'] = inside_page['data']['stats']['ratios']['riskLabel'][:-10]
        heads['CAGR time period'] = inside_page['data']['stats']['ratios']['cagrDuration']
        heads['CAGR rate'] = round(inside_page['data']['stats']['ratios']['cagr'] * 100, 2)
        heads['Minimum investment amount'] = inside_page['data']['stats']['minInvestAmount']

        heads.update(self.getCreatorDetails(inside_page['data']['info']['creator']))
        heads.update(self.getCAGR(scid))
        return heads

    def getCreatorDetails(self, creator):
        # fetching creator's details from other api
        creatorDetails = json.loads(requests.get(f'https://api.smallcase.com/smallcases/publisher?creator={creator}').content)

        if not creatorDetails['data']['publishers']:
            # handling case if publisher details are not found.
            return {key: 'Not Available' for key in ['Number of Smallcases managed by Manager', 'About manager']}

        about = creatorDetails['data']['publishers'][0]['meta']['microSiteContent']['publisherIntro']['description']
        return {'About manager': re.sub(r'</?[A-Za-z]*>', '', about), 'Number of Smallcases managed by Manager': creatorDetails['data']['publishers'][0]['smallcaseCount']}

    def getCAGR(self, scid):
        # fetching CAGR & other related details
        cagr = {}
        performance = json.loads(requests.get(
            f'https://api.smallcase.com/smallcases/historical?scid={scid}&benchmarkId=NGFD&benchmarkType=COMPARE').content)

        try:
            smallcase = performance['data']['smallcase']
            nifty = performance['data']['nifty']
            gold = performance['data']['gold']
            fd = performance['data']['fd']
            cpi = performance['data']['cpi']

            cagr['CAGR: Small Case'] = str(round(smallcase['cagr'] * 100, 2)) + '%'
            cagr['CAGR: Equity'] = str(round(nifty['cagr'] * 100, 2)) + '%'
            cagr['CAGR: FD'] = str(round(fd['cagr'] * 100, 2)) + '%'
            cagr['CAGR: Inflation'] = str(round(cpi['cagr'] * 100, 2)) + '%'

            cagr['Past performance: Small Case'] = 100 + round(smallcase['return'] * 100, 2)
            cagr['Past performance: Equity'] = 100 + round(nifty['return'] * 100, 2)
            cagr['Past performance: FD'] = 100 + round(fd['return'] * 100, 2)
            cagr['Past performance: Inflation'] = 100 + round(cpi['return'] * 100, 2)

        except Exception as e:
            # handling situation when cagr related details are not found
            if not performance['data']:
                cagr_keys = [
                    'Past performance: Small Case','Past performance: Equity', 'Past performance: FD',
                    'Past performance: Inflation', 'CAGR: Small Case', 'CAGR: Equity','CAGR: FD', 'CAGR: Inflation'
                ]
                return {key: 'NOT Available' for key in cagr_keys}
            print(e)

        return cagr

egg = smallcase()
# writing column heads
egg.output.writeheader()
print(f"Successfully writed {egg.getSCID(count=1, readLink=False)} rows.")
egg.openFile.close()
