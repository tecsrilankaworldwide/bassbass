import React, { useEffect, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { useAuth, API } from '../AuthContext';
import Navbar from '../components/Navbar';
import axios from 'axios';
import { CheckCircle, XCircle, Loader2 } from 'lucide-react';

const PaymentSuccessPage = () => {
  const [searchParams] = useSearchParams();
  const { token } = useAuth();
  const [status, setStatus] = useState('checking');
  const [attempts, setAttempts] = useState(0);
  const sessionId = searchParams.get('session_id');
  const bookingId = searchParams.get('booking_id');

  useEffect(() => {
    if (!sessionId) { setStatus('error'); return; }
    pollStatus();
  }, []);

  const pollStatus = async (attempt = 0) => {
    if (attempt >= 5) { setStatus('timeout'); return; }
    try {
      const res = await axios.get(`${API}/payments/status/${sessionId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.data.payment_status === 'paid') {
        setStatus('paid');
      } else if (res.data.status === 'expired') {
        setStatus('expired');
      } else {
        setAttempts(attempt + 1);
        setTimeout(() => pollStatus(attempt + 1), 2000);
      }
    } catch {
      setStatus('error');
    }
  };

  return (
    <div className="min-h-screen bg-[#FAFAF8]">
      <Navbar />
      <div className="max-w-md mx-auto px-4 py-16 text-center">
        {status === 'checking' && (
          <div data-testid="payment-checking">
            <Loader2 className="w-16 h-16 text-amber-500 mx-auto mb-4 animate-spin" />
            <h1 className="text-2xl font-extrabold text-gray-900 mb-2" style={{fontFamily:'Manrope,sans-serif'}}>Checking Payment...</h1>
            <p className="text-gray-500">Please wait while we confirm your payment</p>
          </div>
        )}

        {status === 'paid' && (
          <div data-testid="payment-success">
            <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <CheckCircle className="w-12 h-12 text-green-500" />
            </div>
            <h1 className="text-2xl font-extrabold text-gray-900 mb-2" style={{fontFamily:'Manrope,sans-serif'}}>Payment Successful!</h1>
            <p className="text-gray-500 mb-6">Your booking has been confirmed and the handyman has been notified.</p>
            <Link to="/bookings" className="inline-block px-6 py-3 bg-amber-500 text-white font-semibold rounded-xl hover:bg-amber-600" data-testid="go-bookings">
              View My Bookings
            </Link>
          </div>
        )}

        {(status === 'error' || status === 'expired' || status === 'timeout') && (
          <div data-testid="payment-failed">
            <div className="w-20 h-20 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <XCircle className="w-12 h-12 text-red-500" />
            </div>
            <h1 className="text-2xl font-extrabold text-gray-900 mb-2" style={{fontFamily:'Manrope,sans-serif'}}>
              {status === 'expired' ? 'Payment Expired' : 'Payment Issue'}
            </h1>
            <p className="text-gray-500 mb-6">
              {status === 'timeout' ? 'Could not confirm payment status. Please check your bookings.' : 'Something went wrong. Please try again.'}
            </p>
            <Link to="/bookings" className="inline-block px-6 py-3 bg-amber-500 text-white font-semibold rounded-xl hover:bg-amber-600" data-testid="go-bookings">
              Back to Bookings
            </Link>
          </div>
        )}
      </div>
    </div>
  );
};

export default PaymentSuccessPage;
