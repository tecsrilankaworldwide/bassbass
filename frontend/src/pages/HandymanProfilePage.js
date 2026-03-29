import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useAuth, API } from '../AuthContext';
import Navbar from '../components/Navbar';
import axios from 'axios';
import { Save, MapPin, Clock, Briefcase, Phone, MessageSquare, CheckCircle, Gift, Share2, Copy, Users } from 'lucide-react';

const HandymanProfilePage = () => {
  const { t, i18n } = useTranslation();
  const { user, token } = useAuth();
  const [services, setServices] = useState([]);
  const [districts, setDistricts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [referral, setReferral] = useState(null);
  const [copied, setCopied] = useState(false);
  const lang = i18n.language;

  const [form, setForm] = useState({
    services: [],
    description: '',
    experience_years: 0,
    districts_served: [],
    hourly_rate: 0,
    phone: '',
    whatsapp: '',
    shop_name: '',
  });

  const headers = { Authorization: `Bearer ${token}` };

  useEffect(() => {
    Promise.all([
      axios.get(`${API}/services`),
      axios.get(`${API}/handyman/my-profile`, { headers }),
      axios.get(`${API}/referral/stats`, { headers }).catch(() => ({ data: null }))
    ]).then(([sRes, pRes, rRes]) => {
      setServices(sRes.data.services);
      setDistricts(sRes.data.districts);
      if (pRes.data.profile) {
        setForm({
          services: pRes.data.profile.services || [],
          description: pRes.data.profile.description || '',
          experience_years: pRes.data.profile.experience_years || 0,
          districts_served: pRes.data.profile.districts_served || [],
          hourly_rate: pRes.data.profile.hourly_rate || 0,
          phone: pRes.data.profile.phone || '',
          whatsapp: pRes.data.profile.whatsapp || '',
          shop_name: pRes.data.profile.shop_name || '',
        });
      }
      if (rRes.data) setReferral(rRes.data);
    }).catch(console.error).finally(() => setLoading(false));
  }, []);

  const getServiceName = (s) => {
    if (lang === 'si') return s.name_si;
    if (lang === 'ta') return s.name_ta;
    return s.name_en;
  };

  const toggleService = (id) => {
    setForm(f => ({
      ...f,
      services: f.services.includes(id) ? f.services.filter(s => s !== id) : [...f.services, id]
    }));
  };

  const toggleDistrict = (d) => {
    setForm(f => ({
      ...f,
      districts_served: f.districts_served.includes(d) ? f.districts_served.filter(x => x !== d) : [...f.districts_served, d]
    }));
  };

  const handleSave = async (e) => {
    e.preventDefault();
    setSaving(true);
    setSaved(false);
    try {
      await axios.post(`${API}/handyman/profile`, form, { headers });
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch (err) {
      alert(err.response?.data?.detail || 'Save failed');
    } finally { setSaving(false); }
  };

  const referralLink = referral ? `${window.location.origin}/register?ref=${referral.referral_code}` : '';

  const copyCode = () => {
    navigator.clipboard.writeText(referral.referral_code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const shareReferralWhatsApp = () => {
    const text = `Join TopBass - Sri Lanka's trusted handyman marketplace! Use my referral code: ${referral.referral_code}\n\nRegister here: ${referralLink}`;
    window.open(`https://wa.me/?text=${encodeURIComponent(text)}`, '_blank');
  };

  if (loading) return (
    <div className="min-h-screen bg-[#F5F7F3]">
      <Navbar />
      <div className="flex justify-center py-20"><div className="animate-spin rounded-full h-10 w-10 border-4 border-green-500 border-t-transparent"></div></div>
    </div>
  );

  return (
    <div className="min-h-screen bg-[#F5F7F3]">
      <Navbar />
      <div className="max-w-2xl mx-auto px-4 py-6">
        <h1 className="text-2xl font-extrabold text-gray-900 mb-1" style={{fontFamily:'Manrope,sans-serif'}} data-testid="profile-title">{t('nav.profile')}</h1>
        <p className="text-sm text-gray-500 mb-6">{user?.full_name} &middot; {user?.email}</p>

        {!user?.is_approved && (
          <div className="bg-green-50 border border-green-200 text-green-700 text-sm px-4 py-3 rounded-xl mb-4" data-testid="pending-approval">
            Your account is pending admin approval. Your profile won't be visible to customers until approved.
          </div>
        )}

        {/* Referral Section */}
        {referral && (
          <div className="bg-white rounded-2xl p-5 border border-gray-100 shadow-sm mb-5" data-testid="referral-section">
            <div className="flex items-center gap-2 mb-3">
              <div className="w-8 h-8 bg-orange-500 rounded-lg flex items-center justify-center">
                <Gift className="w-4 h-4 text-white" />
              </div>
              <h2 className="text-sm font-bold text-gray-800">Referral Program</h2>
            </div>

            <div className="grid grid-cols-3 gap-3 mb-4">
              <div className="bg-green-50 rounded-xl p-3 text-center">
                <div className="text-xl font-extrabold text-green-600" style={{fontFamily:'Manrope,sans-serif'}}>{referral.referral_count}</div>
                <div className="text-xs text-gray-500 font-semibold">Referrals</div>
              </div>
              <div className="bg-orange-50 rounded-xl p-3 text-center">
                <div className="text-xl font-extrabold text-orange-600" style={{fontFamily:'Manrope,sans-serif'}}>LKR {referral.referral_credits}</div>
                <div className="text-xs text-gray-500 font-semibold">Credits Earned</div>
              </div>
              <div className={`rounded-xl p-3 text-center ${
                referral.partner_tier?.tier === 'platinum' ? 'bg-gray-900' :
                referral.partner_tier?.tier === 'gold' ? 'bg-amber-50' :
                referral.partner_tier?.tier === 'silver' ? 'bg-gray-100' : 'bg-blue-50'
              }`}>
                <div className={`text-xl font-extrabold ${
                  referral.partner_tier?.tier === 'platinum' ? 'text-white' :
                  referral.partner_tier?.tier === 'gold' ? 'text-amber-600' :
                  referral.partner_tier?.tier === 'silver' ? 'text-gray-700' : 'text-blue-600'
                }`} style={{fontFamily:'Manrope,sans-serif'}}>{referral.partner_tier?.label || 'Bronze'}</div>
                <div className={`text-xs font-semibold ${referral.partner_tier?.tier === 'platinum' ? 'text-gray-400' : 'text-gray-500'}`}>Your Tier</div>
              </div>
            </div>

            {/* Tier Progress */}
            {referral.tiers && (
              <div className="flex items-center gap-1 mb-4">
                {referral.tiers.slice().reverse().map((t, i) => {
                  const active = referral.referral_count >= t.min;
                  return (
                    <div key={t.tier} className="flex-1">
                      <div className={`h-1.5 rounded-full ${active ? (
                        t.tier === 'platinum' ? 'bg-gray-900' :
                        t.tier === 'gold' ? 'bg-amber-400' :
                        t.tier === 'silver' ? 'bg-gray-400' : 'bg-green-400'
                      ) : 'bg-gray-200'}`}></div>
                      <div className={`text-[10px] mt-1 font-semibold text-center ${active ? 'text-gray-700' : 'text-gray-400'}`}>{t.label.split(' ')[0]} ({t.min}+)</div>
                    </div>
                  );
                })}
              </div>
            )}

            <div className="flex items-center gap-2 mb-3">
              <div className="flex-1 bg-gray-50 border-2 border-dashed border-gray-300 rounded-xl px-4 py-2.5 text-center">
                <span className="text-lg font-extrabold text-gray-900 tracking-wider" style={{fontFamily:'Manrope,sans-serif'}} data-testid="referral-code">{referral.referral_code}</span>
              </div>
              <button onClick={copyCode}
                className={`px-3 py-2.5 rounded-xl text-xs font-semibold transition-all ${copied ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'}`}
                data-testid="copy-code-btn">
                <Copy className="w-4 h-4" />
              </button>
            </div>

            <div className="flex gap-2">
              <button onClick={shareReferralWhatsApp}
                className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 bg-[#25D366] text-white font-semibold rounded-xl hover:bg-[#1da851] text-sm"
                data-testid="share-referral-whatsapp">
                <Share2 className="w-4 h-4" />Share on WhatsApp
              </button>
              <button onClick={() => { navigator.clipboard.writeText(referralLink); }}
                className="flex items-center justify-center gap-2 px-4 py-2.5 bg-gray-100 text-gray-700 font-semibold rounded-xl hover:bg-gray-200 text-sm"
                data-testid="copy-link-btn">
                <Copy className="w-4 h-4" />Copy Link
              </button>
            </div>

            {referral.referrals?.length > 0 && (
              <div className="mt-4">
                <h3 className="text-xs font-semibold text-gray-500 mb-2">Recent Referrals</h3>
                <div className="space-y-1.5 max-h-32 overflow-y-auto">
                  {referral.referrals.map(r => (
                    <div key={r.id} className="flex items-center justify-between text-xs bg-gray-50 rounded-lg px-3 py-2">
                      <div className="flex items-center gap-2">
                        <Users className="w-3 h-3 text-gray-400" />
                        <span className="font-semibold text-gray-700">{r.referred_name}</span>
                        <span className="text-gray-400">{r.referred_role}</span>
                      </div>
                      <span className="text-green-600 font-bold">+LKR {r.credit_amount}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        <form onSubmit={handleSave} className="space-y-5">
          {/* Services */}
          <div className="bg-white rounded-2xl p-5 border border-gray-100 shadow-sm">
            <h2 className="text-sm font-bold text-gray-800 mb-3">{t('nav.services')} *</h2>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2" data-testid="service-selector">
              {services.map(s => (
                <button key={s.id} type="button" onClick={() => toggleService(s.id)}
                  className={`p-2.5 rounded-xl text-xs font-semibold border-2 transition-all text-left ${
                    form.services.includes(s.id)
                      ? 'border-green-500 bg-green-50 text-green-700'
                      : 'border-gray-200 text-gray-600 hover:border-gray-300'
                  }`} data-testid={`svc-${s.id}`}>
                  {getServiceName(s)}
                </button>
              ))}
            </div>
          </div>

          {/* Districts */}
          <div className="bg-white rounded-2xl p-5 border border-gray-100 shadow-sm">
            <h2 className="text-sm font-bold text-gray-800 mb-3 flex items-center gap-1.5"><MapPin className="w-4 h-4 text-amber-500" />Districts Served *</h2>
            <div className="grid grid-cols-3 sm:grid-cols-4 gap-2" data-testid="district-selector">
              {districts.map(d => (
                <button key={d} type="button" onClick={() => toggleDistrict(d)}
                  className={`p-2 rounded-lg text-xs font-semibold border-2 transition-all ${
                    form.districts_served.includes(d)
                      ? 'border-green-500 bg-green-50 text-green-700'
                      : 'border-gray-200 text-gray-600 hover:border-gray-300'
                  }`} data-testid={`dist-${d}`}>
                  {d}
                </button>
              ))}
            </div>
          </div>

          {/* Details */}
          <div className="bg-white rounded-2xl p-5 border border-gray-100 shadow-sm space-y-4">
            <h2 className="text-sm font-bold text-gray-800 mb-1">Details</h2>
            <div>
              <label className="block text-xs font-semibold text-gray-600 mb-1">Description / Bio</label>
              <textarea value={form.description} onChange={(e) => setForm(f => ({...f, description: e.target.value}))}
                className="w-full px-3 py-2 border-2 border-gray-200 rounded-xl text-sm focus:border-green-500 outline-none" rows="3"
                placeholder="Tell customers about your skills and experience..." data-testid="profile-description" />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-semibold text-gray-600 mb-1 flex items-center gap-1"><Clock className="w-3 h-3" />Experience (years)</label>
                <input type="number" min="0" value={form.experience_years} onChange={(e) => setForm(f => ({...f, experience_years: parseInt(e.target.value) || 0}))}
                  className="w-full px-3 py-2 border-2 border-gray-200 rounded-xl text-sm focus:border-green-500 outline-none" data-testid="profile-experience" />
              </div>
              <div>
                <label className="block text-xs font-semibold text-gray-600 mb-1">Hourly Rate (LKR)</label>
                <input type="number" min="0" value={form.hourly_rate} onChange={(e) => setForm(f => ({...f, hourly_rate: parseFloat(e.target.value) || 0}))}
                  className="w-full px-3 py-2 border-2 border-gray-200 rounded-xl text-sm focus:border-green-500 outline-none" data-testid="profile-rate" />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-semibold text-gray-600 mb-1 flex items-center gap-1"><Phone className="w-3 h-3" />Phone</label>
                <input type="tel" value={form.phone} onChange={(e) => setForm(f => ({...f, phone: e.target.value}))}
                  className="w-full px-3 py-2 border-2 border-gray-200 rounded-xl text-sm focus:border-green-500 outline-none" placeholder="07XXXXXXXX" data-testid="profile-phone" />
              </div>
              <div>
                <label className="block text-xs font-semibold text-gray-600 mb-1 flex items-center gap-1"><MessageSquare className="w-3 h-3" />WhatsApp</label>
                <input type="tel" value={form.whatsapp} onChange={(e) => setForm(f => ({...f, whatsapp: e.target.value}))}
                  className="w-full px-3 py-2 border-2 border-gray-200 rounded-xl text-sm focus:border-green-500 outline-none" placeholder="+94XXXXXXXXX" data-testid="profile-whatsapp" />
              </div>
            </div>
            {user?.role === 'shop' && (
              <div>
                <label className="block text-xs font-semibold text-gray-600 mb-1 flex items-center gap-1"><Briefcase className="w-3 h-3" />Shop Name</label>
                <input type="text" value={form.shop_name} onChange={(e) => setForm(f => ({...f, shop_name: e.target.value}))}
                  className="w-full px-3 py-2 border-2 border-gray-200 rounded-xl text-sm focus:border-green-500 outline-none" data-testid="profile-shop" />
              </div>
            )}
          </div>

          {/* Save */}
          <button type="submit" disabled={saving}
            className="w-full py-3 bg-green-600 text-white font-bold rounded-xl hover:bg-green-700 disabled:opacity-50 flex items-center justify-center gap-2 transition-colors"
            data-testid="profile-save">
            {saving ? '...' : saved ? <><CheckCircle className="w-5 h-5" />Saved!</> : <><Save className="w-5 h-5" />{t('common.save')}</>}
          </button>
        </form>
      </div>
    </div>
  );
};

export default HandymanProfilePage;
