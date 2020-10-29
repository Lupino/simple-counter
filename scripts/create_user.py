from counter import db

use_db = True


async def main(name, password):
    await db.create_user(name, password)
