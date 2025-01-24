import subprocess
import json
from datetime import datetime

class ExchangeRate:
    def __init__(self, from_cur, to_cur, rate):
        self.from_cur = from_cur
        self.to_cur = to_cur
        self.rate = rate

    def __repr__(self):
        return f"Exchange rate from {self.from_cur} to {self.to_cur} is {self.rate}"
    
class MonthlyPrice:
    def __init__(self, time, value, company, currency):
        self.time = time
        self.value = value
        self.company = company
        self.currency = currency
        self.year = int(time.split('-')[0])
        self.month = int(time.split('-')[1])
        self.day = int(time.split('-')[2])

    def __repr__(self):
        return f"Monthly price for {self.company} at {self.time} is {self.value} {self.currency}"
    
def call_api(url, header=None):
    command = ['curl', '-X', 'GET', url]
    command.extend(['-H', header])
    # print(f"Calling API with command: {command}")
    result = subprocess.run(command, capture_output=True, text=True)
    
    return result.stdout, result.stderr, result.returncode

def unpack_exr(json_data):
    exchange_rates = []
    data = json.loads(json_data)
    for item in data:
        exchange_rate = ExchangeRate(
            from_cur=item['from_currency'],
            to_cur=item['to_currency'],
            rate=item['rate']
        )
        exchange_rates.append(exchange_rate)
    return exchange_rates


def unpack_mon(json_data):
    monthly_data = []
    data = json.loads(json_data)
    for item in data:
        mon_data = MonthlyPrice(
            time=item['timestamp'],
            value=item['value'],
            company=item['company'],
            currency=item['currency']
        )
        monthly_data.append(mon_data)
    return monthly_data

def filter_monthly_data(monthly_data):
    monthly_data = list(filter(lambda x: x.time <= '2025-01-24', monthly_data))
    def is_valid_date(date_str):
        try:
            datetime.strptime(date_str, '%Y-%m-%d')
            return True
        except ValueError:
            return False

    monthly_data = list(filter(lambda x: is_valid_date(x.time), monthly_data))
    monthly_data = list(filter(lambda x: x.year <= 2025, monthly_data))
    monthly_data = list(filter(lambda x: x.value > 0, monthly_data))
    curs = ['EUR', 'USD', 'SEK']
    monthly_data = list(filter(lambda x: x.currency in curs, monthly_data))

    for data in monthly_data:
        if data.currency != 'SEK':
            for rate in exchange_rates:
                if rate.from_cur == data.currency:
                    data.value = data.value * rate.rate
                    data.currency = 'SEK'
                    break

    return monthly_data

def post_annual_data(url, data):
    command = ['curl', '-X', 'POST', url, '-H', 'accept: application/json', '-H', 'Content-Type: application/jon', '-d', json.dumps(data)]
    result = subprocess.run(command, capture_output=True, text=True)
    return result.stdout, result.stderr, result.returncode

# Print the most valuable company each month
def most_valuable_company(monthly_data):
    monthly_groups = {}
    for data in monthly_data:
        year_month = f"{data.year}-{data.month:02d}"
        if year_month not in monthly_groups:
            monthly_groups[year_month] = []
        monthly_groups[year_month].append(data)
    
    # Sort the keys of the dictionary
    sorted_keys = sorted(monthly_groups.keys())
    
    for year_month in sorted_keys:
        data_list = monthly_groups[year_month]
        most_valuable = max(data_list, key=lambda x: x.value)
        print(f"{year_month} - Most valuable company: {most_valuable.company} - Value: {most_valuable.value}")

# Total value of all entries
def total_value(monthly_data, company):
    total = 0
    for data in monthly_data:
        if data.company == company:
            total += data.value
    return total


if __name__ == "__main__":
    url = "https://technical-case-platform-engineer.onrender.com/"

    header = "accept: application/json"
    # Get exchange rates
    exrurl = url + "exchange-rates"
    exr, exrerr, exrret = call_api(exrurl, header)
    exchange_rates = unpack_exr(exr)

    # Get monthly data
    monurl = url + "monthly-data"
    mon, monerr, monret = call_api(monurl, header)
    monthly_data = unpack_mon(mon)

    # Filter monthly data
    monthly_data = filter_monthly_data(monthly_data)
    most_valuable_company(monthly_data)
    print(f'Total value of entris for Nexara: {total_value(monthly_data, "Nexara Technologies")}')

    # Group by company
    companies = {}
    for data in monthly_data:
        if data.company not in companies:
            companies[data.company] = []
        companies[data.company].append(data)

    # Group by year for each company
    for company, data_list in companies.items():
        years = {}
        for data in data_list:
            if data.year not in years:
                years[data.year] = []
            years[data.year].append(data)
        companies[company] = years

    # Avg price per company per year
    avg_prices = {}
    for company, years in companies.items():
        avg_prices[company] = {}
        for year, data_list in years.items():
            total = 0
            for data in data_list:
                total += data.value
            avg_prices[company][year] = total / len(data_list)

    # Print avg prices and post annual data
    post_url = url + "annual-data"
    for company, years in avg_prices.items():
        for year, avg_price in years.items():
            annual_data = {
                "year": year,
                "value": avg_price,
                "company": company,
                "currency": "SEK"
            }
            response, error, returncode = post_annual_data(post_url, annual_data)