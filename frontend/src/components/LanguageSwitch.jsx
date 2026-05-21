function LanguageSwitch({ lang, onSwitch, t }) {
  const langs = [
    { code: 'en', label: t.lang.en },
    { code: 'hi', label: t.lang.hi },
    { code: 'ur', label: t.lang.ur }
  ];

  return (
    <div className="lang-switch">
      {langs.map(l => (
        <button
          key={l.code}
          className={`lang-btn ${lang === l.code ? 'active' : ''}`}
          onClick={() => onSwitch(l.code)}
          aria-pressed={lang === l.code}
        >
          {l.label}
        </button>
      ))}
    </div>
  );
}

export default LanguageSwitch;
