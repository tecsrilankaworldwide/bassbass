"""
TopBass - Service Marketplace API
Find trusted handymen for housework across Sri Lanka
"""
import os
import io
import csv
import math
import uuid
import random
import string
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, HTTPException, Depends, File, UploadFile, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext
from emergentintegrations.payments.stripe.checkout import StripeCheckout, CheckoutSessionResponse, CheckoutStatusResponse, CheckoutSessionRequest
import jwt
import uvicorn

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="TopBass API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# DB Setup
MONGO_URL = os.environ.get("MONGO_URL")
DB_NAME = os.environ.get("DB_NAME", "bassbass_db")
SECRET_KEY = os.environ.get("SECRET_KEY", "bassbass-secret-2026")
STRIPE_API_KEY = os.environ.get("STRIPE_API_KEY")
PAYHERE_MERCHANT_ID = os.environ.get("PAYHERE_MERCHANT_ID", "")
PAYHERE_MERCHANT_SECRET = os.environ.get("PAYHERE_MERCHANT_SECRET", "")
TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN", "")
TWILIO_PHONE_NUMBER = os.environ.get("TWILIO_PHONE_NUMBER", "")
TOPBASS_FEE_PERCENT = float(os.environ.get("TOPBASS_FEE_PERCENT", "10"))
VAT_PERCENT = float(os.environ.get("VAT_PERCENT", "18.5"))
BANK_QR_CODE_URL = "https://customer-assets.emergentagent.com/job_805b6bad-8e70-4f10-8052-c226fb943db2/artifacts/94uaodwg_qrcode.jpg"
REFERRAL_CREDIT_PER_SIGNUP = 500  # LKR per successful referral

PARTNER_TIERS = [
    {"min": 25, "tier": "platinum", "label": "Platinum Partner"},
    {"min": 10, "tier": "gold", "label": "Gold Partner"},
    {"min": 5, "tier": "silver", "label": "Silver Partner"},
    {"min": 0, "tier": "bronze", "label": "Bronze"},
]

def get_partner_tier(referral_count):
    for t in PARTNER_TIERS:
        if referral_count >= t["min"]:
            return {"tier": t["tier"], "label": t["label"]}
    return {"tier": "bronze", "label": "Bronze"}

async def enrich_with_tier(handymen_list):
    """Add partner_tier to a list of handyman profiles."""
    user_ids = [h.get("user_id") for h in handymen_list if h.get("user_id")]
    if not user_ids:
        return
    users = await db.users.find({"id": {"$in": user_ids}}, {"_id": 0, "id": 1, "referral_count": 1}).to_list(len(user_ids))
    count_map = {u["id"]: u.get("referral_count", 0) for u in users}
    for h in handymen_list:
        rc = count_map.get(h.get("user_id"), 0)
        tier = get_partner_tier(rc)
        if tier["tier"] != "bronze":
            h["partner_tier"] = tier

def generate_referral_code(name):
    """Generate a short referral code like NIMAL-5K3."""
    prefix = name.split()[0].upper()[:5]
    suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=3))
    return f"{prefix}-{suffix}"

client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ============================================================================
# CONSTANTS
# ============================================================================

DISTRICTS = [
    "Colombo", "Gampaha", "Kalutara", "Kandy", "Matale", "Nuwara Eliya",
    "Galle", "Matara", "Hambantota", "Jaffna", "Kilinochchi", "Mannar",
    "Mullaitivu", "Vavuniya", "Trincomalee", "Batticaloa", "Ampara",
    "Kurunegala", "Puttalam", "Anuradhapura", "Polonnaruwa", "Badulla",
    "Monaragala", "Ratnapura", "Kegalle"
]

# District center coordinates (lat, lng) for proximity calculations
DISTRICT_COORDS = {
    "Colombo": (6.9271, 79.8612),
    "Gampaha": (7.0840, 80.0098),
    "Kalutara": (6.5854, 79.9607),
    "Kandy": (7.2906, 80.6337),
    "Matale": (7.4675, 80.6234),
    "Nuwara Eliya": (6.9497, 80.7891),
    "Galle": (6.0535, 80.2210),
    "Matara": (5.9549, 80.5550),
    "Hambantota": (6.1429, 81.1212),
    "Jaffna": (9.6615, 80.0255),
    "Kilinochchi": (9.3803, 80.3770),
    "Mannar": (8.9810, 79.9044),
    "Mullaitivu": (9.2671, 80.8142),
    "Vavuniya": (8.7514, 80.4971),
    "Trincomalee": (8.5874, 81.2152),
    "Batticaloa": (7.7310, 81.6747),
    "Ampara": (7.2916, 81.6747),
    "Kurunegala": (7.4863, 80.3647),
    "Puttalam": (8.0362, 79.8283),
    "Anuradhapura": (8.3114, 80.4037),
    "Polonnaruwa": (7.9403, 81.0188),
    "Badulla": (6.9934, 81.0550),
    "Monaragala": (6.8728, 81.3507),
    "Ratnapura": (6.6828, 80.3992),
    "Kegalle": (7.2513, 80.3464),
}

def haversine_km(lat1, lon1, lat2, lon2):
    """Calculate distance between two coordinates in km."""
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

def get_nearby_districts(district, max_km=80):
    """Get districts within max_km of the given district, sorted by distance."""
    if district not in DISTRICT_COORDS:
        return []
    lat1, lon1 = DISTRICT_COORDS[district]
    nearby = []
    for d, (lat2, lon2) in DISTRICT_COORDS.items():
        dist = haversine_km(lat1, lon1, lat2, lon2)
        if dist <= max_km:
            nearby.append({"district": d, "distance_km": round(dist, 1)})
    nearby.sort(key=lambda x: x["distance_km"])
    return nearby

SERVICE_CATEGORIES = [
    {"id": "plumber", "name_en": "Plumbers", "name_si": "ජල කාර්මික", "name_ta": "குழாய் தொழிலாளர்", "icon": "droplets", "image": "https://static.prod-images.emergentagent.com/jobs/3de36ae8-1b12-4467-87dd-98c4995672e0/images/63a43625d4a903f60c9eab2981d6f7183a0f5d55809cc9349b3c0dfcc926590c.png"},
    {"id": "electrician", "name_en": "Electricians", "name_si": "විදුලි කාර්මික", "name_ta": "மின் தொழிலாளர்", "icon": "zap", "image": "https://static.prod-images.emergentagent.com/jobs/3de36ae8-1b12-4467-87dd-98c4995672e0/images/6a39a9c3c9aff1ec63c746a2825e946ce80a111fc9908a174aa51a9ce3159f63.png"},
    {"id": "mason", "name_en": "Masons", "name_si": "ගඩොල් කාර්මික", "name_ta": "கொத்தனார்", "icon": "brick-wall", "image": "https://static.prod-images.emergentagent.com/jobs/3de36ae8-1b12-4467-87dd-98c4995672e0/images/138d7355497dfd9501c3d18ac0791f8dafb607ce66b3ab92b4d5e7d1dbebe41d.png"},
    {"id": "carpenter", "name_en": "Carpenters", "name_si": "වඩු කාර්මික", "name_ta": "தச்சர்", "icon": "hammer", "image": "https://static.prod-images.emergentagent.com/jobs/3de36ae8-1b12-4467-87dd-98c4995672e0/images/cc90e4f1c919455c334b2adae184769b8e4edd2eb57cb3a59c56c8c68d93b831.png"},
    {"id": "painter", "name_en": "Painters", "name_si": "තීන්ත කාර්මික", "name_ta": "வர்ணம் பூசுபவர்", "icon": "paintbrush", "image": "https://static.prod-images.emergentagent.com/jobs/3de36ae8-1b12-4467-87dd-98c4995672e0/images/7c903de658cfa67a4de18cb5313a3df86b85a17b18bf55d4f04cdbc057ae248b.png"},
    {"id": "tiler", "name_en": "Tilers", "name_si": "ටයිල් කාර්මික", "name_ta": "ஓடு பதிப்பவர்", "icon": "grid-3x3", "image": "https://static.prod-images.emergentagent.com/jobs/3de36ae8-1b12-4467-87dd-98c4995672e0/images/25e581c50dd07303f0ba832eae010fd91d210b4536574dca170bf0eb8c479aa2.png"},
    {"id": "ac_repair", "name_en": "A/C Repair", "name_si": "වායු සමනය", "name_ta": "ஏசி பழுது", "icon": "wind", "image": "https://static.prod-images.emergentagent.com/jobs/3de36ae8-1b12-4467-87dd-98c4995672e0/images/adfbf08fc5aaeb2250983b2f501fbb9eeaaa3f52c51e733f2eeb2268280166ba.png"},
    {"id": "cleaner", "name_en": "Cleaners", "name_si": "පිරිසිදු කරන්නන්", "name_ta": "சுத்தம் செய்பவர்", "icon": "sparkles", "image": "https://static.prod-images.emergentagent.com/jobs/3de36ae8-1b12-4467-87dd-98c4995672e0/images/0fc9f1d184cb3c1e6d6b889b12a55a42825184db66af7fd07587b62c92f9a355.png"},
    {"id": "mover", "name_en": "Movers", "name_si": "ගෙනයන්නන්", "name_ta": "பொருள் நகர்த்துபவர்", "icon": "truck", "image": "https://static.prod-images.emergentagent.com/jobs/3de36ae8-1b12-4467-87dd-98c4995672e0/images/4245c93fdadbe62a5684e279e3bace9c3ed4d7302dd0a734f9e3f30988578132.png"},
    {"id": "cctv", "name_en": "CCTV", "name_si": "CCTV ස්ථාපනය", "name_ta": "CCTV நிறுவுதல்", "icon": "camera", "image": "https://static.prod-images.emergentagent.com/jobs/3de36ae8-1b12-4467-87dd-98c4995672e0/images/350eb9c8f479c4dec493e3047cd0c35f3c40f613a87051f7efb69b0261a85827.png"},
    {"id": "welder", "name_en": "Welding", "name_si": "වෙල්ඩින්", "name_ta": "வெல்டிங்", "icon": "flame", "image": "https://static.prod-images.emergentagent.com/jobs/3de36ae8-1b12-4467-87dd-98c4995672e0/images/30d76c90f02eda7d72e208d545ef41185c01b02df26a3e89427f5ad0e16215ef.png"},
    {"id": "landscaping", "name_en": "Landscaping", "name_si": "භූ දර්ශන", "name_ta": "நிலப்பரப்பு", "icon": "trees", "image": "https://static.prod-images.emergentagent.com/jobs/3de36ae8-1b12-4467-87dd-98c4995672e0/images/a20a9a62ee156a858fc26d5d36a10bc99b3e2a89a61435a99b76f3eaba2e9e13.png"},
    {"id": "vehicle_repair", "name_en": "Vehicle Repair", "name_si": "වාහන අලුත්වැඩියා", "name_ta": "வாகன பழுது", "icon": "car", "image": "https://static.prod-images.emergentagent.com/jobs/3de36ae8-1b12-4467-87dd-98c4995672e0/images/c777e08a9507d572ba7cb7a4236be26086f9ce4a2466f7bc43a412ae08c4e59f.png"},
    {"id": "pest_control", "name_en": "Pest Control", "name_si": "පළිබෝධ පාලනය", "name_ta": "பூச்சி கட்டுப்பாடு", "icon": "bug", "image": "https://static.prod-images.emergentagent.com/jobs/3de36ae8-1b12-4467-87dd-98c4995672e0/images/d93f44d2acfcc4c55dd2ad045607248195abfd27df2052d7c6c586ea9b5547cd.png"},
    {"id": "solar", "name_en": "Solar Panel", "name_si": "සූර්ය පැනල", "name_ta": "சோலார் பேனல்", "icon": "sun", "image": "https://static.prod-images.emergentagent.com/jobs/3de36ae8-1b12-4467-87dd-98c4995672e0/images/7c845035e019445cb387e7f7a19ce89a816980d2e1974ee14c148211d9da264f.png"},
    {"id": "curtains", "name_en": "Curtains", "name_si": "තිර රෙදි", "name_ta": "திரைச்சீலை", "icon": "blinds", "image": "https://static.prod-images.emergentagent.com/jobs/3de36ae8-1b12-4467-87dd-98c4995672e0/images/8b89c0d5884787a6e9881074ed00681fb8833ad57446326a7aac4f51459d81ee.png"},
    {"id": "aluminium", "name_en": "Aluminium", "name_si": "ඇලුමිනියම්", "name_ta": "அலுமினியம்", "icon": "door-open", "image": "https://static.prod-images.emergentagent.com/jobs/3de36ae8-1b12-4467-87dd-98c4995672e0/images/8aaacbf243005c07853f8f79a557e55a78e2433507d93289ee29d2e39d47b4a8.png"},
    {"id": "ceiling", "name_en": "Ceiling", "name_si": "සීලිං", "name_ta": "கூரை", "icon": "layout", "image": "https://static.prod-images.emergentagent.com/jobs/3de36ae8-1b12-4467-87dd-98c4995672e0/images/f593cdcbbbf9880bd339f6b1c94c17a640388ea3df5ff27822848898edda07f7.png"},
    {"id": "other", "name_en": "Other Services", "name_si": "වෙනත් සේවා", "name_ta": "பிற சேவைகள்", "icon": "wrench", "image": "https://static.prod-images.emergentagent.com/jobs/3de36ae8-1b12-4467-87dd-98c4995672e0/images/d98503e91f9a78f26a778772767a89e4b6a1cb33ed48878848790c804f67816a.png"},
    {"id": "allround_man", "name_en": "All Round Man", "name_si": "සියලු වැඩ", "name_ta": "அனைத்து வேலை", "icon": "wrench", "image": "https://static.prod-images.emergentagent.com/jobs/3de36ae8-1b12-4467-87dd-98c4995672e0/images/3d6e41280b7397fa3628cc3842f4c69a18a586a91ea3fbe2ed0d79c18a765982.png"},
]

