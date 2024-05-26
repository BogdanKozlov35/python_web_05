import aiohttp
import asyncio
import logging
import websockets
from websockets import WebSocketServerProtocol, WebSocketProtocolError

from my_logger import get_logger
import names

logging.basicConfig(level=logging.INFO)

logger = get_logger('my_logger')


async def get_exchange_today():
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get('https://api.privatbank.ua/p24api/pubinfo?json&exchange&coursid=5') as resp:
                if resp.status == 200:
                    r = await resp.json()
                    exc = next(filter(lambda el: el["ccy"] == "USD", r), None)
                    if exc:
                        return f"USD: buy: {exc['buy']}, sale: {exc['sale']}"
                    else:
                        logger.error("USD data not found")
                else:
                    logger.error(f"Failed to fetch today's exchange rates: {resp.status}")
        except aiohttp.ClientError as err:
            logger.error(f"HTTP error occurred: {str(err)}")
        return "Error: I dint know today's exchange rates."


async def get_exchange(date, currency):
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f'https://api.privatbank.ua/p24api/exchange_rates?date={date}') as resp:
                if resp.status == 200:
                    r = await resp.json()
                    exc = next(filter(lambda el: el["currency"] == currency, r['exchangeRate']), None)
                    if exc:
                        return f"Date: {date}, {currency}: buy: {exc['purchaseRate']}, sale: {exc['saleRate']}"
                    else:
                        logger.error(f"{currency} data not found for date {date}")
                else:
                    logger.error(f"Failed to fetch exchange rates for {date}: {resp.status}")
        except aiohttp.ClientError as err:
            logger.error(f"HTTP error occurred: {str(err)}")
        return f"I cant find rates for {currency} on {date}."


class Server:
    clients = set()

    async def register(self, ws: WebSocketServerProtocol):
        ws.name = names.get_full_name()
        self.clients.add(ws)
        logging.info(f'{ws.remote_address} connects')

    async def unregister(self, ws: WebSocketServerProtocol):
        self.clients.remove(ws)
        logging.info(f'{ws.remote_address} disconnects')

    async def send_to_clients(self, message: str):
        if self.clients:
            [await client.send(message) for client in self.clients]

    async def ws_handler(self, ws: WebSocketServerProtocol):
        await self.register(ws)
        try:
            await self.distrubute(ws)
        except WebSocketProtocolError as err:
            logging.error(err)
        finally:
            await self.unregister(ws)

    async def distrubute(self, ws: WebSocketServerProtocol):
        async for message in ws:

            if message.startswith('exchange'):
                parts = message.split()
                if len(parts) > 1:
                    date = parts[1]
                    print(date)
                    currency = parts[2].upper()
                    print(currency)
                    m = await get_exchange(date, currency)
                else:
                    m = "Invalid 'exchange' command format."
                await self.send_to_clients(m)

            elif message == 'today':
                m = await get_exchange_today()
                await self.send_to_clients(m)
            else:
                await self.send_to_clients(f"{ws.name}: {message}")


async def main():
    server = Server()
    async with websockets.serve(server.ws_handler, 'localhost', 8080):
        await asyncio.Future()  # run forever

if __name__ == '__main__':
    asyncio.run(main())
    logger.info("Server started")