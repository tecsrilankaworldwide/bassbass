import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';

import en from './locales/en.json';
import si from './locales/si.json';
import ta from './locales/ta.json';

const resources = {
  en: { translation: en },
  si: { translation: si },
  ta: { translation: ta }
};

i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources,
    fallbackLng: 'si', // Sinhala as default
    supportedLngs: ['si', 'ta', 'en'],
    interpolation: {
      escapeValue: false
    },
    detection: {
      order: ['localStorage', 'navigator'],
      caches: ['localStorage']
    }
  });

export default i18n;
