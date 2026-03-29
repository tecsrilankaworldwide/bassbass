import React from 'react';
import { Link } from 'react-router-dom';
import Navbar from '../components/Navbar';
import { Search, MapPin, CreditCard, MessageSquare, Bell, BarChart3, Users, Shield, Star, QrCode, Banknote, Upload, Navigation, Globe, ChevronRight } from 'lucide-react';

const LOGO_URL = "https://static.prod-images.emergentagent.com/jobs/3de36ae8-1b12-4467-87dd-98c4995672e0/images/9167dec89e86661796db50a2e4e59dc94289569e89106c1eb1910007d02d8f3f.png";

const features = [
  {
    icon: Search, title: "Smart Search", color: "bg-green-600",
    desc: "Find handymen by name, skill, or service category. Filter by district for local results."
  },
  {
    icon: MapPin, title: "Location-Based Discovery", color: "bg-orange-500",
    desc: "Automatic proximity matching across 25 Sri Lankan districts using geolocation technology."
  },
  {
    icon: Star, title: "Ratings & Reviews", color: "bg-amber-500",
    desc: "Verified customer reviews and star ratings. Top-rated handymen highlighted on the homepage."
  },
  {
    icon: CreditCard, title: "Multiple Payment Options", color: "bg-blue-600",
    desc: "Stripe (Visa/MC), Bank of Ceylon QR transfers, and Cash on Delivery. Flexible for every customer."
  },
  {
    icon: MessageSquare, title: "In-App Chat", color: "bg-purple-600",
    desc: "Real-time messaging between customers and handymen. Discuss job details before and during work."
  },
  {
    icon: Bell, title: "Smart Notifications", color: "bg-red-500",
    desc: "Instant alerts for new bookings, quotes, payments, and messages. Never miss an update."
  },
  {
    icon: BarChart3, title: "Analytics Dashboard", color: "bg-cyan-600",
    desc: "Admin analytics with charts — bookings, revenue, top services, user growth, and district activity."
  },
  {
    icon: Upload, title: "Bulk Onboarding", color: "bg-emerald-600",
    desc: "CSV import for registering multiple handymen at once. Perfect for shops and agencies."
  },
  {
    icon: Shield, title: "Admin Controls", color: "bg-gray-700",
    desc: "Approve/reject handymen, verify bank payments, manage users, and track all accounting."
  },
  {
    icon: Globe, title: "Multi-Language", color: "bg-indigo-600",
    desc: "Full support for English, Sinhala, and Tamil. Serve all communities across Sri Lanka."
  },
  {
    icon: Users, title: "Shop Management", color: "bg-teal-600",
    desc: "Shop owners can manage their team of handymen — add, remove, and track performance."
  },
  {
    icon: QrCode, title: "Bank QR Payments", color: "bg-green-700",
    desc: "Bank of Ceylon Nugegoda — No charges for transfers below LKR 5,000. Split payments supported."
  },
];

const serviceCategories = [
  "Plumbers", "Electricians", "Masons", "Carpenters", "Painters", "Tilers",
  "A/C Repair", "Cleaners", "Movers", "CCTV", "Welding", "Landscaping",
  "Vehicle Repair", "Pest Control", "Solar Panel", "Curtains", "Aluminium",
  "Ceiling", "Other Services", "All Round Man"
];

const billingSteps = [
  { label: "Job Price", example: "LKR 10,000", desc: "Handyman quotes a price" },
  { label: "+ TopBass Fee (10%)", example: "LKR 1,000", desc: "Platform commission" },
  { label: "= Service Charge", example: "LKR 11,000", desc: "Subtotal" },
  { label: "+ VAT (18.5%)", example: "LKR 2,035", desc: "Government tax" },
  { label: "= Customer Total", example: "LKR 13,035", desc: "Final amount" },
];

