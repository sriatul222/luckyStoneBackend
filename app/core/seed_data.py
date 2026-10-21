"""Sample data inserted the first time the server starts (only into empty tables).

Metal rates here are SAMPLE values - update them every day from the admin API
PUT /api/v1/admin/metal-rates.
"""

# (metal, purity, rate per gram in INR)
METAL_RATES = [
    ("gold", "24K", 12850.00),
    ("gold", "22K", 11780.00),
    ("gold", "18K", 9640.00),
    ("gold", "14K", 7500.00),
    ("silver", "999", 165.00),
    ("silver", "925", 152.00),
    ("platinum", "950", 4850.00),
]

# (name, slug, display order)
CATEGORIES = [
    ("Rings", "rings", 1),
    ("Earrings", "earrings", 2),
    ("Necklaces", "necklaces", 3),
    ("Pendants", "pendants", 4),
    ("Bangles", "bangles", 5),
    ("Bracelets", "bracelets", 6),
    ("Mangalsutra", "mangalsutra", 7),
    ("Chains", "chains", 8),
    ("Nose Pins", "nose-pins", 9),
    ("Gold Coins", "gold-coins", 10),
]

# (name, slug, description, display order)
COLLECTIONS = [
    ("Bridal", "bridal", "Heirloom gold and diamond sets for your big day", 1),
    ("Daily Wear", "daily-wear", "Light-weight pieces you can wear every day", 2),
    ("Festive", "festive", "Traditional designs for festivals and celebrations", 3),
    ("Office Wear", "office-wear", "Minimal, elegant jewellery for work", 4),
]

# (title, subtitle, redirect type, redirect value, display order)
BANNERS = [
    ("Bridal Collection", "Up to 25% off on making charges", "collection", "bridal", 1),
    ("Diamonds for Every Day", "Solitaires, studs & pendants", "category", "rings", 2),
    ("Festive Gold", "Temple jewellery & kadas", "collection", "festive", 3),
]

# (name, address, city, state, pincode, phone, opening hours)
STORES = [
    ("Lucky Stone - MG Road", "Sample address, MG Road", "Kochi", "Kerala", "682016", "", "10:00 AM - 9:00 PM"),
    ("Lucky Stone - Indiranagar", "Sample address, 100 Feet Road", "Bengaluru", "Karnataka", "560038", "", "10:00 AM - 9:00 PM"),
    ("Lucky Stone - Andheri", "Sample address, Andheri West", "Mumbai", "Maharashtra", "400058", "", "10:30 AM - 9:30 PM"),
]


def _product(**values):
    defaults = {
        "description": "",
        "collection": None,
        "making_discount_percent": 0,
        "stone_type": "",
        "stone_weight_carat": 0,
        "stone_quality": "",
        "stone_price": 0,
        "gender": "women",
        "occasion": "",
        "sizes": [],
        "stock": 10,
        "is_featured": False,
    }
    defaults.update(values)
    return defaults


RING_SIZES = ["8", "10", "12", "14", "16", "18"]

