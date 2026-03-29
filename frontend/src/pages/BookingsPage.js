import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuth, API } from '../AuthContext';
import Navbar from '../components/Navbar';
import axios from 'axios';
import { Calendar, Clock, MapPin, ChevronLeft, CheckCircle, XCircle, AlertCircle, Loader2, CreditCard, Receipt, MessageSquare, Banknote, QrCode, X, Tag } from 'lucide-react';

const STATUS_CONFIG = {
  pending: { color: 'bg-green-100 text-green-700', icon: Clock },
  quoted: { color: 'bg-indigo-100 text-indigo-700', icon: Receipt },
  accepted: { color: 'bg-blue-100 text-blue-700', icon: CheckCircle },
  in_progress: { color: 'bg-purple-100 text-purple-700', icon: Loader2 },
  completed: { color: 'bg-green-100 text-green-700', icon: CheckCircle },
  rejected: { color: 'bg-red-100 text-red-700', icon: XCircle },
  cancelled: { color: 'bg-gray-100 text-gray-600', icon: XCircle },
};

const BookingsPage = () => {
  const { t } = useTranslation();
  const { user, token } = useAuth();
  const [bookings, setBookings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');
  const [quoteBookingId, setQuoteBookingId] = useState(null);
  const [quotePrice, setQuotePrice] = useState('');
  const [quoting, setQuoting] = useState(false);
  const [paying, setPaying] = useState(null);
  const [showPaymentOptions, setShowPaymentOptions] = useState(null);
  const [showQrModal, setShowQrModal] = useState(null);
  const [qrCodeUrl, setQrCodeUrl] = useState('');
  const [promoCode, setPromoCode] = useState('');
  const [promoApplying, setPromoApplying] = useState(null);
  const [promoResult, setPromoResult] = useState({});
  const headers = { Authorization: `Bearer ${token}` };
  const isHandyman = ['handyman', 'shop'].includes(user?.role);

  useEffect(() => {
    loadBookings();
    axios.get(`${API}/payments/bank-qr`).then(res => setQrCodeUrl(res.data.qr_code_url)).catch(() => {});
  }, []);

  const loadBookings = () => {
    setLoading(true);
    axios.get(`${API}/bookings/my`, { headers })
      .then(res => setBookings(res.data.bookings))
      .catch(console.error)
      .finally(() => setLoading(false));
  };

  const updateStatus = async (bookingId, status) => {
    try {
      await axios.put(`${API}/bookings/${bookingId}/status`, { status }, { headers });
      loadBookings();
    } catch (err) {
      alert(err.response?.data?.detail || 'Update failed');
    }
  };

  const submitQuote = async (bookingId) => {
    if (!quotePrice || parseFloat(quotePrice) <= 0) return;
    setQuoting(true);
    try {
      await axios.put(`${API}/bookings/${bookingId}/quote`, { job_price: parseFloat(quotePrice) }, { headers });
      setQuoteBookingId(null);
      setQuotePrice('');
      loadBookings();
    } catch (err) {
      alert(err.response?.data?.detail || 'Quote failed');
    } finally { setQuoting(false); }
  };

  const initiateStripePayment = async (bookingId) => {
    setPaying(bookingId);
    try {
      const res = await axios.post(`${API}/payments/create-checkout`, {
        booking_id: bookingId,
        origin_url: window.location.origin
      }, { headers });
      window.location.href = res.data.url;
    } catch (err) {
      alert(err.response?.data?.detail || 'Payment failed');
      setPaying(null);
    }
  };

  const initiateCOD = async (bookingId) => {
    setPaying(bookingId);
    try {
      await axios.post(`${API}/payments/cod`, { booking_id: bookingId }, { headers });
      setShowPaymentOptions(null);
      loadBookings();
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed');
    } finally { setPaying(null); }
  };

  const initiateBankTransfer = async (bookingId) => {
    setPaying(bookingId);
    try {
      await axios.post(`${API}/payments/bank-transfer`, { booking_id: bookingId }, { headers });
      setShowQrModal(null);
      setShowPaymentOptions(null);
      loadBookings();
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed');
    } finally { setPaying(null); }
  };

  const applyPromo = async (bookingId) => {
    if (!promoCode.trim()) return;
    setPromoApplying(bookingId);
    try {
      const res = await axios.post(`${API}/promo/apply`, { code: promoCode, booking_id: bookingId }, { headers });
      setPromoResult(prev => ({ ...prev, [bookingId]: { success: true, msg: res.data.message, discount: res.data.discount_amount } }));
      setPromoCode('');
      loadBookings();
    } catch (err) {
      setPromoResult(prev => ({ ...prev, [bookingId]: { success: false, msg: err.response?.data?.detail || 'Invalid code' } }));
    } finally { setPromoApplying(null); }
  };

  const filtered = filter === 'all' ? bookings : bookings.filter(b => b.status === filter);

  const getStatusLabel = (status) => {
    const map = { pending: t('booking.pending'), accepted: t('booking.accepted'), in_progress: t('booking.inProgress'), completed: t('booking.completed'), rejected: t('booking.rejected'), cancelled: t('booking.cancelled'), quoted: t('booking.quoted') };
    return map[status] || status;
  };

  const formatLKR = (n) => n ? `LKR ${Number(n).toLocaleString('en-LK', { minimumFractionDigits: 2 })}` : '';

  const getPaymentStatusLabel = (b) => {
    if (b.payment_status === 'paid') return { text: 'Paid', color: 'text-green-600' };
    if (b.payment_status === 'cod_pending') return { text: 'COD — Pay on completion', color: 'text-orange-600' };
    if (b.payment_status === 'pending_verification') return { text: 'Bank Transfer — Pending verification', color: 'text-blue-600' };
    return null;
  };

  return (
    <div className="min-h-screen bg-[#F5F7F3]">
      <Navbar />
      <div className="max-w-3xl mx-auto px-4 py-6">
        <Link to="/" className="inline-flex items-center gap-1 text-sm text-gray-500 hover:text-green-600 mb-4" data-testid="back-btn">
          <ChevronLeft className="w-4 h-4" />{t('common.back')}
        </Link>
        <h1 className="text-2xl font-extrabold text-gray-900 mb-4" style={{fontFamily:'Manrope,sans-serif'}} data-testid="bookings-title">{t('nav.bookings')}</h1>

        {/* Filter tabs */}
        <div className="flex gap-2 mb-6 flex-wrap" data-testid="booking-filters">
          {['all', 'pending', 'quoted', 'accepted', 'in_progress', 'completed', 'cancelled'].map(f => (
            <button key={f} onClick={() => setFilter(f)}
              className={`px-3 py-1.5 text-xs font-semibold rounded-full transition-colors ${
                filter === f ? 'bg-green-600 text-white' : 'bg-white text-gray-600 border border-gray-200 hover:border-green-400'
              }`} data-testid={`filter-${f}`}>
              {f === 'all' ? 'All' : getStatusLabel(f)}
            </button>
          ))}
        </div>

        {loading ? (
          <div className="flex justify-center py-12"><div className="animate-spin rounded-full h-10 w-10 border-4 border-green-500 border-t-transparent"></div></div>
        ) : filtered.length === 0 ? (
          <div className="bg-white rounded-2xl p-12 text-center border border-gray-100">
            <AlertCircle className="w-12 h-12 text-gray-300 mx-auto mb-3" />
            <p className="text-lg font-semibold text-gray-600">{t('common.noResults')}</p>
          </div>
        ) : (
          <div className="space-y-3" data-testid="bookings-list">
            {filtered.map(b => {
              const sc = STATUS_CONFIG[b.status] || STATUS_CONFIG.pending;
              const StatusIcon = sc.icon;
              const payStatus = getPaymentStatusLabel(b);
              return (
                <div key={b.id} className="bg-white rounded-xl p-4 border border-gray-100 shadow-sm" data-testid={`booking-${b.id}`}>
                  <div className="flex items-start justify-between mb-2">
                    <div>
                      <h3 className="font-bold text-gray-900">
                        {isHandyman ? b.customer_name : b.handyman_name}
                      </h3>
                      <span className="text-xs text-gray-500">{b.service_id}</span>
                    </div>
                    <span className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold ${sc.color}`}>
                      <StatusIcon className="w-3 h-3" />{getStatusLabel(b.status)}
                    </span>
                  </div>

                  {b.description && <p className="text-sm text-gray-600 mb-2">{b.description}</p>}

                  <div className="flex flex-wrap gap-3 text-xs text-gray-500 mb-3">
                    {b.preferred_date && <span className="flex items-center gap-1"><Calendar className="w-3 h-3" />{b.preferred_date}</span>}
                    {b.preferred_time && <span className="flex items-center gap-1"><Clock className="w-3 h-3" />{b.preferred_time}</span>}
                    {b.district && <span className="flex items-center gap-1"><MapPin className="w-3 h-3" />{b.district}</span>}
                  </div>

                  {/* Pricing info */}
                  {b.total > 0 && (
                    <div className="bg-gray-50 rounded-lg p-3 mb-3 text-sm" data-testid={`pricing-${b.id}`}>
                      <div className="flex justify-between text-gray-600"><span>{t('billing.serviceCharge')}</span><span>{formatLKR(b.service_charge)}</span></div>
                      <div className="flex justify-between text-gray-600"><span>VAT (18.5%)</span><span>{formatLKR(b.vat_amount)}</span></div>
                      <div className="flex justify-between font-bold text-gray-900 border-t border-gray-200 pt-1.5 mt-1.5"><span>{t('billing.total')}</span><span>{formatLKR(b.total)}</span></div>
                      {payStatus && (
                        <div className={`flex items-center gap-1 mt-2 text-xs font-semibold ${payStatus.color}`}>
                          <CheckCircle className="w-3 h-3" />{payStatus.text}
                        </div>
                      )}
                      {b.promo_applied && (
                        <div className="flex items-center justify-between mt-2 text-xs text-green-600 font-semibold bg-green-50 px-2 py-1 rounded">
                          <span className="flex items-center gap-1"><Tag className="w-3 h-3" />Promo: {b.promo_code} (-{b.promo_discount_percent}%)</span>
                          <span>-{formatLKR(b.promo_discount_amount)}</span>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Promo Code Input — only for quoted, unpaid bookings without promo */}
                  {!isHandyman && b.status === 'quoted' && !b.promo_applied && b.payment_status !== 'paid' && (
                    <div className="mb-3" data-testid={`promo-section-${b.id}`}>
                      <div className="flex items-center gap-2">
                        <div className="relative flex-1">
                          <Tag className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-gray-400" />
                          <input type="text" value={promoCode} onChange={(e) => setPromoCode(e.target.value.toUpperCase())}
                            placeholder="Promo code" className="w-full pl-9 pr-3 py-2 border-2 border-gray-200 rounded-lg text-xs focus:border-green-500 outline-none"
                            data-testid={`promo-input-${b.id}`} />
                        </div>
                        <button onClick={() => applyPromo(b.id)} disabled={promoApplying === b.id || !promoCode.trim()}
                          className="px-3 py-2 bg-orange-500 text-white text-xs font-semibold rounded-lg hover:bg-orange-600 disabled:opacity-50"
                          data-testid={`promo-apply-${b.id}`}>
                          {promoApplying === b.id ? '...' : 'Apply'}
                        </button>
                      </div>
                      {promoResult[b.id] && (
                        <p className={`text-xs mt-1 font-semibold ${promoResult[b.id].success ? 'text-green-600' : 'text-red-600'}`}>
                          {promoResult[b.id].msg}
                        </p>
                      )}
                    </div>
                  )}

                  {/* Action buttons */}
                  <div className="flex gap-2 flex-wrap">
                    {/* Handyman: Quote price for pending booking */}
                    {isHandyman && b.status === 'pending' && (
                      quoteBookingId === b.id ? (
                        <div className="flex gap-2 items-center w-full">
                          <input type="number" min="1" value={quotePrice} onChange={(e) => setQuotePrice(e.target.value)}
                            placeholder="Job price (LKR)" className="flex-1 px-3 py-1.5 border-2 border-gray-200 rounded-lg text-sm focus:border-green-500 outline-none" data-testid={`quote-input-${b.id}`} />
                          <button onClick={() => submitQuote(b.id)} disabled={quoting}
                            className="px-3 py-1.5 bg-green-600 text-white text-xs font-semibold rounded-lg hover:bg-green-700 disabled:opacity-50" data-testid={`quote-submit-${b.id}`}>
                            {quoting ? '...' : t('billing.sendQuote')}
                          </button>
                          <button onClick={() => { setQuoteBookingId(null); setQuotePrice(''); }}
                            className="px-3 py-1.5 bg-gray-200 text-gray-700 text-xs font-semibold rounded-lg">{t('common.cancel')}</button>
                        </div>
                      ) : (
                        <>
                          <button onClick={() => setQuoteBookingId(b.id)}
                            className="px-3 py-1.5 bg-green-600 text-white text-xs font-semibold rounded-lg hover:bg-green-700" data-testid={`quote-btn-${b.id}`}>
                            {t('billing.quotePrice')}
                          </button>
                          <button onClick={() => updateStatus(b.id, 'rejected')}
                            className="px-3 py-1.5 bg-red-500 text-white text-xs font-semibold rounded-lg hover:bg-red-600" data-testid={`reject-${b.id}`}>
                            Reject
                          </button>
                        </>
                      )
                    )}

                    {/* Customer: Payment options for quoted booking */}
                    {!isHandyman && b.status === 'quoted' && b.payment_status !== 'paid' && b.payment_status !== 'cod_pending' && b.payment_status !== 'pending_verification' && (
                      showPaymentOptions === b.id ? (
                        <div className="w-full space-y-2" data-testid={`payment-options-${b.id}`}>
                          <p className="text-xs font-semibold text-gray-700 mb-1">Choose payment method:</p>

                          {/* Stripe */}
                          <button onClick={() => initiateStripePayment(b.id)} disabled={paying === b.id}
                            className="w-full flex items-center gap-3 px-4 py-3 bg-white border-2 border-gray-200 rounded-xl hover:border-green-500 transition-colors text-left"
                            data-testid={`pay-stripe-${b.id}`}>
                            <div className="w-10 h-10 bg-blue-50 rounded-lg flex items-center justify-center">
                              <CreditCard className="w-5 h-5 text-blue-600" />
                            </div>
                            <div>
                              <p className="text-sm font-bold text-gray-900">Pay by Card (Stripe)</p>
                              <p className="text-xs text-gray-500">Visa, Mastercard, international cards</p>
                            </div>
                          </button>

                          {/* Bank QR */}
                          <button onClick={() => setShowQrModal(b.id)}
                            className="w-full flex items-center gap-3 px-4 py-3 bg-white border-2 border-gray-200 rounded-xl hover:border-green-500 transition-colors text-left"
                            data-testid={`pay-qr-${b.id}`}>
                            <div className="w-10 h-10 bg-green-50 rounded-lg flex items-center justify-center">
                              <QrCode className="w-5 h-5 text-green-600" />
                            </div>
                            <div>
                              <p className="text-sm font-bold text-gray-900">Bank of Ceylon Transfer (QR Code)</p>
                              <p className="text-xs text-gray-500">Scan QR — No charge for transfers below LKR 5,000</p>
                            </div>
                          </button>

                          {/* COD */}
                          <button onClick={() => initiateCOD(b.id)} disabled={paying === b.id}
                            className="w-full flex items-center gap-3 px-4 py-3 bg-white border-2 border-gray-200 rounded-xl hover:border-green-500 transition-colors text-left"
                            data-testid={`pay-cod-${b.id}`}>
                            <div className="w-10 h-10 bg-orange-50 rounded-lg flex items-center justify-center">
                              <Banknote className="w-5 h-5 text-orange-600" />
                            </div>
                            <div>
                              <p className="text-sm font-bold text-gray-900">Cash on Delivery</p>
                              <p className="text-xs text-gray-500">Pay the handyman when job is done</p>
                            </div>
                          </button>

                          <button onClick={() => setShowPaymentOptions(null)}
                            className="text-xs text-gray-500 hover:text-gray-700 font-semibold mt-1">Cancel</button>
                        </div>
                      ) : (
                        <button onClick={() => setShowPaymentOptions(b.id)}
                          className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white text-xs font-semibold rounded-lg hover:bg-green-700" data-testid={`pay-btn-${b.id}`}>
                          <CreditCard className="w-4 h-4" />{t('billing.payNow')}
                        </button>
                      )
                    )}

                    {/* Handyman: Start/Complete work */}
                    {isHandyman && b.status === 'accepted' && (
                      <button onClick={() => updateStatus(b.id, 'in_progress')}
                        className="px-3 py-1.5 bg-purple-500 text-white text-xs font-semibold rounded-lg hover:bg-purple-600" data-testid={`start-${b.id}`}>
                        Start Work
                      </button>
                    )}
                    {isHandyman && b.status === 'in_progress' && (
                      <button onClick={() => updateStatus(b.id, 'completed')}
                        className="px-3 py-1.5 bg-green-500 text-white text-xs font-semibold rounded-lg hover:bg-green-600" data-testid={`complete-${b.id}`}>
                        Mark Complete
                      </button>
                    )}

                    {/* Customer: Cancel pending */}
                    {!isHandyman && b.status === 'pending' && (
                      <button onClick={() => updateStatus(b.id, 'cancelled')}
                        className="px-3 py-1.5 bg-gray-200 text-gray-700 text-xs font-semibold rounded-lg hover:bg-gray-300" data-testid={`cancel-${b.id}`}>
                        {t('common.cancel')}
                      </button>
                    )}

                    {/* Chat button for active bookings */}
                    {['quoted', 'accepted', 'in_progress'].includes(b.status) && (
                      <Link to={`/chat/${b.id}`}
                        className="flex items-center gap-1.5 px-3 py-1.5 bg-green-100 text-green-700 text-xs font-semibold rounded-lg hover:bg-green-200" data-testid={`chat-${b.id}`}>
                        <MessageSquare className="w-3 h-3" />{t('nav.chat')}
                      </Link>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* QR Code Modal */}
      {showQrModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 px-4" data-testid="qr-modal">
          <div className="bg-white rounded-2xl p-6 max-w-sm w-full shadow-xl">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-bold text-gray-900" style={{fontFamily:'Manrope,sans-serif'}}>Bank Transfer</h3>
              <button onClick={() => setShowQrModal(null)} className="text-gray-400 hover:text-gray-600" data-testid="close-qr-modal">
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Bank Details */}
            <div className="bg-green-50 border border-green-200 rounded-xl p-3 mb-4 text-sm">
              <p className="font-bold text-green-800 mb-1">Bank of Ceylon — Nugegoda Super Branch</p>
              <p className="text-green-700">Account: TEC Sri Lanka Worldwide (Pvt.) Ltd</p>
            </div>

            {/* QR Code */}
            <div className="bg-gray-50 rounded-xl p-4 flex items-center justify-center mb-3">
              <img src={qrCodeUrl} alt="Bank QR Code" className="w-48 h-48 object-contain" data-testid="qr-image" />
            </div>

            <p className="text-sm text-gray-600 text-center mb-1">
              Scan with your banking app to pay
            </p>
            <p className="text-sm font-bold text-gray-900 text-center mb-3">
              Amount: {formatLKR(bookings.find(b => b.id === showQrModal)?.total)}
            </p>

            {/* Tip about splitting payments */}
            {bookings.find(b => b.id === showQrModal)?.total > 5000 && (
              <div className="bg-orange-50 border border-orange-200 rounded-lg p-2.5 mb-4 text-xs text-orange-700">
                <p className="font-semibold">No bank charges for transfers below LKR 5,000</p>
                <p className="mt-0.5">You can split into multiple transfers of LKR 5,000 each to avoid charges.</p>
              </div>
            )}

            <button onClick={() => initiateBankTransfer(showQrModal)} disabled={paying}
              className="w-full py-3 bg-green-600 text-white font-semibold rounded-xl hover:bg-green-700 disabled:opacity-50 text-sm"
              data-testid="confirm-bank-transfer">
              {paying ? 'Processing...' : 'I have completed the transfer'}
            </button>
            <p className="text-xs text-gray-400 text-center mt-2">Admin will verify your payment</p>
          </div>
        </div>
      )}
    </div>
  );
};

export default BookingsPage;
