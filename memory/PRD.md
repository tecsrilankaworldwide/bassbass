# TopBass - Handyman Service Marketplace PRD

## Original Problem Statement
Build a handyman service marketplace called "TopBass" for Sri Lanka. A trusted service of TEC SRI LANKA WORLDWIDE (PVT.) LTD.

## Tech Stack
- Frontend: React + Tailwind CSS + i18next + Recharts
- Backend: FastAPI (Python) + MongoDB
- Payments: Stripe + Bank of Ceylon QR + COD + PayHere (pending)
- SMS: Twilio (pending credentials)

## Implemented Features

### Core (Phase 1-3)
- [x] 20 service categories, 25 districts, 3 languages
- [x] Auth, Booking/Quoting, Search, Top-rated, Shop management
- [x] Billing (10% fee + 18.5% VAT), Stripe payments
- [x] In-app chat, Notifications, Admin dashboard

### Phase 4-5: Location, CSV, Analytics, Payments
- [x] Geolocation, CSV import, Analytics charts
- [x] COD + Bank of Ceylon QR + Stripe (3 payment options)
- [x] Demo data + Overview page

### Phase 6-7: Business Protection & Referrals
- [x] Phone masking, WhatsApp profile sharing
- [x] Referral system with tiered badges (Bronze/Silver/Gold/Platinum)

### Phase 8: Promo Codes
- [x] Admin CRUD for promo codes, customer applies at booking

### Phase 9: SMS Notifications (Feb 2026)
- [x] Twilio integration with graceful fallback (code ready, needs credentials)
- [x] SMS sent for: new bookings, quotes, status changes, payments, referrals
- [x] Admin SMS tab: status, event list, test SMS, setup guide
- [x] notify_with_sms() helper sends both in-app + SMS notifications
- [x] Sri Lankan phone number normalization (07X → +947X)

## Demo Accounts
- Admin: admin@bassbass.lk / admin123
- Customer: saman@demo.lk / demo123
- Handyman: nimal@topbass.lk / demo123

## Pending Credentials
- PayHere: PAYHERE_MERCHANT_ID, PAYHERE_MERCHANT_SECRET
- Twilio: TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER

## Remaining Tasks
### P1
- [ ] PayHere activation (Monday with staff)
- [ ] Twilio activation (when user gets account)
### P2
- [ ] i18n translations for new features
- [ ] Refactor server.py into modules
