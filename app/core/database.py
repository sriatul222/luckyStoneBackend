import threading

import psycopg
from psycopg import sql
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from app.core.config import settings
from app.core.seed_data import (
    BANNERS,
    CATEGORIES,
    COLLECTIONS,
    METAL_RATES,
    PRODUCTS,
    STORES,
)


# Give up instead of waiting forever when the database can't be reached
# (e.g. the cloud database while the VPN is off)
CONNECT_TIMEOUT_SECONDS = 10


def _connection_kwargs(dbname: str) -> dict:
    return {
        "host": settings.postgres_host,
        "port": settings.postgres_port,
        "dbname": dbname,
        "user": settings.postgres_user,
        "password": settings.postgres_password,
        # dict_row -> every fetched row is a dict like {"id": 1, "name": "Ring"}
        "row_factory": dict_row,
        "connect_timeout": CONNECT_TIMEOUT_SECONDS,
        # Notice dead connections (e.g. after a Wi-Fi / VPN change) while idle
        "keepalives": 1,
        "keepalives_idle": 30,
        "keepalives_interval": 10,
        "keepalives_count": 3,
    }


class Database:
    def __init__(self):
        # Opening a connection to the cloud database takes ~0.7 s, so requests
        # reuse open connections from this pool instead of connecting each time.
        self.pool = ConnectionPool(
            kwargs=_connection_kwargs(settings.postgres_db),
            min_size=2,
            max_size=10,
            # Wait for a free connection (or a new one) before failing
            timeout=CONNECT_TIMEOUT_SECONDS + 5,
            # Replace connections left unused for 5 minutes
            max_idle=5 * 60,
            name="luckystone",
            open=False,
        )
        self._pool_lock = threading.Lock()

    def get_connection(self):
        """`with database.get_connection() as connection:` borrows a pooled
        connection, commits on success (rolls back on error) and gives it back."""
        if self.pool.closed:
            self.open_pool()  # scripts like make_admin.py skip the app startup
        return self.pool.connection()

    def open_pool(self):
        with self._pool_lock:
            if self.pool.closed:
                self.pool.open(wait=True, timeout=CONNECT_TIMEOUT_SECONDS + 5)

    def close_pool(self):
        with self._pool_lock:
            if not self.pool.closed:
                self.pool.close()

    def _connect(self, dbname: str):
        """A one-off connection outside the pool (database creation)."""
        return psycopg.connect(**_connection_kwargs(dbname))

    def create_database_if_missing(self):
        try:
            self._connect(settings.postgres_db).close()
            return
        except psycopg.OperationalError as error:
            if "does not exist" not in str(error):
                raise

        # Connect to the maintenance database ("postgres", or "defaultdb" on
        # Aiven) to create ours
        with self._connect(settings.postgres_maintenance_db) as connection:
            connection.autocommit = True
            connection.execute(
                sql.SQL("CREATE DATABASE {}").format(sql.Identifier(settings.postgres_db))
            )

    def create_tables(self):
        with self.get_connection() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    email VARCHAR(255) NOT NULL UNIQUE,
                    mobile VARCHAR(20) NOT NULL UNIQUE,
                    password_hash VARCHAR(255) NOT NULL,
                    role VARCHAR(20) NOT NULL DEFAULT 'customer',
                    is_active BOOLEAN NOT NULL DEFAULT TRUE,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );

                -- Today's price of 1 gram for every metal + purity
                CREATE TABLE IF NOT EXISTS metal_rates (
                    id SERIAL PRIMARY KEY,
                    metal VARCHAR(20) NOT NULL,
                    purity VARCHAR(10) NOT NULL,
                    rate_per_gram NUMERIC(12, 2) NOT NULL CHECK (rate_per_gram >= 0),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    UNIQUE (metal, purity)
                );

                CREATE TABLE IF NOT EXISTS categories (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    slug VARCHAR(120) NOT NULL UNIQUE,
                    image_url TEXT NOT NULL DEFAULT '',
                    display_order INT NOT NULL DEFAULT 0,
                    is_active BOOLEAN NOT NULL DEFAULT TRUE
                );

                CREATE TABLE IF NOT EXISTS collections (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    slug VARCHAR(120) NOT NULL UNIQUE,
                    description TEXT NOT NULL DEFAULT '',
                    image_url TEXT NOT NULL DEFAULT '',
                    display_order INT NOT NULL DEFAULT 0,
                    is_active BOOLEAN NOT NULL DEFAULT TRUE
                );

                CREATE TABLE IF NOT EXISTS products (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(200) NOT NULL,
                    slug VARCHAR(220) NOT NULL UNIQUE,
                    sku VARCHAR(50) NOT NULL UNIQUE,
                    description TEXT NOT NULL DEFAULT '',
                    category_id INT NOT NULL REFERENCES categories(id),
                    collection_id INT REFERENCES collections(id) ON DELETE SET NULL,
                    metal VARCHAR(20) NOT NULL,
                    purity VARCHAR(10) NOT NULL,
                    gross_weight NUMERIC(10, 3) NOT NULL,
                    net_weight NUMERIC(10, 3) NOT NULL,
                    making_charge_percent NUMERIC(5, 2) NOT NULL DEFAULT 0,
                    making_discount_percent NUMERIC(5, 2) NOT NULL DEFAULT 0,
                    stone_type VARCHAR(50) NOT NULL DEFAULT '',
                    stone_weight_carat NUMERIC(8, 3) NOT NULL DEFAULT 0,
                    stone_quality VARCHAR(50) NOT NULL DEFAULT '',
                    stone_price NUMERIC(12, 2) NOT NULL DEFAULT 0,
                    gender VARCHAR(10) NOT NULL DEFAULT 'women',
                    occasion VARCHAR(50) NOT NULL DEFAULT '',
                    sizes TEXT[] NOT NULL DEFAULT '{}',
                    image_urls TEXT[] NOT NULL DEFAULT '{}',
                    stock INT NOT NULL DEFAULT 0 CHECK (stock >= 0),
                    is_featured BOOLEAN NOT NULL DEFAULT FALSE,
                    is_active BOOLEAN NOT NULL DEFAULT TRUE,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
                CREATE INDEX IF NOT EXISTS products_category_idx ON products (category_id);

                CREATE TABLE IF NOT EXISTS banners (
                    id SERIAL PRIMARY KEY,
                    title VARCHAR(150) NOT NULL,
                    subtitle VARCHAR(255) NOT NULL DEFAULT '',
                    image_url TEXT NOT NULL DEFAULT '',
                    redirect_type VARCHAR(20) NOT NULL DEFAULT 'none',
                    redirect_value VARCHAR(255) NOT NULL DEFAULT '',
                    display_order INT NOT NULL DEFAULT 0,
                    is_active BOOLEAN NOT NULL DEFAULT TRUE
                );

                CREATE TABLE IF NOT EXISTS stores (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(150) NOT NULL,
                    address TEXT NOT NULL,
                    city VARCHAR(100) NOT NULL,
                    state VARCHAR(100) NOT NULL,
                    pincode VARCHAR(10) NOT NULL,
                    phone VARCHAR(20) NOT NULL DEFAULT '',
                    latitude NUMERIC(9, 6),
                    longitude NUMERIC(9, 6),
                    opening_hours VARCHAR(100) NOT NULL DEFAULT '',
                    is_active BOOLEAN NOT NULL DEFAULT TRUE
                );

                CREATE TABLE IF NOT EXISTS wishlist_items (
                    user_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    product_id INT NOT NULL REFERENCES products(id) ON DELETE CASCADE,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    PRIMARY KEY (user_id, product_id)
                );

                CREATE TABLE IF NOT EXISTS cart_items (
                    id SERIAL PRIMARY KEY,
                    user_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    product_id INT NOT NULL REFERENCES products(id) ON DELETE CASCADE,
                    size VARCHAR(10) NOT NULL DEFAULT '',
                    quantity INT NOT NULL CHECK (quantity > 0),
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    UNIQUE (user_id, product_id, size)
                );

                CREATE TABLE IF NOT EXISTS addresses (
                    id SERIAL PRIMARY KEY,
                    user_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    full_name VARCHAR(100) NOT NULL,
                    mobile VARCHAR(20) NOT NULL,
                    line1 VARCHAR(255) NOT NULL,
                    line2 VARCHAR(255) NOT NULL DEFAULT '',
                    landmark VARCHAR(255) NOT NULL DEFAULT '',
                    city VARCHAR(100) NOT NULL,
                    state VARCHAR(100) NOT NULL,
                    pincode VARCHAR(10) NOT NULL,
                    address_type VARCHAR(20) NOT NULL DEFAULT 'home',
                    is_default BOOLEAN NOT NULL DEFAULT FALSE,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );

                CREATE TABLE IF NOT EXISTS orders (
                    id SERIAL PRIMARY KEY,
                    order_number VARCHAR(30) NOT NULL UNIQUE,
                    user_id INT NOT NULL REFERENCES users(id),
                    status VARCHAR(20) NOT NULL DEFAULT 'PLACED',
                    payment_method VARCHAR(20) NOT NULL,
                    payment_status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
                    shipping_address JSONB NOT NULL,
                    subtotal NUMERIC(14, 2) NOT NULL,
                    discount NUMERIC(14, 2) NOT NULL DEFAULT 0,
                    gst NUMERIC(14, 2) NOT NULL,
                    total NUMERIC(14, 2) NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );

                -- Price is copied into the order so later metal rate changes
                -- never change an old order
                CREATE TABLE IF NOT EXISTS order_items (
                    id SERIAL PRIMARY KEY,
                    order_id INT NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
                    product_id INT REFERENCES products(id) ON DELETE SET NULL,
                    product_name VARCHAR(200) NOT NULL,
                    sku VARCHAR(50) NOT NULL,
                    image_url TEXT NOT NULL DEFAULT '',
                    metal VARCHAR(20) NOT NULL,
                    purity VARCHAR(10) NOT NULL,
                    net_weight NUMERIC(10, 3) NOT NULL,
                    size VARCHAR(10) NOT NULL DEFAULT '',
                    quantity INT NOT NULL,
                    unit_price NUMERIC(14, 2) NOT NULL,
                    line_total NUMERIC(14, 2) NOT NULL,
                    price_breakup JSONB NOT NULL
                );

                CREATE TABLE IF NOT EXISTS reviews (
                    id SERIAL PRIMARY KEY,
                    product_id INT NOT NULL REFERENCES products(id) ON DELETE CASCADE,
                    user_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    rating SMALLINT NOT NULL CHECK (rating BETWEEN 1 AND 5),
                    comment TEXT NOT NULL DEFAULT '',
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    UNIQUE (product_id, user_id)
                );
                """
            )
            self._create_price_view(connection)

    def _create_price_view(self, connection):
        """Jewellery price formula, kept in ONE place:

        metal value     = net weight (g) x today's rate of that metal/purity
        making charges  = metal value x making %
        making discount = making charges x discount %  ("20% off on making")
        subtotal        = metal value + making - discount + stone price
        gst             = subtotal x GST %
        total           = subtotal + gst
        """
        gst = float(settings.gst_percent)
        connection.execute(
            sql.SQL(
                """
                CREATE OR REPLACE VIEW product_prices AS
                WITH base AS (
                    SELECT
                        p.id AS product_id,
                        COALESCE(mr.rate_per_gram, 0) AS metal_rate,
                        ROUND(p.net_weight * COALESCE(mr.rate_per_gram, 0), 2) AS metal_value,
                        p.making_charge_percent,
                        p.making_discount_percent,
                        p.stone_price AS stone_value
                    FROM products p
                    LEFT JOIN metal_rates mr
                        ON mr.metal = p.metal AND mr.purity = p.purity
                ), making AS (
                    SELECT
                        base.*,
                        ROUND(metal_value * making_charge_percent / 100, 2) AS making_charges
                    FROM base
                ), discounted AS (
                    SELECT
                        making.*,
                        ROUND(making_charges * making_discount_percent / 100, 2) AS making_discount
                    FROM making
                ), totals AS (
                    SELECT
                        discounted.*,
                        metal_value + making_charges - making_discount + stone_value AS subtotal,
                        metal_value + making_charges + stone_value AS original_subtotal
                    FROM discounted
                )
                SELECT
                    product_id,
                    metal_rate,
                    metal_value,
                    making_charges,
                    making_discount,
                    stone_value,
                    subtotal,
                    {gst}::NUMERIC AS gst_percent,
                    ROUND(subtotal * {gst} / 100, 2) AS gst,
                    subtotal + ROUND(subtotal * {gst} / 100, 2) AS total,
                    original_subtotal + ROUND(original_subtotal * {gst} / 100, 2) AS original_total
                FROM totals
                """
            ).format(gst=sql.Literal(gst))
        )

    def seed_data(self):
        with self.get_connection() as connection:
            if connection.execute("SELECT COUNT(*) AS count FROM metal_rates").fetchone()["count"] == 0:
                connection.cursor().executemany(
                    "INSERT INTO metal_rates (metal, purity, rate_per_gram) VALUES (%s, %s, %s)",
                    METAL_RATES,
                )

            if connection.execute("SELECT COUNT(*) AS count FROM categories").fetchone()["count"] == 0:
                connection.cursor().executemany(
                    "INSERT INTO categories (name, slug, display_order) VALUES (%s, %s, %s)",
                    CATEGORIES,
                )

            if connection.execute("SELECT COUNT(*) AS count FROM collections").fetchone()["count"] == 0:
                connection.cursor().executemany(
                    """
                    INSERT INTO collections (name, slug, description, display_order)
                    VALUES (%s, %s, %s, %s)
                    """,
                    COLLECTIONS,
                )

            if connection.execute("SELECT COUNT(*) AS count FROM banners").fetchone()["count"] == 0:
                connection.cursor().executemany(
                    """
                    INSERT INTO banners (title, subtitle, redirect_type, redirect_value, display_order)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    BANNERS,
                )

            if connection.execute("SELECT COUNT(*) AS count FROM stores").fetchone()["count"] == 0:
                connection.cursor().executemany(
                    """
                    INSERT INTO stores (name, address, city, state, pincode, phone, opening_hours)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    STORES,
                )

            if connection.execute("SELECT COUNT(*) AS count FROM products").fetchone()["count"] == 0:
                for product in PRODUCTS:
                    connection.execute(
                        """
                        INSERT INTO products (
                            name, slug, sku, description, category_id, collection_id,
                            metal, purity, gross_weight, net_weight,
                            making_charge_percent, making_discount_percent,
                            stone_type, stone_weight_carat, stone_quality, stone_price,
                            gender, occasion, sizes, stock, is_featured
                        )
                        VALUES (
                            %(name)s, %(slug)s, %(sku)s, %(description)s,
                            (SELECT id FROM categories WHERE slug = %(category)s),
                            (SELECT id FROM collections WHERE slug = %(collection)s),
                            %(metal)s, %(purity)s, %(gross_weight)s, %(net_weight)s,
                            %(making_charge_percent)s, %(making_discount_percent)s,
                            %(stone_type)s, %(stone_weight_carat)s, %(stone_quality)s, %(stone_price)s,
                            %(gender)s, %(occasion)s, %(sizes)s, %(stock)s, %(is_featured)s
                        )
                        """,
                        product,
                    )


database = Database()


def initialize_database():
    try:
        database.create_database_if_missing()
    except psycopg.OperationalError as error:
        raise RuntimeError(
            f"Cannot connect to PostgreSQL at {settings.postgres_host}:"
            f"{settings.postgres_port} (database '{settings.postgres_db}'): {error}. "
            "Check your internet / VPN connection and the POSTGRES_* values in .env."
        ) from error
    database.open_pool()
    database.create_tables()
    database.seed_data()
