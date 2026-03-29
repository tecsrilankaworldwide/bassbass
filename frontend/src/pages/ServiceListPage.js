import React, { useState, useEffect } from 'react';
import { Link, useParams, useSearchParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { API } from '../AuthContext';
import Navbar from '../components/Navbar';
import axios from 'axios';
import { Star, MapPin, Clock, ChevronLeft, Navigation } from 'lucide-react';

const ServiceListPage = () => {
  const { t, i18n } = useTranslation();
  const { serviceId } = useParams();
  const [searchParams] = useSearchParams();
  const district = searchParams.get('district') || '';
  const [handymen, setHandymen] = useState([]);
  const [loading, setLoading] = useState(true);
  const [services, setServices] = useState([]);
  const [selectedDistrict, setSelectedDistrict] = useState(district);
  const [districts, setDistricts] = useState([]);
  const [sortByNearby, setSortByNearby] = useState(false);
  const lang = i18n.language;

  useEffect(() => {
    axios.get(`${API}/services`).then(res => { setServices(res.data.services); setDistricts(res.data.districts); });
  }, []);

  useEffect(() => {
    setLoading(true);
    if (sortByNearby && selectedDistrict) {
      const params = new URLSearchParams({ district: selectedDistrict, service: serviceId, radius: '120' });
      axios.get(`${API}/handymen/nearby?${params}`).then(res => setHandymen(res.data.handymen))
        .catch(console.error).finally(() => setLoading(false));
    } else {
      const params = new URLSearchParams();
      params.set('service', serviceId);
      if (selectedDistrict) params.set('district', selectedDistrict);
      axios.get(`${API}/handymen?${params}`).then(res => setHandymen(res.data.handymen))
        .catch(console.error).finally(() => setLoading(false));
    }
  }, [serviceId, selectedDistrict, sortByNearby]);

  const currentService = services.find(s => s.id === serviceId);
  const serviceName = currentService ? (lang === 'si' ? currentService.name_si : lang === 'ta' ? currentService.name_ta : currentService.name_en) : serviceId;

  return (
    <div className="min-h-screen bg-[#F5F7F3]">
      <Navbar />
      <div className="max-w-4xl mx-auto px-4 py-6">
        <Link to="/" className="inline-flex items-center gap-1 text-sm text-gray-500 hover:text-green-600 mb-4" data-testid="back-btn">
          <ChevronLeft className="w-4 h-4" />{t('common.back')}
        </Link>
        <h1 className="text-2xl font-extrabold text-gray-900 mb-2" style={{fontFamily:'Manrope,sans-serif'}} data-testid="service-title">{serviceName}</h1>

        {/* District filter + Nearby toggle */}
        <div className="flex items-center gap-3 mb-6 flex-wrap">
          <div className="flex items-center gap-2">
            <MapPin className="w-4 h-4 text-amber-500" />
            <select value={selectedDistrict} onChange={(e) => setSelectedDistrict(e.target.value)}
              className="text-sm border-2 border-gray-200 rounded-lg px-3 py-1.5 focus:border-green-500 outline-none" data-testid="service-district-filter">
              <option value="">{t('home.allDistricts')}</option>
              {districts.map(d => <option key={d} value={d}>{d}</option>)}
            </select>
          </div>

          {selectedDistrict && (
            <button
              onClick={() => setSortByNearby(!sortByNearby)}
              className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                sortByNearby
                  ? 'bg-green-600 text-white shadow-md'
                  : 'bg-white text-gray-600 border border-gray-200 hover:border-green-400'
              }`}
              data-testid="nearby-toggle">
              <Navigation className="w-3.5 h-3.5" />
              {sortByNearby ? 'Nearby Mode ON' : 'Show Nearby'}
            </button>
          )}

          <span className="text-sm text-gray-500">{handymen.length} found</span>
        </div>

        {loading ? (
          <div className="flex justify-center py-12"><div className="animate-spin rounded-full h-10 w-10 border-4 border-green-500 border-t-transparent"></div></div>
        ) : handymen.length === 0 ? (
          <div className="bg-white rounded-2xl p-12 text-center border border-gray-100">
            <p className="text-lg font-semibold text-gray-600 mb-2">{t('common.noResults')}</p>
            <p className="text-sm text-gray-500">No handymen available for this service{selectedDistrict ? ` in ${selectedDistrict}` : ''} yet</p>
          </div>
        ) : (
          <div className="space-y-3">
            {handymen.map(h => (
              <Link key={h.user_id} to={`/handyman/${h.user_id}`}
                className="block bg-white rounded-xl p-4 border border-gray-100 hover:border-green-400 hover:shadow-md transition-all"
                data-testid={`handyman-card-${h.user_id}`}>
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <h3 className="font-bold text-gray-900">{h.full_name}</h3>
                      {h.shop_name && <span className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full">{h.shop_name}</span>}
                      {h.partner_tier && (
                        <span className={`text-xs px-2 py-0.5 rounded-full font-bold ${
                          h.partner_tier.tier === 'platinum' ? 'bg-gray-900 text-white' :
                          h.partner_tier.tier === 'gold' ? 'bg-amber-100 text-amber-700' :
                          'bg-gray-200 text-gray-700'
                        }`}>{h.partner_tier.label}</span>
                      )}
                    </div>
                    <div className="flex flex-wrap gap-3 text-xs text-gray-500 mb-2">
                      {h.experience_years > 0 && <span className="flex items-center gap-1"><Clock className="w-3 h-3" />{h.experience_years} {t('handyman.experience')}</span>}
                      <span className="flex items-center gap-1"><MapPin className="w-3 h-3" />{h.district}</span>
                      {h.distance_km !== undefined && h.distance_km < 999 && (
                        <span className="flex items-center gap-1 text-green-600 font-semibold">
                          <Navigation className="w-3 h-3" />{h.distance_km} km away
                        </span>
                      )}
                      {h.jobs_completed > 0 && <span>{h.jobs_completed} {t('handyman.jobsCompleted')}</span>}
                    </div>
                    {h.description && <p className="text-sm text-gray-600 line-clamp-2">{h.description}</p>}
                  </div>
                  <div className="text-right ml-4 flex-shrink-0">
                    <div className="flex items-center gap-1 mb-1">
                      <Star className="w-4 h-4 text-amber-400 fill-amber-400" />
                      <span className="text-sm font-bold text-gray-900">{h.rating || '—'}</span>
                      <span className="text-xs text-gray-400">({h.review_count || 0})</span>
                    </div>
                    {h.hourly_rate > 0 && <p className="text-xs text-gray-500">LKR {h.hourly_rate} {t('handyman.rate')}</p>}
                    <span className="mt-2 inline-flex items-center gap-1 px-3 py-1.5 bg-green-500 text-white text-xs font-semibold rounded-lg">
                      View Profile
                    </span>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default ServiceListPage;
