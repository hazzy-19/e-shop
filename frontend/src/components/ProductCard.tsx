import { Link } from 'react-router-dom';
import { ShoppingCart, Star, Heart, Package } from 'lucide-react';
import { Card, CardContent, CardFooter } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { useCart } from '@/store/CartContext';
import { getImageUrl, API_URL } from '@/api/client';
import { useAuth } from '@/lib/AuthContext';
import { useState, useEffect } from 'react';

type Product = {
  id: number;
  name: string;
  description?: string;
  price: number;
  stock: number;
  image_url?: string;
};

type Summary = { avg_rating: number; review_count: number; like_count: number; user_liked: boolean };

export default function ProductCard({ product }: { product: Product }) {
  const { addToCart } = useCart();
  const { user } = useAuth();
  const inStock = product.stock > 0;

  const [summary, setSummary] = useState<Summary | null>(null);
  const [liking, setLiking] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem('token');
    const endpoint = token
      ? `${API_URL}/reviews/${product.id}/summary`
      : `${API_URL}/reviews/${product.id}/public-summary`;
    fetch(endpoint, token ? { headers: { Authorization: `Bearer ${token}` } } : {})
      .then(r => r.ok ? r.json() : null)
      .then(d => d && setSummary(d))
      .catch(() => {});
  }, [product.id]);

  const handleLike = async (e: React.MouseEvent) => {
    e.preventDefault();
    if (!user) return;
    const token = localStorage.getItem('token');
    if (!token || liking) return;
    setLiking(true);
    try {
      const res = await fetch(`${API_URL}/reviews/${product.id}/like`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const d = await res.json();
        setSummary(prev => prev ? { ...prev, liked: d.liked, like_count: d.like_count, user_liked: d.liked } : prev);
      }
    } finally {
      setLiking(false);
    }
  };

  const renderStars = (rating: number) =>
    [1, 2, 3, 4, 5].map(i => (
      <Star
        key={i}
        className={`w-3 h-3 ${i <= Math.round(rating) ? 'fill-amber-400 text-amber-400' : 'fill-muted text-muted-foreground'}`}
      />
    ));

  return (
    <Card className="group flex flex-col overflow-hidden border border-border hover:border-primary/40 hover:shadow-lg hover:shadow-primary/10 transition-all duration-300 rounded-2xl">
      {/* Image */}
      <div className="relative aspect-square overflow-hidden bg-muted">
        {product.image_url ? (
          <img
            src={getImageUrl(product.image_url)}
            alt={product.name}
            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
          />
        ) : (
          <div className="w-full h-full flex flex-col items-center justify-center gap-2 text-muted-foreground">
            <Package className="w-12 h-12 opacity-30" />
            <span className="text-xs">No image</span>
          </div>
        )}

        {/* Like button */}
        {user && (
          <button
            onClick={handleLike}
            disabled={liking}
            className={`absolute top-3 right-3 w-8 h-8 rounded-full flex items-center justify-center
                        backdrop-blur-sm border border-white/20 transition-all duration-200 hover:scale-110
                        ${summary?.user_liked ? 'bg-red-500 text-white' : 'bg-black/30 text-white hover:bg-red-500/80'}`}
            aria-label="Like product"
          >
            <Heart className={`w-4 h-4 ${summary?.user_liked ? 'fill-white' : ''}`} />
          </button>
        )}

        {/* Stock badge */}
        {!inStock && (
          <div className="absolute inset-0 bg-background/70 backdrop-blur-sm flex items-center justify-center">
            <Badge variant="destructive" className="text-sm px-3 py-1">Out of Stock</Badge>
          </div>
        )}
        {inStock && product.stock <= 5 && (
          <Badge className="absolute top-3 left-3 bg-amber-500 text-white text-xs">
            Only {product.stock} left
          </Badge>
        )}
      </div>

      <CardContent className="flex-1 p-4 space-y-2">
        {/* Real rating or empty state */}
        <div className="flex items-center gap-1.5">
          {summary && summary.review_count > 0 ? (
            <>
              {renderStars(summary.avg_rating)}
              <span className="text-xs text-muted-foreground ml-0.5">
                {summary.avg_rating.toFixed(1)} ({summary.review_count})
              </span>
            </>
          ) : (
            <span className="text-xs text-muted-foreground">No reviews yet</span>
          )}
          {summary && summary.like_count > 0 && (
            <span className="ml-auto text-xs text-muted-foreground flex items-center gap-0.5">
              <Heart className="w-3 h-3 fill-red-400 text-red-400" />
              {summary.like_count}
            </span>
          )}
        </div>

        <Link to={`/product/${product.id}`} className="block group/name">
          <h3 className="font-semibold text-base leading-snug group-hover/name:text-primary transition-colors line-clamp-2">
            {product.name}
          </h3>
        </Link>

        {product.description && (
          <p className="text-xs text-muted-foreground line-clamp-2 leading-relaxed">
            {product.description}
          </p>
        )}
      </CardContent>

      <CardFooter className="p-4 pt-0 flex items-center justify-between gap-3">
        <div>
          <span className="text-xl font-bold text-foreground">KSh {product.price.toLocaleString()}</span>
        </div>
        <Button
          size="sm"
          disabled={!inStock}
          onClick={() => addToCart({ ...product, image_url: product.image_url ?? '' })}
          className="gap-1.5 shrink-0"
        >
          <ShoppingCart className="w-3.5 h-3.5" />
          Add
        </Button>
      </CardFooter>
    </Card>
  );
}
