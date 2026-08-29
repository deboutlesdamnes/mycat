// ---------------------------------------------------------------------------
// Supabase project credentials for MyCat accounts + cross-device sync.
//
// Fill both values in from your Supabase dashboard (Project Settings -> API).
// Until BOTH are set, MyCat runs exactly as before: no accounts, and all
// progress stays in this browser's localStorage.
//
// The anon key is meant to be shipped in client code — what protects each
// user's data is row-level security on the `profiles` table. Run this once
// in the Supabase SQL editor to create it:
//
//   create table public.profiles (
//     user_id    uuid primary key references auth.users on delete cascade,
//     state      jsonb not null default '{}'::jsonb,
//     updated_at timestamptz not null default now()
//   );
//   alter table public.profiles enable row level security;
//   create policy "own profile: read"   on public.profiles
//     for select using (auth.uid() = user_id);
//   create policy "own profile: insert" on public.profiles
//     for insert with check (auth.uid() = user_id);
//   create policy "own profile: update" on public.profiles
//     for update using (auth.uid() = user_id);
// ---------------------------------------------------------------------------
window.SUPABASE_CONFIG = {
  url: "https://cesnimeepkzkhrtlvorf.supabase.co",     
  anonKey: "sb_publishable_ejzLDuN30T5ecOl4H2tcuA_9jpdXSN1",  // the "anon" / "public" API key
};
