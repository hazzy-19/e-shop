import { Link } from 'react-router-dom';
import { ShoppingCart, Star, Package } from 'lucide-react';
import { Card, CardContent, CardFooter } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { useCart } from '@/store/CartContext';

type Product = {
  id: number;
  name: string;
  description?: string;
  price: number;
  stock: number;
  image_url?: string;
};

export default function ProductCard({ product }: { product: Product }) {
  const { addToCart } = useCart();
  const inStock = product.stock > 0;

  return (
    <Card className="group flex flex-col overflow-hidden border border-border hover:border-primary/40 hover:shadow-lg hover:shadow-primary/10 transition-all duration-300 rounded-2xl">
      {/* Image */}
      <div className="relative aspect-square overflow-hidden bg-muted">
        {product.image_url ? (
          <img
            src={product.image_url}
            alt={product.name}
            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
          />
        ) : (
          <div className="w-full h-full flex flex-col items-center justify-center gap-2 text-muted-foreground">
            <Package className="w-12 h-12 opacity-30" />
            <span className="text-xs">No image</span>
          </div>
        )}

        {/* Stock badge */}
        {!inStock && (
          <div className="absolute inset-0 bg-background/70 backdrop-blur-sm flex items-center justify-center">
            <Badge variant="destructive" className="text-sm px-3 py-1">Out of Stock</Badge>
          </div>
        )}

        {/* Low stock hint */}
        {inStock && product.stock <= 5 && (
          <Badge className="absolute top-3 left-3 bg-amber-500 text-white text-xs">
            Only {product.stock} left
          </Badge>
        )}
      </div>

      <CardContent className="flex-1 p-4 space-y-2">
        {/* Rating placeholder — gives premium feel */}
        <div className="flex items-center gap-0.5">
          {[1,2,3,4,5].map(i => (
            <Star key={i} className={`w-3 h-3 ${i <= 4 ? 'fill-primary text-primary' : 'fill-muted text-muted-foreground'}`} />
          ))}
          <span className="text-xs text-muted-foreground ml-1">(24)</span>
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
          <span className="text-xl font-bold text-foreground">${product.price.toFixed(2)}</span>
        </div>
        <Button
          size="sm"
          disabled={!inStock}
          onClick={() => addToCart({ ...product, image_url: product.image_url ?? '' })}  className="gap-1.5 shrink-0"
        >
          <ShoppingCart className="w-3.5 h-3.5" />
          Add
        </Button>
      </CardFooter>
    </Card>
  );
}
