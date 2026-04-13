import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { API_URL } from '../api/client';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardFooter } from '@/components/ui/card';
import { Lock, Store } from 'lucide-react';

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isRegistering, setIsRegistering] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    const endpoint = isRegistering ? '/auth/register' : '/auth/login';

    try {
      let res;
      if (isRegistering) {
        res = await fetch(`${API_URL}${endpoint}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email, password }),
        });
      } else {
        const formData = new URLSearchParams();
        formData.append('username', email);
        formData.append('password', password);
        res = await fetch(`${API_URL}${endpoint}`, { method: 'POST', body: formData });
      }

      if (!res.ok) throw new Error(await res.text());
      const data = await res.json();

      if (!isRegistering) {
        localStorage.setItem('token', data.access_token);
        navigate('/');
      } else {
        setIsRegistering(false);
        setError('Account created! Please sign in.');
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Authentication failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-[80vh] flex items-center justify-center">
      <div className="w-full max-w-md space-y-6 px-4">
        {/* Brand */}
        <div className="text-center space-y-2">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-2xl bg-primary/10 border border-primary/20 mb-2">
            <Lock className="w-5 h-5 text-primary" />
          </div>
          <h1 className="text-2xl font-bold tracking-tight">
            {isRegistering ? 'Create an account' : 'Welcome back'}
          </h1>
          <p className="text-muted-foreground text-sm">
            {isRegistering
              ? 'Sign up to start shopping with us.'
              : 'Sign in to your account to continue.'}
          </p>
        </div>

        <Card className="border border-border shadow-sm">
          <CardContent className="pt-6">
            {error && (
              <div className={`mb-4 text-sm rounded-lg px-4 py-3 ${
                error.includes('created') 
                  ? 'bg-primary/10 border border-primary/30 text-primary' 
                  : 'bg-destructive/10 border border-destructive/30 text-destructive'
              }`}>
                {error}
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-1.5">
                <Label htmlFor="email">Email</Label>
                <Input
                  id="email"
                  type="email"
                  placeholder="you@example.com"
                  value={email}
                  onChange={e => setEmail(e.target.value)}
                  required
                  autoComplete="email"
                />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="password">Password</Label>
                <Input
                  id="password"
                  type="password"
                  placeholder="••••••••"
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  required
                  autoComplete={isRegistering ? 'new-password' : 'current-password'}
                />
              </div>
              <Button type="submit" className="w-full" disabled={loading}>
                {loading ? 'Please wait...' : isRegistering ? 'Create Account' : 'Sign In'}
              </Button>
            </form>
          </CardContent>
          <CardFooter className="pb-6 pt-0">
            <div className="w-full text-center text-sm text-muted-foreground">
              {isRegistering ? 'Already have an account? ' : "Don't have an account? "}
              <button
                type="button"
                onClick={() => { setIsRegistering(!isRegistering); setError(''); }}
                className="text-primary font-medium hover:underline underline-offset-2"
              >
                {isRegistering ? 'Sign in' : 'Register'}
              </button>
            </div>
          </CardFooter>
        </Card>

        <div className="text-center">
          <Button asChild variant={"ghost" as const} size={"sm" as const} className="text-muted-foreground">
            <Link to="/"><Store className="w-3.5 h-3.5 mr-1" />Back to store</Link>
          </Button>
        </div>
      </div>
    </div>
  );
}
