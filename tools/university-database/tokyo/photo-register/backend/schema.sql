-- Moderated community university photo submissions.
-- Run in the private Supabase project used for review operations.

create table if not exists public.photo_submissions (
  submission_id text primary key,
  client_submission_id text,
  university_id text not null,
  university_name text not null,
  submitted_at timestamptz not null default now(),
  photo_count integer not null check (photo_count between 1 and 9),
  main_photo jsonb,
  agreements jsonb not null,
  status text not null default 'pending' check (status in ('pending','approved','rejected','published')),
  package_path text not null,
  reviewer_note text,
  reviewed_at timestamptz
);

alter table public.photo_submissions enable row level security;

-- No anonymous read/write policy is created intentionally.
-- Public submissions must enter through the Edge Function using the service role.
-- The review UI should require authenticated operator access.

insert into storage.buckets (id,name,public)
values ('university-photo-submissions','university-photo-submissions',false)
on conflict (id) do update set public=false;
