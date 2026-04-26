import { useEffect, useState } from 'react';
import { API_URL } from '../api/client';
import { Skeleton } from '@/components/ui/skeleton';
import { Separator } from '@/components/ui/separator';
import ProductCard from '@/components/ProductCard';
import HeroSlideshow from '@/components/HeroSlideshow';
import { Tag } from 'lucide-react';

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

const PRODUCT_SKELETON = () => (
  <div className="rounded-2xl border border-border overflow-hidden">
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
);

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

  // Group products by category when no filter is active
  const groupedByCategory: { cat: Category | null; items: Product[] }[] = [];
  if (!selectedCat && !loading) {
    const uncategorised = products.filter(p => !p.category_id);
    categories.forEach(cat => {
      const items = products.filter(p => p.category_id === cat.id);
      if (items.length > 0) groupedByCategory.push({ cat, items });
    });
    if (uncategorised.length > 0) {
      groupedByCategory.push({ cat: null, items: uncategorised });
    }
  }

  const isGrouped = !selectedCat && groupedByCategory.length > 1;

  return (
    <div className="space-y-10">

      {/* ── Hero Slideshow ─────────────────────────────── */}
      <HeroSlideshow />

      {/* ── Category Filter Pills ─────────────────────── */}
      {categories.length > 0 && (
        <section className="flex flex-wrap gap-2">
          <button
            onClick={() => setSelectedCat(null)}
            className={`px-4 py-1.5 rounded-full text-sm font-medium transition-all border ${
              selectedCat === null
                ? 'bg-primary text-primary-foreground border-primary shadow-sm'
                : 'bg-transparent text-foreground border-border hover:bg-muted'
            }`}
          >
            All
          </button>
          {categories.map(cat => (
            <button
              key={cat.id}
              onClick={() => setSelectedCat(cat.id)}
              className={`px-4 py-1.5 rounded-full text-sm font-medium transition-all border ${
                selectedCat === cat.id
                  ? 'bg-primary text-primary-foreground border-primary shadow-sm'
                  : 'bg-transparent text-foreground border-border hover:bg-muted'
              }`}
            >
              {cat.name}
            </button>
          ))}
        </section>
      )}

      {/* ── Products Section ──────────────────────────── */}
      {loading ? (
        <div className="space-y-4">
          <Separator />
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
            {[...Array(8)].map((_, i) => <PRODUCT_SKELETON key={i} />)}
          </div>
        </div>
      ) : products.length === 0 ? (
        <div className="text-center py-24 text-muted-foreground">
          <div className="text-5xl mb-4">🛍️</div>
          <p className="text-lg font-medium">No products yet</p>
          <p className="text-sm">Check back soon or add items via the admin dashboard.</p>
        </div>
      ) : isGrouped ? (
        // ── Grouped by category ──────────────────────
        <div className="space-y-12">
          {groupedByCategory.map(({ cat, items }) => (
            <section key={cat?.id ?? 'uncategorised'} className="space-y-5">
              <div className="flex items-center justify-between gap-3">
                <div className="flex items-center gap-2">
                  <Tag className="w-4 h-4 text-primary" />
                  <h2 className="text-xl font-bold tracking-tight">
                    {cat?.name ?? 'Other Items'}
                  </h2>
                  <span className="text-xs text-muted-foreground bg-muted px-2 py-0.5 rounded-full">
                    {items.length}
                  </span>
                </div>
                <button
                  onClick={() => setSelectedCat(cat?.id ?? null)}
                  className="text-xs text-primary hover:underline underline-offset-2"
                >
                  View all →
                </button>
              </div>
              <Separator />
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
                {items.slice(0, 4).map(product => (
                  <ProductCard key={product.id} product={product} />
                ))}
              </div>
            </section>
          ))}
        </div>
      ) : (
        // ── Single flat grid (category selected or only one cat) ──
        <section className="space-y-5">
          <div className="flex items-center gap-3">
            <Tag className="w-5 h-5 text-primary" />
            <h2 className="text-2xl font-bold tracking-tight">
              {selectedCat ? categories.find(c => c.id === selectedCat)?.name : 'All Products'}
            </h2>
            <span className="text-sm text-muted-foreground ml-auto">{products.length} items</span>
          </div>
          <Separator />
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
            {products.map(product => (
              <ProductCard key={product.id} product={product} />
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
