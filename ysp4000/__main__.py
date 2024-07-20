"""Entry point"""

import asyncio

from ysp4000.ysp import Ysp4000


def main():
    """Debug messages loop"""
    ioloop = asyncio.get_event_loop()
    ysp = Ysp4000(verbose=True)

    coro = ysp.get_async_coro(ioloop)

    ioloop.run_until_complete(coro)
    ioloop.run_forever()
    ioloop.close()


if __name__ == '__main__':
    main()
