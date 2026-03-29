import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../AuthContext';
import Navbar from '../components/Navbar';
import { Wrench, Mail, Lock, Eye, EyeOff } from 'lucide-react';

const LoginPage = () => {
  const { t } = useTranslation();
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPass, setShowPass] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const data = await login(email, password);
      if (data.user.role === 'admin') navigate('/admin');
      else if (['handyman', 'shop'].includes(data.user.role)) navigate('/profile');
      else navigate('/');
    } catch (err) {
      setError(err.response?.data?.detail || 'Login failed');
    } finally { setLoading(false); }
  };

  return (
    <div className="min-h-screen bg-[#FAF9F6]">
      <Navbar />
      <div className="flex items-center justify-center px-4 py-12">
        <div className="w-full max-w-sm">
          <div className="text-center mb-8">
            <div className="w-16 h-16 bg-[#0B2545] rounded-2xl flex items-center justify-center mx-auto mb-4 shadow-lg">
              <Wrench className="w-8 h-8 text-white" />
            </div>
            <h1 className="text-2xl font-bold text-[#0B2545]" style={{fontFamily:'Outfit,sans-serif'}}>{t('auth.login')}</h1>
          </div>

          <form onSubmit={handleSubmit} className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6 space-y-5">
            {error && <div className="bg-red-50 text-[#F05A4A] text-sm font-medium px-4 py-3 rounded-xl border border-red-100" data-testid="login-error">{error}</div>}
            <div>
              <label className="block text-sm font-semibold text-[#0B2545] mb-2">{t('auth.email')}</label>
              <div className="relative">
                <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-[#718096]" />
                <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required
                  className="w-full pl-11 pr-4 py-3 border-2 border-gray-200 rounded-xl text-[#0B2545] focus:border-[#F05A4A] focus:ring-0 outline-none transition-colors"
                  placeholder="you@email.com" data-testid="login-email" />
              </div>
            </div>
            <div>
              <label className="block text-sm font-semibold text-[#0B2545] mb-2">{t('auth.password')}</label>
              <div className="relative">
                <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-[#718096]" />
                <input type={showPass ? 'text' : 'password'} value={password} onChange={(e) => setPassword(e.target.value)} required
                  className="w-full pl-11 pr-11 py-3 border-2 border-gray-200 rounded-xl text-[#0B2545] focus:border-[#F05A4A] focus:ring-0 outline-none transition-colors"
                  data-testid="login-password" />
                <button type="button" onClick={() => setShowPass(!showPass)} className="absolute right-4 top-1/2 -translate-y-1/2 text-[#718096] hover:text-[#0B2545] transition-colors">
                  {showPass ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>
            <button type="submit" disabled={loading}
              className="w-full py-3.5 bg-[#F05A4A] text-white font-bold rounded-xl hover:bg-[#E63946] disabled:opacity-50 active:scale-[0.98] transition-all shadow-sm shadow-[#F05A4A]/20"
              data-testid="login-submit">
              {loading ? <span className="inline-block w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></span> : t('auth.loginBtn')}
            </button>
          </form>

          <p className="text-center text-sm text-[#718096] mt-6">
            {t('auth.noAccount')} <Link to="/register" className="text-[#F05A4A] font-semibold hover:text-[#E63946] transition-colors" data-testid="register-link">{t('auth.register')}</Link>
          </p>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
