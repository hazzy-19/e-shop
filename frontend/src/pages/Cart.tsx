import { useState, useEffect, useRef } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useCart } from '../store/CartContext';
import { useAuth } from '@/lib/AuthContext';
import { API_URL, getImageUrl } from '../api/client';
import { initiatePayment, checkPaymentStatus } from '../api/payhero';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import {
  Trash2, ShoppingBag, ArrowRight, CheckCircle, Phone, Loader2,
  XCircle, Smartphone, MapPin, ChevronRight,
} from 'lucide-react';

type CheckoutStep = 'cart' | 'address' | 'phone' | 'waiting' | 'success' | 'failed';

const STEPS = [
  { key: 'cart',    label: 'Cart' },
  { key: 'address', label: 'Delivery' },
  { key: 'phone',   label: 'Payment' },
];

function StepIndicator({ current }: { current: CheckoutStep }) {
  const visible = ['cart', 'address', 'phone'];
  const idx = visible.indexOf(current);
  return (
    <div className="flex items-center justify-center gap-2 mb-6">
      {STEPS.map((s, i) => (
        <div key={s.key} className="flex items-center gap-2">
          <div className={`flex items-center justify-center w-7 h-7 rounded-full text-xs font-bold transition-colors ${
            i < idx ? 'bg-primary text-primary-foreground'
            : i === idx ? 'bg-primary text-primary-foreground ring-4 ring-primary/20'
            : 'bg-muted text-muted-foreground'
          }`}>
            {i < idx ? '✓' : i + 1}
          </div>
          <span className={`text-xs font-medium hidden sm:block ${i === idx ? 'text-foreground' : 'text-muted-foreground'}`}>
            {s.label}
          </span>
          {i < STEPS.length - 1 && (
            <ChevronRight className="w-3 h-3 text-muted-foreground" />
          )}
        </div>
      ))}
    </div>
  );
}

