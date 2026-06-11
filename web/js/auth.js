// Nova Analytics — authentication layer.
//
// Primary backend: Supabase email/password auth.
// Fallback: a clearly-labeled DEMO backend (localStorage) used only when
// config.js still holds placeholder values, so the experience is demonstrable
// before/without a Supabase project. The public API below is identical for both
// backends, so page code never branches on which one is active.

import { SUPABASE_URL, SUPABASE_ANON_KEY, AFTER_AUTH_REDIRECT } from "./config.js";

export const AFTER_AUTH = AFTER_AUTH_REDIRECT;

const isPlaceholder = (v) => !v || v.includes("YOUR-") || v.trim() === "";
export const usingSupabase = !isPlaceholder(SUPABASE_URL) && !isPlaceholder(SUPABASE_ANON_KEY);

// --- Supabase backend --------------------------------------------------------
let _supabase = null;
async function supa() {
  if (_supabase) return _supabase;
  const { createClient } = await import("https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2/+esm");
  const url = SUPABASE_URL.startsWith("http") ? SUPABASE_URL : `https://${SUPABASE_URL}`;
  _supabase = createClient(url, SUPABASE_ANON_KEY);
  return _supabase;
}

// --- Demo backend (localStorage) --------------------------------------------
const DEMO_USERS = "nova_demo_users";
const DEMO_SESSION = "nova_demo_session";
const seedDemo = () => {
  if (localStorage.getItem(DEMO_USERS)) return;
  // Pre-seeded reviewer credentials so login works out of the box in demo mode.
  localStorage.setItem(DEMO_USERS, JSON.stringify({ "admin@novaanalytics.io": "NovaDemo2026!" }));
};
const demo = {
  async signUp(email, password) {
    seedDemo();
    const users = JSON.parse(localStorage.getItem(DEMO_USERS));
    email = email.toLowerCase().trim();
    if (users[email]) return { error: "An account with this email already exists. Try logging in." };
    users[email] = password;
    localStorage.setItem(DEMO_USERS, JSON.stringify(users));
    localStorage.setItem(DEMO_SESSION, JSON.stringify({ email }));
    return { user: { email } };
  },
  async signIn(email, password) {
    seedDemo();
    const users = JSON.parse(localStorage.getItem(DEMO_USERS));
    email = email.toLowerCase().trim();
    if (!users[email] || users[email] !== password) return { error: "Invalid email or password." };
    localStorage.setItem(DEMO_SESSION, JSON.stringify({ email }));
    return { user: { email } };
  },
  async getUser() {
    const s = localStorage.getItem(DEMO_SESSION);
    return s ? JSON.parse(s) : null;
  },
  async signOut() { localStorage.removeItem(DEMO_SESSION); },
};

// --- Public API --------------------------------------------------------------
export async function signUp(email, password) {
  if (!usingSupabase) return demo.signUp(email, password);
  const sb = await supa();
  const { data, error } = await sb.auth.signUp({ email, password });
  if (error) return { error: error.message };
  return { user: data.user };
}

export async function signIn(email, password) {
  if (!usingSupabase) return demo.signIn(email, password);
  const sb = await supa();
  const { data, error } = await sb.auth.signInWithPassword({ email, password });
  if (error) return { error: error.message };
  return { user: data.user };
}

export async function getUser() {
  if (!usingSupabase) return demo.getUser();
  const sb = await supa();
  const { data } = await sb.auth.getSession();
  return data.session ? data.session.user : null;
}

export async function signOut(redirect = "/login") {
  if (!usingSupabase) await demo.signOut();
  else { const sb = await supa(); await sb.auth.signOut(); }
  window.location.replace(redirect);
}

// Guard a protected page: returns the user or redirects to /login.
export async function requireAuth(redirect = "/login") {
  const user = await getUser();
  if (!user) { window.location.replace(redirect); return null; }
  return user;
}
