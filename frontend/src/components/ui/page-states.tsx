import { RefreshCw, Search, ShieldAlert } from 'lucide-react';

export function LoadingState() {
  return <div className="loading-state">Yuklanmoqda...</div>;
}

export function EmptyState({ message }: { message: string }) {
  return (
    <div className="empty-state">
      <div>
        <Search size={34} />
        <h3>{message}</h3>
      </div>
    </div>
  );
}

export function ErrorState({ message, retry }: { message: string; retry?: () => void }) {
  return (
    <div className="error-state">
      <div>
        <ShieldAlert size={36} />
        <p>{message}</p>
        {retry && (
          <button className="button primary" type="button" onClick={retry}>
            <RefreshCw size={18} /> Qayta urinish
          </button>
        )}
      </div>
    </div>
  );
}