PRODUCTS = [
    _product(
        name="Aarna Diamond Solitaire Ring", slug="aarna-diamond-solitaire-ring", sku="LS-RG-001",
        description="A classic round solitaire set in 18K yellow gold.",
        category="rings", collection="bridal", metal="gold", purity="18K",
        gross_weight=3.20, net_weight=2.90, making_charge_percent=18, making_discount_percent=10,
        stone_type="Diamond", stone_weight_carat=0.30, stone_quality="GH-VS", stone_price=38000,
        occasion="engagement", sizes=RING_SIZES, stock=6, is_featured=True,
    ),
    _product(
        name="Classic Gold Band for Men", slug="classic-gold-band-men", sku="LS-RG-002",
        description="Comfort-fit 22K gold band with a brushed finish.",
        category="rings", collection="daily-wear", metal="gold", purity="22K",
        gross_weight=6.50, net_weight=6.50, making_charge_percent=12,
        gender="men", occasion="daily", sizes=["16", "18", "20", "22", "24"], stock=8,
    ),
    _product(
        name="Platinum Couple Bands", slug="platinum-couple-bands", sku="LS-RG-003",
        description="Matching platinum 950 bands for him and her.",
        category="rings", collection="bridal", metal="platinum", purity="950",
        gross_weight=7.00, net_weight=7.00, making_charge_percent=20,
        gender="unisex", occasion="engagement", sizes=RING_SIZES, stock=4,
    ),
    _product(
        name="Meera Jhumka Earrings", slug="meera-jhumka-earrings", sku="LS-ER-001",
        description="Traditional 22K gold jhumkas with filigree work.",
        category="earrings", collection="festive", metal="gold", purity="22K",
        gross_weight=8.40, net_weight=8.40, making_charge_percent=16, making_discount_percent=20,
        occasion="festive", stock=7, is_featured=True,
    ),
    _product(
        name="Petal Diamond Stud Earrings", slug="petal-diamond-stud-earrings", sku="LS-ER-002",
        description="Five-petal diamond studs in 18K white gold.",
        category="earrings", collection="office-wear", metal="gold", purity="18K",
        gross_weight=2.30, net_weight=2.10, making_charge_percent=15,
        stone_type="Diamond", stone_weight_carat=0.20, stone_quality="EF-VVS", stone_price=26000,
        occasion="daily", stock=12, is_featured=True,
    ),
    _product(
        name="Oxidised Silver Jhumka", slug="oxidised-silver-jhumka", sku="LS-ER-003",
        description="Handcrafted 925 sterling silver jhumkas with an oxidised finish.",
        category="earrings", collection="festive", metal="silver", purity="925",
        gross_weight=12.00, net_weight=12.00, making_charge_percent=25,
        occasion="festive", stock=20,
    ),
    _product(
        name="Lakshmi Temple Necklace", slug="lakshmi-temple-necklace", sku="LS-NK-001",
        description="Temple-style 22K gold necklace with Goddess Lakshmi motifs.",
        category="necklaces", collection="bridal", metal="gold", purity="22K",
        gross_weight=42.50, net_weight=42.50, making_charge_percent=14, making_discount_percent=25,
        occasion="wedding", stock=3, is_featured=True,
    ),
    _product(
        name="Nakshatra Diamond Necklace", slug="nakshatra-diamond-necklace", sku="LS-NK-002",
        description="Star-cluster diamond necklace in 18K gold.",
        category="necklaces", collection="bridal", metal="gold", purity="18K",
        gross_weight=19.00, net_weight=18.20, making_charge_percent=18,
        stone_type="Diamond", stone_weight_carat=1.10, stone_quality="GH-SI", stone_price=98000,
        occasion="wedding", stock=2,
    ),
    _product(
        name="Heart Solitaire Pendant", slug="heart-solitaire-pendant", sku="LS-PD-001",
        description="Heart-shaped diamond pendant, chain not included.",
        category="pendants", collection="daily-wear", metal="gold", purity="18K",
        gross_weight=1.90, net_weight=1.80, making_charge_percent=16,
        stone_type="Diamond", stone_weight_carat=0.15, stone_quality="GH-VS", stone_price=15000,
        occasion="daily", stock=15,
    ),
    _product(
        name="Om Gold Pendant", slug="om-gold-pendant", sku="LS-PD-002",
        description="Sacred Om symbol in 22K gold.",
        category="pendants", collection="daily-wear", metal="gold", purity="22K",
        gross_weight=3.00, net_weight=3.00, making_charge_percent=10,
        gender="unisex", occasion="daily", stock=18,
    ),
    _product(
        name="Kerala Kada Bangles (Pair)", slug="kerala-kada-bangles-pair", sku="LS-BG-001",
        description="Pair of traditional Kerala-style 22K gold kadas.",
        category="bangles", collection="festive", metal="gold", purity="22K",
        gross_weight=24.00, net_weight=24.00, making_charge_percent=11,
        occasion="festive", sizes=["2.4", "2.6", "2.8"], stock=5, is_featured=True,
    ),
    _product(
        name="Infinity Rose Gold Bracelet", slug="infinity-rose-gold-bracelet", sku="LS-BR-001",
        description="Infinity link bracelet in 18K rose gold.",
        category="bracelets", collection="office-wear", metal="gold", purity="18K",
        gross_weight=5.60, net_weight=5.60, making_charge_percent=15,
        occasion="daily", stock=9,
    ),
    _product(
        name="Traditional Mangalsutra", slug="traditional-mangalsutra", sku="LS-MS-001",
        description="22K gold mangalsutra with black beads, 18 inch.",
        category="mangalsutra", collection="bridal", metal="gold", purity="22K",
        gross_weight=12.50, net_weight=12.00, making_charge_percent=13,
        occasion="wedding", stock=6,
    ),
    _product(
        name="Rope Chain 20 inch", slug="rope-chain-20-inch", sku="LS-CH-001",
        description="Twisted rope chain in 22K gold, 20 inch.",
        category="chains", collection="daily-wear", metal="gold", purity="22K",
        gross_weight=10.00, net_weight=10.00, making_charge_percent=8,
        gender="unisex", occasion="daily", stock=10,
    ),
    _product(
        name="Sparkle Diamond Nose Pin", slug="sparkle-diamond-nose-pin", sku="LS-NP-001",
        description="Single diamond nose pin in 18K gold.",
        category="nose-pins", collection="daily-wear", metal="gold", purity="18K",
        gross_weight=0.40, net_weight=0.35, making_charge_percent=20,
        stone_type="Diamond", stone_weight_carat=0.05, stone_quality="GH-SI", stone_price=4500,
        occasion="daily", stock=25,
    ),
    _product(
        name="Lakshmi Gold Coin 10g", slug="lakshmi-gold-coin-10g", sku="LS-GC-001",
        description="24K (999.9) Lakshmi gold coin, 10 grams, BIS hallmarked.",
        category="gold-coins", metal="gold", purity="24K",
        gross_weight=10.00, net_weight=10.00, making_charge_percent=3,
        gender="unisex", occasion="investment", stock=30,
    ),
]
