import { useEffect, useState } from 'react';
import { API_URL } from '../api/client';
import { Skeleton } from '@/components/ui/skeleton';
import { Separator } from '@/components/ui/separator';
import ProductCard from '@/components/ProductCard';
import { Sparkles, Tag } from 'lucide-react';

type Product = {
  id: number;
  name: string;
  description?: string;
  price: number;
  stock: number;
  image_url?: string;
  category_id?: number | null;
};

type Category = {
  id: number;
  name: string;
  slug: string;
};

export default function Storefront() {
  const [products, setProducts] = useState<Product[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [selectedCat, setSelectedCat] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${API_URL}/categories/`)
      .then(res => res.json())
      .then(setCategories)
      .catch(console.error);
  }, []);

  useEffect(() => {
    setLoading(true);
    const catQuery = selectedCat ? `?category_id=${selectedCat}` : '';
    fetch(`${API_URL}/products/${catQuery}`)
      .then(res => res.json())
      .then(data => { setProducts(data); setLoading(false); })
      .catch(() => setLoading(false));
  }, [selectedCat]);

  return (
    <div className="space-y-14">
      {/* Hero */}
      <section className="relative rounded-3xl overflow-hidden bg-gradient-to-br from-primary/10 via-accent to-background border border-primary/20 px-8 py-16 text-center">
        <div className="absolute inset-0 opacity-[0.03] bg-[radial-gradient(circle_at_50%_50%,hsl(172,80%,36%),transparent_60%)]" />
        <div className="relative space-y-4 max-w-2xl mx-auto">
          <div className="inline-flex items-center gap-2 text-sm font-medium text-primary bg-primary/10 border border-primary/20 rounded-full px-4 py-1.5 mb-2">
            <Sparkles className="w-3.5 h-3.5" />
            Curated Collection
          </div>
          <h1 className="text-5xl font-extrabold tracking-tight text-foreground">
            Shop the finest<br />
            <span className="text-primary">essentials</span>
          </h1>
          <p className="text-muted-foreground text-lg max-w-xl mx-auto">
            Premium items, hand-picked for quality. Browse our collection and find something you'll love.
          </p>
        </div>
      </section>

      {/* Categories Filter */}
      {categories.length > 0 && (
                 <section className="flex flex-wrap gap-2 pt-2">
          <button
            onClick={() => setSelectedCat(null)}
            className={`px-4 py-1.5 rounded-full text-sm font-medium transition-colors border ${
              selectedCat === null
                ? 'bg-primary text-primary-foreground border-primary'
                : 'bg-transparent text-foreground border-border hover:bg-muted'
            }`}
          >
            All Products
          </button>
          {categories.map((cat) => (
            <button
              key={cat.id}
              onClick={() => setSelectedCat(cat.id)}
              className={`px-4 py-1.5 rounded-full text-sm font-medium transition-colors border ${
                selectedCat === cat.id
                  ? 'bg-primary text-primary-foreground border-primary'
                  : 'bg-transparent text-foreground border-border hover:bg-muted'
              }`}
            >
              {cat.name}
            </button>
          ))}
        </section>
      )}

      {/* Products */}
      <section className="space-y-6">
        <div className="flex items-center gap-3">
          <Tag className="w-5 h-5 text-primary" />
          <h2 className="text-2xl font-bold tracking-tight">{selectedCat ? categories.find(c => c.id === selectedCat)?.name : 'All Products'}</h2>
          {!loading && (
            <span className="text-sm text-muted-foreground ml-auto">{products.length} items</span>
          )}
        </div>
        <Separator />

        {loading ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
            {[...Array(8)].map((_, i) => (
              <div key={i} className="rounded-2xl border border-border overflow-hidden">
                <Skeleton className="aspect-square w-full" />
                <div className="p-4 space-y-3">
                  <Skeleton className="h-4 w-3/4" />
                  <Skeleton className="h-3 w-full" />
                  <Skeleton className="h-3 w-2/3" />
                  <div className="flex justify-between items-center pt-2">
                    <Skeleton className="h-6 w-16" />
                    <Skeleton className="h-8 w-20 rounded-lg" />
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : products.length === 0 ? (
          <div className="text-center py-24 text-muted-foreground">
            <div className="text-5xl mb-4">🛍️</div>
            <p className="text-lg font-medium">No products yet</p>
            <p className="text-sm">Check back soon or add items via the admin dashboard.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
            {products.map(product => (
              <ProductCard key={product.id} product={product} />
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
