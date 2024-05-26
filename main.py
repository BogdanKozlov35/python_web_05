import sys
from datetime import datetime, timedelta
import asyncio
import platform
import aiohttp


class HttpError(Exception):
    pass


async def request(url: str):
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    return result
                else:
                    raise HttpError(f"Error status: {resp.status} for {url}")
        except (aiohttp.ClientConnectorError, aiohttp.InvalidURL) as err:
            raise HttpError(f'Connection error: {url}', str(err))


async def main(index_days, currencies):
    # d = datetime.now() - timedelta(day=2) -> d.strftime("%d.%m.%Y")
    try:
        num_days = int(index_days)
        if num_days <= 0:
            raise ValueError("Number of days must be a positive integer")
        if num_days >= 10:
            raise ValueError("Number of days must be more than 0 and less than 10")
    except ValueError as ve:
        return f"Error: {ve}"

    d = datetime.now() - timedelta(days=int(index_days))
    shift = d.strftime("%d.%m.%Y")
    try:
        lines = []
        for i in range(num_days):
            d = datetime.now() - timedelta(days=i)
            shift = d.strftime("%d.%m.%Y")
            response = await request(f'https://api.privatbank.ua/p24api/exchange_rates?date={shift}')
            exchange_rates = response.get('exchangeRate', [])
            for rate in exchange_rates:
                date = shift
                baseCurrency = rate.get('baseCurrency', '')
                currency = rate.get('currency', '')
                saleRateNB = rate.get('saleRateNB', '')
                purchaseRateNB = rate.get('purchaseRateNB', '')
                if currency in currencies:
                    lines.append(
                        f"| {date:<10} | {baseCurrency:^13} | {currency:^10} | {saleRateNB:>10} | {purchaseRateNB:>15} | ")
        header = "| {:<10} | {:^10}  | {:^10} | {:>10} | {:>15} |".format("Date", "BaseCurrency", "Currency", "Sale",
                                                                          "Buy")
        separator = "-" * len(header)
        return "\n".join([separator, header, separator] + lines + [separator])
    except HttpError as err:
        return f"Error: {err}"


if __name__ == '__main__':
    if platform.system() == 'Windows':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    message = """ 
    Please try: py ./main.py <number_of_days> (from 1 to 10 days)
    or          py ./main.py <number_of_days> <currency> <currency> <currency> ...
    you can choose currency or bot will use USD and EUR as default
    CURENCIES:
    AUD  AZN  BYN  CAD  CHF CNY  CZK  DKK EUR GBP  GEL  HUF ILS  
    JPY KZT  MDL  NOK  PLN SEK   SGD  TMT  TRY  UAH  USD  UZS XAU 
            """

    if len(sys.argv) > 1:
        try:
            days = int(sys.argv[1])
            currencies = []
            for currency in sys.argv[2:]:
                currencies.append(currency.upper())
            if not currencies:
                currencies = ['USD', 'EUR']
            r = asyncio.run(main(days, currencies))
            print(r)
        except ValueError:
            print(message)
    else:
        print(message)