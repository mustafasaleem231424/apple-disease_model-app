import { usePWA } from '../hooks/usePWA';

function InstallPrompt() {
  const { isInstalled, canInstall, install } = usePWA();

  if (isInstalled || !canInstall) return null;

  return (
    <div style={{
      position: 'fixed',
      bottom: 'calc(20px + var(--safe-bottom))',
      left: '50%',
      transform: 'translateX(-50%)',
      background: 'var(--green-primary)',
      color: 'white',
      padding: '12px 20px',
      borderRadius: 'var(--radius-xl)',
      boxShadow: 'var(--shadow-lg)',
      zIndex: 1000,
      display: 'flex',
      alignItems: 'center',
      gap: '12px',
      fontSize: '14px'
    }}>
      <span>Install app for better experience</span>
      <button
        onClick={install}
        style={{
          background: 'white',
          color: 'var(--green-primary)',
          border: 'none',
          padding: '6px 14px',
          borderRadius: 'var(--radius)',
          fontWeight: '600',
          cursor: 'pointer'
        }}
      >
        Install
      </button>
    </div>
  );
}

export default InstallPrompt;
