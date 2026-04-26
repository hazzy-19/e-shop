export const API_URL = "http://localhost:8000/api";

export const fetchProducts = async () => {
    const response = await fetch(`${API_URL}/products/`);
    if (!response.ok) throw new Error("Failed to fetch products");
    return response.json();
};

// ... other endpoints ...

export const getImageUrl = (url?: string | null) => {
    if (!url) return '';
    if (url.startsWith('http')) return url;
    return `${API_URL.replace('/api', '')}${url.startsWith('/') ? '' : '/'}${url}`;
};
