import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Header from './components/Header';
import Storefront from './pages/Storefront';
import ProductDetail from './pages/ProductDetail';
import Cart from './pages/Cart';
import Login from './pages/Login';
import AdminLayout from './components/AdminLayout';
import AdminDashboard from './pages/AdminDashboard';
import AdminCategories from './pages/AdminCategories';
import AdminProducts from './pages/AdminProducts';
import AdminBulkUpload from './pages/AdminBulkUpload';
import { CartProvider } from './store/CartContext';
import { AuthProvider } from './lib/AuthContext';
import { Toaster } from '@/components/ui/sonner';

function App() {
  return (
    <AuthProvider>
      <CartProvider>
        <Router>
          <div className="min-h-screen flex flex-col bg-background">
            <Header />
            <main className="flex-grow container mx-auto px-4 py-10">
              <Routes>
                <Route path="/" element={<Storefront />} />
                <Route path="/product/:id" element={<ProductDetail />} />
                <Route path="/cart" element={<Cart />} />
                <Route path="/login" element={<Login />} />
                <Route path="/admin" element={<AdminLayout />}>
                  <Route index element={<AdminDashboard />} />
                  <Route path="categories" element={<AdminCategories />} />
                  <Route path="products" element={<AdminProducts />} />
                  <Route path="bulk-upload" element={<AdminBulkUpload />} />
                </Route>
              </Routes>
            </main>
            <footer className="border-t border-border bg-muted/30 text-center text-muted-foreground text-xs py-6 mt-auto">
              © 2026 eshop · Built with ❤️ using React & Shadcn UI
            </footer>
          </div>
          <Toaster />
        </Router>
      </CartProvider>
    </AuthProvider>
  );
}

export default App;
