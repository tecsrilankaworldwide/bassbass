import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { API } from '../AuthContext';
import Navbar from '../components/Navbar';
import axios from 'axios';
import { MapPin, Wrench, Search, Star, Navigation, ChevronRight, Users, Shield, Clock } from 'lucide-react';

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
    <div className="min-h-screen bg-[#FAF9F6]">
      <Navbar />

      {/* Hero Section */}
      <div className="relative bg-gradient-to-br from-[#0B2545] via-[#133C55] to-[#0B2545] py-16 px-4 overflow-hidden">
        {/* Background pattern */}
        <div className="absolute inset-0 opacity-10">
          <div className="absolute top-0 left-0 w-96 h-96 bg-[#F05A4A] rounded-full blur-3xl -translate-x-1/2 -translate-y-1/2"></div>
          <div className="absolute bottom-0 right-0 w-80 h-80 bg-[#F05A4A] rounded-full blur-3xl translate-x-1/4 translate-y-1/4"></div>
        </div>
        
        <div className="max-w-5xl mx-auto text-center relative z-10">
          <img src={LOGO_URL} alt="TopBass" className="w-28 h-28 mx-auto mb-4 object-contain drop-shadow-lg" data-testid="hero-logo" />
          <div className="mb-4">
            <p className="text-2xl sm:text-3xl text-[#F05A4A] tracking-[0.3em] mb-3" style={{fontFamily:'Bebas Neue, sans-serif'}}>
              {t('app.headingLine1') || 'FOR A BIG OR SMALL JOB'}
            </p>
            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold text-white tracking-tight leading-tight" style={{fontFamily:'Outfit,sans-serif'}}>
              {t('app.headingLine2') || 'Get the perfect support.'}
            </h1>
          </div>
          <p className="text-[#E2E8F0] text-base sm:text-lg mb-8 max-w-xl mx-auto">{t('app.subtitle')}</p>

          {/* Search bar */}
          <form onSubmit={handleSearch} className="flex flex-col sm:flex-row items-center gap-3 max-w-2xl mx-auto mb-4" data-testid="search-form">
            <div className="w-full flex-1 flex items-center bg-white rounded-full px-5 py-3.5 shadow-lg focus-within:ring-2 focus-within:ring-[#F05A4A] transition-all">
              <Search className="w-5 h-5 text-[#0B2545] mr-3 flex-shrink-0" />
              <input type="text" value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)}
                placeholder={t('home.searchPlaceholder')}
                className="w-full text-[#0B2545] bg-transparent outline-none font-medium placeholder:text-[#718096]"
                data-testid="search-input" />
            </div>
            <button type="submit" className="w-full sm:w-auto px-8 py-3.5 bg-[#F05A4A] text-white font-bold rounded-full hover:bg-[#E63946] active:scale-95 transition-all shadow-lg shadow-[#F05A4A]/30" data-testid="search-btn">
              {t('home.search')}
            </button>
          </form>

          {/* District Filter */}
          <div className="flex items-center justify-center gap-2 max-w-md mx-auto">
            <div className="flex items-center bg-white/10 backdrop-blur-md rounded-full px-4 py-2.5 border border-white/20">
              <MapPin className="w-4 h-4 text-[#F05A4A] mr-2 flex-shrink-0" />
              <select value={selectedDistrict} onChange={(e) => setSelectedDistrict(e.target.value)}
                className="bg-transparent text-white text-sm outline-none cursor-pointer" data-testid="district-filter">
                <option value="" className="text-[#0B2545]">{t('home.allDistricts')}</option>
                {districts.map(d => <option key={d} value={d} className="text-[#0B2545]">{d}</option>)}
              </select>
            </div>
          </div>
        </div>
      </div>

      {/* Trust Badges */}
      <div className="bg-white border-b border-gray-100 py-4 px-4">
        <div className="max-w-5xl mx-auto flex flex-wrap items-center justify-center gap-6 sm:gap-10">
          <div className="flex items-center gap-2 text-[#4A5568]">
            <Shield className="w-5 h-5 text-[#F05A4A]" />
            <span className="text-sm font-medium">Verified Handymen</span>
          </div>
          <div className="flex items-center gap-2 text-[#4A5568]">
            <Users className="w-5 h-5 text-[#F05A4A]" />
            <span className="text-sm font-medium">500+ Professionals</span>
          </div>
          <div className="flex items-center gap-2 text-[#4A5568]">
            <Clock className="w-5 h-5 text-[#F05A4A]" />
            <span className="text-sm font-medium">Same-Day Service</span>
          </div>
        </div>
      </div>

      {/* Search Results */}
      {searchResults !== null && (
        <div className="max-w-6xl mx-auto px-4 py-8" data-testid="search-results">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-bold text-[#0B2545]" style={{fontFamily:'Outfit,sans-serif'}}>
              {t('home.searchResultsFor')} "{searchQuery}" ({searchResults.length})
            </h2>
            <button onClick={clearSearch} className="text-sm text-[#F05A4A] font-semibold hover:text-[#E63946] transition-colors" data-testid="clear-search">
              {t('home.clearSearch')}
            </button>
          </div>
          {searching ? (
            <div className="flex justify-center py-8"><div className="spinner"></div></div>
          ) : searchResults.length === 0 ? (
            <div className="bg-white rounded-2xl p-8 text-center border border-gray-100 shadow-sm">
              <p className="text-[#718096] font-medium">{t('common.noResults')}</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
              {searchResults.map(h => (
                <Link key={h.user_id} to={`/handyman/${h.user_id}`}
                  className="bg-white rounded-2xl p-5 border border-gray-100 hover:border-[#F05A4A]/30 hover:shadow-lg hover:-translate-y-1 transition-all duration-300" data-testid={`result-${h.user_id}`}>
                  <h3 className="font-bold text-[#0B2545] text-lg">{h.full_name}</h3>
                  {h.shop_name && <span className="inline-block text-xs bg-blue-50 text-[#0B2545] px-2.5 py-1 rounded-full font-medium mt-1">{h.shop_name}</span>}
                  <div className="flex items-center gap-3 mt-3 text-sm text-[#4A5568]">
                    {h.rating > 0 && <span className="flex items-center gap-1"><Star className="w-4 h-4 text-[#F05A4A] fill-[#F05A4A]" />{h.rating}</span>}
                    <span className="flex items-center gap-1"><MapPin className="w-4 h-4" />{h.district}</span>
                  </div>
                  {h.description && <p className="text-sm text-[#718096] mt-3 line-clamp-2">{h.description}</p>}
                </Link>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Services Grid */}
      {searchResults === null && (
        <>
          <div className="max-w-6xl mx-auto px-4 py-10">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-bold text-[#0B2545]" style={{fontFamily:'Outfit,sans-serif'}}>{t('nav.services')}</h2>
              <span className="text-sm text-[#718096]">{services.length} Categories</span>
            </div>
            <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-5 lg:grid-cols-6 gap-4" data-testid="services-grid">
              {services.map((service) => (
                <Link key={service.id}
                  to={`/services/${service.id}${selectedDistrict ? `?district=${selectedDistrict}` : ''}`}
                  className="flex flex-col items-center p-4 bg-white rounded-2xl border border-gray-100 hover:border-[#F05A4A]/30 hover:shadow-lg hover:-translate-y-1 transition-all duration-300 group cursor-pointer"
                  data-testid={`service-${service.id}`}>
                  <div className="w-14 h-14 sm:w-16 sm:h-16 flex items-center justify-center mb-3 group-hover:scale-110 transition-transform">
                    {service.image ? (
                      <img src={service.image} alt={getServiceName(service)} className="w-full h-full object-contain" loading="lazy" />
                    ) : (
                      <Wrench className="w-8 h-8 text-[#0B2545]" />
                    )}
                  </div>
                  <span className="text-xs sm:text-sm font-semibold text-[#0B2545] text-center leading-tight">{getServiceName(service)}</span>
                </Link>
              ))}
            </div>
          </div>

          {/* Nearby Handymen (when district selected) */}
          {nearbyHandymen.length > 0 && selectedDistrict && (
            <div className="max-w-6xl mx-auto px-4 pb-6" data-testid="nearby-section">
              <div className="flex items-center gap-2 mb-6">
                <Navigation className="w-5 h-5 text-[#F05A4A]" />
                <h2 className="text-2xl font-bold text-[#0B2545]" style={{fontFamily:'Outfit,sans-serif'}}>Nearby in {selectedDistrict}</h2>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
                {nearbyHandymen.map(h => (
                  <Link key={h.user_id} to={`/handyman/${h.user_id}`}
                    className="bg-white rounded-2xl p-5 border border-gray-100 hover:border-[#F05A4A]/30 hover:shadow-lg hover:-translate-y-1 transition-all duration-300" data-testid={`nearby-${h.user_id}`}>
                    <div className="flex items-start justify-between mb-3">
                      <div>
                        <h3 className="font-bold text-[#0B2545] text-lg">{h.full_name}</h3>
                        {h.shop_name && <span className="inline-block text-xs bg-blue-50 text-[#0B2545] px-2.5 py-1 rounded-full font-medium mt-1">{h.shop_name}</span>}
                      </div>
                      {h.rating > 0 && (
                        <div className="flex items-center gap-1 bg-[#FFF5F4] px-2.5 py-1.5 rounded-xl">
                          <Star className="w-4 h-4 text-[#F05A4A] fill-[#F05A4A]" />
                          <span className="text-sm font-bold text-[#0B2545]">{h.rating}</span>
                        </div>
                      )}
                    </div>
                    <div className="flex items-center gap-3 text-sm text-[#4A5568] mb-3">
                      <span className="flex items-center gap-1"><MapPin className="w-4 h-4" />{h.district}</span>
                      {h.distance_km !== undefined && h.distance_km < 999 && (
                        <span className="flex items-center gap-1 text-[#F05A4A] font-semibold">
                          <Navigation className="w-4 h-4" />{h.distance_km} km
                        </span>
                      )}
                    </div>
                    {h.description && <p className="text-sm text-[#718096] line-clamp-2">{h.description}</p>}
                  </Link>
                ))}
              </div>
            </div>
          )}

          {/* Top Rated */}
          {topRated.length > 0 && (
            <div className="max-w-6xl mx-auto px-4 pb-10" data-testid="top-rated-section">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-2xl font-bold text-[#0B2545]" style={{fontFamily:'Outfit,sans-serif'}}>{t('home.topRated')}</h2>
                <Link to="/overview" className="flex items-center gap-1 text-sm text-[#F05A4A] font-semibold hover:text-[#E63946] transition-colors">
                  View All <ChevronRight className="w-4 h-4" />
                </Link>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
                {topRated.map(h => (
                  <Link key={h.user_id} to={`/handyman/${h.user_id}`}
                    className="bg-white rounded-2xl p-5 border border-gray-100 hover:border-[#F05A4A]/30 hover:shadow-lg hover:-translate-y-1 transition-all duration-300" data-testid={`top-${h.user_id}`}>
                    <div className="flex items-start justify-between mb-3">
                      <div>
                        <h3 className="font-bold text-[#0B2545] text-lg">{h.full_name}</h3>
                        <div className="flex flex-wrap gap-1.5 mt-1">
                          {h.shop_name && <span className="text-xs bg-blue-50 text-[#0B2545] px-2.5 py-1 rounded-full font-medium">{h.shop_name}</span>}
                          {h.partner_tier && (
                            <span className={`text-xs px-2.5 py-1 rounded-full font-bold ${
                              h.partner_tier.tier === 'platinum' ? 'bg-[#0B2545] text-white' :
                              h.partner_tier.tier === 'gold' ? 'bg-amber-100 text-amber-700' :
                              'bg-gray-100 text-gray-700'
                            }`}>{h.partner_tier.label}</span>
                          )}
                        </div>
                      </div>
                      <div className="flex items-center gap-1 bg-[#FFF5F4] px-2.5 py-1.5 rounded-xl">
                        <Star className="w-4 h-4 text-[#F05A4A] fill-[#F05A4A]" />
                        <span className="text-sm font-bold text-[#0B2545]">{h.rating}</span>
                      </div>
                    </div>
                    <div className="flex items-center gap-2 text-sm text-[#4A5568] mb-3">
                      <MapPin className="w-4 h-4" />{h.district}
                      {h.experience_years > 0 && <span className="text-[#718096]"> &middot; {h.experience_years} yrs exp</span>}
                    </div>
                    {h.description && <p className="text-sm text-[#718096] line-clamp-2">{h.description}</p>}
                  </Link>
                ))}
              </div>
            </div>
          )}
        </>
      )}

      {/* How It Works */}
      <div className="bg-white py-14 px-4 border-t border-gray-100">
        <div className="max-w-4xl mx-auto">
          <h2 className="text-2xl font-bold text-[#0B2545] text-center mb-10" style={{fontFamily:'Outfit,sans-serif'}}>{t('home.howItWorks')}</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {[
              { num: '1', title: t('home.step1'), desc: t('home.step1Desc'), color: 'bg-[#0B2545]' },
              { num: '2', title: t('home.step2'), desc: t('home.step2Desc'), color: 'bg-[#133C55]' },
              { num: '3', title: t('home.step3'), desc: t('home.step3Desc'), color: 'bg-[#F05A4A]' },
            ].map(step => (
              <div key={step.num} className="text-center group">
                <div className={`w-14 h-14 ${step.color} rounded-2xl flex items-center justify-center mx-auto mb-4 text-white text-xl font-bold shadow-lg group-hover:scale-110 transition-transform`}>{step.num}</div>
                <h3 className="font-bold text-[#0B2545] text-lg mb-2">{step.title}</h3>
                <p className="text-sm text-[#718096]">{step.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="bg-[#0B2545] text-white py-10 px-4">
        <div className="max-w-4xl mx-auto text-center">
          <img src={LOGO_URL} alt="TopBass" className="w-16 h-16 mx-auto mb-4 object-contain" />
          <p className="font-bold text-[#F05A4A] text-xl mb-2" style={{fontFamily:'Outfit,sans-serif'}}>TopBass</p>
          <p className="text-[#E2E8F0] text-sm mb-4">{t('app.subtitle')}</p>
          <p className="text-[#718096] text-xs">&copy; 2026 TEC Sri Lanka Worldwide (Pvt.) Ltd. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
};

export default HomePage;
