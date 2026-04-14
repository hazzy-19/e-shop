import { Outlet, Link, useLocation } from 'react-router-dom';
import { LayoutDashboard, Package, FolderTree, UploadCloud } from 'lucide-react';
import { cn } from '@/lib/utils';

export default function AdminLayout() {
  const location = useLocation();

  const links = [
    { name: 'Dashboard', path: '/admin', icon: LayoutDashboard },
    { name: 'Products', path: '/admin/products', icon: Package },
    { name: 'Categories', path: '/admin/categories', icon: FolderTree },
    { name: 'Bulk Upload', path: '/admin/bulk-upload', icon: UploadCloud },
  ];

  return (
    <div className="flex h-full min-h-[70vh] gap-6">
      {/* Sidebar */}
      <aside className="w-64 flex-shrink-0 bg-card rounded-lg border border-border overflow-hidden flex flex-col">
        <div className="p-4 border-b border-border">
          <h2 className="font-semibold text-lg text-primary">Admin Control</h2>
          <p className="text-xs text-muted-foreground mt-1">Manage your storefront</p>
        </div>
        <nav className="flex-1 p-3 space-y-1">
          {links.map((link) => {
            const Icon = link.icon;
            const isActive = location.pathname === link.path || (link.path !== '/admin' && location.pathname.startsWith(link.path));
            
            return (
              <Link
                key={link.path}
                to={link.path}
                className={cn(
                  "flex items-center gap-3 px-3 py-2.5 rounded-md text-sm font-medium transition-colors",
                  isActive 
                    ? "bg-primary text-primary-foreground" 
                    : "text-muted-foreground hover:bg-muted hover:text-foreground"
                )}
              >
                <Icon size={18} />
                {link.name}
              </Link>
            );
          })}
        </nav>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 bg-card rounded-lg border border-border p-6 shadow-sm overflow-auto">
        <Outlet />
      </main>
    </div>
  );
}
