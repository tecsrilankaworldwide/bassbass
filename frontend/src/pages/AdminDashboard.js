import React, { useState, useEffect, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import { useAuth, API } from '../AuthContext';
import Navbar from '../components/Navbar';
import axios from 'axios';
import { Users, BarChart3, CheckCircle, Clock, XCircle, Shield, Receipt, CreditCard, ArrowUpRight, Upload, FileText, TrendingUp, MapPin, Star, Tag, Plus, Trash2 } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, LineChart, Line, CartesianGrid, Legend } from 'recharts';

const CHART_COLORS = ['#16a34a', '#f97316', '#3b82f6', '#ef4444', '#8b5cf6', '#06b6d4', '#ec4899', '#eab308'];

const AdminDashboard = () => {
  const { t } = useTranslation();
  const { token } = useAuth();
  const [activeTab, setActiveTab] = useState('overview');
  const [stats, setStats] = useState(null);
  const [pending, setPending] = useState([]);
  const [users, setUsers] = useState([]);
  const [accounting, setAccounting] = useState(null);
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [filterRole, setFilterRole] = useState('');
  const [csvFile, setCsvFile] = useState(null);
  const [csvUploading, setCsvUploading] = useState(false);
  const [csvResult, setCsvResult] = useState(null);
  const [promoCodes, setPromoCodes] = useState([]);
  const [showPromoForm, setShowPromoForm] = useState(false);
  const [promoForm, setPromoForm] = useState({ code: '', discount_percent: 10, max_uses: 100, description: '', min_order: 0, expires_at: '' });
  const [promoSaving, setPromoSaving] = useState(false);
  const [smsStatus, setSmsStatus] = useState(null);
  const [testPhone, setTestPhone] = useState('');
  const [smsSending, setSmsSending] = useState(false);
  const [smsResult, setSmsResult] = useState('');
  const fileRef = useRef(null);
  const headers = { Authorization: `Bearer ${token}` };

  useEffect(() => { loadData(); }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [statsRes, pendingRes, usersRes, accRes] = await Promise.all([
        axios.get(`${API}/admin/statistics`, { headers }),
        axios.get(`${API}/admin/pending-approvals`, { headers }),
        axios.get(`${API}/admin/users`, { headers }),
        axios.get(`${API}/admin/accounting`, { headers }).catch(() => ({ data: null }))
      ]);
      setStats(statsRes.data);
      setPending(pendingRes.data.pending || []);
      setUsers(usersRes.data.users || []);
      setAccounting(accRes.data);
    } catch (err) { console.error(err); }
    finally { setLoading(false); }
  };

  const loadAnalytics = async () => {
    try {
      const res = await axios.get(`${API}/admin/analytics`, { headers });
      setAnalytics(res.data);
    } catch (err) { console.error(err); }
  };

  const loadPromos = async () => {
    try {
      const res = await axios.get(`${API}/admin/promo-codes`, { headers });
      setPromoCodes(res.data.promo_codes || []);
    } catch (err) { console.error(err); }
  };

  useEffect(() => {
    if (activeTab === 'analytics' && !analytics) loadAnalytics();
    if (activeTab === 'promos' && promoCodes.length === 0) loadPromos();
    if (activeTab === 'sms' && !smsStatus) {
      axios.get(`${API}/admin/sms-status`, { headers }).then(res => setSmsStatus(res.data)).catch(() => {});
    }
  }, [activeTab]);

  const approveUser = async (userId) => {
    try { await axios.put(`${API}/admin/approve/${userId}`, {}, { headers }); loadData(); }
    catch (err) { alert(err.response?.data?.detail || 'Failed'); }
  };
  const rejectUser = async (userId) => {
    try { await axios.put(`${API}/admin/reject/${userId}`, {}, { headers }); loadData(); }
    catch (err) { alert(err.response?.data?.detail || 'Failed'); }
  };
  const markPayoutPaid = async (payoutId) => {
    try { await axios.put(`${API}/admin/payouts/${payoutId}/mark-paid`, {}, { headers }); loadData(); }
    catch (err) { alert(err.response?.data?.detail || 'Failed'); }
  };

  const handleCsvUpload = async () => {
    if (!csvFile) return;
    setCsvUploading(true);
    setCsvResult(null);
    try {
      const formData = new FormData();
      formData.append('file', csvFile);
      const res = await axios.post(`${API}/admin/csv-import`, formData, {
        headers: { ...headers, 'Content-Type': 'multipart/form-data' }
      });
      setCsvResult(res.data.results);
      setCsvFile(null);
      if (fileRef.current) fileRef.current.value = '';
      loadData();
    } catch (err) {
      setCsvResult({ error: err.response?.data?.detail || 'Upload failed' });
    } finally { setCsvUploading(false); }
  };

  const createPromo = async () => {
    if (!promoForm.code || !promoForm.discount_percent) return;
    setPromoSaving(true);
    try {
      await axios.post(`${API}/admin/promo-codes`, promoForm, { headers });
      setShowPromoForm(false);
      setPromoForm({ code: '', discount_percent: 10, max_uses: 100, description: '', min_order: 0, expires_at: '' });
      loadPromos();
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed');
    } finally { setPromoSaving(false); }
  };

  const togglePromo = async (id) => {
    try {
      await axios.put(`${API}/admin/promo-codes/${id}/toggle`, {}, { headers });
      loadPromos();
    } catch (err) { alert('Failed'); }
  };

  const deletePromo = async (id) => {
    if (!window.confirm('Delete this promo code?')) return;
    try {
      await axios.delete(`${API}/admin/promo-codes/${id}`, { headers });
      loadPromos();
    } catch (err) { alert('Failed'); }
  };

  const sendTestSms = async () => {
    if (!testPhone) return;
    setSmsSending(true);
    setSmsResult('');
    try {
      const res = await axios.post(`${API}/admin/send-test-sms`, { phone: testPhone }, { headers });
      setSmsResult(res.data.sent ? 'Test SMS sent successfully!' : 'SMS sending failed');
    } catch (err) {
      setSmsResult(err.response?.data?.detail || 'Failed to send SMS');
    } finally { setSmsSending(false); }
  };

  const downloadTemplate = () => {
    window.open(`${API}/admin/csv-template`, '_blank');
  };

  const filteredUsers = filterRole ? users.filter(u => u.role === filterRole) : users;
  const formatLKR = (n) => n ? `LKR ${Number(n).toLocaleString('en-LK', { minimumFractionDigits: 2 })}` : 'LKR 0.00';

  const tabs = [
    { id: 'overview', label: 'Overview', icon: BarChart3 },
    { id: 'approvals', label: `Approvals (${pending.length})`, icon: Clock },
    { id: 'users', label: 'Users', icon: Users },
    { id: 'promos', label: 'Promo Codes', icon: Tag },
    { id: 'csv', label: 'CSV Import', icon: Upload },
    { id: 'analytics', label: 'Analytics', icon: TrendingUp },
    { id: 'accounting', label: 'Accounting', icon: Receipt },
    { id: 'sms', label: 'SMS', icon: Users },
  ];

  return (
    <div className="min-h-screen bg-[#F5F7F3]">
      <Navbar />
      <div className="max-w-6xl mx-auto px-4 py-6">
        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 bg-green-600 rounded-xl flex items-center justify-center">
            <Shield className="w-5 h-5 text-white" />
          </div>
          <h1 className="text-2xl font-extrabold text-gray-900" style={{fontFamily:'Manrope,sans-serif'}} data-testid="admin-title">{t('nav.admin')} Dashboard</h1>
        </div>

        <div className="flex gap-1 bg-white rounded-xl p-1 shadow-sm border border-gray-100 mb-6 overflow-x-auto" data-testid="admin-tabs">
          {tabs.map(tab => (
            <button key={tab.id} onClick={() => setActiveTab(tab.id)}
              className={`flex items-center justify-center gap-1.5 px-3 py-2.5 rounded-lg text-xs font-semibold transition-all whitespace-nowrap ${activeTab === tab.id ? 'bg-green-600 text-white shadow-md' : 'text-gray-500 hover:bg-green-50'}`} data-testid={`tab-${tab.id}`}>
              <tab.icon className="w-4 h-4" />{tab.label}
            </button>
          ))}
        </div>

        {loading ? (
          <div className="flex justify-center py-12"><div className="animate-spin rounded-full h-10 w-10 border-4 border-green-500 border-t-transparent"></div></div>
        ) : (
          <>
            {/* OVERVIEW */}
            {activeTab === 'overview' && stats && (
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4" data-testid="stats-grid">
                {[
                  { label: 'Customers', value: stats.total_customers, color: 'bg-blue-50 text-blue-600' },
                  { label: 'Handymen', value: stats.total_handymen, color: 'bg-green-50 text-green-600' },
                  { label: 'Approved', value: stats.approved_handymen, color: 'bg-green-50 text-green-600' },
                  { label: 'Pending', value: stats.pending_approvals, color: 'bg-red-50 text-red-600' },
                  { label: 'Total Bookings', value: stats.total_bookings, color: 'bg-purple-50 text-purple-600' },
                  { label: 'Active', value: stats.active_bookings, color: 'bg-cyan-50 text-cyan-600' },
                  { label: 'Completed', value: stats.completed_bookings, color: 'bg-emerald-50 text-emerald-600' },
                  { label: 'Reviews', value: stats.total_reviews, color: 'bg-pink-50 text-pink-600' },
                ].map((s, i) => (
                  <div key={i} className={`rounded-xl p-4 ${s.color} border border-gray-100`}>
                    <div className="text-2xl font-extrabold" style={{fontFamily:'Manrope,sans-serif'}}>{s.value}</div>
                    <div className="text-xs font-semibold mt-1 opacity-80">{s.label}</div>
                  </div>
                ))}
              </div>
            )}

            {/* APPROVALS */}
            {activeTab === 'approvals' && (
              <div data-testid="approvals-section">
                {pending.length === 0 ? (
                  <div className="bg-white rounded-2xl p-12 text-center border border-gray-100">
                    <CheckCircle className="w-12 h-12 text-green-400 mx-auto mb-3" />
                    <p className="text-lg font-semibold text-gray-600">All caught up!</p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {pending.map(u => (
                      <div key={u.id} className="bg-white rounded-xl p-4 border border-gray-100 shadow-sm" data-testid={`pending-${u.id}`}>
                        <div className="flex items-start justify-between">
                          <div>
                            <h3 className="font-bold text-gray-900">{u.full_name}</h3>
                            <p className="text-sm text-gray-500">{u.email} &middot; {u.phone}</p>
                            <div className="flex gap-2 mt-1">
                              <span className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full font-semibold">{u.role}</span>
                              <span className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded-full">{u.district}</span>
                            </div>
                          </div>
                          <div className="flex gap-2">
                            <button onClick={() => approveUser(u.id)} className="px-4 py-2 bg-green-500 text-white text-xs font-semibold rounded-lg hover:bg-green-600" data-testid={`approve-${u.id}`}>Approve</button>
                            <button onClick={() => rejectUser(u.id)} className="px-4 py-2 bg-red-500 text-white text-xs font-semibold rounded-lg hover:bg-red-600" data-testid={`reject-${u.id}`}>Reject</button>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* USERS */}
            {activeTab === 'users' && (
              <div data-testid="users-section">
                <div className="flex gap-2 mb-4 flex-wrap">
                  {['', 'customer', 'handyman', 'shop', 'admin'].map(r => (
                    <button key={r} onClick={() => setFilterRole(r)}
                      className={`px-3 py-1.5 text-xs font-semibold rounded-full transition-colors ${filterRole === r ? 'bg-green-600 text-white' : 'bg-white text-gray-600 border border-gray-200 hover:border-green-400'}`}>
                      {r || 'All'} {r ? '' : `(${users.length})`}
                    </button>
                  ))}
                </div>
                <div className="bg-white rounded-xl border border-gray-100 shadow-sm overflow-hidden">
                  <table className="w-full">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-4 py-2.5 text-left text-xs font-semibold text-gray-600 uppercase">Name</th>
                        <th className="px-4 py-2.5 text-left text-xs font-semibold text-gray-600 uppercase">Email</th>
                        <th className="px-4 py-2.5 text-left text-xs font-semibold text-gray-600 uppercase">Role</th>
                        <th className="px-4 py-2.5 text-left text-xs font-semibold text-gray-600 uppercase">District</th>
                        <th className="px-4 py-2.5 text-left text-xs font-semibold text-gray-600 uppercase">Status</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-50">
                      {filteredUsers.map(u => (
                        <tr key={u.id} className="hover:bg-gray-50">
                          <td className="px-4 py-3 text-sm font-medium text-gray-900">{u.full_name}</td>
                          <td className="px-4 py-3 text-sm text-gray-600">{u.email}</td>
                          <td className="px-4 py-3"><span className={`px-2 py-0.5 rounded-full text-xs font-semibold ${u.role === 'admin' ? 'bg-red-100 text-red-700' : u.role === 'handyman' ? 'bg-green-100 text-green-700' : u.role === 'shop' ? 'bg-blue-100 text-blue-700' : 'bg-gray-100 text-gray-700'}`}>{u.role}</span></td>
                          <td className="px-4 py-3 text-sm text-gray-600">{u.district || '—'}</td>
                          <td className="px-4 py-3">{u.is_approved !== false ? <span className="text-xs text-green-600 font-semibold">Active</span> : <span className="text-xs text-orange-600 font-semibold">Pending</span>}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* PROMO CODES */}
            {activeTab === 'promos' && (
              <div data-testid="promos-section">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-2">
                    <Tag className="w-5 h-5 text-orange-500" />
                    <h2 className="text-lg font-bold text-gray-900" style={{fontFamily:'Manrope,sans-serif'}}>Promo Codes</h2>
                  </div>
                  <button onClick={() => setShowPromoForm(!showPromoForm)}
                    className="flex items-center gap-1.5 px-4 py-2 bg-orange-500 text-white text-xs font-semibold rounded-lg hover:bg-orange-600"
                    data-testid="create-promo-btn">
                    <Plus className="w-4 h-4" />{showPromoForm ? 'Cancel' : 'Create Promo'}
                  </button>
                </div>

                {showPromoForm && (
                  <div className="bg-white rounded-2xl p-5 border border-gray-100 shadow-sm mb-4" data-testid="promo-form">
                    <div className="grid grid-cols-2 gap-3 mb-3">
                      <div>
                        <label className="block text-xs font-semibold text-gray-600 mb-1">Code *</label>
                        <input type="text" value={promoForm.code} onChange={(e) => setPromoForm(f => ({...f, code: e.target.value.toUpperCase()}))}
                          className="w-full px-3 py-2 border-2 border-gray-200 rounded-lg text-sm focus:border-green-500 outline-none" placeholder="e.g. LAUNCH20"
                          data-testid="promo-code-input" />
                      </div>
                      <div>
                        <label className="block text-xs font-semibold text-gray-600 mb-1">Discount % *</label>
                        <input type="number" min="1" max="100" value={promoForm.discount_percent} onChange={(e) => setPromoForm(f => ({...f, discount_percent: parseInt(e.target.value) || 0}))}
                          className="w-full px-3 py-2 border-2 border-gray-200 rounded-lg text-sm focus:border-green-500 outline-none"
                          data-testid="promo-discount-input" />
                      </div>
                      <div>
                        <label className="block text-xs font-semibold text-gray-600 mb-1">Max Uses</label>
                        <input type="number" min="1" value={promoForm.max_uses} onChange={(e) => setPromoForm(f => ({...f, max_uses: parseInt(e.target.value) || 100}))}
                          className="w-full px-3 py-2 border-2 border-gray-200 rounded-lg text-sm focus:border-green-500 outline-none" />
                      </div>
                      <div>
                        <label className="block text-xs font-semibold text-gray-600 mb-1">Min Order (LKR)</label>
                        <input type="number" min="0" value={promoForm.min_order} onChange={(e) => setPromoForm(f => ({...f, min_order: parseFloat(e.target.value) || 0}))}
                          className="w-full px-3 py-2 border-2 border-gray-200 rounded-lg text-sm focus:border-green-500 outline-none" />
                      </div>
                      <div>
                        <label className="block text-xs font-semibold text-gray-600 mb-1">Expires At</label>
                        <input type="date" value={promoForm.expires_at} onChange={(e) => setPromoForm(f => ({...f, expires_at: e.target.value}))}
                          className="w-full px-3 py-2 border-2 border-gray-200 rounded-lg text-sm focus:border-green-500 outline-none" />
                      </div>
                      <div>
                        <label className="block text-xs font-semibold text-gray-600 mb-1">Description</label>
                        <input type="text" value={promoForm.description} onChange={(e) => setPromoForm(f => ({...f, description: e.target.value}))}
                          className="w-full px-3 py-2 border-2 border-gray-200 rounded-lg text-sm focus:border-green-500 outline-none" placeholder="Launch discount" />
                      </div>
                    </div>
                    <button onClick={createPromo} disabled={promoSaving || !promoForm.code}
                      className="px-5 py-2.5 bg-green-600 text-white font-semibold rounded-lg hover:bg-green-700 disabled:opacity-50 text-sm"
                      data-testid="promo-save-btn">
                      {promoSaving ? 'Creating...' : 'Create Code'}
                    </button>
                  </div>
                )}

                {promoCodes.length === 0 ? (
                  <div className="bg-white rounded-2xl p-12 text-center border border-gray-100">
                    <Tag className="w-12 h-12 text-gray-300 mx-auto mb-3" />
                    <p className="text-lg font-semibold text-gray-600">No promo codes yet</p>
                    <p className="text-sm text-gray-400">Create your first one above</p>
                  </div>
                ) : (
                  <div className="space-y-2">
                    {promoCodes.map(p => (
                      <div key={p.id} className={`bg-white rounded-xl p-4 border shadow-sm ${p.is_active ? 'border-gray-100' : 'border-red-100 opacity-60'}`} data-testid={`promo-${p.id}`}>
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-3">
                            <div className="bg-orange-50 rounded-lg px-3 py-2">
                              <span className="text-lg font-extrabold text-orange-600" style={{fontFamily:'Manrope,sans-serif'}}>{p.code}</span>
                            </div>
                            <div>
                              <div className="flex items-center gap-2">
                                <span className="text-sm font-bold text-gray-900">{p.discount_percent}% OFF</span>
                                {p.description && <span className="text-xs text-gray-500">— {p.description}</span>}
                              </div>
                              <div className="flex items-center gap-3 text-xs text-gray-500 mt-0.5">
                                <span>Used: {p.used_count}/{p.max_uses}</span>
                                {p.min_order > 0 && <span>Min: LKR {p.min_order}</span>}
                                {p.expires_at && <span>Expires: {p.expires_at}</span>}
                              </div>
                            </div>
                          </div>
                          <div className="flex items-center gap-2">
                            <button onClick={() => togglePromo(p.id)}
                              className={`px-3 py-1.5 text-xs font-semibold rounded-lg ${p.is_active ? 'bg-red-50 text-red-600 hover:bg-red-100' : 'bg-green-50 text-green-600 hover:bg-green-100'}`}>
                              {p.is_active ? 'Disable' : 'Enable'}
                            </button>
                            <button onClick={() => deletePromo(p.id)} className="p-1.5 text-gray-400 hover:text-red-500" data-testid={`delete-promo-${p.id}`}>
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* CSV IMPORT */}
            {activeTab === 'csv' && (
              <div data-testid="csv-section">
                <div className="bg-white rounded-2xl p-6 border border-gray-100 shadow-sm">
                  <div className="flex items-center gap-3 mb-4">
                    <Upload className="w-6 h-6 text-green-600" />
                    <h2 className="text-lg font-bold text-gray-900" style={{fontFamily:'Manrope,sans-serif'}}>Bulk Handyman Import</h2>
                  </div>
                  <p className="text-sm text-gray-500 mb-4">
                    Upload a CSV file to register multiple handymen at once. Required columns: <code className="bg-gray-100 px-1 rounded text-xs">full_name</code>, <code className="bg-gray-100 px-1 rounded text-xs">email</code>. Optional: <code className="bg-gray-100 px-1 rounded text-xs">phone, password, district, services, description, experience_years</code>
                  </p>

                  <button onClick={downloadTemplate}
                    className="inline-flex items-center gap-2 px-4 py-2 text-sm font-semibold text-green-700 bg-green-50 rounded-lg hover:bg-green-100 border border-green-200 mb-4" data-testid="download-template-btn">
                    <FileText className="w-4 h-4" />Download CSV Template
                  </button>

                  <div className="flex items-center gap-3">
                    <input ref={fileRef} type="file" accept=".csv"
                      onChange={(e) => { setCsvFile(e.target.files[0]); setCsvResult(null); }}
                      className="flex-1 text-sm file:mr-3 file:py-2 file:px-4 file:rounded-lg file:border-0 file:bg-green-600 file:text-white file:font-semibold file:cursor-pointer hover:file:bg-green-700"
                      data-testid="csv-file-input" />
                    <button onClick={handleCsvUpload} disabled={!csvFile || csvUploading}
                      className="px-5 py-2.5 bg-orange-500 text-white font-semibold rounded-lg hover:bg-orange-600 disabled:opacity-50 disabled:cursor-not-allowed text-sm"
                      data-testid="csv-upload-btn">
                      {csvUploading ? 'Uploading...' : 'Import'}
                    </button>
                  </div>

                  {csvResult && (
                    <div className="mt-4" data-testid="csv-result">
                      {csvResult.error ? (
                        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                          <p className="text-sm text-red-700 font-semibold">{csvResult.error}</p>
                        </div>
                      ) : (
                        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                          <div className="flex gap-6 mb-2">
                            <span className="text-sm font-bold text-green-700">Created: {csvResult.created}</span>
                            <span className="text-sm font-bold text-orange-600">Skipped: {csvResult.skipped}</span>
                          </div>
                          {csvResult.errors?.length > 0 && (
                            <div className="mt-2">
                              <p className="text-xs font-semibold text-gray-600 mb-1">Errors:</p>
                              <div className="max-h-32 overflow-y-auto space-y-1">
                                {csvResult.errors.map((e, i) => (
                                  <p key={i} className="text-xs text-red-600">Row {e.row}: {e.reason}{e.email ? ` (${e.email})` : ''}</p>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* ANALYTICS */}
            {activeTab === 'analytics' && (
              <div data-testid="analytics-section">
                {!analytics ? (
                  <div className="flex justify-center py-12"><div className="animate-spin rounded-full h-10 w-10 border-4 border-green-500 border-t-transparent"></div></div>
                ) : (
                  <div className="space-y-6">
                    {/* Summary cards */}
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      <div className="rounded-xl p-4 bg-green-50 text-green-600 border border-gray-100">
                        <div className="text-2xl font-extrabold" style={{fontFamily:'Manrope,sans-serif'}}>{analytics.totals.users}</div>
                        <div className="text-xs font-semibold mt-1 opacity-80">Total Users</div>
                      </div>
                      <div className="rounded-xl p-4 bg-blue-50 text-blue-600 border border-gray-100">
                        <div className="text-2xl font-extrabold" style={{fontFamily:'Manrope,sans-serif'}}>{analytics.totals.handymen}</div>
                        <div className="text-xs font-semibold mt-1 opacity-80">Active Handymen</div>
                      </div>
                      <div className="rounded-xl p-4 bg-purple-50 text-purple-600 border border-gray-100">
                        <div className="text-2xl font-extrabold" style={{fontFamily:'Manrope,sans-serif'}}>{analytics.totals.bookings}</div>
                        <div className="text-xs font-semibold mt-1 opacity-80">Total Bookings</div>
                      </div>
                      <div className="rounded-xl p-4 bg-orange-50 text-orange-600 border border-gray-100">
                        <div className="text-2xl font-extrabold" style={{fontFamily:'Manrope,sans-serif'}}>{formatLKR(analytics.revenue_summary.total_revenue)}</div>
                        <div className="text-xs font-semibold mt-1 opacity-80">Total Revenue</div>
                      </div>
                    </div>

                    {/* Bookings by Status - Pie */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div className="bg-white rounded-2xl p-5 border border-gray-100 shadow-sm">
                        <h3 className="text-sm font-bold text-gray-800 mb-4">Bookings by Status</h3>
                        {Object.keys(analytics.bookings_by_status).length > 0 ? (
                          <ResponsiveContainer width="100%" height={220}>
                            <PieChart>
                              <Pie data={Object.entries(analytics.bookings_by_status).map(([k, v]) => ({ name: k, value: v }))}
                                cx="50%" cy="50%" outerRadius={80} dataKey="value" label={({name, value}) => `${name}: ${value}`}>
                                {Object.keys(analytics.bookings_by_status).map((_, i) => (
                                  <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />
                                ))}
                              </Pie>
                              <Tooltip />
                            </PieChart>
                          </ResponsiveContainer>
                        ) : <p className="text-sm text-gray-400 text-center py-8">No booking data yet</p>}
                      </div>

                      {/* Top Services - Bar */}
                      <div className="bg-white rounded-2xl p-5 border border-gray-100 shadow-sm">
                        <h3 className="text-sm font-bold text-gray-800 mb-4">Top Services</h3>
                        {analytics.top_services.length > 0 ? (
                          <ResponsiveContainer width="100%" height={220}>
                            <BarChart data={analytics.top_services} layout="vertical">
                              <XAxis type="number" />
                              <YAxis type="category" dataKey="service_id" width={90} tick={{fontSize: 11}} />
                              <Tooltip />
                              <Bar dataKey="bookings" fill="#16a34a" radius={[0, 4, 4, 0]} />
                            </BarChart>
                          </ResponsiveContainer>
                        ) : <p className="text-sm text-gray-400 text-center py-8">No service data yet</p>}
                      </div>
                    </div>

                    {/* Bookings Daily - Line chart */}
                    <div className="bg-white rounded-2xl p-5 border border-gray-100 shadow-sm">
                      <h3 className="text-sm font-bold text-gray-800 mb-4">Bookings (Last 30 Days)</h3>
                      {analytics.bookings_daily.length > 0 ? (
                        <ResponsiveContainer width="100%" height={250}>
                          <LineChart data={analytics.bookings_daily}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                            <XAxis dataKey="date" tick={{fontSize: 10}} angle={-45} textAnchor="end" height={60} />
                            <YAxis />
                            <Tooltip />
                            <Legend />
                            <Line type="monotone" dataKey="count" stroke="#16a34a" strokeWidth={2} name="Bookings" dot={{r: 3}} />
                          </LineChart>
                        </ResponsiveContainer>
                      ) : <p className="text-sm text-gray-400 text-center py-8">No recent booking data</p>}
                    </div>

                    {/* Bookings by District + Top Handymen */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div className="bg-white rounded-2xl p-5 border border-gray-100 shadow-sm">
                        <h3 className="text-sm font-bold text-gray-800 mb-4">Top Districts</h3>
                        {analytics.bookings_by_district.length > 0 ? (
                          <ResponsiveContainer width="100%" height={220}>
                            <BarChart data={analytics.bookings_by_district}>
                              <XAxis dataKey="district" tick={{fontSize: 10}} angle={-30} textAnchor="end" height={60} />
                              <YAxis />
                              <Tooltip />
                              <Bar dataKey="count" fill="#f97316" radius={[4, 4, 0, 0]} />
                            </BarChart>
                          </ResponsiveContainer>
                        ) : <p className="text-sm text-gray-400 text-center py-8">No district data yet</p>}
                      </div>

                      <div className="bg-white rounded-2xl p-5 border border-gray-100 shadow-sm">
                        <h3 className="text-sm font-bold text-gray-800 mb-4">Top Handymen</h3>
                        {analytics.top_handymen.length > 0 ? (
                          <div className="space-y-2 max-h-[220px] overflow-y-auto">
                            {analytics.top_handymen.map((h, i) => (
                              <div key={h.user_id} className="flex items-center justify-between p-2 rounded-lg hover:bg-gray-50">
                                <div className="flex items-center gap-2">
                                  <span className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold text-white ${i < 3 ? 'bg-orange-500' : 'bg-gray-400'}`}>{i + 1}</span>
                                  <div>
                                    <p className="text-sm font-semibold text-gray-900">{h.full_name}</p>
                                    <p className="text-xs text-gray-500">{h.district}</p>
                                  </div>
                                </div>
                                <div className="text-right">
                                  <div className="flex items-center gap-1">
                                    <Star className="w-3 h-3 text-orange-400 fill-orange-400" />
                                    <span className="text-xs font-bold">{h.rating}</span>
                                  </div>
                                  <p className="text-xs text-gray-500">{h.jobs_completed} jobs</p>
                                </div>
                              </div>
                            ))}
                          </div>
                        ) : <p className="text-sm text-gray-400 text-center py-8">No handyman data yet</p>}
                      </div>
                    </div>

                    {/* User Growth */}
                    {analytics.user_growth.length > 0 && (
                      <div className="bg-white rounded-2xl p-5 border border-gray-100 shadow-sm">
                        <h3 className="text-sm font-bold text-gray-800 mb-4">User Growth (Last 30 Days)</h3>
                        <ResponsiveContainer width="100%" height={220}>
                          <BarChart data={analytics.user_growth}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                            <XAxis dataKey="date" tick={{fontSize: 10}} angle={-45} textAnchor="end" height={60} />
                            <YAxis />
                            <Tooltip />
                            <Legend />
                            <Bar dataKey="customer" fill="#3b82f6" stackId="a" name="Customers" />
                            <Bar dataKey="handyman" fill="#16a34a" stackId="a" name="Handymen" />
                            <Bar dataKey="shop" fill="#f97316" stackId="a" name="Shops" />
                          </BarChart>
                        </ResponsiveContainer>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}

            {/* ACCOUNTING */}
            {activeTab === 'accounting' && accounting && (
              <div data-testid="accounting-section">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                  {[
                    { label: 'Total Revenue', value: formatLKR(accounting.total_revenue), color: 'bg-green-50 text-green-600' },
                    { label: `TopBass Fee (${accounting.fee_percent}%)`, value: formatLKR(accounting.total_topbass_fee), color: 'bg-green-50 text-green-600' },
                    { label: `VAT (${accounting.vat_percent}%)`, value: formatLKR(accounting.total_vat_collected), color: 'bg-blue-50 text-blue-600' },
                    { label: 'Handyman Pay', value: formatLKR(accounting.total_handyman_pay), color: 'bg-purple-50 text-purple-600' },
                  ].map((s, i) => (
                    <div key={i} className={`rounded-xl p-4 ${s.color} border border-gray-100`} data-testid={`acct-${i}`}>
                      <div className="text-lg font-extrabold" style={{fontFamily:'Manrope,sans-serif'}}>{s.value}</div>
                      <div className="text-xs font-semibold mt-1 opacity-80">{s.label}</div>
                    </div>
                  ))}
                </div>

                <div className="grid grid-cols-3 gap-4 mb-6">
                  <div className="bg-white rounded-xl p-4 border border-gray-100 text-center">
                    <CreditCard className="w-6 h-6 text-green-500 mx-auto mb-1" />
                    <div className="text-xl font-extrabold text-gray-900">{accounting.transaction_count}</div>
                    <div className="text-xs text-gray-500 font-semibold">Paid Transactions</div>
                  </div>
                  <div className="bg-white rounded-xl p-4 border border-gray-100 text-center">
                    <div className="text-xl font-extrabold text-green-600">{formatLKR(accounting.pending_payouts)}</div>
                    <div className="text-xs text-gray-500 font-semibold">Pending Payouts</div>
                  </div>
                  <div className="bg-white rounded-xl p-4 border border-gray-100 text-center">
                    <div className="text-xl font-extrabold text-green-600">{formatLKR(accounting.completed_payouts)}</div>
                    <div className="text-xs text-gray-500 font-semibold">Completed Payouts</div>
                  </div>
                </div>

                {accounting.payouts?.filter(p => p.status === 'pending').length > 0 && (
                  <div className="mb-6">
                    <h3 className="text-sm font-bold text-gray-800 mb-3">Pending Payouts to Handymen</h3>
                    <div className="space-y-2">
                      {accounting.payouts.filter(p => p.status === 'pending').map(p => (
                        <div key={p.id} className="bg-white rounded-lg p-3 border border-gray-100 flex items-center justify-between" data-testid={`payout-${p.id}`}>
                          <div>
                            <span className="font-semibold text-sm text-gray-900">{p.handyman_name}</span>
                            <span className="text-xs text-gray-500 ml-2">Booking: {p.booking_id?.slice(0, 8)}...</span>
                          </div>
                          <div className="flex items-center gap-3">
                            <span className="font-bold text-gray-900">{formatLKR(p.amount)}</span>
                            <button onClick={() => markPayoutPaid(p.id)} className="flex items-center gap-1 px-3 py-1.5 bg-green-500 text-white text-xs font-semibold rounded-lg hover:bg-green-600" data-testid={`mark-paid-${p.id}`}>
                              <ArrowUpRight className="w-3 h-3" />Mark Paid
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {accounting.transactions?.length > 0 && (
                  <div>
                    <h3 className="text-sm font-bold text-gray-800 mb-3">Recent Transactions</h3>
                    <div className="bg-white rounded-xl border border-gray-100 overflow-hidden">
                      <table className="w-full">
                        <thead className="bg-gray-50">
                          <tr>
                            <th className="px-3 py-2 text-left text-xs font-semibold text-gray-600">Customer</th>
                            <th className="px-3 py-2 text-left text-xs font-semibold text-gray-600">Handyman</th>
                            <th className="px-3 py-2 text-right text-xs font-semibold text-gray-600">Job</th>
                            <th className="px-3 py-2 text-right text-xs font-semibold text-gray-600">Fee</th>
                            <th className="px-3 py-2 text-right text-xs font-semibold text-gray-600">VAT</th>
                            <th className="px-3 py-2 text-right text-xs font-semibold text-gray-600">Total</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-50">
                          {accounting.transactions.map(tx => (
                            <tr key={tx.id} className="hover:bg-gray-50">
                              <td className="px-3 py-2 text-sm text-gray-900">{tx.customer_name}</td>
                              <td className="px-3 py-2 text-sm text-gray-600">{tx.handyman_name}</td>
                              <td className="px-3 py-2 text-sm text-right text-gray-600">{formatLKR(tx.job_price)}</td>
                              <td className="px-3 py-2 text-sm text-right text-green-600 font-semibold">{formatLKR(tx.topbass_fee)}</td>
                              <td className="px-3 py-2 text-sm text-right text-blue-600">{formatLKR(tx.vat_amount)}</td>
                              <td className="px-3 py-2 text-sm text-right font-bold text-gray-900">{formatLKR(tx.amount)}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}

                {accounting.transaction_count === 0 && (
                  <div className="bg-white rounded-2xl p-12 text-center border border-gray-100">
                    <Receipt className="w-12 h-12 text-gray-300 mx-auto mb-3" />
                    <p className="text-lg font-semibold text-gray-600">No transactions yet</p>
                    <p className="text-sm text-gray-400">Revenue will appear here once customers start paying</p>
                  </div>
                )}
              </div>
            )}

            {/* SMS NOTIFICATIONS */}
            {activeTab === 'sms' && (
              <div data-testid="sms-section">
                <div className="bg-white rounded-2xl p-6 border border-gray-100 shadow-sm">
                  <h2 className="text-lg font-bold text-gray-900 mb-4" style={{fontFamily:'Manrope,sans-serif'}}>SMS Notifications (Twilio)</h2>
                  
                  <div className={`rounded-xl p-4 mb-5 ${smsStatus?.configured ? 'bg-green-50 border border-green-200' : 'bg-orange-50 border border-orange-200'}`}>
                    <div className="flex items-center gap-2 mb-1">
                      <div className={`w-3 h-3 rounded-full ${smsStatus?.configured ? 'bg-green-500' : 'bg-orange-500'}`}></div>
                      <span className={`font-bold text-sm ${smsStatus?.configured ? 'text-green-700' : 'text-orange-700'}`}>
                        {smsStatus?.configured ? 'SMS Active' : 'SMS Not Configured'}
                      </span>
                    </div>
                    {!smsStatus?.configured && (
                      <p className="text-xs text-orange-600 mt-1">
                        Add these to <code className="bg-white px-1 rounded">backend/.env</code>: <code className="bg-white px-1 rounded">TWILIO_ACCOUNT_SID</code>, <code className="bg-white px-1 rounded">TWILIO_AUTH_TOKEN</code>, <code className="bg-white px-1 rounded">TWILIO_PHONE_NUMBER</code>
                      </p>
                    )}
                  </div>

                  <div className="mb-5">
                    <h3 className="text-sm font-bold text-gray-800 mb-3">SMS will be sent for:</h3>
                    <div className="space-y-2">
                      {[
                        'New booking request (to handyman)',
                        'Price quote sent (to customer)',
                        'Booking status updates (accepted, in progress, completed)',
                        'Payment received — COD or Bank Transfer (to handyman)',
                        'Bank transfer pending verification (to admin)',
                        'New referral signup (to referring handyman)',
                      ].map((event, i) => (
                        <div key={i} className="flex items-center gap-2 text-sm text-gray-600">
                          <CheckCircle className={`w-4 h-4 ${smsStatus?.configured ? 'text-green-500' : 'text-gray-300'}`} />
                          {event}
                        </div>
                      ))}
                    </div>
                  </div>

                  {smsStatus?.configured && (
                    <div className="border-t border-gray-100 pt-4">
                      <h3 className="text-sm font-bold text-gray-800 mb-2">Send Test SMS</h3>
                      <div className="flex items-center gap-2">
                        <input type="tel" value={testPhone} onChange={(e) => setTestPhone(e.target.value)}
                          placeholder="07XXXXXXXX" className="flex-1 px-3 py-2 border-2 border-gray-200 rounded-lg text-sm focus:border-green-500 outline-none"
                          data-testid="test-sms-phone" />
                        <button onClick={sendTestSms} disabled={smsSending || !testPhone}
                          className="px-4 py-2 bg-green-600 text-white text-sm font-semibold rounded-lg hover:bg-green-700 disabled:opacity-50"
                          data-testid="send-test-sms-btn">
                          {smsSending ? 'Sending...' : 'Send Test'}
                        </button>
                      </div>
                      {smsResult && (
                        <p className={`text-xs mt-2 font-semibold ${smsResult.includes('success') ? 'text-green-600' : 'text-red-600'}`}>{smsResult}</p>
                      )}
                    </div>
                  )}

                  <div className="mt-5 bg-gray-50 rounded-xl p-4">
                    <h3 className="text-sm font-bold text-gray-800 mb-2">How to set up Twilio:</h3>
                    <ol className="space-y-1.5 text-xs text-gray-600">
                      <li>1. Go to <a href="https://console.twilio.com" target="_blank" rel="noopener noreferrer" className="text-green-600 underline">console.twilio.com</a> and create an account</li>
                      <li>2. Get your Account SID and Auth Token from the dashboard</li>
                      <li>3. Buy a phone number (or use the trial number)</li>
                      <li>4. Add the 3 values to your backend/.env file</li>
                      <li>5. Restart the backend — SMS will start working automatically</li>
                    </ol>
                  </div>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default AdminDashboard;
