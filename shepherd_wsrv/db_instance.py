from contextlib import asynccontextmanager

from motor.motor_asyncio import AsyncIOMotorClient

from beanie import init_beanie
from fastapi import FastAPI
from typing_extensions import deprecated

from .data_models.product import Product, Category
from .data_models.user import User


@deprecated("use context-manager instead")
async def db_init():
    """Call this from within your event loop to get beanie setup."""
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    # Note: if ".shp" does not exist, it will be created
    await init_beanie(database=client.shp, document_models=[Product])


@asynccontextmanager
async def db_context(app: FastAPI):
    """Initialize application services."""
    # Note: if ".shp" does not exist, it will be created
    app.db = AsyncIOMotorClient("mongodb://localhost:27017").shp
    await init_beanie(app.db, document_models=[Product, User])
    print("DB-Startup complete")
    yield
    print("DB-Shutdown complete")


async def db_insert_test():
    await db_init()

    chocolate = Category(name="Chocolate", description="A preparation of roasted and ground cacao seeds.")
    tonybar = Product(name="Tony's", price=5.95, category=chocolate)
    marsbar = Product(name="Mars", price=1, category=chocolate)

    await tonybar.insert()
    await Product.insert_one(marsbar)

    result = await Product.find(Product.price < 2).to_list()
    # _ = Product.find(In(Product.category.name, ["Chocolate", "Fruits"])).to_list()
    # _ = Product.find({"price": 1000}).to_list()
    # more complex searches possible [, nextCriteria] or chain .find(nextCriteria)
    # by ID
    # bar = await Product.get("608da169eb9e17281f0ab2ff")
    # TODO: filtering is awesome! https://beanie-odm.dev/tutorial/finding-documents/
    print(result)

    #await Product.find(Product.name == "Mars").set(Product.price >= 1)
    #await Product.find(Product.name == "Tony's").delete()
    #await Product.find(Product.name == "Tony's").upsert() -> when nothing found insert new one



# TODO: dump to file, restore from it - can beanie or motor do it?
