import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { API } from '../AuthContext';
import Navbar from '../components/Navbar';
import axios from 'axios';
import { MapPin, Wrench, Search, Star, Navigation } from 'lucide-react';

const LOGO_URL = "https://static.prod-images.emergentagent.com/jobs/3de36ae8-1b12-4467-87dd-98c4995672e0/images/9167dec89e86661796db50a2e4e59dc94289569e89106c1eb1910007d02d8f3f.png";

const HomePage = () => {
  const { t, i18n } = useTranslation();
  const [services, setServices] = useState([]);
  const [districts, setDistricts] = useState([]);
  const [selectedDistrict, setSelectedDistrict] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState(null);
  const [searching, setSearching] = useState(false);
  const [topRated, setTopRated] = useState([]);
  const [nearbyHandymen, setNearbyHandymen] = useState([]);
  const lang = i18n.language;

  useEffect(() => {
    Promise.all([
      axios.get(`${API}/services`),
      axios.get(`${API}/handymen/top-rated`)
    ]).then(([sRes, tRes]) => {
      setServices(sRes.data.services);
      setDistricts(sRes.data.districts);
      setTopRated(tRes.data.handymen);
    }).catch(console.error);
  }, []);

  const getServiceName = (s) => {
    if (lang === 'si') return s.name_si;
    if (lang === 'ta') return s.name_ta;
    return s.name_en;
  };

  useEffect(() => {
    if (selectedDistrict) {
      axios.get(`${API}/handymen/nearby?district=${selectedDistrict}&radius=80&limit=6`)
        .then(res => setNearbyHandymen(res.data.handymen))
        .catch(() => setNearbyHandymen([]));
    } else {
      setNearbyHandymen([]);
    }
  }, [selectedDistrict]);

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!searchQuery.trim()) { setSearchResults(null); return; }
    setSearching(true);
    try {
      const params = new URLSearchParams({ q: searchQuery.trim() });
      if (selectedDistrict) params.append('district', selectedDistrict);
      const res = await axios.get(`${API}/handymen?${params}`);
      setSearchResults(res.data.handymen);
    } catch { setSearchResults([]); }
    finally { setSearching(false); }
  };

  const clearSearch = () => { setSearchQuery(''); setSearchResults(null); };

  return (
    <div className="min-h-screen bg-[#F5F7F3]">
      <Navbar />

      {/* Hero + Search */}
      <div className="bg-gradient-to-b from-green-50 to-[#F5F7F3] py-8 px-4">
        <div className="max-w-3xl mx-auto text-center">
          <img src={LOGO_URL} alt="TopBass" className="w-32 h-32 mx-auto mb-2 object-contain" data-testid="hero-logo" />
          <p className="text-sm text-gray-500 tracking-wide mb-5">{t('app.subtitle')}</p>

          {/* Search bar */}
          <form onSubmit={handleSearch} className="flex items-center gap-2 max-w-lg mx-auto mb-3" data-testid="search-form">
            <div className="flex-1 flex items-center bg-white rounded-xl border-2 border-gray-200 px-3 py-2.5 shadow-sm focus-within:border-green-500 transition-colors">
              <Search className="w-5 h-5 text-green-600 mr-2 flex-shrink-0" />
              <input type="text" value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)}
                placeholder={t('home.searchPlaceholder')}
                className="w-full text-sm text-gray-700 bg-transparent outline-none"
                data-testid="search-input" />
            </div>
            <button type="submit" className="px-5 py-2.5 bg-orange-500 text-white font-semibold rounded-xl hover:bg-orange-600 transition-colors text-sm" data-testid="search-btn">
              {t('home.search')}
            </button>
          </form>

          {/* District Filter */}
          <div className="flex items-center justify-center gap-2 max-w-md mx-auto">
            <div className="flex-1 flex items-center bg-white rounded-xl border-2 border-gray-200 px-3 py-2.5 shadow-sm">
              <MapPin className="w-5 h-5 text-orange-500 mr-2 flex-shrink-0" />
              <select value={selectedDistrict} onChange={(e) => setSelectedDistrict(e.target.value)}
                className="w-full text-sm text-gray-700 bg-transparent outline-none" data-testid="district-filter">
                <option value="">{t('home.allDistricts')}</option>
                {districts.map(d => <option key={d} value={d}>{d}</option>)}
              </select>
            </div>
          </div>
        </div>
      </div>

      {/* Search Results */}
      {searchResults !== null && (
        <div className="max-w-6xl mx-auto px-4 py-6" data-testid="search-results">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-bold text-gray-800" style={{fontFamily:'Manrope,sans-serif'}}>
              {t('home.searchResultsFor')} "{searchQuery}" ({searchResults.length})
            </h2>
            <button onClick={clearSearch} className="text-sm text-green-600 font-semibold hover:text-green-700" data-testid="clear-search">
              {t('home.clearSearch')}
            </button>
          </div>
          {searching ? (
            <div className="flex justify-center py-8"><div className="animate-spin rounded-full h-8 w-8 border-4 border-green-500 border-t-transparent"></div></div>
          ) : searchResults.length === 0 ? (
            <div className="bg-white rounded-2xl p-8 text-center border border-gray-100">
              <p className="text-gray-500 font-medium">{t('common.noResults')}</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
              {searchResults.map(h => (
                <Link key={h.user_id} to={`/handyman/${h.user_id}`}
                  className="bg-white rounded-xl p-4 border border-gray-100 hover:border-green-400 hover:shadow-md transition-all" data-testid={`result-${h.user_id}`}>
                  <h3 className="font-bold text-gray-900">{h.full_name}</h3>
                  {h.shop_name && <span className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full">{h.shop_name}</span>}
                  <div className="flex items-center gap-2 mt-2 text-sm text-gray-500">
                    {h.rating > 0 && <span className="flex items-center gap-1"><Star className="w-3 h-3 text-orange-400 fill-orange-400" />{h.rating}</span>}
                    <span className="flex items-center gap-1"><MapPin className="w-3 h-3" />{h.district}</span>
                  </div>
                  {h.description && <p className="text-xs text-gray-500 mt-2 line-clamp-2">{h.description}</p>}
                </Link>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Services Grid */}
      {searchResults === null && (
        <>
          <div className="max-w-6xl mx-auto px-4 py-8">
            <h2 className="text-xl font-bold text-gray-800 mb-5" style={{fontFamily:'Manrope,sans-serif'}}>{t('nav.services')}</h2>
            <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-5 lg:grid-cols-6 gap-4" data-testid="services-grid">
              {services.map((service) => (
                <Link key={service.id}
                  to={`/services/${service.id}${selectedDistrict ? `?district=${selectedDistrict}` : ''}`}
                  className="flex flex-col items-center p-3 bg-white rounded-2xl border border-gray-100 hover:border-green-400 hover:shadow-lg transition-all group cursor-pointer"
                  data-testid={`service-${service.id}`}>
                  <div className="w-16 h-16 sm:w-20 sm:h-20 flex items-center justify-center mb-2 group-hover:scale-110 transition-transform">
                    {service.image ? (
                      <img src={service.image} alt={getServiceName(service)} className="w-full h-full object-contain" loading="lazy" />
                    ) : (
                      <Wrench className="w-10 h-10 text-gray-800" />
                    )}
                  </div>
                  <span className="text-xs font-semibold text-gray-700 text-center leading-tight">{getServiceName(service)}</span>
                </Link>
              ))}
            </div>
          </div>

          {/* Nearby Handymen (when district selected) */}
          {nearbyHandymen.length > 0 && selectedDistrict && (
            <div className="max-w-6xl mx-auto px-4 pb-4" data-testid="nearby-section">
              <div className="flex items-center gap-2 mb-5">
                <Navigation className="w-5 h-5 text-green-600" />
                <h2 className="text-xl font-bold text-gray-800" style={{fontFamily:'Manrope,sans-serif'}}>Nearby in {selectedDistrict}</h2>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
                {nearbyHandymen.map(h => (
                  <Link key={h.user_id} to={`/handyman/${h.user_id}`}
                    className="bg-white rounded-xl p-4 border border-gray-100 hover:border-green-300 hover:shadow-md transition-all" data-testid={`nearby-${h.user_id}`}>
                    <div className="flex items-start justify-between mb-2">
                      <div>
                        <h3 className="font-bold text-gray-900">{h.full_name}</h3>
                        {h.shop_name && <span className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full">{h.shop_name}</span>}
                      </div>
                      {h.rating > 0 && (
                        <div className="flex items-center gap-1 bg-orange-50 px-2 py-1 rounded-lg">
                          <Star className="w-4 h-4 text-orange-400 fill-orange-400" />
                          <span className="text-sm font-bold text-orange-700">{h.rating}</span>
                        </div>
                      )}
                    </div>
                    <div className="flex items-center gap-2 text-xs text-gray-500 mb-2">
                      <span className="flex items-center gap-1"><MapPin className="w-3 h-3" />{h.district}</span>
                      {h.distance_km !== undefined && h.distance_km < 999 && (
                        <span className="flex items-center gap-1 text-green-600 font-semibold">
                          <Navigation className="w-3 h-3" />{h.distance_km} km
                        </span>
                      )}
                    </div>
                    {h.description && <p className="text-xs text-gray-500 line-clamp-2">{h.description}</p>}
                  </Link>
                ))}
              </div>
            </div>
          )}

          {/* Top Rated */}
          {topRated.length > 0 && (
            <div className="max-w-6xl mx-auto px-4 pb-8" data-testid="top-rated-section">
              <h2 className="text-xl font-bold text-gray-800 mb-5" style={{fontFamily:'Manrope,sans-serif'}}>{t('home.topRated')}</h2>
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
                {topRated.map(h => (
                  <Link key={h.user_id} to={`/handyman/${h.user_id}`}
                    className="bg-white rounded-xl p-4 border border-gray-100 hover:border-green-300 hover:shadow-md transition-all" data-testid={`top-${h.user_id}`}>
                    <div className="flex items-start justify-between mb-2">
                      <div>
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
                      <div className="flex items-center gap-1 bg-orange-50 px-2 py-1 rounded-lg">
                        <Star className="w-4 h-4 text-orange-400 fill-orange-400" />
                        <span className="text-sm font-bold text-orange-700">{h.rating}</span>
                      </div>
                    </div>
                    <div className="flex items-center gap-1 text-xs text-gray-500 mb-2">
                      <MapPin className="w-3 h-3" />{h.district}
                      {h.experience_years > 0 && <span> &middot; {h.experience_years} yrs</span>}
                    </div>
                    {h.description && <p className="text-xs text-gray-500 line-clamp-2">{h.description}</p>}
                  </Link>
                ))}
              </div>
            </div>
          )}
        </>
      )}

      {/* How It Works */}
      <div className="bg-white py-10 px-4 border-t border-gray-100">
        <div className="max-w-4xl mx-auto">
          <h2 className="text-xl font-bold text-gray-800 text-center mb-8" style={{fontFamily:'Manrope,sans-serif'}}>{t('home.howItWorks')}</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {[
              { num: '1', title: t('home.step1'), desc: t('home.step1Desc'), color: 'bg-green-600' },
              { num: '2', title: t('home.step2'), desc: t('home.step2Desc'), color: 'bg-orange-500' },
              { num: '3', title: t('home.step3'), desc: t('home.step3Desc'), color: 'bg-red-500' },
            ].map(step => (
              <div key={step.num} className="text-center">
                <div className={`w-12 h-12 ${step.color} rounded-full flex items-center justify-center mx-auto mb-3 text-white text-xl font-bold`}>{step.num}</div>
                <h3 className="font-bold text-gray-800 mb-1">{step.title}</h3>
                <p className="text-sm text-gray-500">{step.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="bg-green-900 text-green-200 py-6 px-4 text-center text-sm">
        <img src={LOGO_URL} alt="TopBass" className="w-16 h-16 mx-auto mb-2 object-contain" />
        <p className="font-semibold text-orange-400 mb-1">TopBass</p>
        <p>{t('app.subtitle')}</p>
      </footer>
    </div>
  );
};

export default HomePage;
