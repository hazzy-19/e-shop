import { useState, useEffect } from 'react';
import { Outlet, Link, useLocation, useNavigate } from 'react-router-dom';
import { LayoutDashboard, Package, FolderTree, UploadCloud, ShieldCheck, Loader2, KeyRound } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useAuth } from '@/lib/AuthContext';
import { API_URL } from '@/api/client';

// ── 2FA Gate ──────────────────────────────────────────────────────
function TwoFactorGate({ onVerified }: { onVerified: () => void }) {
  const [code, setCode] = useState('');
  const [loading, setLoading] = useState(false);
  const [requesting, setRequesting] = useState(false);
  const [error, setError] = useState('');
  const [sent, setSent] = useState(false);
  const { user } = useAuth();

  const requestCode = async () => {
    setRequesting(true);
    setError('');
    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`${API_URL}/auth/admin/request-2fa`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        setSent(true);
      } else {
        setError('Failed to send code. Make sure you have admin access.');
      }
    } catch {
      setError('Network error. Is the backend running?');
    } finally {
      setRequesting(false);
    }
  };

  const verify = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`${API_URL}/auth/admin/verify-2fa`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ code }),
      });
      if (res.ok) {
        sessionStorage.setItem('admin_2fa_verified', 'true');
        onVerified();
      } else {
        const d = await res.json();
        setError(d.detail || 'Invalid or expired code.');
      }
    } catch {
      setError('Network error.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-[70vh] flex items-center justify-center">
      <div className="w-full max-w-md">
        <div className="bg-card border border-border rounded-2xl shadow-xl overflow-hidden">
          <div className="bg-gradient-to-br from-primary/20 via-primary/5 to-transparent px-8 pt-8 pb-6 text-center">
            <div className="w-14 h-14 bg-primary/10 border border-primary/20 rounded-2xl flex items-center justify-center mx-auto mb-4">
              <ShieldCheck className="w-7 h-7 text-primary" />
            </div>
            <h1 className="text-2xl font-bold tracking-tight">Admin Verification</h1>
            <p className="text-muted-foreground text-sm mt-1">
              {sent
                ? 'Enter the 6-digit code sent to your Telegram'
                : 'A verification code will be sent to your Telegram bot'}
            </p>
          </div>

          <div className="px-8 py-6 space-y-4">
            {!sent ? (
              <button
                onClick={requestCode}
                disabled={requesting}
                className="w-full h-11 flex items-center justify-center gap-2 rounded-lg bg-primary text-primary-foreground font-semibold text-sm hover:bg-primary/90 transition-colors disabled:opacity-60"
              >
                {requesting ? <Loader2 className="w-4 h-4 animate-spin" /> : <KeyRound className="w-4 h-4" />}
                {requesting ? 'Sending...' : 'Send Code to Telegram'}
              </button>
            ) : (
              <form onSubmit={verify} className="space-y-4">
                <div className="space-y-1.5">
                  <label className="text-sm font-medium">6-Digit Code</label>
                  <input
                    type="text"
                    inputMode="numeric"
                    maxLength={6}
                    value={code}
                    onChange={e => setCode(e.target.value.replace(/\D/g, ''))}
                    placeholder="123456"
                    className="w-full h-12 px-4 text-center text-2xl font-mono tracking-widest rounded-lg border border-border bg-background focus:outline-none focus:ring-2 focus:ring-primary/50 transition-shadow"
                    autoFocus
                  />
                </div>
                {error && (
                  <p className="text-sm text-destructive bg-destructive/10 px-3 py-2 rounded-lg">{error}</p>
                )}
                <button
                  type="submit"
                  disabled={loading || code.length !== 6}
                  className="w-full h-11 rounded-lg bg-primary text-primary-foreground font-semibold text-sm hover:bg-primary/90 transition-colors disabled:opacity-60"
                >
                  {loading ? 'Verifying...' : 'Verify & Enter Dashboard'}
                </button>
                <button
                  type="button"
                  onClick={() => { setSent(false); setCode(''); setError(''); }}
                  className="w-full text-sm text-muted-foreground hover:text-foreground"
                >
                  Resend code
                </button>
              </form>
            )}

            {error && !sent && (
              <p className="text-sm text-destructive bg-destructive/10 px-3 py-2 rounded-lg">{error}</p>
            )}
          </div>

          <div className="pb-6 text-center text-xs text-muted-foreground">
            Signed in as <span className="text-primary font-medium">{user?.email}</span>
          </div>
        </div>
      </div>
    </div>
  );
}

// ── Main AdminLayout ───────────────────────────────────────────────
export default function AdminLayout() {
  const location = useLocation();
  const navigate = useNavigate();
  const { isAdmin, loading, user } = useAuth();
  const [verified, setVerified] = useState(
    () => sessionStorage.getItem('admin_2fa_verified') === 'true'
  );

  // Redirect non-admins
  useEffect(() => {
    if (!loading && !isAdmin) {
      navigate('/login', { replace: true });
    }
  }, [isAdmin, loading, navigate]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[70vh]">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  if (!isAdmin) return null;

  if (!verified) {
    return <TwoFactorGate onVerified={() => setVerified(true)} />;
  }

  const links = [
    { name: 'Dashboard', path: '/admin', icon: LayoutDashboard },
    { name: 'Products', path: '/admin/products', icon: Package },
    { name: 'Categories', path: '/admin/categories', icon: FolderTree },
    { name: 'Bulk Upload', path: '/admin/bulk-upload', icon: UploadCloud },
  ];

  return (
    <div className="flex h-full min-h-[70vh] gap-6">
      {/* Sidebar */}
      <aside className="w-64 flex-shrink-0 bg-card rounded-lg border border-border overflow-hidden flex flex-col">
        <div className="p-4 border-b border-border">
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-5 h-5 text-primary" />
            <h2 className="font-semibold text-lg text-primary">Admin Control</h2>
          </div>
          <p className="text-xs text-muted-foreground mt-1 truncate">{user?.email}</p>
        </div>
        <nav className="flex-1 p-3 space-y-1">
          {links.map((link) => {
            const Icon = link.icon;
            const isActive = location.pathname === link.path ||
              (link.path !== '/admin' && location.pathname.startsWith(link.path));
            return (
              <Link
                key={link.path}
                to={link.path}
                className={cn(
                  'flex items-center gap-3 px-3 py-2.5 rounded-md text-sm font-medium transition-colors',
                  isActive
                    ? 'bg-primary text-primary-foreground'
                    : 'text-muted-foreground hover:bg-muted hover:text-foreground'
                )}
              >
                <Icon size={18} />
                {link.name}
              </Link>
            );
          })}
        </nav>
        <div className="p-3 border-t border-border">
          <button
            onClick={() => {
              sessionStorage.removeItem('admin_2fa_verified');
              setVerified(false);
            }}
            className="w-full flex items-center gap-2 px-3 py-2 text-xs text-muted-foreground hover:text-destructive hover:bg-destructive/10 rounded-md transition-colors"
          >
            <ShieldCheck className="w-3.5 h-3.5" />
            Lock Session
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 bg-card rounded-lg border border-border p-6 shadow-sm overflow-auto">
        <Outlet />
      </main>
    </div>
  );
}
