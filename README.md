# E-shop

A modern e-commerce application with a React (Vite+Shadcn UI) frontend and a FastAPI (PostgreSQL) backend, featuring a Telegram bot for admin management.

## Project Structure

- `/frontend` - React application built with TypeScript, Tailwind CSS, and Shadcn UI.
- `/backend` - FastAPI Python application using SQLAlchemy mapped to PostgreSQL, and a python-telegram-bot admin assistant.

## Setup Instructions

### Backend (Python/FastAPI)

1. Open a terminal and navigate to the `backend` folder:
   ```bash
   cd backend
   ```
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   # Windows:
   .\venv\Scripts\activate
   # macOS/Linux:
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Configure environment variables:
   Copy `.env.example` to `.env` and fill in your PostgreSQL credentials and Telegram Bot token.

5. Start the backend:
   ```bash
   # On Windows, you can simply run:
   .\start.bat
   ```

### Frontend (React/Vite)

1. Open a terminal and navigate to the `frontend` folder:
   ```bash
   cd frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Start the development server:
   ```bash
   npm run dev
   ```

## Features
- **Storefront**: Browse products with categories.
- **Cart & Checkout**: Add items to your cart and checkout.
- **Admin Dashboard**: View statistics and manage orders.
- **Telegram Bot**: Add products, bulk upload products via CSV, and hide/reveal products on the fly directly from Telegram.
