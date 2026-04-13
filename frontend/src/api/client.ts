export const API_URL = "http://localhost:8000/api";

export const fetchProducts = async () => {
    const response = await fetch(`${API_URL}/products/`);
    if (!response.ok) throw new Error("Failed to fetch products");
    return response.json();
};

// ... other endpoints ...
