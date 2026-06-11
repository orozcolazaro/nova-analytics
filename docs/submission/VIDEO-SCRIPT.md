# Video walkthrough script (5–10 min)

A suggested structure. Speak naturally — these are beats, not a teleprompter.
Have two browser tabs ready: the live Vercel URL and the GitHub repo.

## 0. Intro (30s)
- "Hi, I'm <name>. This is my walkthrough of the Nova Analytics whitelabel build."
- One sentence on the brief: "I forked an open-source lead-gen dashboard, rebranded
  it as a fictional client — Nova Analytics — added a landing page with real auth,
  and deployed it live on Vercel."

## 1. Landing page (1.5 min)
- Open the live URL. Scroll slowly through hero → features → how-it-works → CTA.
- Call out the branding: the nova mark, the gradient wordmark, the "signal in the
  dark" aesthetic, the live-looking signal preview card in the hero.
- Resize the window (or open dev-tools device mode) to show it's **responsive**.
- "No references to the original product remain anywhere in the UI."

## 2. Signup → dashboard (1.5 min)
- Click **Get started** → signup page. Create an account with a fresh email.
- Show the redirect straight into the **dashboard** after signup.
- Walk the dashboard: the branded top bar with your signed-in email, the 8 scored
  leads, filters, sorting, status badges.
- Expand a row → show the score breakdown, active roles, and the **AI-drafted
  outreach** message (note it's signed "Nova Analytics" — fully rebranded).

## 3. Auth is real (1 min)
- Click **Log out** → back to login.
- Manually type `/dashboard` in the URL bar → show it **redirects to /login**
  (the dashboard is actually gated, not just hidden).
- Log back in with the test credentials → back in the dashboard.

## 4. Technical decisions (2 min)
- Show the GitHub repo briefly. Mention:
  - **Architecture:** dependency-free static site (HTML + Alpine.js + Tailwind),
    no build step → rock-solid demo + instant deploys.
  - **Auth:** Supabase email/password — real managed auth, minimal code; the anon
    key is public by design (RLS protects data). A demo fallback keeps the flow
    working before Supabase is wired.
  - **Deploy:** Vercel, root directory `web/`, automatic HTTPS, push-to-deploy CI/CD.
  - **Tests/CI:** GitHub Actions runs ruff + pytest on every push (36 tests green).
  - **Whitelabel:** scrubbed every "Greensoft" string including inside the sample
    data and the Python prompts; fixed the tests that asserted on them.
- Briefly mention the AI-assisted workflow: "I drove this with Claude Code —
  brainstormed the approach, had it build the brand system and pages, and verified
  the auth flow in a live preview before deploying."

## 5. Limitations & wrap (45s)
- Be honest: "Auth gates the UI client-side; the production hardening is RLS-backed
  data in Supabase. Sample data is curated; wiring the daily pipeline output is a
  small follow-up."
- "Repo, live URL, and test credentials are in the submission. Thanks for watching."

## Recording tips
- Loom or OBS at 1080p. Close noisy tabs/notifications.
- Do a 20-second dry run of the signup so it's smooth on camera.
- If Supabase email-confirmation is on, use the pre-created test account for the
  login demo instead of a fresh signup.
