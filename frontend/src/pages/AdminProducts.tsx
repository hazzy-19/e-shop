import { useEffect, useState } from 'react';
import { API_URL } from '@/api/client';
import { Package, EyeOff } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';

export default function AdminProducts() {
  const [products, setProducts] = useState<any[]>([]);

  useEffect(() => {
    fetchProducts();
  }, []);

  const fetchProducts = () => {
    fetch(`${API_URL}/products/`)
      .then(r => r.json())
      .then(setProducts);
  };

  const handleHide = async (id: number) => {
    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`${API_URL}/products/${id}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        setProducts(prev => prev.filter(p => p.id !== id));
      }
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-primary">Products</h1>
        <p className="text-muted-foreground">Manage your current active inventory.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {products.length === 0 && <p className="text-muted-foreground">No active products.</p>}
        {products.map((p) => (
          <div key={p.id} className="bg-card border border-border rounded-xl overflow-hidden shadow-sm flex flex-col">
            <div className="h-40 bg-muted/50 border-b border-border flex items-center justify-center overflow-hidden">
              {p.image_url ? (
                <img src={p.image_url.startsWith('http') ? p.image_url : `${API_URL.replace('/api', '')}${p.image_url}`} alt={p.name} className="w-full h-full object-cover" />
              ) : (
                <Package className="text-muted-foreground opacity-30 w-12 h-12" />
              )}
            </div>
            <div className="p-4 flex-1 flex flex-col">
              <div className="flex justify-between items-start mb-2">
                <h3 className="font-semibold text-lg line-clamp-1">{p.name}</h3>
                <span className="font-bold text-primary">${p.price.toFixed(2)}</span>
              </div>
              <div className="flex justify-between items-center mt-auto pt-4">
                <Badge variant={p.stock > 0 ? "default" : "destructive"}>
                  {p.stock} in stock
                </Badge>
                <Button variant="ghost" size="sm" className="text-muted-foreground hover:text-destructive" onClick={() => handleHide(p.id)}>
                  <EyeOff size={16} className="mr-2" /> Hide
                </Button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