# ============================================================================
# MODELS
# ============================================================================

class UserRegister(BaseModel):
    email: str
    password: str
    full_name: str
    phone: str
    role: str = "customer"  # customer, handyman, shop, admin
    district: str = "Colombo"
    referral_code: str = ""

class UserLogin(BaseModel):
    email: str
    password: str

class HandymanProfile(BaseModel):
    services: List[str]
    description: str = ""
    experience_years: int = 0
    districts_served: List[str] = []
    hourly_rate: float = 0
    phone: str = ""
    whatsapp: str = ""
    shop_name: str = ""

class BookingCreate(BaseModel):
    handyman_id: str
    service_id: str
    description: str
    preferred_date: str = ""
    preferred_time: str = ""
    address: str = ""
    district: str = ""
    phone: str = ""

class ReviewCreate(BaseModel):
    rating: int  # 1-5
    comment: str = ""

class ChatMessage(BaseModel):
    booking_id: str
    message: str

class QuotePrice(BaseModel):
    job_price: float

class PaymentInitiate(BaseModel):
    booking_id: str
    origin_url: str
    gateway: str = "stripe"  # "stripe" or "payhere"

# ============================================================================
# AUTH HELPERS
# ============================================================================

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def create_token(data: dict) -> str:
    payload = {**data, "exp": datetime.now(timezone.utc) + timedelta(days=7)}
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

async def get_current_user(authorization: str = Depends(lambda: None)):
    from fastapi import Request
    return None

from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer(auto_error=False)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=["HS256"])
        user = await db.users.find_one({"id": payload["user_id"]}, {"_id": 0, "hashed_password": 0})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_optional_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if not credentials:
        return None
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=["HS256"])
        user = await db.users.find_one({"id": payload["user_id"]}, {"_id": 0, "hashed_password": 0})
        return user
    except:
        return None

# ============================================================================
# STARTUP
# ============================================================================

@app.on_event("startup")
async def startup():
    try:
        await client.admin.command('ping')
        logger.info("Connected to MongoDB")
        
        # Create indexes
        await db.users.create_index("email", unique=True)
        await db.users.create_index([("role", 1), ("is_active", 1)])
        await db.handyman_profiles.create_index("user_id", unique=True)
        # Drop old compound index if exists (MongoDB doesn't support compound indexes on multiple array fields)
        try:
            await db.handyman_profiles.drop_index("services_1_districts_served_1")
        except Exception:
            pass  # Index doesn't exist
        # Create separate indexes for services and districts_served
        await db.handyman_profiles.create_index("services")
        await db.handyman_profiles.create_index("districts_served")
        await db.bookings.create_index([("customer_id", 1), ("status", 1)])
        await db.bookings.create_index([("handyman_id", 1), ("status", 1)])
        await db.reviews.create_index([("handyman_id", 1)])
        
        # Seed admin
        admin = await db.users.find_one({"email": "admin@bassbass.lk"})
        if not admin:
            await db.users.insert_one({
                "id": str(uuid.uuid4()),
                "email": "admin@bassbass.lk",
                "hashed_password": get_password_hash("admin123"),
                "full_name": "System Admin",
                "phone": "0771234567",
                "role": "admin",
                "district": "Colombo",
                "created_at": datetime.now(timezone.utc),
                "is_active": True
            })
            logger.info("Admin user seeded")
        
        logger.info("Database ready")
    except Exception as e:
        logger.error(f"DB Error: {e}")

# ============================================================================
# DEMO DATA SEEDING
# ============================================================================

