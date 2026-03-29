import React, { useState, useEffect } from 'react';
import { Link, useParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuth, API } from '../AuthContext';
import Navbar from '../components/Navbar';
import axios from 'axios';
import { Star, MapPin, Phone, Clock, ChevronLeft, MessageSquare, Briefcase, Send, Share2, Lock } from 'lucide-react';

const HandymanDetailPage = () => {
  const { t, i18n } = useTranslation();
  const { userId } = useParams();
  const { user, token } = useAuth();
  const [profile, setProfile] = useState(null);
  const [reviews, setReviews] = useState([]);
  const [loading, setLoading] = useState(true);
  const [services, setServices] = useState([]);
  const [showBooking, setShowBooking] = useState(false);
  const [bookingForm, setBookingForm] = useState({ description: '', preferred_date: '', preferred_time: '', address: '', district: '', phone: '' });
  const [submitting, setSubmitting] = useState(false);
  const [bookingMsg, setBookingMsg] = useState('');
  const [showReview, setShowReview] = useState(false);
  const [reviewForm, setReviewForm] = useState({ rating: 5, comment: '' });
  const lang = i18n.language;

  useEffect(() => {
    const headers = token ? { Authorization: `Bearer ${token}` } : {};
    Promise.all([
      axios.get(`${API}/handymen/${userId}`, { headers }),
      axios.get(`${API}/services`)
    ]).then(([hRes, sRes]) => {
      setProfile(hRes.data.profile);
      setReviews(hRes.data.reviews || []);
      setServices(sRes.data.services);
    }).catch(console.error).finally(() => setLoading(false));
  }, [userId, token]);

  const getServiceName = (id) => {
    const s = services.find(sv => sv.id === id);
    if (!s) return id;
    if (lang === 'si') return s.name_si;
    if (lang === 'ta') return s.name_ta;
    return s.name_en;
  };

  const handleBooking = async (e) => {
    e.preventDefault();
    if (!user) return;
    setSubmitting(true);
    try {
      const payload = {
        handyman_id: userId,
        service_id: profile.services?.[0] || 'other',
        ...bookingForm
      };
      await axios.post(`${API}/bookings/create`, payload, { headers: { Authorization: `Bearer ${token}` } });
      setBookingMsg('success');
      setShowBooking(false);
      setBookingForm({ description: '', preferred_date: '', preferred_time: '', address: '', district: '', phone: '' });
    } catch (err) {
      setBookingMsg(err.response?.data?.detail || 'Booking failed');
    } finally { setSubmitting(false); }
  };

  const handleReview = async (e) => {
    e.preventDefault();
    if (!user) return;
    try {
      await axios.post(`${API}/reviews/${userId}`, reviewForm, { headers: { Authorization: `Bearer ${token}` } });
      const headers = token ? { Authorization: `Bearer ${token}` } : {};
      const res = await axios.get(`${API}/handymen/${userId}`, { headers });
      setProfile(res.data.profile);
      setReviews(res.data.reviews || []);
      setShowReview(false);
      setReviewForm({ rating: 5, comment: '' });
    } catch (err) {
      alert(err.response?.data?.detail || 'Review failed');
    }
  };

  const shareOnWhatsApp = () => {
    const profileUrl = window.location.href;
    const text = `Check out ${profile.full_name} on TopBass - Sri Lanka's trusted handyman marketplace!\n\n${profileUrl}`;
    window.open(`https://wa.me/?text=${encodeURIComponent(text)}`, '_blank');
  };

  if (loading) return (
    <div className="min-h-screen bg-[#F5F7F3]">
      <Navbar />
      <div className="flex justify-center py-20"><div className="animate-spin rounded-full h-10 w-10 border-4 border-green-500 border-t-transparent"></div></div>
    </div>
  );

  if (!profile) return (
    <div className="min-h-screen bg-[#F5F7F3]">
      <Navbar />
      <div className="max-w-3xl mx-auto px-4 py-12 text-center">
        <p className="text-lg font-semibold text-gray-600">{t('common.noResults')}</p>
        <Link to="/" className="text-green-600 font-semibold mt-2 inline-block">{t('common.back')}</Link>
      </div>
    </div>
  );

  const hasBooking = profile.has_active_booking;

  return (
    <div className="min-h-screen bg-[#F5F7F3]">
      <Navbar />
      <div className="max-w-3xl mx-auto px-4 py-6">
        <Link to="/" className="inline-flex items-center gap-1 text-sm text-gray-500 hover:text-green-600 mb-4" data-testid="back-btn">
          <ChevronLeft className="w-4 h-4" />{t('common.back')}
        </Link>

        {/* Profile Card */}
        <div className="bg-white rounded-2xl p-6 border border-gray-100 shadow-sm mb-4" data-testid="handyman-profile-card">
          <div className="flex items-start justify-between mb-4">
            <div>
              <h1 className="text-2xl font-extrabold text-gray-900" style={{fontFamily:'Manrope,sans-serif'}} data-testid="handyman-name">{profile.full_name}</h1>
              {profile.shop_name && <span className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full mt-1 inline-block">{profile.shop_name}</span>}
              {profile.partner_tier && (
                <span className={`text-xs px-2.5 py-0.5 rounded-full mt-1 inline-block font-bold ml-1 ${
                  profile.partner_tier.tier === 'platinum' ? 'bg-gray-900 text-white' :
                  profile.partner_tier.tier === 'gold' ? 'bg-amber-100 text-amber-700 border border-amber-300' :
                  'bg-gray-200 text-gray-700'
                }`} data-testid="partner-badge">{profile.partner_tier.label}</span>
              )}
            </div>
            <div className="text-right">
              <div className="flex items-center gap-1">
                <Star className="w-5 h-5 text-amber-400 fill-amber-400" />
                <span className="text-lg font-bold text-gray-900">{profile.rating || '—'}</span>
                <span className="text-sm text-gray-400">({profile.review_count || 0})</span>
              </div>
            </div>
          </div>

          <div className="flex flex-wrap gap-3 text-sm text-gray-600 mb-4">
            {profile.experience_years > 0 && (
              <span className="flex items-center gap-1.5 bg-gray-50 px-3 py-1.5 rounded-lg">
                <Clock className="w-4 h-4 text-gray-400" />{profile.experience_years} {t('handyman.experience')}
              </span>
            )}
            <span className="flex items-center gap-1.5 bg-gray-50 px-3 py-1.5 rounded-lg">
              <MapPin className="w-4 h-4 text-gray-400" />{profile.district}
            </span>
            {profile.jobs_completed > 0 && (
              <span className="flex items-center gap-1.5 bg-gray-50 px-3 py-1.5 rounded-lg">
                <Briefcase className="w-4 h-4 text-gray-400" />{profile.jobs_completed} {t('handyman.jobsCompleted')}
              </span>
            )}
            {profile.hourly_rate > 0 && (
              <span className="bg-green-50 text-green-700 px-3 py-1.5 rounded-lg font-semibold">LKR {profile.hourly_rate} {t('handyman.rate')}</span>
            )}
          </div>

          {profile.description && <p className="text-sm text-gray-600 mb-4">{profile.description}</p>}

          {/* Services */}
          {profile.services?.length > 0 && (
            <div className="mb-4">
              <h3 className="text-xs font-semibold text-gray-500 uppercase mb-2">{t('nav.services')}</h3>
              <div className="flex flex-wrap gap-2">
                {profile.services.map(s => (
                  <span key={s} className="bg-green-50 text-green-700 text-xs font-semibold px-3 py-1 rounded-full">{getServiceName(s)}</span>
                ))}
              </div>
            </div>
          )}

          {/* Districts Served */}
          {profile.districts_served?.length > 0 && (
            <div className="mb-4">
              <h3 className="text-xs font-semibold text-gray-500 uppercase mb-2">{t('auth.district')}</h3>
              <div className="flex flex-wrap gap-2">
                {profile.districts_served.map(d => (
                  <span key={d} className="bg-gray-100 text-gray-700 text-xs font-semibold px-3 py-1 rounded-full">{d}</span>
                ))}
              </div>
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex flex-wrap gap-3 mt-5">
            {/* Phone — only visible if has active booking */}
            {hasBooking && profile.phone ? (
              <a href={`tel:${profile.phone}`} className="flex items-center gap-2 px-5 py-2.5 bg-green-500 text-white font-semibold rounded-xl hover:bg-green-600 transition-colors" data-testid="call-btn">
                <Phone className="w-4 h-4" />{t('handyman.callNow')}
              </a>
            ) : (
              <div className="flex items-center gap-2 px-5 py-2.5 bg-gray-100 text-gray-500 font-semibold rounded-xl cursor-default" data-testid="call-locked">
                <Lock className="w-4 h-4" />
                {profile.phone_masked ? `${profile.phone_masked}` : 'Contact hidden'}
                <span className="text-xs font-normal ml-1">— Book first</span>
              </div>
            )}

            {/* WhatsApp — only visible if has active booking */}
            {hasBooking && profile.whatsapp && (
              <a href={`https://wa.me/${profile.whatsapp.replace(/[^0-9]/g, '')}`} target="_blank" rel="noopener noreferrer"
                className="flex items-center gap-2 px-5 py-2.5 bg-emerald-500 text-white font-semibold rounded-xl hover:bg-emerald-600 transition-colors" data-testid="whatsapp-btn">
                <MessageSquare className="w-4 h-4" />{t('handyman.whatsapp')}
              </a>
            )}

            {/* Book Now button */}
            {user && user.role === 'customer' && (
              <button onClick={() => setShowBooking(true)}
                className="flex items-center gap-2 px-5 py-2.5 bg-green-600 text-white font-semibold rounded-xl hover:bg-green-700 transition-colors" data-testid="book-btn">
                <Send className="w-4 h-4" />{t('handyman.bookNow')}
              </button>
            )}

            {/* Share on WhatsApp — always visible */}
            <button onClick={shareOnWhatsApp}
              className="flex items-center gap-2 px-5 py-2.5 bg-[#25D366] text-white font-semibold rounded-xl hover:bg-[#1da851] transition-colors" data-testid="share-whatsapp-btn">
              <Share2 className="w-4 h-4" />Share on WhatsApp
            </button>
          </div>

          {!user && (
            <p className="text-xs text-gray-500 mt-3">
              <Link to="/login" className="text-green-600 font-semibold hover:underline">Login</Link> and book this handyman to see their contact details
            </p>
          )}

          {bookingMsg === 'success' && (
            <div className="mt-3 bg-green-50 text-green-700 text-sm font-medium px-4 py-2.5 rounded-lg" data-testid="booking-success">Booking request sent successfully!</div>
          )}
        </div>

        {/* Booking Form */}
        {showBooking && (
          <div className="bg-white rounded-2xl p-6 border border-gray-100 shadow-sm mb-4" data-testid="booking-form">
            <h2 className="text-lg font-bold text-gray-900 mb-4" style={{fontFamily:'Manrope,sans-serif'}}>{t('handyman.bookNow')}</h2>
            <form onSubmit={handleBooking} className="space-y-3">
              <div>
                <label className="block text-xs font-semibold text-gray-600 mb-1">{t('booking.describe')} *</label>
                <textarea required value={bookingForm.description} onChange={(e) => setBookingForm(f => ({...f, description: e.target.value}))}
                  className="w-full px-3 py-2 border-2 border-gray-200 rounded-xl text-sm focus:border-green-500 outline-none" rows="3" data-testid="booking-description" />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-gray-600 mb-1">{t('booking.date')}</label>
                  <input type="date" value={bookingForm.preferred_date} onChange={(e) => setBookingForm(f => ({...f, preferred_date: e.target.value}))}
                    className="w-full px-3 py-2 border-2 border-gray-200 rounded-xl text-sm focus:border-green-500 outline-none" data-testid="booking-date" />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-gray-600 mb-1">{t('booking.time')}</label>
                  <input type="time" value={bookingForm.preferred_time} onChange={(e) => setBookingForm(f => ({...f, preferred_time: e.target.value}))}
                    className="w-full px-3 py-2 border-2 border-gray-200 rounded-xl text-sm focus:border-green-500 outline-none" data-testid="booking-time" />
                </div>
              </div>
              <div>
                <label className="block text-xs font-semibold text-gray-600 mb-1">{t('booking.address')}</label>
                <input type="text" value={bookingForm.address} onChange={(e) => setBookingForm(f => ({...f, address: e.target.value}))}
                  className="w-full px-3 py-2 border-2 border-gray-200 rounded-xl text-sm focus:border-green-500 outline-none" data-testid="booking-address" />
              </div>
              <div>
                <label className="block text-xs font-semibold text-gray-600 mb-1">{t('auth.phone')}</label>
                <input type="tel" value={bookingForm.phone} onChange={(e) => setBookingForm(f => ({...f, phone: e.target.value}))}
                  className="w-full px-3 py-2 border-2 border-gray-200 rounded-xl text-sm focus:border-green-500 outline-none" placeholder="07XXXXXXXX" data-testid="booking-phone" />
              </div>
              <div className="flex gap-3 pt-2">
                <button type="button" onClick={() => setShowBooking(false)} className="flex-1 py-2.5 bg-gray-100 text-gray-700 font-semibold rounded-xl hover:bg-gray-200">{t('common.cancel')}</button>
                <button type="submit" disabled={submitting} className="flex-1 py-2.5 bg-green-600 text-white font-semibold rounded-xl hover:bg-green-700 disabled:opacity-50" data-testid="booking-submit">
                  {submitting ? '...' : t('booking.submit')}
                </button>
              </div>
            </form>
          </div>
        )}

        {/* Reviews */}
        <div className="bg-white rounded-2xl p-6 border border-gray-100 shadow-sm" data-testid="reviews-section">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-bold text-gray-900" style={{fontFamily:'Manrope,sans-serif'}}>{t('handyman.reviews')} ({reviews.length})</h2>
            {user && user.role === 'customer' && (
              <button onClick={() => setShowReview(!showReview)} className="text-sm text-green-600 font-semibold hover:text-green-700" data-testid="write-review-btn">
                Write Review
              </button>
            )}
          </div>

          {showReview && (
            <form onSubmit={handleReview} className="mb-4 p-4 bg-green-50 rounded-xl space-y-3" data-testid="review-form">
              <div>
                <label className="block text-xs font-semibold text-gray-600 mb-1">Rating</label>
                <div className="flex gap-1">
                  {[1, 2, 3, 4, 5].map(n => (
                    <button key={n} type="button" onClick={() => setReviewForm(f => ({...f, rating: n}))}
                      className="p-1" data-testid={`star-${n}`}>
                      <Star className={`w-6 h-6 ${n <= reviewForm.rating ? 'text-amber-400 fill-amber-400' : 'text-gray-300'}`} />
                    </button>
                  ))}
                </div>
              </div>
              <textarea value={reviewForm.comment} onChange={(e) => setReviewForm(f => ({...f, comment: e.target.value}))}
                className="w-full px-3 py-2 border-2 border-gray-200 rounded-xl text-sm focus:border-green-500 outline-none" rows="2" placeholder="Your review..." data-testid="review-comment" />
              <button type="submit" className="px-4 py-2 bg-green-600 text-white font-semibold rounded-lg hover:bg-green-700 text-sm" data-testid="review-submit">Submit Review</button>
            </form>
          )}

          {reviews.length === 0 ? (
            <p className="text-sm text-gray-500">{t('handyman.noReviews')}</p>
          ) : (
            <div className="space-y-3">
              {reviews.map(r => (
                <div key={r.id} className="border-b border-gray-100 pb-3 last:border-0" data-testid={`review-${r.id}`}>
                  <div className="flex items-center gap-2 mb-1">
                    <span className="font-semibold text-sm text-gray-800">{r.customer_name}</span>
                    <div className="flex gap-0.5">
                      {[1, 2, 3, 4, 5].map(n => (
                        <Star key={n} className={`w-3 h-3 ${n <= r.rating ? 'text-amber-400 fill-amber-400' : 'text-gray-300'}`} />
                      ))}
                    </div>
                  </div>
                  {r.comment && <p className="text-sm text-gray-600">{r.comment}</p>}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default HandymanDetailPage;
