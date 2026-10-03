"""Reference tariff data.

This is a curated, *indicative* subset of the Harmonized System used for demo
classification and landed-cost estimates. Rates are simplified MFN ad-valorem
duties and are NOT a substitute for the official tariff schedule of the
importing country. Swap this module for a real tariff API in production.
"""

from dataclasses import dataclass, field

# Import VAT / GST / sales-tax style rates applied at the border.
IMPORT_TAX = {
    "US": ("Sales tax (not collected at border)", 0.0),
    "CA": ("GST", 0.05),
    "GB": ("VAT", 0.20),
    "DE": ("VAT", 0.19),
    "FR": ("VAT", 0.20),
    "NL": ("VAT", 0.21),
    "IT": ("VAT", 0.22),
    "ES": ("VAT", 0.21),
    "IN": ("IGST", 0.18),
    "CN": ("VAT", 0.13),
    "JP": ("Consumption tax", 0.10),
    "AU": ("GST", 0.10),
    "AE": ("VAT", 0.05),
    "SG": ("GST", 0.09),
    "MX": ("IVA", 0.16),
    "BR": ("ICMS/IPI (approx.)", 0.18),
}

EU = {"DE", "FR", "NL", "IT", "ES", "BE", "AT", "PL", "IE", "PT", "SE", "DK", "FI"}

# Customs value basis: US/CA/AU value goods FOB, most others CIF.
FOB_VALUATION = {"US", "CA", "AU"}

# Free-trade agreements (simplified): pairs of (origin, destination) groups
# that qualify for 0% duty given proof of preferential origin.
FTA_GROUPS = {
    "USMCA": {"US", "CA", "MX"},
    "EU Single Market": EU,
    "UK-Japan CEPA": {"GB", "JP"},
    "India-UAE CEPA": {"IN", "AE"},
    "AU-SG SAFTA": {"AU", "SG"},
}

# US Merchandise Processing Fee (formal entry) & Harbor Maintenance Fee.
US_MPF_RATE, US_MPF_MIN, US_MPF_MAX = 0.003464, 32.71, 634.62
US_HMF_RATE = 0.00125


@dataclass(frozen=True)
class HSCode:
    code: str  # 6-digit HS subheading, formatted XXXX.XX
    description: str
    chapter: str
    keywords: tuple[str, ...]
    rates: dict[str, float] = field(default_factory=dict)  # country/"EU" -> ad valorem
    default_rate: float = 0.05
    restricted: str | None = None  # licensing / control note

    def rate_for(self, destination: str) -> float:
        if destination in self.rates:
            return self.rates[destination]
        if destination in EU and "EU" in self.rates:
            return self.rates["EU"]
        return self.default_rate


