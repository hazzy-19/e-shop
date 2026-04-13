import { Link } from 'react-router-dom';
import { useCart } from '../store/CartContext';
import { ShoppingCart, User, LayoutDashboard } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';

export default function Header() {
  const { items } = useCart();
  const itemCount = items.reduce((sum, item) => sum + item.quantity, 0);
  const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;

  return (
    <header className="sticky top-0 z-50 bg-white/80 backdrop-blur-xl border-b border-border shadow-sm">
      <div className="container mx-auto px-6 py-3 flex items-center justify-between gap-6">
        {/* Logo — clicking it takes you home */}
        <Link to="/" className="flex items-center gap-2 group">
          <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center shadow-md group-hover:scale-105 transition-transform">
            <ShoppingCart className="w-4 h-4 text-primary-foreground" />
          </div>
          <span className="text-xl font-bold text-foreground tracking-tight">
            e<span className="text-primary">shop</span>
          </span>
        </Link>

        {/* Nav — only Admin if logged in */}
        {token && (
          <>
            <Separator orientation="vertical" className="h-6 hidden md:block" />
            <nav className="hidden md:flex items-center gap-1">
              <Button asChild variant={"ghost" as const} size={"sm" as const} className="text-muted-foreground hover:text-foreground">
                <Link to="/admin">
                  <LayoutDashboard className="w-4 h-4 mr-1" />
                  Admin
                </Link>
              </Button>
            </nav>
          </>
        )}

        {/* Spacer */}
        <div className="flex-1" />

        {/* Actions */}
        <div className="flex items-center gap-2">
          <Button asChild variant={"ghost" as const} size={"icon" as const} className="relative">
            <Link to="/cart" aria-label="Cart">
              <ShoppingCart className="w-5 h-5" />
              {itemCount > 0 && (
                <Badge className="absolute -top-1.5 -right-1.5 h-5 w-5 p-0 flex items-center justify-center text-[10px] rounded-full">
                  {itemCount}
                </Badge>
              )}
            </Link>
          </Button>
          <Button asChild variant={token ? ("outline" as const) : ("default" as const)} size={"sm" as const}>
            <Link to="/login">
              <User className="w-4 h-4 mr-1.5" />
              {token ? 'Account' : 'Sign In'}
            </Link>
          </Button>
        </div>
      </div>
    </header>
  );
}
