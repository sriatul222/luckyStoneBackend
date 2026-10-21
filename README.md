# Lucky Stone Backend

FastAPI + PostgreSQL backend for the **Lucky Stone** Flutter app (`AndroidStudioProjects/luckyStone`),
an online jewellery store in the style of Malabar Gold / BlueStone / CaratLane.

- Gold, diamond, silver and platinum jewellery
- **Live pricing**: product prices are calculated from today's metal rate, so updating the
  rate once re-prices every product
- Customer APIs: auth, home, products with filters, wishlist, cart, addresses, orders, reviews, store locator
- Admin APIs: metal rates, products, categories, collections, banners, stores, orders, users, image upload

Every response has the same shape, success or error:

```json
{ "success": true, "message": "Products fetched successfully", "data": { } }
{ "success": false, "message": "Only 2 left in stock", "data": null }
```

## Project structure

```text
.
├── app
│   ├── api                 # Routers (URLs)
│   │   ├── admin           # /api/v1/admin/... (admin token only)
│   │   ├── auth.py
│   │   ├── catalog.py      # home, metal rates, categories, collections, banners, stores
│   │   ├── products.py     # product list / details / reviews
│   │   └── shop.py         # wishlist, cart, addresses, orders
│   ├── core
│   │   ├── config.py       # settings from .env
│   │   ├── database.py     # tables, price view, auto-create database
│   │   ├── seed_data.py    # sample categories / products / metal rates
│   │   ├── security.py     # password hashing + JWT
│   │   ├── dependencies.py # get_current_user / require_admin
│   │   └── exception_handlers.py
│   ├── repositories        # SQL queries (psycopg)
│   ├── schemas             # Pydantic request / response models
│   ├── services            # Business rules (stock checks, order flow, ...)
│   └── main.py
├── media                   # Uploaded images (served at /media/...)
├── scripts/make_admin.py
├── tests
└── main.py
```

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env      # then fill in your PostgreSQL password + a JWT secret
python main.py
```

Open the API docs at http://127.0.0.1:8000/docs

You do **not** need to create the database or tables in pgAdmin. On first start the server creates the
`luckystone_db` database, all tables, and sample data: 10 categories, 4 collections, 16 products,
metal rates, banners and stores.

### Make yourself admin

1. Register from the app or from `/docs` → `POST /api/v1/auth/register`
2. Run `python scripts/make_admin.py your@email.com`
3. Log in again and use the new token for `/api/v1/admin/...` APIs
   (in `/docs` click **Authorize** and paste the token)

### Run tests

Tests use a separate `luckystone_test_db` database that is created and dropped automatically
(on the same server as `.env`). To create / drop it they connect to `POSTGRES_MAINTENANCE_DB`:
`postgres` on a normal PostgreSQL server, `defaultdb` on Aiven (Aiven has no `postgres` database).

```bash
pytest
```

## How the price is calculated

The formula lives in one place: the `product_prices` SQL view in `app/core/database.py`.

```text
metal value     = net weight (g) x today's rate for that metal + purity
making charges  = metal value x making %
making discount = making charges x discount %     ("20% off on making charges")
subtotal        = metal value + making charges - making discount + stone price
GST (3%)        = subtotal x 3%
total           = subtotal + GST
```

Product details return this as `price_breakup`. When an order is placed, the price is copied into the
order, so later rate changes never change old orders.

## API endpoints

Use the `Authorization: Bearer <access_token>` header on 🔒 APIs.
The token comes from register / login.

### Auth
| Method | Endpoint | Work |
| --- | --- | --- |
| POST | `/api/v1/auth/register` | Register with name, email, mobile, password → token |
| POST | `/api/v1/auth/login` | Login with `username` (email or mobile) + password → token |
| GET 🔒 | `/api/v1/auth/me` | My profile |
| PUT 🔒 | `/api/v1/auth/me` | Update name / email / mobile |
| POST 🔒 | `/api/v1/auth/change-password` | Change password |

### Catalog (no login needed)
| Method | Endpoint | Work |
| --- | --- | --- |
| GET | `/api/v1/home` | Metal rates, banners, categories, collections, featured, new arrivals |
| GET | `/api/v1/metal-rates` | Today's gold / silver / platinum rates |
| GET | `/api/v1/categories` | Rings, earrings, necklaces, ... |
| GET | `/api/v1/collections` | Bridal, daily wear, festive, office wear |
| GET | `/api/v1/banners` | Home carousel banners |
| GET | `/api/v1/stores?city=Kochi` | Store locator |
| GET | `/api/v1/products` | List with filters (below) |
| GET | `/api/v1/products/{id}` | Details + price breakup (`is_wishlisted` if token sent) |
| GET | `/api/v1/products/{id}/reviews` | Reviews |
| POST 🔒 | `/api/v1/products/{id}/reviews` | Add / edit my review (rating 1-5) |

Product filters: `q`, `category`, `collection`, `metal` (gold/silver/platinum), `purity` (22K, 18K, 925 …),
`gender`, `occasion`, `min_price`, `max_price`, `featured`, `in_stock`,
`sort` (newest / price_low_to_high / price_high_to_low / popular / rating), `page`, `page_size`.

### Shopping 🔒
| Method | Endpoint | Work |
| --- | --- | --- |
| GET | `/api/v1/wishlist` | My wishlist |
| POST | `/api/v1/wishlist` | Add `{ "product_id": 1 }` |
| DELETE | `/api/v1/wishlist/{product_id}` | Remove |
| GET | `/api/v1/cart` | Cart items + summary (subtotal, discount, GST, total) |
| POST | `/api/v1/cart/items` | Add `{ "product_id": 1, "quantity": 1, "size": "12" }` |
| PUT | `/api/v1/cart/items/{item_id}` | Change quantity |
| DELETE | `/api/v1/cart/items/{item_id}` | Remove item |
| DELETE | `/api/v1/cart` | Empty cart |
| GET / POST | `/api/v1/addresses` | List / add address |
| PUT / DELETE | `/api/v1/addresses/{id}` | Edit / delete address |
| POST | `/api/v1/orders` | Place order from cart `{ "address_id": 1, "payment_method": "COD" }` |
| GET | `/api/v1/orders` | My orders |
| GET | `/api/v1/orders/{id}` | Order details |
| POST | `/api/v1/orders/{id}/cancel` | Cancel (only PLACED / CONFIRMED) |

### Admin 🔒 (admin role)
| Method | Endpoint | Work |
| --- | --- | --- |
| PUT | `/api/v1/admin/metal-rates` | Update today's rates `{ "rates": [{ "metal": "gold", "purity": "22K", "rate_per_gram": 11800 }] }` |
| GET / POST | `/api/v1/admin/products` | All products (incl. hidden) / create |
| GET / PUT / DELETE | `/api/v1/admin/products/{id}` | Read / update / hide product |
| GET / POST / PUT / DELETE | `/api/v1/admin/categories`, `/collections`, `/banners`, `/stores` | Manage catalog |
| POST | `/api/v1/admin/uploads` | Upload image (form-data `file`, `folder`) → `/media/...` url |
| GET | `/api/v1/admin/orders?status=PLACED` | All orders |
| PUT | `/api/v1/admin/orders/{id}/status` | PLACED → CONFIRMED → SHIPPED → DELIVERED (or CANCELLED) |
| GET | `/api/v1/admin/users` | All users |
| PUT | `/api/v1/admin/users/{id}/role` / `status` | Make admin / block user |

## Deploy to Render (free)

`render.yaml` describes a free Render web service. The database stays on Aiven.

1. Push this folder to a **private** GitHub repo (`.env` is git-ignored, never push it).
2. Render dashboard → **New → Blueprint** → pick the repo → Render reads `render.yaml`.
3. Enter `POSTGRES_HOST`, `POSTGRES_USER` and `POSTGRES_PASSWORD` (the Aiven values from your
   `.env`) when asked. `JWT_SECRET_KEY` is generated by Render.
4. Deploy. The API is at `https://<service-name>.onrender.com/` (docs at `/docs`).

Notes:

- Render runs `uvicorn app.main:app --host 0.0.0.0 --port $PORT` (not `main.py`).
- Free services sleep after 15 minutes without traffic; the next request takes up to a minute.
- Uploaded images (`/media`) are lost on every deploy or restart of a free service.
- If Aiven's **Allowed IP addresses** is not `0.0.0.0/0`, add Render's outbound IPs
  (Render service → Connect → Outbound).
- Locally, `python main.py` still runs on port 8000 (set `PORT` in `.env` to change it).

## Connect from the Flutter app

The Flutter app reads its base URL from `lib/api/urls.dart`:

- Android emulator → `http://10.0.2.2:8000/` (automatic)
- iOS simulator → `http://127.0.0.1:8000/` (automatic)
- Real phone on the same Wi-Fi → `flutter run --dart-define-from-file=config/dev.json`
- Render (any network) → `flutter run --dart-define-from-file=config/prod.json`

## Not built yet

- Online payment gateway (Razorpay etc.). `ONLINE` orders are saved with `payment_status = PENDING`
- OTP login and SMS / email notifications
- Product images: seed products have no images. Upload them with `/api/v1/admin/uploads` and put the URLs
  in `image_urls`
