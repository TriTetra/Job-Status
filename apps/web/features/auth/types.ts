/** GET /api/auth/me */
export interface Me {
  id: string;
  email: string;
  first_name: string | null;
  last_name: string | null;
  onboarding_state: string;
  is_admin: boolean;
}

/** Body of POST /api/auth/setup and /api/auth/invites/accept */
export interface NewAccount {
  email: string;
  password: string;
  first_name?: string;
  last_name?: string;
}

/** GET /api/auth/invites (admin) */
export interface Invite {
  id: string;
  email: string | null;
  created_at: string;
  expires_at: string;
  used_at: string | null;
  used_by_email: string | null;
}

/** POST /api/auth/invites — the link is only ever returned here */
export interface CreatedInvite {
  id: string;
  email: string | null;
  expires_at: string;
  url: string;
}
