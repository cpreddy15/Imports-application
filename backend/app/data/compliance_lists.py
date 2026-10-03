"""Demo compliance reference lists.

Illustrative only — production screening must use live government lists
(OFAC SDN, EU Consolidated List, UK HMT, BIS Entity List, UN) via a licensed
screening provider.
"""

# Comprehensively sanctioned / embargoed jurisdictions (simplified).
EMBARGOED_COUNTRIES = {
    "CU": "Cuba",
    "IR": "Iran",
    "KP": "North Korea",
    "SY": "Syria",
}

# Jurisdictions with significant sectoral sanctions / heightened due diligence.
HIGH_RISK_COUNTRIES = {
    "RU": "Russia — sectoral sanctions, broad export controls",
    "BY": "Belarus — sectoral sanctions",
    "VE": "Venezuela — targeted sanctions",
    "MM": "Myanmar — targeted sanctions",
    "AF": "Afghanistan — targeted sanctions",
}

# Fictitious sample denied parties for demo screening.
DENIED_PARTIES = [
    {"name": "Global Dual-Use Trading LLC", "list": "Demo Entity List", "country": "AE"},
    {"name": "Northern Star Shipping Co", "list": "Demo SDN List", "country": "KP"},
    {"name": "Apex Precision Components", "list": "Demo Entity List", "country": "CN"},
    {"name": "Caspian Petro Logistics", "list": "Demo SDN List", "country": "IR"},
    {"name": "Volga Aero Systems", "list": "Demo Sectoral List", "country": "RU"},
]

# HS chapters/headings that typically need permits or are controlled.
CONTROLLED_PREFIXES = {
    "93": "Arms and ammunition — export licence required",
    "2844": "Radioactive elements — nuclear controls",
    "3601": "Explosives — dangerous goods & licensing",
    "8526": "Radar/radio navigation — possible dual-use control",
    "8542.31": "Advanced ICs — possible export licence (dual-use)",
    "8507.60": "Lithium batteries — dangerous goods",
    "3004": "Pharmaceuticals — regulator approval",
    "0106": "Live animals — CITES / veterinary certificate",
}
