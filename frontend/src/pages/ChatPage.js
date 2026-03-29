import React, { useState, useEffect, useRef } from 'react';
import { Link, useParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuth, API } from '../AuthContext';
import Navbar from '../components/Navbar';
import axios from 'axios';
import { ChevronLeft, Send, MessageSquare } from 'lucide-react';

const ChatPage = () => {
  const { t } = useTranslation();
  const { bookingId } = useParams();
  const { user, token } = useAuth();
  const [messages, setMessages] = useState([]);
  const [conversations, setConversations] = useState([]);
  const [otherUser, setOtherUser] = useState(null);
  const [bookingInfo, setBookingInfo] = useState(null);
  const [newMsg, setNewMsg] = useState('');
  const [sending, setSending] = useState(false);
  const [loading, setLoading] = useState(true);
  const messagesEnd = useRef(null);
  const pollRef = useRef(null);
  const headers = { Authorization: `Bearer ${token}` };

  useEffect(() => {
    if (bookingId) {
      loadMessages();
      pollRef.current = setInterval(loadMessages, 5000);
      return () => clearInterval(pollRef.current);
    } else {
      loadConversations();
    }
  }, [bookingId]);

  useEffect(() => {
    messagesEnd.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const loadMessages = () => {
    axios.get(`${API}/chat/messages/${bookingId}`, { headers })
      .then(res => {
        setMessages(res.data.messages);
        setOtherUser(res.data.other_user);
        setBookingInfo(res.data.booking);
        setLoading(false);
      }).catch(() => setLoading(false));
  };

  const loadConversations = () => {
    setLoading(true);
    axios.get(`${API}/chat/conversations`, { headers })
      .then(res => setConversations(res.data.conversations))
      .catch(console.error)
      .finally(() => setLoading(false));
  };

  const sendMessage = async (e) => {
    e.preventDefault();
    if (!newMsg.trim() || sending) return;
    setSending(true);
    try {
      await axios.post(`${API}/chat/send`, { booking_id: bookingId, message: newMsg.trim() }, { headers });
      setNewMsg('');
      loadMessages();
    } catch (err) {
      alert(err.response?.data?.detail || 'Send failed');
    } finally { setSending(false); }
  };

  const formatTime = (iso) => {
    if (!iso) return '';
    const d = new Date(iso);
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const formatDate = (iso) => {
    if (!iso) return '';
    const d = new Date(iso);
    const today = new Date();
    if (d.toDateString() === today.toDateString()) return 'Today';
    const yesterday = new Date(today); yesterday.setDate(today.getDate() - 1);
    if (d.toDateString() === yesterday.toDateString()) return 'Yesterday';
    return d.toLocaleDateString();
  };

  // Conversation List View
  if (!bookingId) {
    return (
      <div className="min-h-screen bg-[#F5F7F3]">
        <Navbar />
        <div className="max-w-3xl mx-auto px-4 py-6">
          <h1 className="text-2xl font-extrabold text-gray-900 mb-4" style={{fontFamily:'Manrope,sans-serif'}} data-testid="chat-title">{t('nav.chat')}</h1>
          {loading ? (
            <div className="flex justify-center py-12"><div className="animate-spin rounded-full h-10 w-10 border-4 border-green-500 border-t-transparent"></div></div>
          ) : conversations.length === 0 ? (
            <div className="bg-white rounded-2xl p-12 text-center border border-gray-100">
              <MessageSquare className="w-12 h-12 text-gray-300 mx-auto mb-3" />
              <p className="text-lg font-semibold text-gray-600">{t('chat.noConversations')}</p>
              <p className="text-sm text-gray-400 mt-1">{t('chat.startFromBooking')}</p>
            </div>
          ) : (
            <div className="space-y-2" data-testid="conversations-list">
              {conversations.map(c => (
                <Link key={c.booking_id} to={`/chat/${c.booking_id}`}
                  className="flex items-center gap-3 bg-white rounded-xl p-4 border border-gray-100 hover:border-green-400 hover:shadow-sm transition-all" data-testid={`convo-${c.booking_id}`}>
                  <div className="w-10 h-10 bg-green-100 rounded-full flex items-center justify-center flex-shrink-0">
                    <span className="text-green-700 font-bold text-sm">{c.other_user_name?.charAt(0) || '?'}</span>
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between">
                      <h3 className="font-semibold text-gray-900 text-sm truncate">{c.other_user_name}</h3>
                      {c.last_message_time && <span className="text-xs text-gray-400 flex-shrink-0 ml-2">{formatDate(c.last_message_time)}</span>}
                    </div>
                    <p className="text-xs text-gray-500 truncate">{c.last_message || c.service_id}</p>
                  </div>
                  {c.unread_count > 0 && (
                    <span className="w-5 h-5 bg-orange-500 text-white rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0">{c.unread_count}</span>
                  )}
                </Link>
              ))}
            </div>
          )}
        </div>
      </div>
    );
  }

  // Chat View
  return (
    <div className="min-h-screen bg-[#F5F7F3] flex flex-col">
      <Navbar />
      {/* Chat Header */}
      <div className="bg-white border-b border-gray-200 px-4 py-3">
        <div className="max-w-3xl mx-auto flex items-center gap-3">
          <Link to="/chat" className="text-gray-500 hover:text-green-600" data-testid="chat-back"><ChevronLeft className="w-5 h-5" /></Link>
          <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center">
            <span className="text-green-700 font-bold text-xs">{otherUser?.name?.charAt(0) || '?'}</span>
          </div>
          <div>
            <h2 className="font-bold text-gray-900 text-sm" data-testid="chat-other-name">{otherUser?.name || 'Loading...'}</h2>
            {bookingInfo && <p className="text-xs text-gray-500">{bookingInfo.service_id} &middot; {bookingInfo.status}</p>}
          </div>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-4" data-testid="messages-area">
        <div className="max-w-3xl mx-auto space-y-2">
          {loading ? (
            <div className="flex justify-center py-8"><div className="animate-spin rounded-full h-8 w-8 border-4 border-green-500 border-t-transparent"></div></div>
          ) : messages.length === 0 ? (
            <div className="text-center py-8 text-sm text-gray-400">No messages yet. Say hello!</div>
          ) : (
            messages.map(m => {
              const isMe = m.sender_id === user?.id;
              return (
                <div key={m.id} className={`flex ${isMe ? 'justify-end' : 'justify-start'}`} data-testid={`msg-${m.id}`}>
                  <div className={`max-w-[75%] px-3.5 py-2 rounded-2xl text-sm ${
                    isMe ? 'bg-green-600 text-white rounded-br-md' : 'bg-white text-gray-800 border border-gray-100 rounded-bl-md'
                  }`}>
                    {!isMe && <div className="text-xs font-semibold text-green-600 mb-0.5">{m.sender_name}</div>}
                    <p className="break-words">{m.message}</p>
                    <div className={`text-[10px] mt-1 ${isMe ? 'text-green-200' : 'text-gray-400'} text-right`}>{formatTime(m.created_at)}</div>
                  </div>
                </div>
              );
            })
          )}
          <div ref={messagesEnd} />
        </div>
      </div>

      {/* Message Input */}
      <div className="bg-white border-t border-gray-200 px-4 py-3">
        <form onSubmit={sendMessage} className="max-w-3xl mx-auto flex items-center gap-2" data-testid="chat-form">
          <input type="text" value={newMsg} onChange={(e) => setNewMsg(e.target.value)}
            placeholder={t('chat.typePlaceholder')}
            className="flex-1 px-4 py-2.5 bg-gray-100 rounded-xl text-sm outline-none focus:bg-white focus:ring-2 focus:ring-green-500 transition-all"
            data-testid="chat-input" />
          <button type="submit" disabled={sending || !newMsg.trim()}
            className="w-10 h-10 bg-green-600 text-white rounded-xl flex items-center justify-center hover:bg-green-700 disabled:opacity-40 transition-colors"
            data-testid="chat-send">
            <Send className="w-4 h-4" />
          </button>
        </form>
      </div>
    </div>
  );
};

export default ChatPage;
