function LanguageSwitch({ lang, onSwitch, t }) {
  return (
    <div className="lang-switch">
      <button
        className={`lang-btn ${lang === 'en' ? 'active' : ''}`}
        onClick={() => onSwitch('en')}
      >
        {t.lang.en}
      </button>
      <button
        className={`lang-btn ${lang === 'hi' ? 'active' : ''}`}
        onClick={() => onSwitch('hi')}
      >
        {t.lang.hi}
      </button>
    </div>
  );
}

export default LanguageSwitch;
