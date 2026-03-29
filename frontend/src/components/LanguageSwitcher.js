import React from 'react';
import { useTranslation } from 'react-i18next';
import { Globe } from 'lucide-react';

const languages = [
  { code: 'si', name: 'සිංහල', flag: '🇱🇰' },
  { code: 'ta', name: 'தமிழ்', flag: '🇱🇰' },
  { code: 'en', name: 'English', flag: '🇬🇧' }
];

const LanguageSwitcher = ({ className = '' }) => {
  const { i18n } = useTranslation();
  const [isOpen, setIsOpen] = React.useState(false);
  
  const currentLang = languages.find(l => l.code === i18n.language) || languages[0];

  const changeLanguage = (code) => {
    i18n.changeLanguage(code);
    setIsOpen(false);
  };

  return (
    <div className={`relative ${className}`}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-3 py-2 rounded-lg bg-white/80 hover:bg-white border border-[#E5E7EB] shadow-sm transition-all"
        data-testid="language-switcher-btn"
      >
        <Globe className="w-4 h-4 text-[#F59E0B]" />
        <span className="text-sm font-medium text-[#374151]">{currentLang.flag} {currentLang.name}</span>
      </button>
      
      {isOpen && (
        <div className="absolute top-full mt-2 right-0 bg-white rounded-lg shadow-lg border border-[#E5E7EB] overflow-hidden z-50 min-w-[140px]">
          {languages.map((lang) => (
            <button
              key={lang.code}
              onClick={() => changeLanguage(lang.code)}
              className={`w-full px-4 py-2.5 text-left text-sm flex items-center gap-2 hover:bg-green-50 transition-colors ${
                i18n.language === lang.code ? 'bg-green-50 text-green-700 font-semibold' : 'text-[#374151]'
              }`}
              data-testid={`lang-${lang.code}`}
            >
              <span>{lang.flag}</span>
              <span>{lang.name}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
};

export default LanguageSwitcher;
