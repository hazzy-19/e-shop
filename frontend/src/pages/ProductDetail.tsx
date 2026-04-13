import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useCart } from '../store/CartContext';
import { API_URL } from '../api/client';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Skeleton } from '@/components/ui/skeleton';
import { ShoppingCart, ArrowLeft, Package, CheckCircle2, XCircle, Star } from 'lucide-react';

type RawProduct = {
  id: number;
  name: string;
  description?: string;
  price: number;
  stock: number;
  image_url?: string;
};

export default function ProductDetail() {
  const { id } = useParams();
  const [product, setProduct] = useState<RawProduct | null>(null);
  const [loading, setLoading] = useState(true);
  const [added, setAdded] = useState(false);
  const { addToCart } = useCart();

  useEffect(() => {
    fetch(`${API_URL}/products/`)
      .then(res => res.json())
      .then(data => {
        setProduct(data.find((p: RawProduct) => p.id === Number(id)) || null);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, [id]);

  const handleAdd = () => {
    if (!product) return;
    addToCart({ ...product, image_url: product.image_url ?? '' });
    setAdded(true);
    setTimeout(() => setAdded(false), 1800);
  };

  if (loading) {
    return (
      <div className="max-w-5xl mx-auto flex flex-col md:flex-row gap-12 mt-10">
        <Skeleton className="md:w-1/2 aspect-square rounded-2xl" />
        <div className="md:w-1/2 space-y-4">
          <Skeleton className="h-10 w-3/4" />
          <Skeleton className="h-8 w-24" />
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-5/6" />
          <Skeleton className="h-12 w-40 mt-6" />
        </div>
      </div>
    );
  }

  if (!product) {
    return (
      <div className="text-center py-24 space-y-4">
        <p className="text-2xl font-bold text-foreground">Product not found</p>
        <Button asChild variant={"outline" as const}>
          <Link to="/"><ArrowLeft className="w-4 h-4 mr-1" /> Back to store</Link>
        </Button>
      </div>
    );
  }

  const inStock = product.stock > 0;

  return (
    <div className="max-w-5xl mx-auto mt-8 space-y-6">
      <Button asChild variant={"ghost" as const} size={"sm" as const} className="text-muted-foreground -ml-2">
        <Link to="/"><ArrowLeft className="w-4 h-4 mr-1" />All Products</Link>
      </Button>

      <div className="flex flex-col md:flex-row gap-10 lg:gap-16">
        {/* Image */}
        <div className="md:w-1/2">
          <div className="aspect-square rounded-2xl overflow-hidden bg-muted border border-border shadow-md">
            {product.image_url ? (
              <img src={product.image_url} alt={product.name} className="w-full h-full object-cover" />
            ) : (
              <div className="w-full h-full flex flex-col items-center justify-center gap-3 text-muted-foreground">
                <Package className="w-16 h-16 opacity-20" />
                <span className="text-sm">No image available</span>
              </div>
            )}
          </div>
        </div>

        {/* Details */}
        <div className="md:w-1/2 flex flex-col justify-center space-y-5">
          <div className="space-y-2">
            <div className="flex items-center gap-0.5">
              {[1,2,3,4,5].map(i => (
                <Star key={i} className={`w-4 h-4 ${i <= 4 ? 'fill-primary text-primary' : 'fill-muted text-muted'}`} />
              ))}
              <span className="text-sm text-muted-foreground ml-2">4.0 (24 reviews)</span>
            </div>
            <h1 className="text-4xl font-extrabold tracking-tight text-foreground">{product.name}</h1>
            <p className="text-3xl font-bold text-primary">${product.price.toFixed(2)}</p>
          </div>

          <Separator />

          <p className="text-muted-foreground leading-relaxed">
            {product.description || 'No description provided for this item.'}
          </p>

          <div className="flex items-center gap-2 text-sm">
            {inStock ? (
            <Badge variant={"outline" as const} className="border-emerald-500 text-emerald-600 gap-1">
              <CheckCircle2 className="w-3.5 h-3.5" /> In Stock ({product.stock} remaining)
            </Badge>
          ) : (
            <Badge variant={"outline" as const} className="border-destructive text-destructive gap-1">
              <XCircle className="w-3.5 h-3.5" /> Out of Stock
            </Badge>
          )}
        </div>

        <Button
          size={"lg" as const}
            disabled={!inStock}
            onClick={handleAdd}
            className="w-full md:w-auto gap-2 text-base mt-2"
          >
            <ShoppingCart className="w-4 h-4" />
            {added ? '✓ Added to Cart!' : inStock ? 'Add to Cart' : 'Unavailable'}
          </Button>
        </div>
      </div>
    </div>
  );
}
