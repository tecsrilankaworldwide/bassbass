import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useAuth, API } from '../AuthContext';
import Navbar from '../components/Navbar';
import axios from 'axios';
import { UserPlus, Users, Star, MapPin, Trash2, Eye, EyeOff } from 'lucide-react';

const ShopDashboard = () => {
  const { t } = useTranslation();
  const { user, token } = useAuth();
  const [handymen, setHandymen] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAdd, setShowAdd] = useState(false);
  const [addForm, setAddForm] = useState({ email: '', password: '', full_name: '', phone: '', district: '' });
  const [submitting, setSubmitting] = useState(false);
  const [msg, setMsg] = useState('');
  const [showPwd, setShowPwd] = useState(false);
  const [districts, setDistricts] = useState([]);
  const headers = { Authorization: `Bearer ${token}` };

  useEffect(() => {
    loadData();
  }, []);

  const loadData = () => {
    setLoading(true);
    Promise.all([
      axios.get(`${API}/shop/my-handymen`, { headers }),
      axios.get(`${API}/services`)
    ]).then(([hRes, sRes]) => {
      setHandymen(hRes.data.handymen);
      setDistricts(sRes.data.districts);
    }).catch(console.error).finally(() => setLoading(false));
  };

  const handleAdd = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setMsg('');
    try {
      await axios.post(`${API}/shop/add-handyman`, addForm, { headers });
      setMsg('success');
      setAddForm({ email: '', password: '', full_name: '', phone: '', district: '' });
      setShowAdd(false);
      loadData();
    } catch (err) {
      setMsg(err.response?.data?.detail || 'Failed to add');
    } finally { setSubmitting(false); }
  };

  const handleRemove = async (userId) => {
    if (!window.confirm('Remove this handyman from your shop?')) return;
    try {
      await axios.delete(`${API}/shop/remove-handyman/${userId}`, { headers });
      loadData();
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed');
    }
  };

  const activeHandymen = handymen.filter(h => h.is_active !== false);

  return (
    <div className="min-h-screen bg-[#F5F7F3]">
      <Navbar />
      <div className="max-w-4xl mx-auto px-4 py-6">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-extrabold text-gray-900" style={{fontFamily:'Manrope,sans-serif'}} data-testid="shop-title">
              {user?.full_name || 'Shop'} Dashboard
            </h1>
            <p className="text-sm text-gray-500">{t('shop.manageHandymen')}</p>
          </div>
          <button onClick={() => setShowAdd(!showAdd)}
            className="flex items-center gap-2 px-4 py-2.5 bg-green-600 text-white font-semibold rounded-xl hover:bg-green-700 transition-colors text-sm"
            data-testid="add-handyman-btn">
            <UserPlus className="w-4 h-4" />{t('shop.addHandyman')}
          </button>
        </div>

        {msg === 'success' && (
          <div className="bg-green-50 text-green-700 text-sm font-medium px-4 py-2.5 rounded-xl mb-4" data-testid="add-success">
            Handyman added successfully!
          </div>
        )}
        {msg && msg !== 'success' && (
          <div className="bg-red-50 text-red-700 text-sm font-medium px-4 py-2.5 rounded-xl mb-4" data-testid="add-error">{msg}</div>
        )}

        {/* Add Handyman Form */}
        {showAdd && (
          <div className="bg-white rounded-2xl p-5 border border-gray-100 shadow-sm mb-6" data-testid="add-handyman-form">
            <h2 className="text-base font-bold text-gray-800 mb-4">{t('shop.addHandyman')}</h2>
            <form onSubmit={handleAdd} className="space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-gray-600 mb-1">{t('auth.fullName')} *</label>
                  <input required type="text" value={addForm.full_name} onChange={(e) => setAddForm(f => ({...f, full_name: e.target.value}))}
                    className="w-full px-3 py-2 border-2 border-gray-200 rounded-xl text-sm focus:border-green-500 outline-none" data-testid="add-name" />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-gray-600 mb-1">{t('auth.phone')} *</label>
                  <input required type="tel" value={addForm.phone} onChange={(e) => setAddForm(f => ({...f, phone: e.target.value}))}
                    className="w-full px-3 py-2 border-2 border-gray-200 rounded-xl text-sm focus:border-green-500 outline-none" placeholder="07XXXXXXXX" data-testid="add-phone" />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-gray-600 mb-1">{t('auth.email')} *</label>
                  <input required type="email" value={addForm.email} onChange={(e) => setAddForm(f => ({...f, email: e.target.value}))}
                    className="w-full px-3 py-2 border-2 border-gray-200 rounded-xl text-sm focus:border-green-500 outline-none" data-testid="add-email" />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-gray-600 mb-1">{t('auth.password')} *</label>
                  <div className="relative">
                    <input required type={showPwd ? 'text' : 'password'} value={addForm.password} onChange={(e) => setAddForm(f => ({...f, password: e.target.value}))}
                      className="w-full px-3 py-2 border-2 border-gray-200 rounded-xl text-sm focus:border-green-500 outline-none pr-10" data-testid="add-password" />
                    <button type="button" onClick={() => setShowPwd(!showPwd)} className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400">
                      {showPwd ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                  </div>
                </div>
              </div>
              <div>
                <label className="block text-xs font-semibold text-gray-600 mb-1">{t('auth.district')} *</label>
                <select required value={addForm.district} onChange={(e) => setAddForm(f => ({...f, district: e.target.value}))}
                  className="w-full px-3 py-2 border-2 border-gray-200 rounded-xl text-sm focus:border-green-500 outline-none" data-testid="add-district">
                  <option value="">Select...</option>
                  {districts.map(d => <option key={d} value={d}>{d}</option>)}
                </select>
              </div>
              <div className="flex gap-3 pt-1">
                <button type="button" onClick={() => setShowAdd(false)} className="flex-1 py-2.5 bg-gray-100 text-gray-700 font-semibold rounded-xl hover:bg-gray-200 text-sm">{t('common.cancel')}</button>
                <button type="submit" disabled={submitting} className="flex-1 py-2.5 bg-green-600 text-white font-semibold rounded-xl hover:bg-green-700 disabled:opacity-50 text-sm" data-testid="add-submit">
                  {submitting ? '...' : t('shop.addHandyman')}
                </button>
              </div>
            </form>
          </div>
        )}

        {/* Stats */}
        <div className="grid grid-cols-3 gap-4 mb-6">
          <div className="bg-green-50 rounded-xl p-4 border border-green-100 text-center" data-testid="stat-total">
            <Users className="w-6 h-6 text-green-600 mx-auto mb-1" />
            <div className="text-2xl font-extrabold text-green-700">{activeHandymen.length}</div>
            <div className="text-xs font-semibold text-green-600">{t('shop.totalHandymen')}</div>
          </div>
          <div className="bg-green-50 rounded-xl p-4 border border-green-100 text-center" data-testid="stat-approved">
            <div className="text-2xl font-extrabold text-green-700">{activeHandymen.filter(h => h.is_approved).length}</div>
            <div className="text-xs font-semibold text-green-600">{t('shop.approved')}</div>
          </div>
          <div className="bg-gray-50 rounded-xl p-4 border border-gray-100 text-center" data-testid="stat-pending">
            <div className="text-2xl font-extrabold text-gray-700">{activeHandymen.filter(h => !h.is_approved).length}</div>
            <div className="text-xs font-semibold text-gray-500">{t('shop.pendingApproval')}</div>
          </div>
        </div>

        {/* Handymen List */}
        {loading ? (
          <div className="flex justify-center py-12"><div className="animate-spin rounded-full h-10 w-10 border-4 border-green-500 border-t-transparent"></div></div>
        ) : activeHandymen.length === 0 ? (
          <div className="bg-white rounded-2xl p-12 text-center border border-gray-100">
            <Users className="w-12 h-12 text-gray-300 mx-auto mb-3" />
            <p className="text-lg font-semibold text-gray-600">{t('shop.noHandymen')}</p>
            <p className="text-sm text-gray-400 mt-1">Click "Add Handyman" to add your first team member</p>
          </div>
        ) : (
          <div className="space-y-3" data-testid="handymen-list">
            {activeHandymen.map(h => (
              <div key={h.id} className="bg-white rounded-xl p-4 border border-gray-100 shadow-sm" data-testid={`worker-${h.id}`}>
                <div className="flex items-start justify-between">
                  <div>
                    <h3 className="font-bold text-gray-900">{h.full_name}</h3>
                    <p className="text-sm text-gray-500">{h.email} &middot; {h.phone}</p>
                    <div className="flex items-center gap-2 mt-1.5">
                      <span className="flex items-center gap-1 text-xs text-gray-500"><MapPin className="w-3 h-3" />{h.district}</span>
                      {h.profile?.rating > 0 && (
                        <span className="flex items-center gap-1 text-xs text-green-600"><Star className="w-3 h-3 fill-amber-400 text-amber-400" />{h.profile.rating}</span>
                      )}
                      {h.is_approved
                        ? <span className="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded-full font-semibold">Active</span>
                        : <span className="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded-full font-semibold">Pending</span>
                      }
                    </div>
                    {h.profile?.services?.length > 0 && (
                      <div className="flex gap-1 mt-2">
                        {h.profile.services.map(s => (
                          <span key={s} className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded-full">{s}</span>
                        ))}
                      </div>
                    )}
                  </div>
                  <button onClick={() => handleRemove(h.id)}
                    className="p-2 text-red-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors" data-testid={`remove-${h.id}`}>
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default ShopDashboard;
