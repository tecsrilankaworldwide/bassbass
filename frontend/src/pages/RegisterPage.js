import React, { useState, useEffect } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuth, API } from '../AuthContext';
import Navbar from '../components/Navbar';
import axios from 'axios';
import { Wrench, Mail, Lock, User, Phone, MapPin, Gift } from 'lucide-react';

const RegisterPage = () => {
  const { t } = useTranslation();
  const { register } = useAuth();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [districts, setDistricts] = useState([]);
  const [form, setForm] = useState({
    email: '', password: '', full_name: '', phone: '',
    role: 'customer', district: 'Colombo',
    referral_code: searchParams.get('ref') || ''
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    axios.get(`${API}/services`).then(res => setDistricts(res.data.districts)).catch(() => {});
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await register(form);
      if (['handyman', 'shop'].includes(form.role)) navigate('/profile');
      else navigate('/');
    } catch (err) {
      setError(err.response?.data?.detail || 'Registration failed');
    } finally { setLoading(false); }
  };

  const update = (key, val) => setForm(f => ({ ...f, [key]: val }));

  return (
    <div className="min-h-screen bg-[#F5F7F3]">
      <Navbar />
      <div className="flex items-center justify-center px-4 py-8">
        <div className="w-full max-w-sm">
          <div className="text-center mb-6">
            <div className="w-14 h-14 bg-green-600 rounded-2xl flex items-center justify-center mx-auto mb-3">
              <Wrench className="w-7 h-7 text-white" />
            </div>
            <h1 className="text-2xl font-extrabold text-gray-900" style={{fontFamily:'Manrope,sans-serif'}}>{t('auth.register')}</h1>
          </div>

          <form onSubmit={handleSubmit} className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6 space-y-3">
            {error && <div className="bg-red-50 text-red-700 text-sm px-3 py-2 rounded-lg">{error}</div>}

            {form.referral_code && (
              <div className="bg-green-50 border border-green-200 text-green-700 text-sm px-3 py-2 rounded-lg flex items-center gap-2" data-testid="referral-banner">
                <Gift className="w-4 h-4" />Referred by: <strong>{form.referral_code}</strong>
              </div>
            )}
            
            {/* Role selector */}
            <div className="grid grid-cols-3 gap-2" data-testid="role-selector">
              {[
                { val: 'customer', label: t('auth.asCustomer') },
                { val: 'handyman', label: t('auth.asHandyman') },
                { val: 'shop', label: t('auth.asShop') },
              ].map(r => (
                <button key={r.val} type="button" onClick={() => update('role', r.val)}
                  className={`p-2 rounded-lg text-xs font-semibold border-2 transition-all ${
                    form.role === r.val ? 'border-green-500 bg-green-50 text-green-700' : 'border-gray-200 text-gray-500 hover:border-gray-300'
                  }`} data-testid={`role-${r.val}`}>
                  {r.label}
                </button>
              ))}
            </div>

            <div>
              <label className="block text-xs font-semibold text-gray-600 mb-1">{t('auth.fullName')}</label>
              <div className="relative">
                <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                <input type="text" required value={form.full_name} onChange={(e) => update('full_name', e.target.value)}
                  className="w-full pl-10 pr-3 py-2.5 border-2 border-gray-200 rounded-xl text-sm focus:border-green-500 outline-none" data-testid="reg-name" />
              </div>
            </div>
            <div>
              <label className="block text-xs font-semibold text-gray-600 mb-1">{t('auth.email')}</label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                <input type="email" required value={form.email} onChange={(e) => update('email', e.target.value)}
                  className="w-full pl-10 pr-3 py-2.5 border-2 border-gray-200 rounded-xl text-sm focus:border-green-500 outline-none" data-testid="reg-email" />
              </div>
            </div>
            <div>
              <label className="block text-xs font-semibold text-gray-600 mb-1">{t('auth.phone')}</label>
              <div className="relative">
                <Phone className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                <input type="tel" required value={form.phone} onChange={(e) => update('phone', e.target.value)}
                  className="w-full pl-10 pr-3 py-2.5 border-2 border-gray-200 rounded-xl text-sm focus:border-green-500 outline-none"
                  placeholder="07XXXXXXXX" data-testid="reg-phone" />
              </div>
            </div>
            <div>
              <label className="block text-xs font-semibold text-gray-600 mb-1">{t('auth.district')}</label>
              <div className="relative">
                <MapPin className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                <select value={form.district} onChange={(e) => update('district', e.target.value)}
                  className="w-full pl-10 pr-3 py-2.5 border-2 border-gray-200 rounded-xl text-sm focus:border-green-500 outline-none appearance-none bg-white" data-testid="reg-district">
                  {districts.map(d => <option key={d} value={d}>{d}</option>)}
                </select>
              </div>
            </div>
            <div>
              <label className="block text-xs font-semibold text-gray-600 mb-1">{t('auth.password')}</label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                <input type="password" required value={form.password} onChange={(e) => update('password', e.target.value)}
                  className="w-full pl-10 pr-3 py-2.5 border-2 border-gray-200 rounded-xl text-sm focus:border-green-500 outline-none" data-testid="reg-password" />
              </div>
            </div>

            {/* Referral code input */}
            {!searchParams.get('ref') && (
              <div>
                <label className="block text-xs font-semibold text-gray-600 mb-1">Referral Code (optional)</label>
                <div className="relative">
                  <Gift className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                  <input type="text" value={form.referral_code} onChange={(e) => update('referral_code', e.target.value.toUpperCase())}
                    className="w-full pl-10 pr-3 py-2.5 border-2 border-gray-200 rounded-xl text-sm focus:border-green-500 outline-none"
                    placeholder="e.g. NIMAL-5K3" data-testid="reg-referral" />
                </div>
              </div>
            )}

            <button type="submit" disabled={loading}
              className="w-full py-3 bg-green-600 text-white font-bold rounded-xl hover:bg-green-700 disabled:opacity-50 mt-2"
              data-testid="reg-submit">
              {loading ? '...' : t('auth.registerBtn')}
            </button>
          </form>
          <p className="text-center text-sm text-gray-500 mt-4">
            {t('auth.hasAccount')} <Link to="/login" className="text-green-600 font-semibold">{t('auth.login')}</Link>
          </p>
        </div>
      </div>
    </div>
  );
};

export default RegisterPage;