const OverviewPage = () => {
  return (
    <div className="min-h-screen bg-[#F5F7F3]">
      <Navbar />

      {/* Hero */}
      <div className="bg-gradient-to-b from-green-50 to-[#F5F7F3] py-12 px-4">
        <div className="max-w-4xl mx-auto text-center">
          <img src={LOGO_URL} alt="TopBass" className="w-36 h-36 mx-auto mb-4 object-contain" />
          <h1 className="text-4xl sm:text-5xl font-extrabold text-gray-900 mb-3" style={{fontFamily:'Manrope,sans-serif'}}>
            TopBass
          </h1>
          <p className="text-sm text-gray-500 tracking-wide mb-2">A TRUSTED SERVICE OF TEC SRI LANKA WORLDWIDE (PVT.) LTD</p>
          <p className="text-lg text-gray-600 max-w-xl mx-auto mb-8">
            Sri Lanka's premier handyman service marketplace. Connecting customers with trusted, verified professionals across all 25 districts.
          </p>
          <div className="flex items-center justify-center gap-4 flex-wrap">
            <Link to="/" className="px-8 py-3 bg-green-600 text-white font-bold rounded-xl hover:bg-green-700 transition-colors shadow-lg" data-testid="explore-app-btn">
              Explore the App
            </Link>
            <Link to="/login" className="px-8 py-3 bg-white text-green-700 font-bold rounded-xl hover:bg-green-50 transition-colors border-2 border-green-200" data-testid="login-btn">
              Login / Register
            </Link>
          </div>
        </div>
      </div>

      {/* Key Numbers */}
      <div className="max-w-4xl mx-auto px-4 py-10">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[
            { num: "20", label: "Service Categories", color: "text-green-600" },
            { num: "25", label: "Districts Covered", color: "text-orange-500" },
            { num: "3", label: "Languages", color: "text-blue-600" },
            { num: "3", label: "Payment Methods", color: "text-purple-600" },
          ].map((s, i) => (
            <div key={i} className="bg-white rounded-2xl p-5 text-center border border-gray-100 shadow-sm">
              <div className={`text-4xl font-extrabold ${s.color}`} style={{fontFamily:'Manrope,sans-serif'}}>{s.num}</div>
              <div className="text-sm font-semibold text-gray-600 mt-1">{s.label}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Platform Features */}
      <div className="bg-white py-12 px-4 border-t border-gray-100">
        <div className="max-w-5xl mx-auto">
          <h2 className="text-2xl font-extrabold text-gray-900 text-center mb-2" style={{fontFamily:'Manrope,sans-serif'}}>
            Platform Features
          </h2>
          <p className="text-sm text-gray-500 text-center mb-10">Everything you need to run a world-class service marketplace</p>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
            {features.map((f, i) => (
              <div key={i} className="rounded-xl p-5 border border-gray-100 hover:border-green-300 hover:shadow-md transition-all bg-[#F5F7F3]" data-testid={`feature-${i}`}>
                <div className={`w-10 h-10 ${f.color} rounded-lg flex items-center justify-center mb-3`}>
                  <f.icon className="w-5 h-5 text-white" />
                </div>
                <h3 className="font-bold text-gray-900 mb-1">{f.title}</h3>
                <p className="text-xs text-gray-500 leading-relaxed">{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* 20 Service Categories */}
      <div className="max-w-5xl mx-auto px-4 py-12">
        <h2 className="text-2xl font-extrabold text-gray-900 text-center mb-2" style={{fontFamily:'Manrope,sans-serif'}}>
          20 Service Categories
        </h2>
        <p className="text-sm text-gray-500 text-center mb-8">Each with custom-designed silhouette icons</p>
        <div className="flex flex-wrap justify-center gap-2">
          {serviceCategories.map((s, i) => (
            <span key={i} className="px-3 py-1.5 bg-white rounded-full text-xs font-semibold text-gray-700 border border-gray-200">{s}</span>
          ))}
        </div>
      </div>

      {/* How Billing Works */}
      <div className="bg-white py-12 px-4 border-t border-gray-100">
        <div className="max-w-3xl mx-auto">
          <h2 className="text-2xl font-extrabold text-gray-900 text-center mb-2" style={{fontFamily:'Manrope,sans-serif'}}>
            Transparent Billing
          </h2>
          <p className="text-sm text-gray-500 text-center mb-8">Clear breakdown — customers see exactly what they pay</p>
          <div className="space-y-3">
            {billingSteps.map((step, i) => (
              <div key={i} className={`flex items-center justify-between p-4 rounded-xl ${i === billingSteps.length - 1 ? 'bg-green-50 border-2 border-green-300' : 'bg-gray-50 border border-gray-100'}`}>
                <div>
                  <p className={`text-sm font-bold ${i === billingSteps.length - 1 ? 'text-green-700' : 'text-gray-800'}`}>{step.label}</p>
                  <p className="text-xs text-gray-500">{step.desc}</p>
                </div>
                <span className={`text-sm font-extrabold ${i === billingSteps.length - 1 ? 'text-green-700' : 'text-gray-900'}`} style={{fontFamily:'Manrope,sans-serif'}}>{step.example}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Payment Methods */}
      <div className="max-w-4xl mx-auto px-4 py-12">
        <h2 className="text-2xl font-extrabold text-gray-900 text-center mb-8" style={{fontFamily:'Manrope,sans-serif'}}>
          Payment Methods
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          <div className="bg-white rounded-2xl p-6 border border-gray-100 shadow-sm text-center">
            <div className="w-14 h-14 bg-blue-50 rounded-xl flex items-center justify-center mx-auto mb-3">
              <CreditCard className="w-7 h-7 text-blue-600" />
            </div>
            <h3 className="font-bold text-gray-900 mb-1">Stripe (Cards)</h3>
            <p className="text-xs text-gray-500">Visa, Mastercard, and international cards. Secure checkout powered by Stripe.</p>
          </div>
          <div className="bg-white rounded-2xl p-6 border border-gray-100 shadow-sm text-center">
            <div className="w-14 h-14 bg-green-50 rounded-xl flex items-center justify-center mx-auto mb-3">
              <QrCode className="w-7 h-7 text-green-600" />
            </div>
            <h3 className="font-bold text-gray-900 mb-1">Bank of Ceylon QR</h3>
            <p className="text-xs text-gray-500">Scan and pay from any bank app. No charges below LKR 5,000. Nugegoda Super Branch.</p>
          </div>
          <div className="bg-white rounded-2xl p-6 border border-gray-100 shadow-sm text-center">
            <div className="w-14 h-14 bg-orange-50 rounded-xl flex items-center justify-center mx-auto mb-3">
              <Banknote className="w-7 h-7 text-orange-600" />
            </div>
            <h3 className="font-bold text-gray-900 mb-1">Cash on Delivery</h3>
            <p className="text-xs text-gray-500">Pay the handyman directly when the job is completed. Simple and trusted.</p>
          </div>
        </div>
      </div>

      {/* User Roles */}
      <div className="bg-white py-12 px-4 border-t border-gray-100">
        <div className="max-w-4xl mx-auto">
          <h2 className="text-2xl font-extrabold text-gray-900 text-center mb-8" style={{fontFamily:'Manrope,sans-serif'}}>
            User Roles
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            {[
              { role: "Customer", color: "border-blue-300 bg-blue-50", items: ["Browse 20 service categories", "Book handymen by district", "Chat with handymen", "Pay via Stripe, Bank QR, or Cash", "Rate and review after job completion"] },
              { role: "Handyman", color: "border-green-300 bg-green-50", items: ["Create professional profile", "Receive booking requests", "Quote prices for jobs", "Chat with customers", "Track completed jobs and earnings"] },
              { role: "Shop Owner", color: "border-orange-300 bg-orange-50", items: ["Manage team of handymen", "Add/remove workers", "Bulk import via CSV", "Track shop performance", "All handyman features included"] },
              { role: "Admin", color: "border-red-300 bg-red-50", items: ["Approve/reject handymen", "Full analytics dashboard", "Revenue & accounting reports", "Verify bank payments", "Manage all users and payouts"] },
            ].map((r, i) => (
              <div key={i} className={`rounded-2xl p-5 border-2 ${r.color}`}>
                <h3 className="font-bold text-gray-900 text-lg mb-3">{r.role}</h3>
                <ul className="space-y-1.5">
                  {r.items.map((item, j) => (
                    <li key={j} className="flex items-center gap-2 text-sm text-gray-700">
                      <ChevronRight className="w-3 h-3 text-green-500 flex-shrink-0" />{item}
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* How it Works */}
      <div className="max-w-4xl mx-auto px-4 py-12">
        <h2 className="text-2xl font-extrabold text-gray-900 text-center mb-8" style={{fontFamily:'Manrope,sans-serif'}}>
          How It Works
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {[
            { num: "1", title: "Find", desc: "Search by service or browse categories. Filter by your district.", color: "bg-green-600" },
            { num: "2", title: "Book", desc: "Send a booking request with job details, date, and location.", color: "bg-orange-500" },
            { num: "3", title: "Pay", desc: "Handyman quotes a price. Pay by card, bank QR, or cash.", color: "bg-blue-600" },
            { num: "4", title: "Review", desc: "Rate and review after the job. Help others find great handymen.", color: "bg-purple-600" },
          ].map(step => (
            <div key={step.num} className="text-center">
              <div className={`w-14 h-14 ${step.color} rounded-full flex items-center justify-center mx-auto mb-3 text-white text-2xl font-bold shadow-lg`}>{step.num}</div>
              <h3 className="font-bold text-gray-800 mb-1">{step.title}</h3>
              <p className="text-xs text-gray-500">{step.desc}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Demo Accounts */}
      <div className="bg-green-900 py-10 px-4">
        <div className="max-w-3xl mx-auto text-center">
          <h2 className="text-2xl font-extrabold text-white mb-2" style={{fontFamily:'Manrope,sans-serif'}}>Demo Accounts</h2>
          <p className="text-green-300 text-sm mb-6">Use these to explore the platform</p>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="bg-green-800/50 rounded-xl p-4 border border-green-700">
              <p className="text-orange-400 font-bold text-sm mb-1">Admin</p>
              <p className="text-green-200 text-xs">admin@bassbass.lk</p>
              <p className="text-green-300 text-xs">Password: admin123</p>
            </div>
            <div className="bg-green-800/50 rounded-xl p-4 border border-green-700">
              <p className="text-orange-400 font-bold text-sm mb-1">Customer</p>
              <p className="text-green-200 text-xs">saman@demo.lk</p>
              <p className="text-green-300 text-xs">Password: demo123</p>
            </div>
            <div className="bg-green-800/50 rounded-xl p-4 border border-green-700">
              <p className="text-orange-400 font-bold text-sm mb-1">Handyman</p>
              <p className="text-green-200 text-xs">nimal@topbass.lk</p>
              <p className="text-green-300 text-xs">Password: demo123</p>
            </div>
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="bg-green-950 text-green-200 py-8 px-4 text-center">
        <img src={LOGO_URL} alt="TopBass" className="w-20 h-20 mx-auto mb-3 object-contain" />
        <p className="font-bold text-orange-400 text-lg mb-1">TopBass</p>
        <p className="text-xs text-green-400 mb-4">A TRUSTED SERVICE OF TEC SRI LANKA WORLDWIDE (PVT.) LTD</p>
        <p className="text-xs text-green-500">Built with care for the people of Sri Lanka</p>
      </footer>
    </div>
  );
};

export default OverviewPage;
