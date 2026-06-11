// Nova Analytics — public client configuration.
//
// These two values are PUBLIC by design. The Supabase anon key is safe to ship
// in client code (row-level security, not secrecy, protects your data). Fill
// them in after creating your Supabase project:
//   Supabase dashboard -> Project Settings -> API
//
// Until both are filled in, the app runs in clearly-labeled DEMO mode (auth is
// emulated in localStorage) so the landing page and login flow are fully
// demonstrable without any backend. Real Supabase auth activates automatically
// the moment valid values are present here.

export const SUPABASE_URL = "https://mfkdpwupggudwbnaowot.supabase.co";
export const SUPABASE_ANON_KEY = "sb_publishable_ZPLJbP3-U_Ep9d7x2018sQ_CPd-5Gtl";

// Where to send users after a successful login / signup.
export const AFTER_AUTH_REDIRECT = "/dashboard";
