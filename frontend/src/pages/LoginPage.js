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
    <div className="min-h-screen bg-[#F5F7F3]">
      <Navbar />
      <div className="flex items-center justify-center px-4 py-12">
        <div className="w-full max-w-sm">
          <div className="text-center mb-8">
            <div className="w-16 h-16 bg-green-600 rounded-2xl flex items-center justify-center mx-auto mb-4">
              <Wrench className="w-8 h-8 text-white" />
            </div>
            <h1 className="text-2xl font-extrabold text-gray-900" style={{fontFamily:'Manrope,sans-serif'}}>{t('auth.login')}</h1>
          </div>

          <form onSubmit={handleSubmit} className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6 space-y-4">
            {error && <div className="bg-red-50 text-red-700 text-sm font-medium px-3 py-2 rounded-lg" data-testid="login-error">{error}</div>}
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-1">{t('auth.email')}</label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required
                  className="w-full pl-10 pr-3 py-2.5 border-2 border-gray-200 rounded-xl text-sm focus:border-green-500 focus:ring-0 outline-none"
                  placeholder="you@email.com" data-testid="login-email" />
              </div>
            </div>
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-1">{t('auth.password')}</label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                <input type={showPass ? 'text' : 'password'} value={password} onChange={(e) => setPassword(e.target.value)} required
                  className="w-full pl-10 pr-10 py-2.5 border-2 border-gray-200 rounded-xl text-sm focus:border-green-500 focus:ring-0 outline-none"
                  data-testid="login-password" />
                <button type="button" onClick={() => setShowPass(!showPass)} className="absolute right-3 top-1/2 -translate-y-1/2">
                  {showPass ? <EyeOff className="w-4 h-4 text-gray-400" /> : <Eye className="w-4 h-4 text-gray-400" />}
                </button>
              </div>
            </div>
            <button type="submit" disabled={loading}
              className="w-full py-3 bg-green-600 text-white font-bold rounded-xl hover:bg-green-700 disabled:opacity-50 transition-colors"
              data-testid="login-submit">
              {loading ? '...' : t('auth.loginBtn')}
            </button>
          </form>

          <p className="text-center text-sm text-gray-500 mt-4">
            {t('auth.noAccount')} <Link to="/register" className="text-green-600 font-semibold hover:text-green-700" data-testid="register-link">{t('auth.register')}</Link>
          </p>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
