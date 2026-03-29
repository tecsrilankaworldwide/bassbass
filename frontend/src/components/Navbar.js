import React, { useState, useEffect, useRef } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuth, API } from '../AuthContext';
import LanguageSwitcher from './LanguageSwitcher';
import axios from 'axios';
import { Menu, X, LogOut, Bell, MessageSquare } from 'lucide-react';

const LOGO_URL = "https://static.prod-images.emergentagent.com/jobs/3de36ae8-1b12-4467-87dd-98c4995672e0/images/9167dec89e86661796db50a2e4e59dc94289569e89106c1eb1910007d02d8f3f.png";

const Navbar = () => {
  const { t } = useTranslation();
  const { user, token, logout } = useAuth();
  const navigate = useNavigate();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [notifOpen, setNotifOpen] = useState(false);
  const [notifications, setNotifications] = useState([]);
  const [unread, setUnread] = useState(0);
  const notifRef = useRef(null);

  useEffect(() => {
    if (user && token) {
      loadNotifs();
      const interval = setInterval(loadNotifs, 15000);
      return () => clearInterval(interval);
    }
  }, [user, token]);

  useEffect(() => {
    const handleClick = (e) => { if (notifRef.current && !notifRef.current.contains(e.target)) setNotifOpen(false); };
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, []);

  const loadNotifs = () => {
    axios.get(`${API}/notifications`, { headers: { Authorization: `Bearer ${token}` } })
      .then(res => { setNotifications(res.data.notifications); setUnread(res.data.unread_count); })
      .catch(() => {});
  };

  const markAllRead = () => {
    axios.put(`${API}/notifications/read-all`, {}, { headers: { Authorization: `Bearer ${token}` } })
      .then(() => { setUnread(0); setNotifications(n => n.map(x => ({...x, is_read: true}))); });
  };

  const handleLogout = () => { logout(); navigate('/'); };

  const timeAgo = (iso) => {
    if (!iso) return '';
    const diff = (Date.now() - new Date(iso).getTime()) / 1000;
    if (diff < 60) return 'now';
    if (diff < 3600) return `${Math.floor(diff / 60)}m`;
    if (diff < 86400) return `${Math.floor(diff / 3600)}h`;
    return `${Math.floor(diff / 86400)}d`;
  };

  return (
    <nav className="backdrop-blur-xl bg-white/90 border-b border-gray-200/50 sticky top-0 z-50 shadow-sm">
      <div className="max-w-6xl mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          <Link to="/" className="flex items-center gap-2.5" data-testid="nav-logo">
            <img src={LOGO_URL} alt="TopBass" className="w-10 h-10 object-contain" />
            <span className="text-xl font-bold text-[#0B2545]" style={{fontFamily:'Outfit,sans-serif'}}>TopBass</span>
          </Link>

          {/* Desktop */}
          <div className="hidden md:flex items-center gap-1">
            <Link to="/" className="text-sm font-medium text-[#4A5568] hover:text-[#0B2545] hover:bg-[#F0F4F8] px-3 py-2 rounded-lg transition-colors">{t('nav.home')}</Link>
            <Link to="/overview" className="text-sm font-medium text-[#4A5568] hover:text-[#0B2545] hover:bg-[#F0F4F8] px-3 py-2 rounded-lg transition-colors" data-testid="nav-overview">About</Link>
            {user && (
              <>
                <Link to="/bookings" className="text-sm font-medium text-[#4A5568] hover:text-[#0B2545] hover:bg-[#F0F4F8] px-3 py-2 rounded-lg transition-colors" data-testid="nav-bookings">{t('nav.bookings')}</Link>
                <Link to="/chat" className="text-sm font-medium text-[#4A5568] hover:text-[#0B2545] hover:bg-[#F0F4F8] px-3 py-2 rounded-lg transition-colors flex items-center gap-1.5" data-testid="nav-chat">
                  <MessageSquare className="w-4 h-4" />{t('nav.chat')}
                </Link>
                {user.role === 'admin' && <Link to="/admin" className="text-sm font-medium text-[#4A5568] hover:text-[#0B2545] hover:bg-[#F0F4F8] px-3 py-2 rounded-lg transition-colors" data-testid="nav-admin">{t('nav.admin')}</Link>}
                {user.role === 'shop' && <Link to="/shop" className="text-sm font-medium text-[#4A5568] hover:text-[#0B2545] hover:bg-[#F0F4F8] px-3 py-2 rounded-lg transition-colors" data-testid="nav-shop">{t('nav.shop')}</Link>}
                {['handyman', 'shop'].includes(user.role) && <Link to="/profile" className="text-sm font-medium text-[#4A5568] hover:text-[#0B2545] hover:bg-[#F0F4F8] px-3 py-2 rounded-lg transition-colors">{t('nav.profile')}</Link>}

                {/* Notification Bell */}
                <div className="relative ml-2" ref={notifRef}>
                  <button onClick={() => { setNotifOpen(!notifOpen); if (!notifOpen && unread > 0) markAllRead(); }}
                    className="relative p-2.5 text-[#4A5568] hover:text-[#0B2545] hover:bg-[#F0F4F8] rounded-lg transition-colors" data-testid="nav-notifications">
                    <Bell className="w-5 h-5" />
                    {unread > 0 && (
                      <span className="absolute -top-0.5 -right-0.5 min-w-[18px] h-[18px] bg-[#F05A4A] text-white text-[10px] font-bold rounded-full flex items-center justify-center px-1" data-testid="notif-badge">{unread}</span>
                    )}
                  </button>
                  {notifOpen && (
                    <div className="absolute right-0 top-full mt-2 w-80 bg-white rounded-2xl shadow-xl border border-gray-100 overflow-hidden z-50" data-testid="notif-dropdown">
                      <div className="px-4 py-3 border-b border-gray-100 flex items-center justify-between bg-[#FAF9F6]">
                        <span className="font-bold text-sm text-[#0B2545]">Notifications</span>
                        {unread > 0 && <button onClick={markAllRead} className="text-xs text-[#F05A4A] font-semibold hover:text-[#E63946]">Mark all read</button>}
                      </div>
                      <div className="max-h-80 overflow-y-auto">
                        {notifications.length === 0 ? (
                          <div className="px-4 py-8 text-center text-sm text-[#718096]">No notifications</div>
                        ) : (
                          notifications.slice(0, 15).map(n => (
                            <Link key={n.id} to={n.link || '/bookings'} onClick={() => setNotifOpen(false)}
                              className={`block px-4 py-3 border-b border-gray-50 hover:bg-[#F0F4F8] transition-colors ${!n.is_read ? 'bg-blue-50/50' : ''}`} data-testid={`notif-${n.id}`}>
                              <div className="flex items-start gap-2">
                                {!n.is_read && <div className="w-2 h-2 bg-[#F05A4A] rounded-full mt-1.5 flex-shrink-0"></div>}
                                <div className={!n.is_read ? '' : 'ml-4'}>
                                  <p className="text-sm font-semibold text-[#0B2545]">{n.title}</p>
                                  <p className="text-xs text-[#718096] line-clamp-1">{n.message}</p>
                                  <span className="text-[10px] text-[#A0AEC0]">{timeAgo(n.created_at)}</span>
                                </div>
                              </div>
                            </Link>
                          ))
                        )}
                      </div>
                    </div>
                  )}
                </div>
              </>
            )}
            <div className="ml-2">
              <LanguageSwitcher />
            </div>
            {user ? (
              <button onClick={handleLogout} className="flex items-center gap-1.5 text-sm font-medium text-[#F05A4A] hover:text-[#E63946] hover:bg-red-50 px-3 py-2 rounded-lg transition-colors ml-1" data-testid="nav-logout">
                <LogOut className="w-4 h-4" />{t('nav.logout')}
              </button>
            ) : (
              <Link to="/login" className="ml-2 px-5 py-2 bg-[#F05A4A] text-white font-semibold rounded-full text-sm hover:bg-[#E63946] active:scale-95 transition-all shadow-sm shadow-[#F05A4A]/20" data-testid="nav-login">{t('nav.login')}</Link>
            )}
          </div>

          {/* Mobile toggle */}
          <div className="flex items-center gap-2 md:hidden">
            {user && (
              <div className="relative" ref={notifRef}>
                <button onClick={() => { setNotifOpen(!notifOpen); if (!notifOpen && unread > 0) markAllRead(); }} className="relative p-2 text-[#4A5568]">
                  <Bell className="w-5 h-5" />
                  {unread > 0 && <span className="absolute -top-0.5 -right-0.5 min-w-[16px] h-4 bg-[#F05A4A] text-white text-[10px] font-bold rounded-full flex items-center justify-center px-1">{unread}</span>}
                </button>
              </div>
            )}
            <button className="p-2 hover:bg-[#F0F4F8] rounded-lg transition-colors" onClick={() => setMobileOpen(!mobileOpen)} data-testid="nav-mobile-toggle">
              {mobileOpen ? <X className="w-6 h-6 text-[#0B2545]" /> : <Menu className="w-6 h-6 text-[#0B2545]" />}
            </button>
          </div>
        </div>

        {/* Mobile menu */}
        {mobileOpen && (
          <div className="md:hidden pb-4 space-y-1 border-t border-gray-100 pt-3" data-testid="nav-mobile-menu">
            <Link to="/" onClick={() => setMobileOpen(false)} className="block px-4 py-2.5 text-sm font-medium text-[#0B2545] hover:bg-[#F0F4F8] rounded-xl">{t('nav.home')}</Link>
            <Link to="/overview" onClick={() => setMobileOpen(false)} className="block px-4 py-2.5 text-sm font-medium text-[#0B2545] hover:bg-[#F0F4F8] rounded-xl">About</Link>
            {user && (
              <>
                <Link to="/bookings" onClick={() => setMobileOpen(false)} className="block px-4 py-2.5 text-sm font-medium text-[#0B2545] hover:bg-[#F0F4F8] rounded-xl">{t('nav.bookings')}</Link>
                <Link to="/chat" onClick={() => setMobileOpen(false)} className="block px-4 py-2.5 text-sm font-medium text-[#0B2545] hover:bg-[#F0F4F8] rounded-xl">{t('nav.chat')}</Link>
                {['handyman', 'shop'].includes(user.role) && <Link to="/profile" onClick={() => setMobileOpen(false)} className="block px-4 py-2.5 text-sm font-medium text-[#0B2545] hover:bg-[#F0F4F8] rounded-xl">{t('nav.profile')}</Link>}
                {user.role === 'shop' && <Link to="/shop" onClick={() => setMobileOpen(false)} className="block px-4 py-2.5 text-sm font-medium text-[#0B2545] hover:bg-[#F0F4F8] rounded-xl">{t('nav.shop')}</Link>}
                {user.role === 'admin' && <Link to="/admin" onClick={() => setMobileOpen(false)} className="block px-4 py-2.5 text-sm font-medium text-[#0B2545] hover:bg-[#F0F4F8] rounded-xl">{t('nav.admin')}</Link>}
              </>
            )}
            <div className="px-4 py-2.5"><LanguageSwitcher /></div>
            {user ? (
              <button onClick={() => { handleLogout(); setMobileOpen(false); }} className="w-full text-left px-4 py-2.5 text-sm font-medium text-[#F05A4A] hover:bg-red-50 rounded-xl">{t('nav.logout')}</button>
            ) : (
              <Link to="/login" onClick={() => setMobileOpen(false)} className="block px-4 py-2.5 text-sm font-semibold text-[#F05A4A] hover:bg-red-50 rounded-xl">{t('nav.login')}</Link>
            )}
          </div>
        )}
      </div>
    </nav>
  );
};

export default Navbar;
