import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './AuthContext';
import './i18n/i18n';
import HomePage from './pages/HomePage';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import ServiceListPage from './pages/ServiceListPage';
import HandymanDetailPage from './pages/HandymanDetailPage';
import BookingsPage from './pages/BookingsPage';
import HandymanProfilePage from './pages/HandymanProfilePage';
import AdminDashboard from './pages/AdminDashboard';
import ShopDashboard from './pages/ShopDashboard';
import PaymentSuccessPage from './pages/PaymentSuccessPage';
import ChatPage from './pages/ChatPage';
import OverviewPage from './pages/OverviewPage';

function ProtectedRoute({ children, roles }) {
  const { user, loading } = useAuth();
  if (loading) return <div className="flex items-center justify-center min-h-screen"><div className="animate-spin rounded-full h-10 w-10 border-4 border-amber-500 border-t-transparent"></div></div>;
  if (!user) return <Navigate to="/login" />;
  if (roles && !roles.includes(user.role)) return <Navigate to="/" />;
  return children;
}

function App() {
  return (
    <AuthProvider>
      <Router>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/services/:serviceId" element={<ServiceListPage />} />
          <Route path="/handyman/:userId" element={<HandymanDetailPage />} />
          <Route path="/bookings" element={<ProtectedRoute><BookingsPage /></ProtectedRoute>} />
          <Route path="/profile" element={<ProtectedRoute roles={['handyman', 'shop']}><HandymanProfilePage /></ProtectedRoute>} />
          <Route path="/admin" element={<ProtectedRoute roles={['admin']}><AdminDashboard /></ProtectedRoute>} />
          <Route path="/shop" element={<ProtectedRoute roles={['shop']}><ShopDashboard /></ProtectedRoute>} />
          <Route path="/payment/success" element={<ProtectedRoute><PaymentSuccessPage /></ProtectedRoute>} />
          <Route path="/chat" element={<ProtectedRoute><ChatPage /></ProtectedRoute>} />
          <Route path="/chat/:bookingId" element={<ProtectedRoute><ChatPage /></ProtectedRoute>} />
          <Route path="/overview" element={<OverviewPage />} />
          <Route path="*" element={<Navigate to="/" />} />
        </Routes>
      </Router>
    </AuthProvider>
  );
}

export default App;