@app.post("/api/admin/seed-demo")
async def seed_demo_data(current_user: dict = Depends(get_current_user)):
    """Seed realistic demo data for presentation."""
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    # Check if already seeded
    if await db.users.find_one({"email": "nimal@topbass.lk"}):
        return {"message": "Demo data already exists", "seeded": False}

    demo_handymen = [
        {"name": "Nimal Perera", "email": "nimal@topbass.lk", "phone": "0771234001", "district": "Colombo", "services": ["plumber", "ac_repair"], "desc": "15 years experience in plumbing and AC repair. Certified technician. Available 7 days.", "exp": 15, "rate": 2500},
        {"name": "Kamal Silva", "email": "kamal@topbass.lk", "phone": "0771234002", "district": "Gampaha", "services": ["electrician", "solar"], "desc": "Licensed electrician and solar panel installer. Worked on 200+ residential projects.", "exp": 12, "rate": 3000},
        {"name": "Sunil Fernando", "email": "sunil@topbass.lk", "phone": "0771234003", "district": "Kandy", "services": ["mason", "tiler"], "desc": "Expert mason and tiler. Specializing in modern bathroom and kitchen renovations.", "exp": 20, "rate": 2800},
        {"name": "Ruwan Jayawardena", "email": "ruwan@topbass.lk", "phone": "0771234004", "district": "Colombo", "services": ["painter", "ceiling"], "desc": "Professional painter. Interior and exterior. Texture painting specialist.", "exp": 8, "rate": 2000},
        {"name": "Chaminda Bandara", "email": "chaminda@topbass.lk", "phone": "0771234005", "district": "Galle", "services": ["carpenter", "aluminium"], "desc": "Master carpenter. Custom furniture, doors, windows, and aluminium fabrication.", "exp": 18, "rate": 3500},
        {"name": "Lakshan Wijesinghe", "email": "lakshan@topbass.lk", "phone": "0771234006", "district": "Matara", "services": ["cctv", "electrician"], "desc": "CCTV and security system specialist. Hikvision certified installer.", "exp": 6, "rate": 3200},
        {"name": "Pradeep Kumara", "email": "pradeep@topbass.lk", "phone": "0771234007", "district": "Kurunegala", "services": ["vehicle_repair", "welder"], "desc": "Vehicle repair and welding. All makes and models. Mobile service available.", "exp": 10, "rate": 2200},
        {"name": "Asanka Mendis", "email": "asanka@topbass.lk", "phone": "0771234008", "district": "Ratnapura", "services": ["landscaping", "cleaner"], "desc": "Garden landscaping and professional cleaning services for homes and offices.", "exp": 7, "rate": 1800},
        {"name": "Dinesh Rajapaksha", "email": "dinesh@topbass.lk", "phone": "0771234009", "district": "Colombo", "services": ["pest_control"], "desc": "Government certified pest control. Termite, cockroach, mosquito treatments.", "exp": 9, "rate": 4000},
        {"name": "Mahesh Samarasinghe", "email": "mahesh@topbass.lk", "phone": "0771234010", "district": "Gampaha", "services": ["mover"], "desc": "Reliable moving service. Packing, loading, transport. Colombo and suburbs.", "exp": 5, "rate": 5000},
        {"name": "Tharanga Dissanayake", "email": "tharanga@topbass.lk", "phone": "0771234011", "district": "Kandy", "services": ["curtains", "ceiling"], "desc": "Curtain fitting and false ceiling expert. Modern and traditional designs.", "exp": 11, "rate": 2600},
        {"name": "Sampath Wickramasinghe", "email": "sampath@topbass.lk", "phone": "0771234012", "district": "Colombo", "services": ["allround_man"], "desc": "All-round handyman. Small repairs, installations, and maintenance. No job too small.", "exp": 14, "rate": 1500},
    ]

    demo_customers = [
        {"name": "Saman Kumara", "email": "saman@demo.lk", "phone": "0761234001", "district": "Colombo"},
        {"name": "Dilini Perera", "email": "dilini@demo.lk", "phone": "0761234002", "district": "Gampaha"},
        {"name": "Kasun Jayasuriya", "email": "kasun@demo.lk", "phone": "0761234003", "district": "Kandy"},
        {"name": "Ayesha Fernando", "email": "ayesha@demo.lk", "phone": "0761234004", "district": "Galle"},
        {"name": "Ruwanthi Silva", "email": "ruwanthi@demo.lk", "phone": "0761234005", "district": "Colombo"},
    ]

    handyman_ids = []
    customer_ids = []

    # Create handymen
    for h in demo_handymen:
        uid = str(uuid.uuid4())
        handyman_ids.append(uid)
        await db.users.insert_one({
            "id": uid, "email": h["email"], "hashed_password": get_password_hash("demo123"),
            "full_name": h["name"], "phone": h["phone"], "role": "handyman",
            "district": h["district"], "is_approved": True,
            "created_at": datetime.now(timezone.utc) - timedelta(days=random.randint(10, 90)),
            "is_active": True
        })
        nearby = [h["district"]]
        for nd in get_nearby_districts(h["district"], 60):
            if nd["district"] != h["district"]:
                nearby.append(nd["district"])
        await db.handyman_profiles.insert_one({
            "user_id": uid, "full_name": h["name"], "services": h["services"],
            "description": h["desc"], "experience_years": h["exp"],
            "districts_served": nearby[:5], "hourly_rate": h["rate"],
            "phone": h["phone"], "whatsapp": h["phone"], "shop_name": "",
            "district": h["district"], "rating": 0, "review_count": 0,
            "jobs_completed": 0, "is_approved": True,
            "created_at": datetime.now(timezone.utc) - timedelta(days=random.randint(10, 90)),
            "updated_at": datetime.now(timezone.utc)
        })

    # Create customers
    for c in demo_customers:
        uid = str(uuid.uuid4())
        customer_ids.append(uid)
        await db.users.insert_one({
            "id": uid, "email": c["email"], "hashed_password": get_password_hash("demo123"),
            "full_name": c["name"], "phone": c["phone"], "role": "customer",
            "district": c["district"], "is_approved": True,
            "created_at": datetime.now(timezone.utc) - timedelta(days=random.randint(5, 60)),
            "is_active": True
        })

    # Create bookings with various statuses
    statuses = ["completed", "completed", "completed", "completed", "accepted", "in_progress", "quoted", "pending"]
    service_ids = ["plumber", "electrician", "mason", "painter", "carpenter", "cctv", "pest_control", "cleaner"]
    descriptions = [
        "Kitchen tap leaking badly, need urgent repair",
        "Install new ceiling fans in 3 bedrooms",
        "Bathroom renovation - retiling and waterproofing",
        "Repaint living room and hallway walls",
        "Build custom bookshelf for study room",
        "Install 4 CCTV cameras around the house",
        "Full house pest treatment for termites",
        "Deep cleaning of 3-bedroom apartment",
    ]

    for i in range(min(len(statuses), len(handyman_ids), len(customer_ids))):
        cust_idx = i % len(customer_ids)
        handy_idx = i % len(handyman_ids)
        status = statuses[i]
        job_price = random.choice([3000, 5000, 8000, 10000, 15000, 20000])
        billing = calculate_billing(job_price)
        days_ago = random.randint(1, 25)

        booking = {
            "id": str(uuid.uuid4()),
            "customer_id": customer_ids[cust_idx],
            "customer_name": demo_customers[cust_idx]["name"],
            "customer_phone": demo_customers[cust_idx]["phone"],
            "handyman_id": handyman_ids[handy_idx],
            "handyman_name": demo_handymen[handy_idx]["name"],
            "service_id": service_ids[i % len(service_ids)],
            "description": descriptions[i % len(descriptions)],
            "preferred_date": (datetime.now(timezone.utc) + timedelta(days=random.randint(1, 14))).strftime("%Y-%m-%d"),
            "preferred_time": random.choice(["9:00 AM", "10:00 AM", "2:00 PM", "4:00 PM"]),
            "address": f"{random.randint(1,200)} {random.choice(['Main St', 'Temple Rd', 'Lake Rd', 'Hill St'])}, {demo_customers[cust_idx]['district']}",
            "district": demo_customers[cust_idx]["district"],
            "status": status,
            "created_at": datetime.now(timezone.utc) - timedelta(days=days_ago),
        }

        if status in ["quoted", "accepted", "in_progress", "completed"]:
            booking.update({
                "job_price": job_price,
                "topbass_fee": billing["topbass_fee"],
                "service_charge": billing["service_charge"],
                "vat_amount": billing["vat_amount"],
                "total": billing["total"],
                "quoted_at": datetime.now(timezone.utc) - timedelta(days=days_ago - 1),
            })

        if status in ["accepted", "in_progress", "completed"]:
            booking["payment_status"] = "paid"
            booking["payment_method"] = random.choice(["stripe", "bank_transfer", "cod"])
            booking["paid_at"] = datetime.now(timezone.utc) - timedelta(days=days_ago - 1)

            # Create payment transaction
            await db.payment_transactions.insert_one({
                "id": str(uuid.uuid4()),
                "session_id": f"DEMO-{str(uuid.uuid4())[:8]}",
                "booking_id": booking["id"],
                "customer_id": customer_ids[cust_idx],
                "customer_name": demo_customers[cust_idx]["name"],
                "handyman_id": handyman_ids[handy_idx],
                "handyman_name": demo_handymen[handy_idx]["name"],
                "amount": billing["total"],
                "currency": "LKR",
                "job_price": job_price,
                "topbass_fee": billing["topbass_fee"],
                "vat_amount": billing["vat_amount"],
                "payment_status": "paid",
                "gateway": booking["payment_method"],
                "created_at": datetime.now(timezone.utc) - timedelta(days=days_ago),
                "paid_at": datetime.now(timezone.utc) - timedelta(days=days_ago - 1),
            })

        if status == "completed":
            booking["completed_at"] = datetime.now(timezone.utc) - timedelta(days=max(0, days_ago - 3))
            await db.handyman_profiles.update_one(
                {"user_id": handyman_ids[handy_idx]},
                {"$inc": {"jobs_completed": 1}}
            )

        await db.bookings.insert_one(booking)

    # Create reviews for completed bookings
    review_comments = [
        "Excellent work! Very professional and on time.",
        "Great service. Fixed everything perfectly. Highly recommend.",
        "Very skilled craftsman. Fair pricing too.",
        "Good job overall. Will hire again for sure.",
        "Outstanding quality. Very neat and clean work.",
        "Reliable and trustworthy. Arrived on time and did a great job.",
    ]

    completed = await db.bookings.find({"status": "completed"}).to_list(20)
    for i, b in enumerate(completed):
        rating = random.choice([4, 4, 5, 5, 5])
        await db.reviews.insert_one({
            "id": str(uuid.uuid4()),
            "handyman_id": b["handyman_id"],
            "customer_id": b["customer_id"],
            "customer_name": b["customer_name"],
            "rating": rating,
            "comment": review_comments[i % len(review_comments)],
            "created_at": datetime.now(timezone.utc) - timedelta(days=random.randint(1, 15))
        })
        # Update handyman rating
        pipeline = [
            {"$match": {"handyman_id": b["handyman_id"]}},
            {"$group": {"_id": None, "avg": {"$avg": "$rating"}, "cnt": {"$sum": 1}}}
        ]
        result = await db.reviews.aggregate(pipeline).to_list(1)
        if result:
            await db.handyman_profiles.update_one(
                {"user_id": b["handyman_id"]},
                {"$set": {"rating": round(result[0]["avg"], 1), "review_count": result[0]["cnt"]}}
            )

    return {
        "message": "Demo data seeded successfully!",
        "seeded": True,
        "handymen_created": len(demo_handymen),
        "customers_created": len(demo_customers),
        "bookings_created": len(statuses),
        "demo_password": "demo123"
    }

# ============================================================================
# AUTH ENDPOINTS
# ============================================================================

