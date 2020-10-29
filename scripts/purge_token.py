from counter import db
from time import sleep
import logging

logger = logging.getLogger(__name__)

use_db = True


async def main():
    while True:
        logger.info('Purge old tokens')
        await db.purge_tokens()
        sleep(60)
