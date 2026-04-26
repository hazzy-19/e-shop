/**
 * Payhero payment API client — frontend wrapper.
 * Calls the backend /api/payments/* endpoints.
 */
import { API_URL } from './client';

function getAuthHeaders(): HeadersInit {
  const token = localStorage.getItem('token');
  return {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}

// ─── Types ───────────────────────────────────────

export interface PaymentInitiateResponse {
  transaction_id: string;
  status: string;
  message: string;
}

export interface PaymentStatusResponse {
  transaction_id: string;
  order_id: number;
  amount: number;
  phone_number: string;
  status: string;
  status_detail: string | null;
  created_at: string;
  confirmed_at: string | null;
}

// ─── API Calls ───────────────────────────────────

/**
 * Initiate an M-Pesa STK Push for an order.
 * The customer will receive a PIN prompt on their phone.
 */
export async function initiatePayment(
  orderId: number,
  phoneNumber: string
): Promise<PaymentInitiateResponse> {
  const res = await fetch(`${API_URL}/payments/initiate`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify({
      order_id: orderId,
      phone_number: phoneNumber,
    }),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Failed to initiate payment');
  }
  return res.json();
}

/**
 * Poll the payment status.
 * Call this every few seconds after initiating payment.
 */
export async function checkPaymentStatus(
  transactionId: string
): Promise<PaymentStatusResponse> {
  const res = await fetch(`${API_URL}/payments/status/${transactionId}`, {
    headers: getAuthHeaders(),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Failed to check payment status');
  }
  return res.json();
}

/**
 * Get all payments for the current user.
 */
export async function getMyPayments(): Promise<PaymentStatusResponse[]> {
  const res = await fetch(`${API_URL}/payments/my`, {
    headers: getAuthHeaders(),
  });

  if (!res.ok) {
    throw new Error('Failed to fetch payments');
  }
  return res.json();
}