@app.post("/api/auth/register")
async def register(data: UserRegister):
    existing = await db.users.find_one({"email": data.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user = {
        "id": str(uuid.uuid4()),
        "email": data.email,
        "hashed_password": get_password_hash(data.password),
        "full_name": data.full_name,
        "phone": data.phone,
        "role": data.role,
        "district": data.district,
        "is_approved": data.role == "customer",
        "created_at": datetime.now(timezone.utc),
        "is_active": True
    }

    # Generate referral code for handymen/shops
    if data.role in ["handyman", "shop"]:
        user["referral_code"] = generate_referral_code(data.full_name)
        user["referral_credits"] = 0
        user["referral_count"] = 0
    
    # Handle referral code from a referring handyman
    referred_by = None
    if data.referral_code and data.referral_code.strip():
        referrer = await db.users.find_one({"referral_code": data.referral_code.strip().upper()})
        if referrer:
            user["referred_by"] = referrer["id"]
            user["referred_by_code"] = data.referral_code.strip().upper()
            referred_by = referrer
    
    await db.users.insert_one(user)
    
    # Credit the referrer
    if referred_by:
        await db.users.update_one(
            {"id": referred_by["id"]},
            {"$inc": {"referral_credits": REFERRAL_CREDIT_PER_SIGNUP, "referral_count": 1}}
        )
        await db.referrals.insert_one({
            "id": str(uuid.uuid4()),
            "referrer_id": referred_by["id"],
            "referrer_name": referred_by["full_name"],
            "referred_id": user["id"],
            "referred_name": data.full_name,
            "referred_role": data.role,
            "credit_amount": REFERRAL_CREDIT_PER_SIGNUP,
            "created_at": datetime.now(timezone.utc)
        })
        # Notify referrer
        await create_notification(
            referred_by["id"],
            "New Referral!",
            f"{data.full_name} joined TopBass using your code! You earned LKR {REFERRAL_CREDIT_PER_SIGNUP} credit.",
            "/profile", "referral"
        )
    
    token = create_token({"user_id": user["id"], "role": user["role"]})
    user.pop("_id", None)
    user.pop("hashed_password", None)
    
    return {"access_token": token, "user": user, "message": "Registration successful" + (" - Awaiting admin approval" if data.role in ["handyman", "shop"] else "")}

@app.post("/api/auth/login")
async def login(data: UserLogin):
    user = await db.users.find_one({"email": data.email})
    if not user or not verify_password(data.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not user.get("is_active", True):
        raise HTTPException(status_code=403, detail="Account deactivated")
    
    token = create_token({"user_id": user["id"], "role": user["role"]})
    user.pop("_id", None)
    user.pop("hashed_password", None)
    
    return {"access_token": token, "user": user}

@app.get("/api/auth/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    return {"user": current_user}

# ============================================================================
# REFERRAL SYSTEM
# ============================================================================

@app.get("/api/referral/stats")
async def referral_stats(current_user: dict = Depends(get_current_user)):
    """Get referral stats for the current handyman/shop."""
    user = await db.users.find_one({"id": current_user["id"]}, {"_id": 0, "referral_code": 1, "referral_credits": 1, "referral_count": 1})
    if not user or not user.get("referral_code"):
        # Generate one if missing
        code = generate_referral_code(current_user["full_name"])
        await db.users.update_one({"id": current_user["id"]}, {"$set": {"referral_code": code, "referral_credits": 0, "referral_count": 0}})
        user = {"referral_code": code, "referral_credits": 0, "referral_count": 0}

    referrals = await db.referrals.find({"referrer_id": current_user["id"]}, {"_id": 0}).sort("created_at", -1).limit(20).to_list(20)

    return {
        "referral_code": user.get("referral_code", ""),
        "referral_credits": user.get("referral_credits", 0),
        "referral_count": user.get("referral_count", 0),
        "credit_per_referral": REFERRAL_CREDIT_PER_SIGNUP,
        "partner_tier": get_partner_tier(user.get("referral_count", 0)),
        "tiers": PARTNER_TIERS,
        "referrals": referrals
    }

# ============================================================================
# SERVICE CATEGORIES
# ============================================================================

@app.get("/api/services")
async def get_services():
    return {"services": SERVICE_CATEGORIES, "districts": DISTRICTS}

# ============================================================================
# HANDYMAN PROFILES
# ============================================================================

@app.post("/api/handyman/profile")
async def create_or_update_profile(profile: HandymanProfile, current_user: dict = Depends(get_current_user)):
    if current_user["role"] not in ["handyman", "shop", "admin"]:
        raise HTTPException(status_code=403, detail="Not a handyman or shop")
    
    profile_data = {
        "user_id": current_user["id"],
        "full_name": current_user["full_name"],
        "services": profile.services,
        "description": profile.description,
        "experience_years": profile.experience_years,
        "districts_served": profile.districts_served,
        "hourly_rate": profile.hourly_rate,
        "phone": profile.phone or current_user.get("phone", ""),
        "whatsapp": profile.whatsapp,
        "shop_name": profile.shop_name,
        "district": current_user.get("district", "Colombo"),
        "rating": 0,
        "review_count": 0,
        "jobs_completed": 0,
        "is_approved": current_user.get("is_approved", False),
        "updated_at": datetime.now(timezone.utc)
    }
    
    await db.handyman_profiles.update_one(
        {"user_id": current_user["id"]},
        {"$set": profile_data, "$setOnInsert": {"created_at": datetime.now(timezone.utc)}},
        upsert=True
    )
    
    return {"message": "Profile saved", "profile": profile_data}

@app.get("/api/handyman/my-profile")
async def get_my_profile(current_user: dict = Depends(get_current_user)):
    profile = await db.handyman_profiles.find_one({"user_id": current_user["id"]}, {"_id": 0})
    return {"profile": profile}

@app.get("/api/handymen")
async def list_handymen(
    service: Optional[str] = None,
    district: Optional[str] = None,
    q: Optional[str] = None,
    page: int = 1,
    limit: int = 20
):
    query = {"is_approved": True}
    if service:
        query["services"] = service
    if district:
        query["districts_served"] = district
    if q and q.strip():
        query["$or"] = [
            {"full_name": {"$regex": q.strip(), "$options": "i"}},
            {"description": {"$regex": q.strip(), "$options": "i"}},
            {"shop_name": {"$regex": q.strip(), "$options": "i"}},
        ]
    
    total = await db.handyman_profiles.count_documents(query)
    skip = (page - 1) * limit
    
    handymen = await db.handyman_profiles.find(query, {"_id": 0}).sort("rating", -1).skip(skip).limit(limit).to_list(limit)
    # Remove phone from listing results — must book to see contact
    for h in handymen:
        h.pop("phone", None)
        h.pop("whatsapp", None)
    await enrich_with_tier(handymen)
    
    return {"handymen": handymen, "total": total, "page": page, "pages": (total + limit - 1) // limit}

@app.get("/api/handymen/top-rated")
async def top_rated_handymen(limit: int = 6):
    handymen = await db.handyman_profiles.find(
        {"is_approved": True, "rating": {"$gt": 0}}, {"_id": 0}
    ).sort("rating", -1).limit(limit).to_list(limit)
    for h in handymen:
        h.pop("phone", None)
        h.pop("whatsapp", None)
    await enrich_with_tier(handymen)
    return {"handymen": handymen}

@app.get("/api/handymen/nearby")
async def get_nearby_handymen(
    district: str,
    service: Optional[str] = None,
    radius: int = 80,
    limit: int = 20
):
    """Find handymen in nearby districts, sorted by proximity."""
    nearby = get_nearby_districts(district, max_km=radius)
    nearby_names = [n["district"] for n in nearby]
    dist_map = {n["district"]: n["distance_km"] for n in nearby}

    query = {"is_approved": True, "districts_served": {"$in": nearby_names}}
    if service:
        query["services"] = service

    handymen = await db.handyman_profiles.find(query, {"_id": 0}).to_list(200)

    # Assign minimum distance for each handyman
    for h in handymen:
        served = h.get("districts_served", [])
        distances = [dist_map.get(d, 999) for d in served if d in dist_map]
        h["distance_km"] = min(distances) if distances else 999

    handymen.sort(key=lambda h: (h["distance_km"], -(h.get("rating", 0))))
    for h in handymen:
        h.pop("phone", None)
        h.pop("whatsapp", None)
    await enrich_with_tier(handymen)
    return {"handymen": handymen[:limit], "total": len(handymen), "from_district": district}

@app.get("/api/handymen/{user_id}")
async def get_handyman_detail(user_id: str, request: Request):
    profile = await db.handyman_profiles.find_one({"user_id": user_id, "is_approved": True}, {"_id": 0})
    if not profile:
        raise HTTPException(status_code=404, detail="Handyman not found")
    
    reviews = await db.reviews.find({"handyman_id": user_id}, {"_id": 0}).sort("created_at", -1).limit(10).to_list(10)
    
    # Check if requester has an active booking with this handyman
    has_active_booking = False
    try:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token_str = auth_header.split(" ")[1]
            payload = jwt.decode(token_str, SECRET_KEY, algorithms=["HS256"])
            requester_id = payload.get("sub")
            if requester_id:
                active = await db.bookings.find_one({
                    "customer_id": requester_id,
                    "handyman_id": user_id,
                    "status": {"$in": ["accepted", "in_progress", "completed"]}
                })
                has_active_booking = active is not None
    except Exception:
        pass
    
    # Mask phone if no active booking
    if not has_active_booking:
        if profile.get("phone"):
            phone = profile["phone"]
            profile["phone_masked"] = phone[:3] + "****" + phone[-2:] if len(phone) > 5 else "****"
            profile["phone"] = None
        if profile.get("whatsapp"):
            profile["whatsapp"] = None
    
    profile["has_active_booking"] = has_active_booking

    # Add partner tier
    user_data = await db.users.find_one({"id": user_id}, {"_id": 0, "referral_count": 1})
    rc = user_data.get("referral_count", 0) if user_data else 0
    tier = get_partner_tier(rc)
    if tier["tier"] != "bronze":
        profile["partner_tier"] = tier

    return {"profile": profile, "reviews": reviews}

# ============================================================================
# BOOKINGS
# ============================================================================

@app.post("/api/bookings/create")
async def create_booking(booking: BookingCreate, current_user: dict = Depends(get_current_user)):
    handyman = await db.handyman_profiles.find_one({"user_id": booking.handyman_id, "is_approved": True})
    if not handyman:
        raise HTTPException(status_code=404, detail="Handyman not found")
    
    booking_data = {
        "id": str(uuid.uuid4()),
        "customer_id": current_user["id"],
        "customer_name": current_user["full_name"],
        "customer_phone": booking.phone or current_user.get("phone", ""),
        "handyman_id": booking.handyman_id,
        "handyman_name": handyman.get("full_name", ""),
        "service_id": booking.service_id,
        "description": booking.description,
        "preferred_date": booking.preferred_date,
        "preferred_time": booking.preferred_time,
        "address": booking.address,
        "district": booking.district or current_user.get("district", ""),
        "status": "pending",
        "created_at": datetime.now(timezone.utc)
    }
    
    await db.bookings.insert_one(booking_data)
    booking_data.pop("_id", None)
    
    # Notify handyman about new booking (in-app + SMS)
    await notify_with_sms(
        booking.handyman_id,
        "New Booking Request",
        f"{current_user['full_name']} requested your service",
        "/bookings",
        "booking"
    )
    
    return {"booking": booking_data, "message": "Booking request sent!"}

@app.get("/api/bookings/my")
async def get_my_bookings(current_user: dict = Depends(get_current_user)):
    if current_user["role"] in ["handyman", "shop"]:
        bookings = await db.bookings.find({"handyman_id": current_user["id"]}, {"_id": 0}).sort("created_at", -1).to_list(50)
    else:
        bookings = await db.bookings.find({"customer_id": current_user["id"]}, {"_id": 0}).sort("created_at", -1).to_list(50)
    
    return {"bookings": bookings}

@app.put("/api/bookings/{booking_id}/status")
async def update_booking_status(booking_id: str, data: Dict[str, str], current_user: dict = Depends(get_current_user)):
    new_status = data.get("status")
    if new_status not in ["accepted", "rejected", "in_progress", "completed", "cancelled", "quoted"]:
        raise HTTPException(status_code=400, detail="Invalid status")
    
    booking = await db.bookings.find_one({"id": booking_id})
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    # Handyman can accept/reject/complete, customer can cancel
    if current_user["role"] in ["handyman", "shop"] and booking["handyman_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not your booking")
    
    update = {"status": new_status, "updated_at": datetime.now(timezone.utc)}
    if new_status == "completed":
        update["completed_at"] = datetime.now(timezone.utc)
        await db.handyman_profiles.update_one(
            {"user_id": booking["handyman_id"]},
            {"$inc": {"jobs_completed": 1}}
        )
        # Auto-create payout record for handyman
        if booking.get("job_price"):
            payout = {
                "id": str(uuid.uuid4()),
                "booking_id": booking_id,
                "handyman_id": booking["handyman_id"],
                "handyman_name": booking.get("handyman_name", ""),
                "amount": booking["job_price"],
                "status": "pending",
                "created_at": datetime.now(timezone.utc)
            }
            await db.payouts.insert_one(payout)
    
    await db.bookings.update_one({"id": booking_id}, {"$set": update})
    
    # Send notification to the other party
    if new_status in ["accepted", "rejected", "in_progress", "completed", "cancelled"]:
        titles = {
            "accepted": "Booking Accepted",
            "rejected": "Booking Rejected", 
            "in_progress": "Work Started",
            "completed": "Job Completed",
            "cancelled": "Booking Cancelled"
        }
        if current_user["id"] == booking["handyman_id"]:
            await notify_with_sms(booking["customer_id"], titles.get(new_status, "Booking Update"), f"Your booking has been {new_status}", "/bookings", "booking")
        else:
            await notify_with_sms(booking["handyman_id"], titles.get(new_status, "Booking Update"), f"Booking has been {new_status}", "/bookings", "booking")
    
    return {"message": f"Booking {new_status}"}

# ============================================================================
# REVIEWS
# ============================================================================

@app.post("/api/reviews/{handyman_id}")
async def create_review(handyman_id: str, review: ReviewCreate, current_user: dict = Depends(get_current_user)):
    if review.rating < 1 or review.rating > 5:
        raise HTTPException(status_code=400, detail="Rating must be 1-5")
    
    review_data = {
        "id": str(uuid.uuid4()),
        "handyman_id": handyman_id,
        "customer_id": current_user["id"],
        "customer_name": current_user["full_name"],
        "rating": review.rating,
        "comment": review.comment,
        "created_at": datetime.now(timezone.utc)
    }
    
    await db.reviews.insert_one(review_data)
    
    # Update average rating
    pipeline = [
        {"$match": {"handyman_id": handyman_id}},
        {"$group": {"_id": None, "avg_rating": {"$avg": "$rating"}, "count": {"$sum": 1}}}
    ]
    result = await db.reviews.aggregate(pipeline).to_list(1)
    if result:
        await db.handyman_profiles.update_one(
            {"user_id": handyman_id},
            {"$set": {"rating": round(result[0]["avg_rating"], 1), "review_count": result[0]["count"]}}
        )
    
    return {"message": "Review submitted"}

# ============================================================================
# ADMIN
# ============================================================================

@app.get("/api/admin/pending-approvals")
async def get_pending_approvals(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    
    pending = await db.users.find(
        {"role": {"$in": ["handyman", "shop"]}, "is_approved": False, "is_active": True},
        {"_id": 0, "hashed_password": 0}
    ).to_list(100)
    
    # Get profiles
    for user in pending:
        profile = await db.handyman_profiles.find_one({"user_id": user["id"]}, {"_id": 0})
        user["profile"] = profile
    
    return {"pending": pending}

@app.put("/api/admin/approve/{user_id}")
async def approve_user(user_id: str, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    
    await db.users.update_one({"id": user_id}, {"$set": {"is_approved": True}})
    await db.handyman_profiles.update_one({"user_id": user_id}, {"$set": {"is_approved": True}})
    
    return {"message": "User approved"}

@app.put("/api/admin/reject/{user_id}")
async def reject_user(user_id: str, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    
    await db.users.update_one({"id": user_id}, {"$set": {"is_active": False}})
    return {"message": "User rejected"}

@app.get("/api/admin/statistics")
async def admin_stats(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    
    return {
        "total_customers": await db.users.count_documents({"role": "customer"}),
        "total_handymen": await db.users.count_documents({"role": {"$in": ["handyman", "shop"]}}),
        "approved_handymen": await db.handyman_profiles.count_documents({"is_approved": True}),
        "pending_approvals": await db.users.count_documents({"is_approved": False, "role": {"$in": ["handyman", "shop"]}, "is_active": True}),
        "total_bookings": await db.bookings.count_documents({}),
        "active_bookings": await db.bookings.count_documents({"status": {"$in": ["pending", "accepted", "in_progress"]}}),
        "completed_bookings": await db.bookings.count_documents({"status": "completed"}),
        "total_reviews": await db.reviews.count_documents({})
    }

@app.get("/api/admin/users")
async def admin_list_users(role: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    
    query = {"is_active": True}
    if role:
        query["role"] = role
    
    users = await db.users.find(query, {"_id": 0, "hashed_password": 0}).sort("created_at", -1).to_list(500)
    return {"users": users}

# ============================================================================
# SHOP: Add handymen under a shop
# ============================================================================

@app.post("/api/shop/add-handyman")
async def shop_add_handyman(data: UserRegister, current_user: dict = Depends(get_current_user)):
    if current_user["role"] not in ["shop", "admin"]:
        raise HTTPException(status_code=403, detail="Shop or admin only")
    
    existing = await db.users.find_one({"email": data.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user = {
        "id": str(uuid.uuid4()),
        "email": data.email,
        "hashed_password": get_password_hash(data.password),
        "full_name": data.full_name,
        "phone": data.phone,
        "role": "handyman",
        "district": data.district,
        "shop_id": current_user["id"],
        "shop_name": current_user.get("full_name", ""),
        "is_approved": current_user.get("is_approved", False),
        "created_at": datetime.now(timezone.utc),
        "is_active": True
    }
    
    await db.users.insert_one(user)
    user.pop("_id", None)
    user.pop("hashed_password", None)
    
    return {"user": user, "message": "Handyman added to your shop"}

@app.get("/api/shop/my-handymen")
async def shop_my_handymen(current_user: dict = Depends(get_current_user)):
    if current_user["role"] not in ["shop", "admin"]:
        raise HTTPException(status_code=403, detail="Shop or admin only")
    
    users = await db.users.find(
        {"shop_id": current_user["id"]}, {"_id": 0, "hashed_password": 0}
    ).to_list(100)
    
    for u in users:
        profile = await db.handyman_profiles.find_one({"user_id": u["id"]}, {"_id": 0})
        u["profile"] = profile
    
    return {"handymen": users}

@app.delete("/api/shop/remove-handyman/{user_id}")
async def shop_remove_handyman(user_id: str, current_user: dict = Depends(get_current_user)):
    if current_user["role"] not in ["shop", "admin"]:
        raise HTTPException(status_code=403, detail="Shop or admin only")
    
    user = await db.users.find_one({"id": user_id, "shop_id": current_user["id"]})
    if not user:
        raise HTTPException(status_code=404, detail="Handyman not found in your shop")
    
    await db.users.update_one({"id": user_id}, {"$set": {"is_active": False}})
    await db.handyman_profiles.update_one({"user_id": user_id}, {"$set": {"is_approved": False}})
    
    return {"message": "Handyman removed from shop"}

# ============================================================================
# BILLING & PRICING
# ============================================================================

def calculate_billing(job_price: float):
    """Calculate billing breakdown. Customer sees service_charge + VAT."""
    fee = round(job_price * TOPBASS_FEE_PERCENT / 100, 2)
    service_charge = round(job_price + fee, 2)  # What customer sees
    vat = round(service_charge * VAT_PERCENT / 100, 2)
    total = round(service_charge + vat, 2)
    return {
        "job_price": job_price,
        "topbass_fee": fee,
        "service_charge": service_charge,
        "vat_percent": VAT_PERCENT,
        "vat_amount": vat,
        "total": total
    }

@app.put("/api/bookings/{booking_id}/quote")
async def set_booking_price(booking_id: str, data: QuotePrice, current_user: dict = Depends(get_current_user)):
    """Handyman sets a price for the job when accepting."""
    if current_user["role"] not in ["handyman", "shop"]:
        raise HTTPException(status_code=403, detail="Handyman only")
    
    booking = await db.bookings.find_one({"id": booking_id})
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking["handyman_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not your booking")
    
    billing = calculate_billing(data.job_price)
    
    update = {
        "status": "quoted",
        "job_price": data.job_price,
        "topbass_fee": billing["topbass_fee"],
        "service_charge": billing["service_charge"],
        "vat_amount": billing["vat_amount"],
        "total": billing["total"],
        "payment_status": "pending",
        "quoted_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    }
    await db.bookings.update_one({"id": booking_id}, {"$set": update})
    
    # Notify customer about the quote (in-app + SMS)
    await notify_with_sms(
        booking["customer_id"],
        "Price Quote Received",
        f"Your handyman quoted LKR {billing['total']:.2f} for the job",
        "/bookings",
        "billing"
    )
    
    return {"message": "Price quoted", "billing": billing}

@app.get("/api/bookings/{booking_id}/billing")
async def get_booking_billing(booking_id: str, current_user: dict = Depends(get_current_user)):
    """Get billing breakdown for a booking."""
    booking = await db.bookings.find_one({"id": booking_id}, {"_id": 0})
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking["customer_id"] != current_user["id"] and booking["handyman_id"] != current_user["id"] and current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    
    return {
        "booking_id": booking_id,
        "service_charge": booking.get("service_charge", 0),
        "vat_percent": VAT_PERCENT,
        "vat_amount": booking.get("vat_amount", 0),
        "total": booking.get("total", 0),
        "payment_status": booking.get("payment_status", "pending"),
        "status": booking.get("status")
    }

# ============================================================================
# STRIPE PAYMENTS
# ============================================================================

@app.post("/api/payments/create-checkout")
async def create_payment_checkout(data: PaymentInitiate, request: Request, current_user: dict = Depends(get_current_user)):
    """Create Stripe checkout session for a booking."""
    booking = await db.bookings.find_one({"id": data.booking_id})
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking["customer_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not your booking")
    if not booking.get("total"):
        raise HTTPException(status_code=400, detail="No price quoted yet")
    if booking.get("payment_status") == "paid":
        raise HTTPException(status_code=400, detail="Already paid")
    
    # Amount in LKR
    total = float(booking["total"])
    
    host_url = str(request.base_url).rstrip("/")
    webhook_url = f"{host_url}/api/webhook/stripe"
    stripe_checkout = StripeCheckout(api_key=STRIPE_API_KEY, webhook_url=webhook_url)
    
    origin = data.origin_url.rstrip("/")
    success_url = f"{origin}/payment/success?session_id={{CHECKOUT_SESSION_ID}}&booking_id={data.booking_id}"
    cancel_url = f"{origin}/bookings"
    
    checkout_request = CheckoutSessionRequest(
        amount=total,
        currency="lkr",
        success_url=success_url,
        cancel_url=cancel_url,
        metadata={
            "booking_id": data.booking_id,
            "customer_id": current_user["id"],
            "customer_name": current_user["full_name"]
        }
    )
    
    session = await stripe_checkout.create_checkout_session(checkout_request)
    
    # Save payment transaction
    txn = {
        "id": str(uuid.uuid4()),
        "session_id": session.session_id,
        "booking_id": data.booking_id,
        "customer_id": current_user["id"],
        "customer_name": current_user["full_name"],
        "handyman_id": booking["handyman_id"],
        "handyman_name": booking.get("handyman_name", ""),
        "amount": total,
        "currency": "LKR",
        "job_price": booking.get("job_price", 0),
        "topbass_fee": booking.get("topbass_fee", 0),
        "vat_amount": booking.get("vat_amount", 0),
        "payment_status": "initiated",
        "metadata": {"booking_id": data.booking_id},
        "created_at": datetime.now(timezone.utc)
    }
    await db.payment_transactions.insert_one(txn)
    
    return {"url": session.url, "session_id": session.session_id}

@app.get("/api/payments/status/{session_id}")
async def get_payment_status(session_id: str, request: Request, current_user: dict = Depends(get_current_user)):
    """Check payment status and update booking."""
    host_url = str(request.base_url).rstrip("/")
    webhook_url = f"{host_url}/api/webhook/stripe"
    stripe_checkout = StripeCheckout(api_key=STRIPE_API_KEY, webhook_url=webhook_url)
    
    status = await stripe_checkout.get_checkout_status(session_id)
    
    txn = await db.payment_transactions.find_one({"session_id": session_id})
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    # Update transaction and booking if paid (only once)
    if status.payment_status == "paid" and txn.get("payment_status") != "paid":
        await db.payment_transactions.update_one(
            {"session_id": session_id},
            {"$set": {"payment_status": "paid", "paid_at": datetime.now(timezone.utc)}}
        )
        await db.bookings.update_one(
            {"id": txn["booking_id"]},
            {"$set": {"payment_status": "paid", "status": "accepted", "paid_at": datetime.now(timezone.utc)}}
        )
    elif status.payment_status != "paid" and status.status == "expired":
        await db.payment_transactions.update_one(
            {"session_id": session_id},
            {"$set": {"payment_status": "expired"}}
        )
    
    return {
        "status": status.status,
        "payment_status": status.payment_status,
        "amount_total": status.amount_total,
        "currency": status.currency,
        "booking_id": txn.get("booking_id")
    }

@app.post("/api/webhook/stripe")
async def stripe_webhook(request: Request):
    """Handle Stripe webhook events."""
    body = await request.body()
    signature = request.headers.get("Stripe-Signature", "")
    
    try:
        host_url = str(request.base_url).rstrip("/")
        webhook_url = f"{host_url}/api/webhook/stripe"
        stripe_checkout = StripeCheckout(api_key=STRIPE_API_KEY, webhook_url=webhook_url)
        event = await stripe_checkout.handle_webhook(body, signature)
        
        if event.payment_status == "paid":
            await db.payment_transactions.update_one(
                {"session_id": event.session_id},
                {"$set": {"payment_status": "paid", "paid_at": datetime.now(timezone.utc)}}
            )
            txn = await db.payment_transactions.find_one({"session_id": event.session_id})
            if txn:
                await db.bookings.update_one(
                    {"id": txn["booking_id"]},
                    {"$set": {"payment_status": "paid", "status": "accepted", "paid_at": datetime.now(timezone.utc)}}
                )
    except Exception as e:
        logger.error(f"Webhook error: {e}")
    
    return {"status": "ok"}

# ============================================================================
# COD (Cash on Delivery) & BANK QR PAYMENTS
# ============================================================================

@app.get("/api/payments/bank-qr")
async def get_bank_qr():
    """Return the bank QR code image URL for payment."""
    return {"qr_code_url": BANK_QR_CODE_URL}

@app.post("/api/payments/cod")
async def pay_cod(data: Dict[str, str], current_user: dict = Depends(get_current_user)):
    """Customer chooses Cash on Delivery — booking is accepted, payment on completion."""
    booking_id = data.get("booking_id")
    booking = await db.bookings.find_one({"id": booking_id})
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking["customer_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not your booking")
    if not booking.get("total"):
        raise HTTPException(status_code=400, detail="No price quoted yet")
    if booking.get("payment_status") == "paid":
        raise HTTPException(status_code=400, detail="Already paid")

    await db.bookings.update_one(
        {"id": booking_id},
        {"$set": {
            "payment_method": "cod",
            "payment_status": "cod_pending",
            "status": "accepted",
            "updated_at": datetime.now(timezone.utc)
        }}
    )

    # Notify handyman (in-app + SMS)
    await notify_with_sms(
        booking["handyman_id"],
        "Booking Accepted (COD)",
        f"{current_user['full_name']} accepted the quote — Cash payment on completion",
        "/bookings", "billing"
    )

    return {"message": "Booking accepted with Cash on Delivery. Pay the handyman upon job completion."}

@app.post("/api/payments/bank-transfer")
async def pay_bank_transfer(data: Dict[str, str], current_user: dict = Depends(get_current_user)):
    """Customer confirms they paid via bank QR transfer."""
    booking_id = data.get("booking_id")
    booking = await db.bookings.find_one({"id": booking_id})
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking["customer_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not your booking")
    if not booking.get("total"):
        raise HTTPException(status_code=400, detail="No price quoted yet")
    if booking.get("payment_status") == "paid":
        raise HTTPException(status_code=400, detail="Already paid")

    # Save transaction
    txn = {
        "id": str(uuid.uuid4()),
        "session_id": f"BT-{booking_id[:8]}",
        "booking_id": booking_id,
        "customer_id": current_user["id"],
        "customer_name": current_user["full_name"],
        "handyman_id": booking["handyman_id"],
        "handyman_name": booking.get("handyman_name", ""),
        "amount": float(booking["total"]),
        "currency": "LKR",
        "job_price": booking.get("job_price", 0),
        "topbass_fee": booking.get("topbass_fee", 0),
        "vat_amount": booking.get("vat_amount", 0),
        "payment_status": "pending_verification",
        "gateway": "bank_transfer",
        "created_at": datetime.now(timezone.utc)
    }
    await db.payment_transactions.insert_one(txn)

    await db.bookings.update_one(
        {"id": booking_id},
        {"$set": {
            "payment_method": "bank_transfer",
            "payment_status": "pending_verification",
            "status": "accepted",
            "updated_at": datetime.now(timezone.utc)
        }}
    )

    # Notify handyman and admin (in-app + SMS)
    await notify_with_sms(
        booking["handyman_id"],
        "Booking Accepted (Bank Transfer)",
        f"{current_user['full_name']} paid via bank transfer — pending verification",
        "/bookings", "billing"
    )

    # Notify admin for verification
    admins = await db.users.find({"role": "admin"}, {"_id": 0, "id": 1}).to_list(10)
    for a in admins:
        await notify_with_sms(
            a["id"],
            "Bank Transfer Pending Verification",
            f"Customer {current_user['full_name']} claims bank transfer of LKR {booking['total']:.2f}",
            "/admin", "billing"
        )

    return {"message": "Bank transfer noted. Your booking is accepted and payment will be verified by admin."}

@app.put("/api/admin/verify-bank-payment/{booking_id}")
async def verify_bank_payment(booking_id: str, current_user: dict = Depends(get_current_user)):
    """Admin verifies a bank transfer payment."""
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    booking = await db.bookings.find_one({"id": booking_id})
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    await db.bookings.update_one(
        {"id": booking_id},
        {"$set": {"payment_status": "paid", "paid_at": datetime.now(timezone.utc)}}
    )
    await db.payment_transactions.update_one(
        {"booking_id": booking_id, "gateway": "bank_transfer"},
        {"$set": {"payment_status": "paid", "paid_at": datetime.now(timezone.utc)}}
    )

    await create_notification(
        booking["customer_id"],
        "Payment Verified",
        "Your bank transfer has been verified. Thank you!",
        "/bookings", "billing"
    )

    return {"message": "Bank transfer verified"}

# ============================================================================
# PAYHERE INTEGRATION (Sri Lankan local gateway)
# ============================================================================

@app.post("/api/payments/payhere-checkout")
async def payhere_checkout(data: PaymentInitiate, request: Request, current_user: dict = Depends(get_current_user)):
    """Generate PayHere checkout parameters for client-side form submission."""
    import hashlib
    
    booking = await db.bookings.find_one({"id": data.booking_id})
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking["customer_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not your booking")
    if not booking.get("total"):
        raise HTTPException(status_code=400, detail="No price quoted yet")
    if booking.get("payment_status") == "paid":
        raise HTTPException(status_code=400, detail="Already paid")
    if not PAYHERE_MERCHANT_ID or not PAYHERE_MERCHANT_SECRET:
        raise HTTPException(status_code=503, detail="PayHere not configured")
    
    order_id = f"TB-{data.booking_id[:8]}"
    amount = f"{float(booking['total']):.2f}"
    currency = "LKR"
    
    # PayHere hash: MD5(merchant_id + order_id + amount + currency + secret)
    hash_str = PAYHERE_MERCHANT_ID + order_id + amount + currency + hashlib.md5(PAYHERE_MERCHANT_SECRET.encode()).hexdigest().upper()
    payment_hash = hashlib.md5(hash_str.encode()).hexdigest().upper()
    
    origin = data.origin_url.rstrip("/")
    host_url = str(request.base_url).rstrip("/")
    
    # Save transaction
    txn = {
        "id": str(uuid.uuid4()),
        "session_id": order_id,
        "booking_id": data.booking_id,
        "customer_id": current_user["id"],
        "customer_name": current_user["full_name"],
        "handyman_id": booking["handyman_id"],
        "handyman_name": booking.get("handyman_name", ""),
        "amount": float(booking["total"]),
        "currency": "LKR",
        "job_price": booking.get("job_price", 0),
        "topbass_fee": booking.get("topbass_fee", 0),
        "vat_amount": booking.get("vat_amount", 0),
        "payment_status": "initiated",
        "gateway": "payhere",
        "created_at": datetime.now(timezone.utc)
    }
    await db.payment_transactions.insert_one(txn)
    
    return {
        "merchant_id": PAYHERE_MERCHANT_ID,
        "order_id": order_id,
        "amount": amount,
        "currency": currency,
        "hash": payment_hash,
        "return_url": f"{origin}/payment/success?gateway=payhere&booking_id={data.booking_id}&order_id={order_id}",
        "cancel_url": f"{origin}/bookings",
        "notify_url": f"{host_url}/api/webhook/payhere",
        "first_name": current_user.get("full_name", "").split()[0] if current_user.get("full_name") else "",
        "last_name": " ".join(current_user.get("full_name", "").split()[1:]) if current_user.get("full_name") else "",
        "email": current_user.get("email", ""),
        "phone": current_user.get("phone", ""),
        "items": f"TopBass Service - Booking {data.booking_id[:8]}",
        "sandbox": PAYHERE_MERCHANT_ID.startswith("sandbox") or os.environ.get("PAYHERE_SANDBOX", "false") == "true"
    }

@app.post("/api/webhook/payhere")
async def payhere_webhook(request: Request):
    """Handle PayHere payment notification."""
    import hashlib
    
    try:
        form = await request.form()
        merchant_id = form.get("merchant_id", "")
        order_id = form.get("order_id", "")
        payment_id = form.get("payment_id", "")
        payhere_amount = form.get("payhere_amount", "")
        payhere_currency = form.get("payhere_currency", "")
        status_code = form.get("status_code", "")
        md5sig = form.get("md5sig", "")
        
        # Verify hash
        secret_hash = hashlib.md5(PAYHERE_MERCHANT_SECRET.encode()).hexdigest().upper()
        local_hash = hashlib.md5(
            f"{merchant_id}{order_id}{payhere_amount}{payhere_currency}{status_code}{secret_hash}".encode()
        ).hexdigest().upper()
        
        if local_hash == md5sig and status_code == "2":
            # Payment successful
            await db.payment_transactions.update_one(
                {"session_id": order_id, "gateway": "payhere"},
                {"$set": {"payment_status": "paid", "paid_at": datetime.now(timezone.utc), "payment_id": payment_id}}
            )
            txn = await db.payment_transactions.find_one({"session_id": order_id, "gateway": "payhere"})
            if txn:
                await db.bookings.update_one(
                    {"id": txn["booking_id"]},
                    {"$set": {"payment_status": "paid", "status": "accepted", "paid_at": datetime.now(timezone.utc)}}
                )
                # Notify handyman
                await create_notification(txn["handyman_id"], "Payment Received", f"Customer paid LKR {payhere_amount} for booking", "/bookings", "billing")
        elif status_code == "-1":
            await db.payment_transactions.update_one(
                {"session_id": order_id, "gateway": "payhere"},
                {"$set": {"payment_status": "cancelled"}}
            )
    except Exception as e:
        logger.error(f"PayHere webhook error: {e}")
    
    return {"status": "ok"}

# ============================================================================
# ACCOUNTING (Admin)
# ============================================================================

@app.get("/api/admin/accounting")
async def admin_accounting(current_user: dict = Depends(get_current_user)):
    """Admin accounting dashboard — revenue, VAT, payouts breakdown."""
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    
    paid_txns = await db.payment_transactions.find({"payment_status": "paid"}, {"_id": 0}).to_list(1000)
    payouts = await db.payouts.find({}, {"_id": 0}).to_list(1000)
    
    total_revenue = sum(t.get("amount", 0) for t in paid_txns)
    total_topbass_fee = sum(t.get("topbass_fee", 0) for t in paid_txns)
    total_vat = sum(t.get("vat_amount", 0) for t in paid_txns)
    total_handyman_pay = sum(t.get("job_price", 0) for t in paid_txns)
    
    pending_payouts = sum(p.get("amount", 0) for p in payouts if p.get("status") == "pending")
    completed_payouts = sum(p.get("amount", 0) for p in payouts if p.get("status") == "paid")
    
    return {
        "total_revenue": round(total_revenue, 2),
        "total_topbass_fee": round(total_topbass_fee, 2),
        "total_vat_collected": round(total_vat, 2),
        "total_handyman_pay": round(total_handyman_pay, 2),
        "transaction_count": len(paid_txns),
        "pending_payouts": round(pending_payouts, 2),
        "completed_payouts": round(completed_payouts, 2),
        "fee_percent": TOPBASS_FEE_PERCENT,
        "vat_percent": VAT_PERCENT,
        "transactions": paid_txns[-20:],
        "payouts": payouts[-20:]
    }

@app.put("/api/admin/payouts/{payout_id}/mark-paid")
async def mark_payout_paid(payout_id: str, current_user: dict = Depends(get_current_user)):
    """Admin marks a handyman payout as paid."""
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    
    payout = await db.payouts.find_one({"id": payout_id})
    if not payout:
        raise HTTPException(status_code=404, detail="Payout not found")
    
    await db.payouts.update_one(
        {"id": payout_id},
        {"$set": {"status": "paid", "paid_at": datetime.now(timezone.utc)}}
    )
    return {"message": "Payout marked as paid"}

# ============================================================================
# NOTIFICATIONS
# ============================================================================

# ============================================================================
# SMS NOTIFICATIONS (Twilio)
# ============================================================================

twilio_client = None
if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN:
    try:
        from twilio.rest import Client as TwilioClient
        twilio_client = TwilioClient(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        logger.info("Twilio SMS configured")
    except Exception as e:
        logger.warning(f"Twilio setup failed: {e}")

async def send_sms(phone: str, message: str):
    """Send SMS via Twilio. Fails silently if not configured."""
    if not twilio_client or not TWILIO_PHONE_NUMBER:
        logger.debug(f"SMS skipped (not configured): {phone}")
        return False
    try:
        # Normalize Sri Lankan numbers to E.164
        clean = phone.strip().replace(" ", "")
        if clean.startswith("0"):
            clean = "+94" + clean[1:]
        elif not clean.startswith("+"):
            clean = "+94" + clean
        
        twilio_client.messages.create(
            body=message,
            from_=TWILIO_PHONE_NUMBER,
            to=clean
        )
        logger.info(f"SMS sent to {clean}")
        return True
    except Exception as e:
        logger.warning(f"SMS failed to {phone}: {e}")
        return False

async def notify_with_sms(user_id: str, title: str, message: str, link: str = "", ntype: str = "info"):
    """Create in-app notification AND send SMS if user has phone."""
    await create_notification(user_id, title, message, link, ntype)
    # Try to send SMS
    user = await db.users.find_one({"id": user_id}, {"_id": 0, "phone": 1})
    if user and user.get("phone"):
        await send_sms(user["phone"], f"TopBass: {title}\n{message}")

@app.get("/api/admin/sms-status")
async def sms_status(current_user: dict = Depends(get_current_user)):
    """Check if SMS is configured."""
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    return {
        "configured": twilio_client is not None and bool(TWILIO_PHONE_NUMBER),
        "provider": "Twilio",
        "note": "Add TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER to backend/.env"
    }

@app.post("/api/admin/send-test-sms")
async def send_test_sms(data: dict, current_user: dict = Depends(get_current_user)):
    """Admin sends a test SMS."""
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    phone = data.get("phone", "")
    if not phone:
        raise HTTPException(status_code=400, detail="Phone required")
    if not twilio_client:
        raise HTTPException(status_code=503, detail="SMS not configured. Add Twilio credentials to .env")
    success = await send_sms(phone, "This is a test SMS from TopBass! Your SMS notifications are working.")
    return {"sent": success, "phone": phone}

async def create_notification(user_id: str, title: str, message: str, link: str = "", ntype: str = "info"):
    """Helper to create a notification for a user."""
    notif = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "title": title,
        "message": message,
        "link": link,
        "type": ntype,
        "is_read": False,
        "created_at": datetime.now(timezone.utc)
    }
    await db.notifications.insert_one(notif)

@app.get("/api/notifications")
async def get_notifications(current_user: dict = Depends(get_current_user)):
    notifs = await db.notifications.find(
        {"user_id": current_user["id"]}, {"_id": 0}
    ).sort("created_at", -1).limit(50).to_list(50)
    unread = sum(1 for n in notifs if not n.get("is_read"))
    # Convert datetime to string
    for n in notifs:
        if isinstance(n.get("created_at"), datetime):
            n["created_at"] = n["created_at"].isoformat()
    return {"notifications": notifs, "unread_count": unread}

@app.put("/api/notifications/read-all")
async def mark_notifications_read(current_user: dict = Depends(get_current_user)):
    await db.notifications.update_many(
        {"user_id": current_user["id"], "is_read": False},
        {"$set": {"is_read": True}}
    )
    return {"message": "All marked as read"}

@app.put("/api/notifications/{notif_id}/read")
async def mark_notification_read(notif_id: str, current_user: dict = Depends(get_current_user)):
    await db.notifications.update_one(
        {"id": notif_id, "user_id": current_user["id"]},
        {"$set": {"is_read": True}}
    )
    return {"message": "Marked as read"}

# ============================================================================
# CHAT
# ============================================================================

@app.post("/api/chat/send")
async def send_chat_message(data: ChatMessage, current_user: dict = Depends(get_current_user)):
    booking = await db.bookings.find_one({"id": data.booking_id})
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    # Only customer or handyman of this booking can chat
    if current_user["id"] not in [booking["customer_id"], booking["handyman_id"]]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    msg = {
        "id": str(uuid.uuid4()),
        "booking_id": data.booking_id,
        "sender_id": current_user["id"],
        "sender_name": current_user["full_name"],
        "sender_role": current_user["role"],
        "message": data.message.strip(),
        "is_read": False,
        "created_at": datetime.now(timezone.utc)
    }
    await db.chat_messages.insert_one(msg)
    msg.pop("_id", None)
    if isinstance(msg.get("created_at"), datetime):
        msg["created_at"] = msg["created_at"].isoformat()
    
    # Notify the other party
    recipient_id = booking["handyman_id"] if current_user["id"] == booking["customer_id"] else booking["customer_id"]
    recipient_name = booking.get("handyman_name", "") if current_user["id"] == booking["customer_id"] else booking.get("customer_name", "")
    await create_notification(
        recipient_id,
        f"New message from {current_user['full_name']}",
        data.message[:100],
        f"/chat/{data.booking_id}",
        "chat"
    )
    
    return {"message": msg}

@app.get("/api/chat/messages/{booking_id}")
async def get_chat_messages(booking_id: str, current_user: dict = Depends(get_current_user)):
    booking = await db.bookings.find_one({"id": booking_id})
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    if current_user["id"] not in [booking["customer_id"], booking["handyman_id"]]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    messages = await db.chat_messages.find(
        {"booking_id": booking_id}, {"_id": 0}
    ).sort("created_at", 1).to_list(200)
    
    for m in messages:
        if isinstance(m.get("created_at"), datetime):
            m["created_at"] = m["created_at"].isoformat()
    
    # Mark messages as read for current user
    await db.chat_messages.update_many(
        {"booking_id": booking_id, "sender_id": {"$ne": current_user["id"]}, "is_read": False},
        {"$set": {"is_read": True}}
    )
    
    other_id = booking["handyman_id"] if current_user["id"] == booking["customer_id"] else booking["customer_id"]
    other_name = booking.get("handyman_name", "") if current_user["id"] == booking["customer_id"] else booking.get("customer_name", "")
    
    return {
        "messages": messages,
        "booking": {
            "id": booking["id"],
            "service_id": booking.get("service_id", ""),
            "status": booking.get("status", ""),
            "description": booking.get("description", "")
        },
        "other_user": {"id": other_id, "name": other_name}
    }

@app.get("/api/chat/conversations")
async def get_conversations(current_user: dict = Depends(get_current_user)):
    """Get list of active conversations (bookings with messages)."""
    uid = current_user["id"]
    
    # Find all bookings for this user
    bookings = await db.bookings.find(
        {"$or": [{"customer_id": uid}, {"handyman_id": uid}]}, {"_id": 0}
    ).sort("created_at", -1).to_list(50)
    
    convos = []
    for b in bookings:
        last_msg = await db.chat_messages.find_one(
            {"booking_id": b["id"]}, {"_id": 0}, sort=[("created_at", -1)]
        )
        unread = await db.chat_messages.count_documents(
            {"booking_id": b["id"], "sender_id": {"$ne": uid}, "is_read": False}
        )
        
        other_name = b.get("handyman_name", "") if b["customer_id"] == uid else b.get("customer_name", "")
        other_id = b["handyman_id"] if b["customer_id"] == uid else b["customer_id"]
        
        last_text = ""
        last_time = ""
        if last_msg:
            last_text = last_msg.get("message", "")[:60]
            if isinstance(last_msg.get("created_at"), datetime):
                last_time = last_msg["created_at"].isoformat()
            else:
                last_time = str(last_msg.get("created_at", ""))
        
        convos.append({
            "booking_id": b["id"],
            "other_user_id": other_id,
            "other_user_name": other_name,
            "service_id": b.get("service_id", ""),
            "status": b.get("status", ""),
            "last_message": last_text,
            "last_message_time": last_time,
            "unread_count": unread,
            "has_messages": last_msg is not None
        })
    
    # Sort: conversations with messages first, then by unread
    convos.sort(key=lambda c: (not c["has_messages"], -c["unread_count"]))
    
    return {"conversations": convos}

# ============================================================================
# LOCATION / NEARBY
# ============================================================================

@app.get("/api/districts/nearby")
async def get_nearby_districts_api(district: str, radius: int = 80):
    """Get districts near a given district within radius km."""
    nearby = get_nearby_districts(district, max_km=radius)
    return {"district": district, "radius_km": radius, "nearby": nearby}

# Note: /api/handymen/nearby is defined earlier in the file (before /api/handymen/{user_id})
# to ensure proper route matching

# ============================================================================
# CSV IMPORT (Admin / Shop)
# ============================================================================

@app.post("/api/admin/csv-import")
async def csv_import_handymen(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    """Import handymen from CSV. Columns: full_name, email, phone, password, district, services (comma-sep), description, experience_years"""
    if current_user["role"] not in ["admin", "shop"]:
        raise HTTPException(status_code=403, detail="Admin or shop only")

    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files accepted")

    content = await file.read()
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = content.decode("latin-1")

    reader = csv.DictReader(io.StringIO(text))
    results = {"created": 0, "skipped": 0, "errors": []}
    row_num = 0

    for row in reader:
        row_num += 1
        email = (row.get("email") or "").strip().lower()
        full_name = (row.get("full_name") or "").strip()
        phone = (row.get("phone") or "").strip()
        password = (row.get("password") or "").strip() or "topbass123"
        district = (row.get("district") or "Colombo").strip()
        services_raw = (row.get("services") or "").strip()
        description = (row.get("description") or "").strip()
        exp_years = 0
        try:
            exp_years = int(row.get("experience_years") or 0)
        except ValueError:
            pass

        if not email or not full_name:
            results["errors"].append({"row": row_num, "reason": "Missing email or full_name"})
            results["skipped"] += 1
            continue

        existing = await db.users.find_one({"email": email})
        if existing:
            results["errors"].append({"row": row_num, "email": email, "reason": "Email already exists"})
            results["skipped"] += 1
            continue

        user_id = str(uuid.uuid4())
        user_doc = {
            "id": user_id,
            "email": email,
            "hashed_password": get_password_hash(password),
            "full_name": full_name,
            "phone": phone,
            "role": "handyman",
            "district": district,
            "is_approved": current_user["role"] == "admin",
            "created_at": datetime.now(timezone.utc),
            "is_active": True,
        }
        if current_user["role"] == "shop":
            user_doc["shop_id"] = current_user["id"]
            user_doc["shop_name"] = current_user.get("full_name", "")
            user_doc["is_approved"] = current_user.get("is_approved", False)

        await db.users.insert_one(user_doc)

        services_list = [s.strip() for s in services_raw.split(",") if s.strip()] if services_raw else []
        districts_served = [district] if district else []

        profile_doc = {
            "user_id": user_id,
            "full_name": full_name,
            "services": services_list,
            "description": description,
            "experience_years": exp_years,
            "districts_served": districts_served,
            "hourly_rate": 0,
            "phone": phone,
            "whatsapp": "",
            "shop_name": user_doc.get("shop_name", ""),
            "district": district,
            "rating": 0,
            "review_count": 0,
            "jobs_completed": 0,
            "is_approved": user_doc["is_approved"],
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }
        await db.handyman_profiles.insert_one(profile_doc)
        results["created"] += 1

    return {"message": f"Import complete: {results['created']} created, {results['skipped']} skipped", "results": results}

@app.get("/api/admin/csv-template")
async def csv_template():
    """Download a CSV template for handyman import."""
    from fastapi.responses import StreamingResponse
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["full_name", "email", "phone", "password", "district", "services", "description", "experience_years"])
    writer.writerow(["Kamal Silva", "kamal@example.com", "0771234567", "pass123", "Colombo", "plumber,electrician", "Experienced plumber", "5"])
    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode("utf-8")),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=topbass_handyman_template.csv"}
    )

# ============================================================================
# ANALYTICS (Admin)
# ============================================================================

@app.get("/api/admin/analytics")
async def admin_analytics(current_user: dict = Depends(get_current_user)):
    """Advanced analytics: time-series data, top services, top handymen, user growth."""
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    now = datetime.now(timezone.utc)
    thirty_days_ago = now - timedelta(days=30)

    # Bookings by status
    status_pipeline = [
        {"$group": {"_id": "$status", "count": {"$sum": 1}}}
    ]
    status_data = await db.bookings.aggregate(status_pipeline).to_list(20)
    bookings_by_status = {s["_id"]: s["count"] for s in status_data}

    # Bookings per day (last 30 days)
    daily_pipeline = [
        {"$match": {"created_at": {"$gte": thirty_days_ago}}},
        {"$group": {
            "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$created_at"}},
            "count": {"$sum": 1},
            "revenue": {"$sum": {"$ifNull": ["$total", 0]}}
        }},
        {"$sort": {"_id": 1}}
    ]
    daily_data = await db.bookings.aggregate(daily_pipeline).to_list(31)
    bookings_daily = [{"date": d["_id"], "count": d["count"], "revenue": round(d["revenue"], 2)} for d in daily_data]

    # Top services (by booking count)
    service_pipeline = [
        {"$group": {"_id": "$service_id", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 10}
    ]
    service_data = await db.bookings.aggregate(service_pipeline).to_list(10)
    top_services = [{"service_id": s["_id"], "bookings": s["count"]} for s in service_data if s["_id"]]

    # Top handymen (by completed jobs)
    top_handymen_pipeline = [
        {"$match": {"is_approved": True, "jobs_completed": {"$gt": 0}}},
        {"$sort": {"jobs_completed": -1, "rating": -1}},
        {"$limit": 10},
        {"$project": {"_id": 0, "full_name": 1, "user_id": 1, "rating": 1, "jobs_completed": 1, "district": 1, "services": 1}}
    ]
    top_handymen = await db.handyman_profiles.aggregate(top_handymen_pipeline).to_list(10)

    # User registration over time (last 30 days)
    user_growth_pipeline = [
        {"$match": {"created_at": {"$gte": thirty_days_ago}}},
        {"$group": {
            "_id": {
                "date": {"$dateToString": {"format": "%Y-%m-%d", "date": "$created_at"}},
                "role": "$role"
            },
            "count": {"$sum": 1}
        }},
        {"$sort": {"_id.date": 1}}
    ]
    user_growth_data = await db.users.aggregate(user_growth_pipeline).to_list(100)
    user_growth = {}
    for ug in user_growth_data:
        date = ug["_id"]["date"]
        role = ug["_id"]["role"]
        if date not in user_growth:
            user_growth[date] = {"date": date, "customer": 0, "handyman": 0, "shop": 0}
        if role in user_growth[date]:
            user_growth[date][role] = ug["count"]
    user_growth_list = sorted(user_growth.values(), key=lambda x: x["date"])

    # Bookings by district
    district_pipeline = [
        {"$match": {"district": {"$ne": ""}}},
        {"$group": {"_id": "$district", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 10}
    ]
    district_data = await db.bookings.aggregate(district_pipeline).to_list(10)
    bookings_by_district = [{"district": d["_id"], "count": d["count"]} for d in district_data if d["_id"]]

    # Revenue summary
    paid_txns = await db.payment_transactions.find({"payment_status": "paid"}, {"_id": 0, "amount": 1, "topbass_fee": 1, "vat_amount": 1, "job_price": 1}).to_list(1000)
    total_revenue = sum(t.get("amount", 0) for t in paid_txns)
    total_fee = sum(t.get("topbass_fee", 0) for t in paid_txns)

    return {
        "bookings_by_status": bookings_by_status,
        "bookings_daily": bookings_daily,
        "top_services": top_services,
        "top_handymen": top_handymen,
        "user_growth": user_growth_list,
        "bookings_by_district": bookings_by_district,
        "revenue_summary": {
            "total_revenue": round(total_revenue, 2),
            "total_platform_fee": round(total_fee, 2),
            "total_transactions": len(paid_txns)
        },
        "totals": {
            "users": await db.users.count_documents({}),
            "handymen": await db.handyman_profiles.count_documents({"is_approved": True}),
            "bookings": await db.bookings.count_documents({}),
            "reviews": await db.reviews.count_documents({})
        }
    }

# ============================================================================
# PROMO CODES (Admin)
# ============================================================================

@app.post("/api/admin/promo-codes")
async def create_promo_code(data: dict, current_user: dict = Depends(get_current_user)):
    """Admin creates a promo code."""
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    
    code = (data.get("code") or "").strip().upper()
    discount_percent = float(data.get("discount_percent", 0))
    max_uses = int(data.get("max_uses", 100))
    expires_at = data.get("expires_at", "")
    description = data.get("description", "")
    min_order = float(data.get("min_order", 0))
    
    if not code or discount_percent <= 0 or discount_percent > 100:
        raise HTTPException(status_code=400, detail="Invalid code or discount percentage")
    
    existing = await db.promo_codes.find_one({"code": code})
    if existing:
        raise HTTPException(status_code=400, detail="Promo code already exists")
    
    promo = {
        "id": str(uuid.uuid4()),
        "code": code,
        "discount_percent": discount_percent,
        "max_uses": max_uses,
        "used_count": 0,
        "min_order": min_order,
        "description": description,
        "is_active": True,
        "expires_at": expires_at,
        "created_at": datetime.now(timezone.utc),
    }
    await db.promo_codes.insert_one(promo)
    promo.pop("_id", None)
    return {"message": f"Promo code {code} created", "promo": promo}

@app.get("/api/admin/promo-codes")
async def list_promo_codes(current_user: dict = Depends(get_current_user)):
    """List all promo codes."""
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    promos = await db.promo_codes.find({}, {"_id": 0}).sort("created_at", -1).to_list(100)
    return {"promo_codes": promos}

@app.put("/api/admin/promo-codes/{promo_id}/toggle")
async def toggle_promo_code(promo_id: str, current_user: dict = Depends(get_current_user)):
    """Toggle promo code active/inactive."""
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    promo = await db.promo_codes.find_one({"id": promo_id})
    if not promo:
        raise HTTPException(status_code=404, detail="Not found")
    new_status = not promo.get("is_active", True)
    await db.promo_codes.update_one({"id": promo_id}, {"$set": {"is_active": new_status}})
    return {"message": f"Promo code {'activated' if new_status else 'deactivated'}"}

@app.delete("/api/admin/promo-codes/{promo_id}")
async def delete_promo_code(promo_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a promo code."""
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    await db.promo_codes.delete_one({"id": promo_id})
    return {"message": "Promo code deleted"}

@app.post("/api/promo/validate")
async def validate_promo_code(data: dict, current_user: dict = Depends(get_current_user)):
    """Validate a promo code and return discount details."""
    code = (data.get("code") or "").strip().upper()
    booking_total = float(data.get("total", 0))
    
    promo = await db.promo_codes.find_one({"code": code, "is_active": True})
    if not promo:
        raise HTTPException(status_code=400, detail="Invalid or expired promo code")
    
    if promo["used_count"] >= promo["max_uses"]:
        raise HTTPException(status_code=400, detail="Promo code usage limit reached")
    
    if promo.get("expires_at"):
        try:
            exp = datetime.fromisoformat(promo["expires_at"].replace("Z", "+00:00"))
            if datetime.now(timezone.utc) > exp:
                raise HTTPException(status_code=400, detail="Promo code has expired")
        except (ValueError, TypeError):
            pass
    
    if booking_total > 0 and promo.get("min_order", 0) > 0 and booking_total < promo["min_order"]:
        raise HTTPException(status_code=400, detail=f"Minimum order LKR {promo['min_order']} required")
    
    # Check if user already used this code
    used = await db.promo_usages.find_one({"user_id": current_user["id"], "code": code})
    if used:
        raise HTTPException(status_code=400, detail="You have already used this promo code")
    
    discount_amount = round(booking_total * promo["discount_percent"] / 100, 2) if booking_total > 0 else 0
    
    return {
        "valid": True,
        "code": code,
        "discount_percent": promo["discount_percent"],
        "discount_amount": discount_amount,
        "description": promo.get("description", ""),
        "new_total": round(booking_total - discount_amount, 2)
    }

@app.post("/api/promo/apply")
async def apply_promo_code(data: dict, current_user: dict = Depends(get_current_user)):
    """Apply a promo code to a booking — reduces the total."""
    code = (data.get("code") or "").strip().upper()
    booking_id = data.get("booking_id")
    
    booking = await db.bookings.find_one({"id": booking_id})
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking["customer_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not your booking")
    if not booking.get("total"):
        raise HTTPException(status_code=400, detail="No quote on this booking yet")
    if booking.get("promo_applied"):
        raise HTTPException(status_code=400, detail="A promo code is already applied")
    
    promo = await db.promo_codes.find_one({"code": code, "is_active": True})
    if not promo:
        raise HTTPException(status_code=400, detail="Invalid or expired promo code")
    if promo["used_count"] >= promo["max_uses"]:
        raise HTTPException(status_code=400, detail="Promo code usage limit reached")
    
    used = await db.promo_usages.find_one({"user_id": current_user["id"], "code": code})
    if used:
        raise HTTPException(status_code=400, detail="You have already used this promo code")
    
    original_total = float(booking["total"])
    discount_amount = round(original_total * promo["discount_percent"] / 100, 2)
    new_total = round(original_total - discount_amount, 2)
    
    await db.bookings.update_one({"id": booking_id}, {"$set": {
        "promo_code": code,
        "promo_discount_percent": promo["discount_percent"],
        "promo_discount_amount": discount_amount,
        "original_total": original_total,
        "total": new_total,
        "promo_applied": True,
        "updated_at": datetime.now(timezone.utc)
    }})
    
    await db.promo_codes.update_one({"code": code}, {"$inc": {"used_count": 1}})
    await db.promo_usages.insert_one({
        "id": str(uuid.uuid4()),
        "user_id": current_user["id"],
        "code": code,
        "booking_id": booking_id,
        "discount_amount": discount_amount,
        "created_at": datetime.now(timezone.utc)
    })
    
    return {
        "message": f"Promo code {code} applied! You saved LKR {discount_amount:.2f}",
        "discount_amount": discount_amount,
        "original_total": original_total,
        "new_total": new_total
    }

# ============================================================================
# API ROOT
# ============================================================================

@app.get("/api/")
async def root():
    return {
        "name": "TopBass API",
        "version": "1.0.0",
        "status": "operational",
        "tagline": "Find trusted handymen across Sri Lanka"
    }

# ============================================================================
# STARTUP
# ============================================================================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8001))
    uvicorn.run(app, host="0.0.0.0", port=port)
