# TopBass - Handyman Service Marketplace PRD

## Original Problem Statement
Finish the TopBass handyman service marketplace app from https://github.com/tecsrilankaworldwide/bassbass with a "teen pacific academic color palette" design theme.

## App Description
TopBass is a service marketplace connecting customers with trusted handymen across Sri Lanka. A trusted service of TEC SRI LANKA WORLDWIDE (PVT.) LTD.

## Tech Stack
- **Frontend**: React 18 + Tailwind CSS + i18next + Recharts
- **Backend**: FastAPI (Python) + MongoDB Atlas
- **Payments**: Stripe + Bank of Ceylon QR + COD
- **SMS**: Twilio (code ready, needs credentials)

## User Personas
1. **Customer**: Homeowners/businesses needing handyman services
2. **Handyman**: Service providers (plumbers, electricians, carpenters, etc.)
3. **Shop Owner**: Manages multiple handymen under one business
4. **Admin**: Platform administrator managing approvals and operations

## Core Features (Implemented)

### Phase 1-3: Foundation
- [x] 20 service categories (plumber, electrician, mason, carpenter, painter, tiler, AC repair, cleaner, mover, CCTV, welder, landscaping, vehicle repair, pest control, solar, curtains, aluminium, ceiling, other, all-round man)
- [x] 25 Sri Lankan districts with geolocation
- [x] 3 languages (Sinhala, Tamil, English)
- [x] User authentication (JWT)
- [x] Booking/Quoting system
- [x] Search & filtering
- [x] Top-rated handymen display
- [x] Shop management for businesses

### Phase 4-5: Advanced Features
- [x] Geolocation with nearby handymen
- [x] CSV import for bulk data
- [x] Analytics dashboard
- [x] Multiple payment options (Stripe, COD, Bank QR)
- [x] Demo data seeding

### Phase 6-7: Business Protection
- [x] Phone number masking until booking confirmed
- [x] WhatsApp profile sharing
- [x] Referral system with tiered badges (Bronze/Silver/Gold/Platinum)

### Phase 8: Marketing
- [x] Promo codes (admin CRUD, customer apply)

### Phase 9: Communications
- [x] Twilio SMS integration (code ready)
- [x] In-app notifications
- [x] Chat messaging system

### Phase 10: Design Refresh (Jan 2026)
- [x] Teen Pacific Academic color palette
  - Academic Navy (#0B2545) - Primary, headings
  - Sunset Coral (#F05A4A) - CTAs, accents
  - Pacific Pearl (#FAF9F6) - Background
  - Pacific Blue (#133C55) - Secondary
- [x] New fonts: Outfit (headings), DM Sans (body)
- [x] Glassmorphism navbar
- [x] Updated components (buttons, cards, badges)

## Test Credentials
- **Admin**: admin@bassbass.lk / admin123
- **Demo Customer**: saman@demo.lk / demo123
- **Demo Handyman**: nimal@topbass.lk / demo123

## API Endpoints
- `POST /api/auth/register` - Register user
- `POST /api/auth/login` - Login user
- `GET /api/services` - List service categories
- `GET /api/handymen` - Search handymen
- `GET /api/handymen/nearby` - Find nearby handymen
- `POST /api/bookings/create` - Create booking
- `PUT /api/bookings/{id}/quote` - Set price quote
- `POST /api/payments/create-checkout` - Stripe checkout
- `GET /api/admin/statistics` - Admin stats

## Remaining Tasks

### P1 (High Priority)
- [ ] PayHere integration (waiting for credentials)
- [ ] Twilio activation (waiting for credentials)

### P2 (Medium Priority)
- [ ] Complete i18n translations for new features
- [ ] Refactor server.py into modules

### Future Enhancements
- [ ] Push notifications (mobile)
- [ ] In-app ratings prompts
- [ ] Recurring booking support
- [ ] Invoice generation

## Latest Update: Jan 29, 2026
- Applied Teen Pacific Academic design theme
- All 20 service categories working
- Search, login, admin dashboard tested
- 100% test pass rate