HS_CODES: list[HSCode] = [
    HSCode("0901.21", "Coffee, roasted, not decaffeinated", "09 Coffee, tea, maté and spices",
           ("coffee", "roasted", "beans", "espresso"), {"US": 0.0, "EU": 0.075, "GB": 0.06, "IN": 1.0, "CN": 0.15, "JP": 0.12}, 0.08),
    HSCode("0902.30", "Black tea (fermented), in packings ≤ 3 kg", "09 Coffee, tea, maté and spices",
           ("tea", "black tea", "chai", "assam", "darjeeling"), {"US": 0.0, "EU": 0.0, "GB": 0.0, "IN": 1.0, "CN": 0.15}, 0.05),
    HSCode("0904.11", "Pepper of the genus Piper, neither crushed nor ground", "09 Coffee, tea, maté and spices",
           ("pepper", "black pepper", "peppercorn", "spice"), {"US": 0.0, "EU": 0.0, "IN": 0.7}, 0.05),
    HSCode("1006.30", "Semi-milled or wholly milled rice", "10 Cereals",
           ("rice", "basmati", "jasmine rice", "milled rice"), {"US": 0.112, "EU": 0.175, "JP": 0.0, "CN": 0.65}, 0.10),
    HSCode("2204.21", "Wine of fresh grapes, in containers ≤ 2 L", "22 Beverages, spirits and vinegar",
           ("wine", "red wine", "white wine", "bottle", "champagne"), {"US": 0.063, "EU": 0.032, "GB": 0.04, "IN": 1.5, "CN": 0.14}, 0.10),
    HSCode("3004.90", "Medicaments, packaged for retail sale (other)", "30 Pharmaceutical products",
           ("medicine", "tablets", "pharmaceutical", "drug", "capsules", "paracetamol"), {"US": 0.0, "EU": 0.0, "IN": 0.10, "CN": 0.03}, 0.0,
           "Requires drug-regulator registration (e.g. FDA, EMA, CDSCO) at destination"),
    HSCode("3304.99", "Beauty, make-up and skin-care preparations (other)", "33 Essential oils, cosmetics",
           ("cosmetics", "cream", "skincare", "lotion", "moisturizer", "serum"), {"US": 0.0, "EU": 0.0, "IN": 0.20, "CN": 0.01}, 0.05),
    HSCode("3923.21", "Sacks and bags of polymers of ethylene", "39 Plastics and articles thereof",
           ("plastic bag", "polyethylene", "poly bag", "packaging bag"), {"US": 0.03, "EU": 0.065, "IN": 0.15}, 0.06),
    HSCode("4011.10", "New pneumatic rubber tyres for motor cars", "40 Rubber and articles thereof",
           ("tyre", "tire", "car tire", "rubber tyre"), {"US": 0.04, "EU": 0.045, "IN": 0.10, "CN": 0.06}, 0.08),
    HSCode("4202.21", "Handbags with outer surface of leather", "42 Leather articles, handbags",
           ("handbag", "leather bag", "purse", "tote"), {"US": 0.09, "EU": 0.03, "GB": 0.03, "IN": 0.20, "CN": 0.10}, 0.08),
    HSCode("4202.92", "Travel, sports and similar bags of textile/plastic", "42 Leather articles, handbags",
           ("backpack", "duffel", "travel bag", "luggage", "suitcase"), {"US": 0.176, "EU": 0.027, "IN": 0.20}, 0.10),
    HSCode("4418.73", "Assembled flooring panels of bamboo", "44 Wood and articles of wood",
           ("bamboo", "flooring", "parquet", "wood floor"), {"US": 0.032, "EU": 0.0}, 0.05),
    HSCode("4819.10", "Cartons, boxes of corrugated paper or paperboard", "48 Paper and paperboard",
           ("carton", "corrugated box", "cardboard box", "shipping box"), {"US": 0.0, "EU": 0.0, "IN": 0.10}, 0.05),
    HSCode("5208.12", "Woven cotton fabrics, unbleached, plain weave", "52 Cotton",
           ("cotton fabric", "woven cotton", "greige", "textile roll"), {"US": 0.074, "EU": 0.08, "IN": 0.10, "CN": 0.10}, 0.08),
    HSCode("6109.10", "T-shirts, singlets and vests, knitted, of cotton", "61 Apparel, knitted or crocheted",
           ("t-shirt", "tshirt", "tee", "cotton shirt", "vest", "singlet"), {"US": 0.165, "EU": 0.12, "GB": 0.12, "IN": 0.20, "CN": 0.06, "CA": 0.18}, 0.12),
    HSCode("6203.42", "Men's trousers and shorts, of cotton (not knitted)", "62 Apparel, not knitted",
           ("jeans", "trousers", "pants", "denim", "shorts", "chinos"), {"US": 0.166, "EU": 0.12, "GB": 0.12, "IN": 0.20}, 0.12),
    HSCode("6204.43", "Women's dresses of synthetic fibres", "62 Apparel, not knitted",
           ("dress", "women's dress", "gown", "polyester dress"), {"US": 0.16, "EU": 0.12, "IN": 0.20}, 0.12),
    HSCode("6403.99", "Footwear with leather uppers (other)", "64 Footwear",
           ("shoes", "leather shoes", "boots", "footwear", "loafers"), {"US": 0.085, "EU": 0.08, "IN": 0.35, "CN": 0.10}, 0.10),
    HSCode("6404.11", "Sports footwear with textile uppers", "64 Footwear",
           ("sneakers", "trainers", "running shoes", "sports shoes"), {"US": 0.20, "EU": 0.169, "IN": 0.35}, 0.12),
    HSCode("6911.10", "Tableware and kitchenware of porcelain or china", "69 Ceramic products",
           ("porcelain", "ceramic plate", "dinnerware", "mug", "tableware", "china"), {"US": 0.08, "EU": 0.12, "IN": 0.20}, 0.08),
    HSCode("7113.19", "Jewellery of precious metal other than silver", "71 Precious stones, metals, jewellery",
           ("gold jewelry", "jewellery", "necklace", "ring", "bracelet", "gold"), {"US": 0.055, "EU": 0.025, "IN": 0.20, "AE": 0.05}, 0.06),
    HSCode("7208.51", "Flat-rolled iron/non-alloy steel, hot-rolled, > 10 mm", "72 Iron and steel",
           ("steel plate", "hot rolled", "steel sheet", "iron plate"), {"US": 0.25, "EU": 0.0, "IN": 0.075}, 0.05,
           "Subject to safeguard / Section 232 measures in several markets"),
    HSCode("7318.15", "Threaded screws and bolts of iron or steel", "73 Articles of iron or steel",
           ("bolt", "screw", "fastener", "nut and bolt", "hex bolt"), {"US": 0.085, "EU": 0.037, "IN": 0.10}, 0.06),
    HSCode("7323.93", "Table/kitchen articles of stainless steel", "73 Articles of iron or steel",
           ("stainless steel", "cookware", "pot", "pan", "kitchenware", "utensils"), {"US": 0.02, "EU": 0.032, "IN": 0.20}, 0.06),
    HSCode("8414.51", "Table, floor, wall or ceiling fans ≤ 125 W", "84 Machinery and mechanical appliances",
           ("fan", "ceiling fan", "table fan", "electric fan"), {"US": 0.047, "EU": 0.032, "IN": 0.20}, 0.06),
    HSCode("8471.30", "Portable computers ≤ 10 kg (laptops, tablets)", "84 Machinery and mechanical appliances",
           ("laptop", "notebook computer", "tablet", "macbook", "chromebook", "computer"), {"US": 0.0, "EU": 0.0, "IN": 0.0, "CN": 0.0}, 0.0),
    HSCode("8471.60", "Input or output units (keyboards, mice)", "84 Machinery and mechanical appliances",
           ("keyboard", "mouse", "scanner", "input device"), {"US": 0.0, "EU": 0.0}, 0.0),
    HSCode("8501.31", "DC motors and generators, output ≤ 750 W", "85 Electrical machinery",
           ("dc motor", "electric motor", "brushless motor"), {"US": 0.04, "EU": 0.027, "IN": 0.075}, 0.04),
    HSCode("8504.40", "Static converters (power supplies, chargers, inverters)", "85 Electrical machinery",
           ("charger", "power supply", "adapter", "inverter", "power bank"), {"US": 0.0, "EU": 0.0, "IN": 0.20}, 0.03),
    HSCode("8507.60", "Lithium-ion accumulators (batteries)", "85 Electrical machinery",
           ("lithium battery", "li-ion", "battery pack", "lithium-ion", "ev battery"), {"US": 0.034, "EU": 0.027, "IN": 0.20, "CN": 0.10}, 0.04,
           "Dangerous goods (UN3480/UN3481) — IATA/IMDG packaging & declaration required"),
    HSCode("8517.13", "Smartphones", "85 Electrical machinery",
           ("smartphone", "mobile phone", "cell phone", "iphone", "android phone"), {"US": 0.0, "EU": 0.0, "IN": 0.20, "CN": 0.0}, 0.0),
    HSCode("8517.62", "Machines for reception/transmission of data (routers, switches)", "85 Electrical machinery",
           ("router", "network switch", "modem", "wifi", "access point"), {"US": 0.0, "EU": 0.0, "IN": 0.20}, 0.0),
    HSCode("8528.72", "Television receivers, colour", "85 Electrical machinery",
           ("television", "tv", "smart tv", "led tv", "monitor"), {"US": 0.05, "EU": 0.14, "IN": 0.20}, 0.10),
    HSCode("8541.43", "Photovoltaic cells assembled in modules (solar panels)", "85 Electrical machinery",
           ("solar panel", "photovoltaic", "pv module", "solar module"), {"US": 0.0, "EU": 0.0, "IN": 0.40}, 0.0,
           "Check anti-dumping / countervailing duties by origin"),
    HSCode("8542.31", "Electronic integrated circuits: processors and controllers", "85 Electrical machinery",
           ("microchip", "processor", "integrated circuit", "semiconductor", "cpu", "gpu", "chip"), {"US": 0.0, "EU": 0.0, "CN": 0.0}, 0.0,
           "Advanced computing ICs may require an export licence (e.g. US EAR ECCN 3A090)"),
    HSCode("8703.80", "Motor cars with only electric motor for propulsion", "87 Vehicles",
           ("electric car", "ev", "electric vehicle", "tesla"), {"US": 0.025, "EU": 0.10, "IN": 0.70, "CN": 0.15}, 0.10),
    HSCode("8711.60", "Motorcycles and cycles with electric motor (e-bikes)", "87 Vehicles",
           ("e-bike", "electric bicycle", "electric scooter", "electric motorcycle"), {"US": 0.0, "EU": 0.06, "IN": 0.70}, 0.06),
    HSCode("8712.00", "Bicycles and other cycles, not motorised", "87 Vehicles",
           ("bicycle", "bike", "cycle", "mountain bike"), {"US": 0.055, "EU": 0.14, "IN": 0.35}, 0.10),
    HSCode("9018.90", "Medical, surgical instruments and appliances (other)", "90 Optical, medical instruments",
           ("medical device", "surgical instrument", "catheter", "medical equipment"), {"US": 0.0, "EU": 0.0, "IN": 0.075}, 0.0,
           "Medical-device registration required at destination"),
    HSCode("9102.11", "Wrist-watches, battery powered, mechanical display", "91 Clocks and watches",
           ("watch", "wristwatch", "quartz watch"), {"US": 0.06, "EU": 0.045, "IN": 0.20}, 0.06),
    HSCode("9403.60", "Wooden furniture (other)", "94 Furniture, bedding, lighting",
           ("wooden furniture", "table", "chair", "cabinet", "wardrobe", "furniture"), {"US": 0.0, "EU": 0.0, "IN": 0.25}, 0.05),
    HSCode("9405.42", "LED luminaires and lighting fittings", "94 Furniture, bedding, lighting",
           ("led light", "lamp", "light fixture", "luminaire", "led bulb"), {"US": 0.039, "EU": 0.047, "IN": 0.20}, 0.05),
    HSCode("9503.00", "Toys, scale models, puzzles", "95 Toys, games and sports equipment",
           ("toy", "puzzle", "doll", "lego", "model kit", "children"), {"US": 0.0, "EU": 0.047, "IN": 0.70, "CN": 0.05}, 0.05,
           "Toy safety certification (CPSIA / EN 71 / CE) required"),
    HSCode("9506.91", "Gym, fitness and athletic equipment", "95 Toys, games and sports equipment",
           ("dumbbell", "treadmill", "gym equipment", "fitness", "yoga mat", "exercise"), {"US": 0.046, "EU": 0.027, "IN": 0.20}, 0.05),
]

HS_INDEX = {h.code: h for h in HS_CODES}


def lookup(code: str) -> HSCode | None:
    code = code.strip()
    if code in HS_INDEX:
        return HS_INDEX[code]
    digits = "".join(c for c in code if c.isdigit())
    if len(digits) >= 6:
        return HS_INDEX.get(f"{digits[:4]}.{digits[4:6]}")
    return None
