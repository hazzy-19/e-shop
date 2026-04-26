import { Link } from 'react-router-dom';
import { useCart } from '../store/CartContext';
import { useAuth } from '@/lib/AuthContext';
import { ShoppingCart, User, LayoutDashboard, LogOut } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { toast } from 'sonner';

export default function Header() {
  const { items } = useCart();
  const { user, isAdmin, logout } = useAuth();
  const itemCount = items.reduce((sum, item) => sum + item.quantity, 0);

  const handleLogout = async () => {
    await logout();
    toast.success('Signed out successfully.');
  };

  return (
    <header className="sticky top-0 z-50 bg-white/80 backdrop-blur-xl border-b border-border shadow-sm">
      <div className="container mx-auto px-6 py-3 flex items-center justify-between gap-6">
        {/* Logo */}
        <Link to="/" className="flex items-center gap-2 group">
          <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center shadow-md group-hover:scale-105 transition-transform">
            <ShoppingCart className="w-4 h-4 text-primary-foreground" />
          </div>
          <span className="text-xl font-bold text-foreground tracking-tight">
            e<span className="text-primary">shop</span>
          </span>
        </Link>

        {/* Admin Nav — only for admin users */}
        {isAdmin && (
          <>
            <Separator orientation="vertical" className="h-6 hidden md:block" />
            <nav className="hidden md:flex items-center gap-1">
              <Button asChild variant={"ghost" as const} size={"sm" as const} className="text-muted-foreground hover:text-foreground">
                <Link to="/admin">
                  <LayoutDashboard className="w-4 h-4 mr-1" />
                  Admin Panel
                </Link>
              </Button>
            </nav>
          </>
        )}

        {/* Spacer */}
        <div className="flex-1" />

        {/* Actions */}
        <div className="flex items-center gap-2">
          {/* Cart */}
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

          {user ? (
            /* Logged-in state: show email + sign out */
            <div className="flex items-center gap-2">
              <span className="hidden md:block text-xs text-muted-foreground max-w-[140px] truncate">
                {user.email}
              </span>
              <Button
                variant={"outline" as const}
                size={"sm" as const}
                onClick={handleLogout}
                className="text-muted-foreground"
              >
                <LogOut className="w-4 h-4 mr-1.5" />
                Sign Out
              </Button>
            </div>
          ) : (
            /* Logged-out state: Sign In button */
            <Button asChild variant={"default" as const} size={"sm" as const}>
              <Link to="/login">
                <User className="w-4 h-4 mr-1.5" />
                Sign In
              </Link>
            </Button>
          )}
        </div>
      </div>
    </header>
  );
}
