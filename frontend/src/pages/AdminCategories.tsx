import { useEffect, useState } from 'react';
import { API_URL } from '@/api/client';
import { Button } from '@/components/ui/button';
import { FolderTree, Plus } from 'lucide-react';

type Category = {
  id: number;
  name: string;
  slug: string;
  subcategories: Category[];
};

export default function AdminCategories() {
  const [categories, setCategories] = useState<Category[]>([]);

  useEffect(() => {
    fetch(`${API_URL}/categories/`)
      .then(r => r.json())
      .then(setCategories)
      .catch(console.error);
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-primary">Categories</h1>
          <p className="text-muted-foreground">Manage your storefront navigation tree.</p>
        </div>
        <Button className="flex items-center gap-2">
          <Plus size={16} /> Add Category
        </Button>
      </div>

      <div className="bg-muted/30 border border-border rounded-xl p-6">
        {categories.length === 0 ? (
          <div className="text-center py-12 text-muted-foreground">
            <FolderTree className="w-12 h-12 mx-auto mb-4 opacity-20" />
            <p>No categories found.</p>
          </div>
        ) : (
          <ul className="space-y-3">
            {categories.map(c => (
              <li key={c.id} className="bg-card border border-border p-4 rounded-lg flex justify-between items-center">
                <div>
                  <span className="font-semibold">{c.name}</span>
                  <span className="text-xs text-muted-foreground ml-3">/{c.slug}</span>
                  {c.subcategories && c.subcategories.length > 0 && (
                    <div className="mt-2 pl-4 border-l-2 border-border space-y-1">
                      {c.subcategories.map(s => (
                        <div key={s.id} className="text-sm text-muted-foreground flex items-center gap-2">
                          <div className="w-2 h-[1px] bg-border" />
                          {s.name}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
                <Button variant="outline" size="sm">Edit</Button>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
