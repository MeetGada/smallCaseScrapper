import requests, json, re, time, csv

class smallcase:
    def __init__(self):
        # defining column names for output.csv
        headers = [
            'Title', 'Managed By', 'Small Description', 'CAGR time period', 'CAGR rate', 'Volatility', 'Overview',
            'Minimum investment amount', 'Launch Date', 'Past performance: Small Case', 'Past performance: Equity',
            'Past performance: FD', 'Past performance: Inflation', 'CAGR: Small Case', 'CAGR: Equity', 'CAGR: FD',
            'CAGR: Inflation', 'Number of Smallcases managed by Manager', 'About manager'
        ]
        # opening csv file for writing data in 'w' mode
        self.openFile = open('output.csv', 'w', newline="")

        self.output = csv.DictWriter(self.openFile, fieldnames=headers)
        # writing column names in output.csv
        self.output.writeheader()

    def getSCID(self, count):
        # initially count is 1
        discover = requests.get(
            f'https://api.smallcase.com/smallcases/discover?count=10&offset={count}&sortBy=popularity&sortOrder=-1&risk=&public=false&private=false&maxMinInvestAmount=&sids=&excludeScids=&scids=&recentlyLaunched=false&searchString=')
        js = json.loads(discover.content)
        for egg in js['data']:
            heads = {
                'Managed By': egg['info']['publisherName'],
                'Title': egg['info']['name']
            }
            heads.update(self.getCaseData(egg['scid']))

            self.output.writerow(heads)
            print(count, '\tsleeping for 10 seconds')
            # sleeping for 10 secs to avoid from getting banned from the servers
            time.sleep(10)
        return count + 10

    def getCaseData(self, scid):
        # this dictionary will store all of the remaining values
        heads = {}

        # getting page data through api
        api = requests.get(f'https://api.smallcase.com/smallcases/smallcase?scid={scid}')
        inside_page = json.loads(api.content)

        # the following details are avaiable using the api
        heads['Small Description'] = inside_page['data']['info']['shortDescription']

        # removing html tags from overview using regex
        heads['Overview'] = re.sub(r'</?[A-Za-z]*>', '', inside_page['data']['rationale'])

        # formatting date in DD/MM/YYYY format
        heads['Launch Date'] = ('/').join(inside_page['data']['info']['created'][:10].split('-')[::-1])
        heads['Volatility'] = inside_page['data']['stats']['ratios']['riskLabel'][:-10]
        heads['CAGR time period'] = inside_page['data']['stats']['ratios']['cagrDuration']
        heads['CAGR rate'] = round(inside_page['data']['stats']['ratios']['cagr'] * 100, 2)
        heads['Minimum investment amount'] = inside_page['data']['stats']['minInvestAmount']

        # fetching creator's details
        heads.update(self.getCreatorDetails(inside_page['data']['info']['creator']))

        # fetching CAGR and related details
        heads.update(self.getCAGR(scid))

        return heads

    def getCreatorDetails(self, creator):
        # fetching creator's details from other api
        creatorDetails = json.loads(requests.get(f'https://api.smallcase.com/smallcases/publisher?creator={creator}').content)

        # removing html tags from description using regex
        about = creatorDetails['data']['publishers'][0]['meta']['microSiteContent']['publisherIntro']['description']
        return {
            'About manager': re.sub(r'</?[A-Za-z]*>', '', about),
            'Number of Smallcases managed by Manager': creatorDetails['data']['publishers'][0]['smallcaseCount']
        }

    def getCAGR(self, scid):
        # fetching CAGR & other related details
        cagr = {}
        performance = json.loads(requests.get(
            f'https://api.smallcase.com/smallcases/historical?scid={scid}&benchmarkId=NGFD&benchmarkType=COMPARE').content)

        smallcase = performance['data']['smallcase']
        nifty = performance['data']['nifty']
        gold = performance['data']['gold']
        fd = performance['data']['fd']
        cpi = performance['data']['cpi']

        # converting float values to string and appending "%" in the end to format as e.g. 23.06%
        # here, round() is used to restrict values upto 2 digits after decimal point.
        cagr['CAGR: Small Case'] = str(round(smallcase['cagr'] * 100, 2)) + '%'
        cagr['CAGR: Equity'] = str(round(nifty['cagr'] * 100, 2)) + '%'
        cagr['CAGR: FD'] = str(round(fd['cagr'] * 100, 2)) + '%'
        cagr['CAGR: Inflation'] = str(round(cpi['cagr'] * 100, 2)) + '%'

        # addition of 100 to returns in percentage is performed to get the actual return value on 100 rupees.
        # here data is obtained as 15.783811522180713 so, we need to restrict it till 2 digits after decimal point,
        # so we'll use round().
        cagr['Past performance: Small Case'] = 100 + round(smallcase['return'] * 100, 2)
        cagr['Past performance: Equity'] = 100 + round(nifty['return'] * 100, 2)
        cagr['Past performance: FD'] = 100 + round(fd['return'] * 100, 2)
        cagr['Past performance: Inflation'] = 100 + round(cpi['return'] * 100, 2)

        return cagr

egg = smallcase()
count = 1

# calling getSCID() 5 times for writing all case details
for i in range(6):
    count = egg.getSCID(count)

# closing the csv file avoid data corruption
egg.openFile.close()