# Supabase setup (authentication)

Nova Analytics uses Supabase email/password auth. This takes ~5 minutes and is
free. Until you complete it, the site runs in **demo mode** (auth emulated in the
browser) — which is fine for a quick look, but do this for *real* logins.

## 1. Create the project

1. Go to <https://supabase.com> → sign in → **New project**.
2. Name it `nova-analytics`, pick a region close to you, set a database password
   (you won't need it for this), and create the project. Wait ~2 minutes for it
   to provision.

## 2. Get your public keys

1. Project → **Project Settings** (gear) → **API**.
2. Copy:
   - **Project URL** → e.g. `https://abcdxyz.supabase.co`
   - **anon public** key (a long JWT).

## 3. Put them in the app

Edit [`web/js/config.js`](../../web/js/config.js):

```js
export const SUPABASE_URL = "https://abcdxyz.supabase.co";   // your Project URL
export const SUPABASE_ANON_KEY = "eyJhbGciOi...";            // your anon public key
```

Commit and push — Vercel redeploys automatically, and real Supabase auth turns on
(the demo fallback turns off the moment these are no longer placeholders).

> These values are **public by design**. The anon key is meant to be shipped in
> client code; your data is protected by Supabase row-level security, not by
> hiding the key.

## 4. Make signup → login instant (recommended for reviewers)

By default Supabase requires email confirmation, which blocks immediate login.
For a smooth demo:

- Project → **Authentication** → **Providers** → **Email** →
  turn **off** "Confirm email" → Save.

Now a brand-new signup is logged in immediately and redirected to the dashboard.

## 5. Create the reviewer test account

So reviewers can log in without signing up, pre-create the account:

- Project → **Authentication** → **Users** → **Add user** → **Create new user**.
- Email: `admin@novaanalytics.io`
- Password: `NovaDemo2026!`  (or your own — then share it in your submission)
- Check **Auto Confirm User** → Create.

That's it. Test it at `https://<your-vercel-url>/login`.
