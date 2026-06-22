/**
 * Centralized API configuration for FlowZint Support BOT frontend.
 * Set VITE_API_BASE_URL in frontend/.env to point at a hosted backend.
 * Set VITE_ADMIN_API_KEY in frontend/.env with the shared admin secret key.
 */

export const API_BASE: string =
  import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export const ADMIN_API_KEY: string =
  import.meta.env.VITE_ADMIN_API_KEY || '';

/** Standard headers for public (customer) API calls */
export const publicHeaders = {
  'Content-Type': 'application/json',
};

/** Standard headers for admin/agent API calls — includes auth key */
export const adminHeaders = {
  'Content-Type': 'application/json',
  'X-Admin-Key': ADMIN_API_KEY,
};
