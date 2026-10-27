/** GET /api/auth/me */
export interface Me {
  id: string;
  email: string;
  first_name: string | null;
  last_name: string | null;
  onboarding_state: string;
}
