-- Users/profiles are backed by Supabase Auth user id

create table if not exists public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  email text not null,
  full_name text,
  created_at timestamptz default now(),
  stripe_customer_id text,
  plan text default 'free', -- 'free', 'base', 'per_truck'
  max_trucks integer default 0,
  daily_digest boolean default true
);

create table if not exists public.trucks (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references auth.users(id) on delete cascade,
  name text not null,
  vin text,
  telematics_provider text, -- samsara, motive, geotab
  external_vehicle_id text,
  created_at timestamptz default now()
);

create table if not exists public.telematics_connections (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references auth.users(id) on delete cascade,
  provider text not null,
  access_token text,
  refresh_token text,
  expires_at timestamptz,
  scope text,
  created_at timestamptz default now()
);

create table if not exists public.reefer_events (
  id bigserial primary key,
  user_id uuid references auth.users(id) on delete cascade,
  truck_id uuid references public.trucks(id) on delete cascade,
  provider text,
  event_type text, -- temperature, door, defrost, ignition, location, setpoint
  cargo_type text,
  temperature numeric,
  setpoint numeric,
  latitude numeric,
  longitude numeric,
  raw_payload jsonb,
  occurred_at timestamptz not null
);

create table if not exists public.reefer_trips (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references auth.users(id) on delete cascade,
  truck_id uuid references public.trucks(id) on delete cascade,
  started_at timestamptz,
  ended_at timestamptz,
  origin text,
  destination text,
  receiver_lat numeric,
  receiver_lng numeric,
  cargo_type text,
  status text default 'open' -- open/completed
);

create table if not exists public.reefer_certificates (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references auth.users(id) on delete cascade,
  truck_id uuid references public.trucks(id) on delete cascade,
  trip_id uuid references public.reefer_trips(id),
  pdf_url text,
  ipfs_cid text,
  polygon_tx_hash text,
  created_at timestamptz default now()
);

create table if not exists public.recipient_emails (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references auth.users(id) on delete cascade,
  truck_id uuid references public.trucks(id),
  driver_email text,
  shipper_email text,
  broker_email text,
  insurance_email text,
  created_at timestamptz default now()
);

alter table public.profiles enable row level security;
alter table public.trucks enable row level security;
alter table public.telematics_connections enable row level security;
alter table public.reefer_events enable row level security;
alter table public.reefer_trips enable row level security;
alter table public.reefer_certificates enable row level security;
alter table public.recipient_emails enable row level security;

-- Basic RLS: users can see their own data
create policy "Users can manage own profile"
  on public.profiles for all
  using (auth.uid() = id)
  with check (auth.uid() = id);

create policy "Users manage own trucks"
  on public.trucks for all
  using (auth.uid() = user_id)
  with check (auth.uid() = user_id);

create policy "Users manage own telematics connections"
  on public.telematics_connections for all
  using (auth.uid() = user_id)
  with check (auth.uid() = user_id);

create policy "Users manage own events"
  on public.reefer_events for all
  using (auth.uid() = user_id)
  with check (auth.uid() = user_id);

create policy "Users manage own trips"
  on public.reefer_trips for all
  using (auth.uid() = user_id)
  with check (auth.uid() = user_id);

create policy "Users manage own certificates"
  on public.reefer_certificates for all
  using (auth.uid() = user_id)
  with check (auth.uid() = user_id);

create policy "Users manage own recipient emails"
  on public.recipient_emails for all
  using (auth.uid() = user_id)
  with check (auth.uid() = user_id);