export default function Cart() {
  const { items, removeFromCart, total, clearCart } = useCart();
  const { user, getToken } = useAuth();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const [step, setStep] = useState<CheckoutStep>('cart');
  const [phoneNumber, setPhoneNumber] = useState('');
  const [orderId, setOrderId] = useState<number | null>(null);
  const [transactionId, setTransactionId] = useState('');
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Shipping address state
  const [address, setAddress] = useState({ street: '', city: '', county: '' });
  const [savedAddress, setSavedAddress] = useState('');

  // Load saved address from backend
  useEffect(() => {
    if (!user) return;
    getToken().then(token => {
      if (!token) return;
      fetch(`${API_URL}/auth/me`, { headers: { Authorization: `Bearer ${token}` } })
        .then(r => r.ok ? r.json() : null)
        .then(d => { if (d?.shipping_address) setSavedAddress(d.shipping_address); })
        .catch(() => {});
    });
  }, [user]);

  useEffect(() => {
    return () => { if (pollingRef.current) clearInterval(pollingRef.current); };
  }, []);

  // ── Step 1: Proceed to address ────────────────
  const handleToAddress = () => {
    if (!user) {
      navigate('/login');
      return;
    }
    setError('');
    setStep('address');
  };

  // ── Step 2: Save address and create order ─────
  const handleSaveAddress = async () => {
    const finalAddress = savedAddress ||
      [address.street, address.city, address.county].filter(Boolean).join(', ');

    if (!finalAddress.trim()) {
      setError('Please enter a delivery address.');
      return;
    }
    setLoading(true);
    setError('');
    try {
      const token = await getToken();
      if (!token) { navigate('/login'); return; }

      // Save address to user profile
      await fetch(`${API_URL}/auth/profile`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ shipping_address: finalAddress }),
      });

      // Create the order with the address
      const res = await fetch(`${API_URL}/orders/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({
          items: items.map(i => ({ product_id: i.product.id, quantity: i.quantity })),
          shipping_address: finalAddress,
        }),
      });
      if (!res.ok) throw new Error(await res.text());
      const order = await res.json();
      setOrderId(order.id);
      setSavedAddress(finalAddress);
      setStep('phone');
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Something went wrong.');
    } finally {
      setLoading(false);
    }
  };

  // ── Step 3: Initiate M-Pesa ───────────────────
  const handlePayment = async () => {
    if (!orderId || !phoneNumber.trim()) return;
    setLoading(true);
    setError('');
    try {
      const result = await initiatePayment(orderId, phoneNumber.trim());
      setTransactionId(result.transaction_id);
      setStep('waiting');

      pollingRef.current = setInterval(async () => {
        try {
          const status = await checkPaymentStatus(result.transaction_id);
          if (status.status === 'completed') {
            if (pollingRef.current) clearInterval(pollingRef.current);
            clearCart();
            setStep('success');
          } else if (status.status === 'failed' || status.status === 'cancelled') {
            if (pollingRef.current) clearInterval(pollingRef.current);
            setStep('failed');
          }
        } catch { /* silent */ }
      }, 5000);

      setTimeout(() => {
        if (pollingRef.current) { clearInterval(pollingRef.current); pollingRef.current = null; }
      }, 120000);

    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to initiate payment.');
    } finally {
      setLoading(false);
    }
  };

  // ── Success ───────────────────────────────────
  if (step === 'success') {
    return (
      <div className="max-w-lg mx-auto py-24 text-center space-y-6">
        <div className="w-20 h-20 rounded-full bg-green-500/10 flex items-center justify-center mx-auto">
          <CheckCircle className="w-10 h-10 text-green-500" />
        </div>
        <div className="space-y-2">
          <h2 className="text-2xl font-bold">Payment Successful!</h2>
          <p className="text-muted-foreground">Your M-Pesa payment has been confirmed.</p>
          {transactionId && (
            <p className="font-mono text-sm bg-muted px-3 py-1.5 rounded-md inline-block">TX: {transactionId}</p>
          )}
        </div>
        <Button asChild>
          <Link to="/">Continue Shopping <ArrowRight className="w-4 h-4 ml-1" /></Link>
        </Button>
      </div>
    );
  }

  // ── Failed ────────────────────────────────────
  if (step === 'failed') {
    return (
      <div className="max-w-lg mx-auto py-24 text-center space-y-6">
        <div className="w-20 h-20 rounded-full bg-destructive/10 flex items-center justify-center mx-auto">
          <XCircle className="w-10 h-10 text-destructive" />
        </div>
        <h2 className="text-2xl font-bold">Payment Failed</h2>
        <p className="text-muted-foreground">The M-Pesa payment was not completed. Please try again.</p>
        <div className="flex gap-3 justify-center">
          <Button variant="outline" onClick={() => { setStep('phone'); setError(''); }}>Try Again</Button>
          <Button asChild variant="ghost"><Link to="/">Back to Shop</Link></Button>
        </div>
      </div>
    );
  }

  // ── Waiting for M-Pesa ────────────────────────
  if (step === 'waiting') {
    return (
      <div className="max-w-md mx-auto py-24 text-center space-y-6">
        <div className="w-20 h-20 rounded-full bg-primary/10 flex items-center justify-center mx-auto">
          <Smartphone className="w-10 h-10 text-primary" />
        </div>
        <div className="space-y-2">
          <h2 className="text-2xl font-bold">Check Your Phone</h2>
          <p className="text-muted-foreground">An M-Pesa STK push has been sent to <strong>{phoneNumber}</strong>.</p>
          <p className="text-sm text-muted-foreground">Enter your M-Pesa PIN to complete the payment.</p>
          <div className="flex items-center justify-center gap-2 text-primary mt-4">
            <Loader2 className="w-4 h-4 animate-spin" />
            <span className="text-sm">Waiting for confirmation...</span>
          </div>
        </div>
        <Card className="text-left border border-border">
          <CardContent className="p-4 space-y-2 text-sm">
            <div className="flex justify-between"><span className="text-muted-foreground">Amount</span><span className="font-bold text-primary">KSh {total.toFixed(2)}</span></div>
            <div className="flex justify-between"><span className="text-muted-foreground">Phone</span><span>{phoneNumber}</span></div>
            {transactionId && <div className="flex justify-between"><span className="text-muted-foreground">TX ID</span><span className="font-mono text-xs">{transactionId}</span></div>}
          </CardContent>
        </Card>
        <Button variant="outline" onClick={() => { if (pollingRef.current) clearInterval(pollingRef.current); setStep('phone'); setError(''); }}>
          ← Back
        </Button>
      </div>
    );
  }

  // ── Address Step ──────────────────────────────
  if (step === 'address') {
    const hasAddr = !!savedAddress;
    return (
      <div className="max-w-lg mx-auto space-y-6">
        <StepIndicator current="address" />
        <Card className="border border-border">
          <CardHeader>
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center">
                <MapPin className="w-5 h-5 text-primary" />
              </div>
              <div>
                <CardTitle className="text-lg">Delivery Address</CardTitle>
                <p className="text-sm text-muted-foreground">Where should we deliver your order?</p>
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            {error && (
              <div className="bg-destructive/10 border border-destructive/30 text-destructive text-sm rounded-lg px-4 py-3">{error}</div>
            )}

            {hasAddr ? (
              // Saved address UI
              <div className="space-y-3">
                <div className="p-4 rounded-xl border border-primary/30 bg-primary/5 flex items-start gap-3">
                  <MapPin className="w-4 h-4 text-primary mt-0.5 shrink-0" />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium">Saved address</p>
                    <p className="text-sm text-muted-foreground mt-0.5">{savedAddress}</p>
                  </div>
                </div>
                <button
                  onClick={() => setSavedAddress('')}
                  className="text-xs text-primary hover:underline"
                >
                  Use a different address
                </button>
              </div>
            ) : (
              // Address form
              <div className="space-y-3">
                <div className="space-y-1.5">
                  <label className="text-sm font-medium">Street / Estate</label>
                  <input
                    type="text"
                    value={address.street}
                    onChange={e => setAddress(a => ({ ...a, street: e.target.value }))}
                    placeholder="e.g. Westlands, Moi Avenue"
                    className="w-full h-10 px-3 rounded-lg border border-border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
                  />
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-1.5">
                    <label className="text-sm font-medium">City</label>
                    <input
                      type="text"
                      value={address.city}
                      onChange={e => setAddress(a => ({ ...a, city: e.target.value }))}
                      placeholder="Nairobi"
                      className="w-full h-10 px-3 rounded-lg border border-border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
                    />
                  </div>
                  <div className="space-y-1.5">
                    <label className="text-sm font-medium">County / Area</label>
                    <input
                      type="text"
                      value={address.county}
                      onChange={e => setAddress(a => ({ ...a, county: e.target.value }))}
                      placeholder="Nairobi County"
                      className="w-full h-10 px-3 rounded-lg border border-border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
                    />
                  </div>
                </div>
              </div>
            )}

            <Button
              className="w-full gap-2"
              size="lg"
              onClick={handleSaveAddress}
              disabled={loading}
            >
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <ArrowRight className="w-4 h-4" />}
              {loading ? 'Saving...' : 'Continue to Payment'}
            </Button>
            <Button variant="ghost" className="w-full" onClick={() => setStep('cart')}>
              ← Back to Cart
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  // ── Phone / M-Pesa step ───────────────────────
  if (step === 'phone') {
    return (
      <div className="max-w-md mx-auto space-y-6">
        <StepIndicator current="phone" />
        <Card className="border border-border">
          <CardHeader>
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center">
                <Phone className="w-5 h-5 text-primary" />
              </div>
              <div>
                <CardTitle className="text-lg">M-Pesa Payment</CardTitle>
                <p className="text-sm text-muted-foreground">Enter your Safaricom number to receive the STK push</p>
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            {error && (
              <div className="bg-destructive/10 border border-destructive/30 text-destructive text-sm rounded-lg px-4 py-3">{error}</div>
            )}
            {savedAddress && (
              <div className="flex items-center gap-2 text-xs text-muted-foreground p-3 bg-muted rounded-lg">
                <MapPin className="w-3.5 h-3.5 shrink-0" />
                Delivering to: <span className="font-medium text-foreground truncate">{savedAddress}</span>
              </div>
            )}
            <div className="space-y-1.5">
              <label className="text-sm font-medium">M-Pesa Phone Number</label>
              <input
                type="tel"
                value={phoneNumber}
                onChange={e => setPhoneNumber(e.target.value)}
                placeholder="e.g. 0712345678"
                className="w-full h-11 px-4 rounded-lg border border-border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
                autoFocus
              />
              <p className="text-xs text-muted-foreground">Format: 07XXXXXXXX or 01XXXXXXXX</p>
            </div>
            <div className="text-sm p-3 rounded-lg bg-muted space-y-1">
              <div className="flex justify-between"><span className="text-muted-foreground">Total to pay</span><span className="font-bold text-primary text-base">KSh {total.toFixed(2)}</span></div>
            </div>
            <Button className="w-full gap-2" size="lg" onClick={handlePayment} disabled={loading || !phoneNumber.trim()}>
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Smartphone className="w-4 h-4" />}
              {loading ? 'Initiating...' : 'Send M-Pesa Request'}
            </Button>
            <Button variant="ghost" className="w-full" onClick={() => { setStep('address'); setError(''); }}>
              ← Change Address
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  // ── Empty cart ────────────────────────────────
  if (items.length === 0) {
    return (
      <div className="max-w-lg mx-auto py-24 text-center space-y-6">
        <div className="w-20 h-20 rounded-full bg-muted flex items-center justify-center mx-auto">
          <ShoppingBag className="w-10 h-10 text-muted-foreground" />
        </div>
        <div className="space-y-2">
          <h2 className="text-2xl font-bold">Your cart is empty</h2>
          <p className="text-muted-foreground">Looks like you haven't added anything yet.</p>
        </div>
        <Button asChild><Link to="/">Browse Products</Link></Button>
      </div>
    );
  }

  // ── Cart view ─────────────────────────────────
  return (
    <div className="max-w-4xl mx-auto space-y-8">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold tracking-tight">Your Cart</h1>
        <Badge variant="secondary">{items.reduce((s, i) => s + i.quantity, 0)} items</Badge>
      </div>

      {error && (
        <div className="bg-destructive/10 border border-destructive/30 text-destructive text-sm rounded-lg px-4 py-3">{error}</div>
      )}

      <div className="grid md:grid-cols-3 gap-8">
        {/* Items */}
        <div className="md:col-span-2 space-y-3">
          {items.map(item => (
            <Card key={item.product.id} className="border border-border">
              <CardContent className="p-4 flex items-center gap-4">
                <div className="w-16 h-16 rounded-xl overflow-hidden bg-muted shrink-0">
                  {item.product.image_url ? (
                    <img src={getImageUrl(item.product.image_url)} alt={item.product.name} className="w-full h-full object-cover" />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center text-muted-foreground text-xs">No img</div>
                  )}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="font-semibold text-sm truncate">{item.product.name}</p>
                  <p className="text-muted-foreground text-xs mt-0.5">Qty: {item.quantity}</p>
                </div>
                <div className="flex items-center gap-3 shrink-0">
                  <span className="font-bold text-base">KSh {(item.product.price * item.quantity).toLocaleString()}</span>
                  <Button variant="ghost" size="icon" onClick={() => removeFromCart(item.product.id)}
                    className="text-destructive hover:text-destructive hover:bg-destructive/10 h-8 w-8">
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Order Summary */}
        <div>
          <Card className="border border-border sticky top-24">
            <CardHeader className="pb-4">
              <CardTitle className="text-base">Order Summary</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2 text-sm">
                {items.map(item => (
                  <div key={item.product.id} className="flex justify-between text-muted-foreground">
                    <span className="truncate mr-2">{item.product.name} × {item.quantity}</span>
                    <span className="shrink-0">KSh {(item.product.price * item.quantity).toLocaleString()}</span>
                  </div>
                ))}
              </div>
              <Separator />
              <div className="flex justify-between font-bold text-lg">
                <span>Total</span>
                <span className="text-primary">KSh {total.toLocaleString()}</span>
              </div>

              {/* THE CHECKOUT BUTTON */}
              <Button
                className="w-full gap-2 h-12 text-base"
                size="lg"
                onClick={handleToAddress}
                disabled={loading}
              >
                {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : null}
                Checkout
                <ArrowRight className="w-4 h-4" />
              </Button>

              <Button asChild variant="ghost" className="w-full text-sm text-muted-foreground">
                <Link to="/">Continue Shopping</Link>
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
