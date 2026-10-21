from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.admin.catalog import router as admin_catalog_router
from app.api.admin.orders_users import router as admin_orders_users_router
from app.api.admin.products import router as admin_products_router
from app.api.admin.uploads import router as admin_uploads_router
from app.api.auth import router as auth_router
from app.api.catalog import router as catalog_router
from app.api.products import router as products_router
from app.api.shop import address_router, cart_router, order_router, wishlist_router
from app.core.config import settings
from app.core.database import database, initialize_database
from app.core.exception_handlers import register_exception_handlers


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Creates the database, tables and sample data on first run, and opens
    # the connection pool
    initialize_database()
    yield
    database.close_pool()


app = FastAPI(
    title=settings.project_name,
    description=(
        "Backend for the Lucky Stone jewellery shopping app: gold, diamond, "
        "silver and platinum jewellery with live metal-rate pricing."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)
register_exception_handlers(app)

settings.media_dir.mkdir(parents=True, exist_ok=True)
app.mount(settings.media_url, StaticFiles(directory=settings.media_dir), name="media")


@app.get("/", tags=["Health"])
def health_check():
    return {
        "success": True,
        "message": f"{settings.project_name} is running",
        "data": {"docs_url": "/docs"},
    }


app.include_router(auth_router)
app.include_router(catalog_router)
app.include_router(products_router)
app.include_router(wishlist_router)
app.include_router(cart_router)
app.include_router(address_router)
app.include_router(order_router)

app.include_router(admin_catalog_router)
app.include_router(admin_products_router)
app.include_router(admin_orders_users_router)
app.include_router(admin_uploads_router)
