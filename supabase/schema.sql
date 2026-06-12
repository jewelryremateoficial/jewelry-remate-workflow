-- ============================================================
-- Jewelry Remate · Workflow Editor — Esquema de base de datos
-- Pegar COMPLETO en Supabase → SQL Editor → Run.
-- Es seguro correrlo una sola vez en un proyecto nuevo.
-- ============================================================

-- ---------- TABLAS ----------

-- Equipos (organizaciones). Jewelry Remate = 1 fila.
create table public.organizations (
  id          uuid primary key default gen_random_uuid(),
  name        text not null,
  created_at  timestamptz not null default now()
);

-- Quién pertenece a qué equipo y con qué rol.
create table public.memberships (
  org_id      uuid not null references public.organizations(id) on delete cascade,
  user_id     uuid not null references auth.users(id) on delete cascade,
  role        text not null default 'editor' check (role in ('admin','editor','viewer')),
  created_at  timestamptz not null default now(),
  primary key (org_id, user_id)
);

-- Invitaciones por correo: al iniciar sesión por primera vez,
-- la persona invitada se vuelve miembro automáticamente.
create table public.invitations (
  email       text primary key,
  org_id      uuid not null references public.organizations(id) on delete cascade,
  role        text not null default 'editor' check (role in ('admin','editor','viewer')),
  created_at  timestamptz not null default now()
);

-- El workflow completo (el objeto G de la app) como JSON.
create table public.workflows (
  id          uuid primary key default gen_random_uuid(),
  org_id      uuid not null references public.organizations(id) on delete cascade,
  name        text not null default 'Workflow',
  graph       jsonb not null default '{}'::jsonb,
  version     int  not null default 1,
  updated_at  timestamptz not null default now(),
  updated_by  uuid references auth.users(id)
);

-- Metadata de archivos adjuntos (el binario vive en Storage).
create table public.files (
  id            uuid primary key default gen_random_uuid(),
  workflow_id   uuid not null references public.workflows(id) on delete cascade,
  owner_type    text not null check (owner_type in ('node','edge','card')),
  owner_id      text not null,
  name          text not null,
  mime          text,
  size          bigint,
  storage_path  text not null,
  created_at    timestamptz not null default now(),
  created_by    uuid references auth.users(id)
);

-- ---------- FUNCIONES DE PERMISOS ----------
-- security definer: evita recursión de RLS al consultar memberships.

create or replace function public.is_member(org uuid) returns boolean
language sql stable security definer set search_path = public as $$
  select exists (select 1 from memberships m where m.org_id = org and m.user_id = auth.uid());
$$;

create or replace function public.is_editor(org uuid) returns boolean
language sql stable security definer set search_path = public as $$
  select exists (select 1 from memberships m where m.org_id = org and m.user_id = auth.uid()
                 and m.role in ('admin','editor'));
$$;

create or replace function public.is_admin(org uuid) returns boolean
language sql stable security definer set search_path = public as $$
  select exists (select 1 from memberships m where m.org_id = org and m.user_id = auth.uid()
                 and m.role = 'admin');
$$;

-- ---------- ALTA AUTOMÁTICA DE INVITADOS ----------

create or replace function public.handle_new_user() returns trigger
language plpgsql security definer set search_path = public as $$
begin
  insert into memberships (org_id, user_id, role)
  select i.org_id, new.id, i.role
  from invitations i
  where lower(i.email) = lower(new.email)
  on conflict do nothing;
  return new;
end; $$;

create trigger on_auth_user_created
  after insert on auth.users
  for each row execute function public.handle_new_user();

-- Para usuarios que YA habían iniciado sesión antes de ser invitados:
create or replace function public.claim_invitations() returns void
language sql security definer set search_path = public as $$
  insert into memberships (org_id, user_id, role)
  select i.org_id, u.id, i.role
  from invitations i
  join auth.users u on lower(u.email) = lower(i.email)
  on conflict do nothing;
$$;

-- ---------- ACTUALIZACIÓN AUTOMÁTICA DE updated_at ----------

create or replace function public.touch_workflow() returns trigger
language plpgsql security definer set search_path = public as $$
begin
  new.updated_at := now();
  new.updated_by := auth.uid();
  return new;
end; $$;

create trigger workflows_touch
  before update on public.workflows
  for each row execute function public.touch_workflow();

-- ---------- SEGURIDAD (RLS) ----------

alter table public.organizations enable row level security;
alter table public.memberships  enable row level security;
alter table public.invitations  enable row level security;
alter table public.workflows    enable row level security;
alter table public.files        enable row level security;

-- organizations: solo miembros la ven
create policy org_select on public.organizations
  for select using (public.is_member(id));

-- memberships: miembros ven la lista de su equipo; solo admin la modifica
create policy mem_select on public.memberships
  for select using (public.is_member(org_id));
create policy mem_insert on public.memberships
  for insert with check (public.is_admin(org_id));
create policy mem_update on public.memberships
  for update using (public.is_admin(org_id));
create policy mem_delete on public.memberships
  for delete using (public.is_admin(org_id));

-- invitations: solo admin
create policy inv_select on public.invitations
  for select using (public.is_admin(org_id));
create policy inv_insert on public.invitations
  for insert with check (public.is_admin(org_id));
create policy inv_delete on public.invitations
  for delete using (public.is_admin(org_id));

-- workflows: miembros leen; editores/admin escriben
create policy wf_select on public.workflows
  for select using (public.is_member(org_id));
create policy wf_insert on public.workflows
  for insert with check (public.is_editor(org_id));
create policy wf_update on public.workflows
  for update using (public.is_editor(org_id));
create policy wf_delete on public.workflows
  for delete using (public.is_admin(org_id));

-- files: igual que workflows (vía su workflow)
create policy fi_select on public.files
  for select using (public.is_member((select w.org_id from public.workflows w where w.id = workflow_id)));
create policy fi_insert on public.files
  for insert with check (public.is_editor((select w.org_id from public.workflows w where w.id = workflow_id)));
create policy fi_delete on public.files
  for delete using (public.is_editor((select w.org_id from public.workflows w where w.id = workflow_id)));

-- ---------- STORAGE (archivos adjuntos) ----------
-- Bucket privado; las rutas empiezan con el org_id: <org_id>/<workflow_id>/<archivo>

insert into storage.buckets (id, name, public)
values ('workflow-files', 'workflow-files', false);

create policy storage_read on storage.objects
  for select using (
    bucket_id = 'workflow-files'
    and public.is_member((split_part(name, '/', 1))::uuid)
  );
create policy storage_write on storage.objects
  for insert with check (
    bucket_id = 'workflow-files'
    and public.is_editor((split_part(name, '/', 1))::uuid)
  );
create policy storage_delete on storage.objects
  for delete using (
    bucket_id = 'workflow-files'
    and public.is_editor((split_part(name, '/', 1))::uuid)
  );

-- ---------- TIEMPO REAL ----------
alter publication supabase_realtime add table public.workflows;

-- ---------- DATOS INICIALES ----------
-- El equipo, el workflow vacío y el primer admin (dueño).

insert into public.organizations (id, name)
values ('4a7c2e10-9b3d-4f6a-8c5e-2d1f0b9a8e7c', 'Jewelry Remate');

insert into public.workflows (id, org_id, name, graph)
values ('b3d9f8a2-5c41-4e7b-9a6d-1e8c7f2a3b4d',
        '4a7c2e10-9b3d-4f6a-8c5e-2d1f0b9a8e7c',
        'Workflow Operativo', '{}'::jsonb);

-- 👇 El dueño/admin. (Cambia el correo si usas otro en Supabase.)
insert into public.invitations (email, org_id, role)
values ('jewelryremateoficial@gmail.com', '4a7c2e10-9b3d-4f6a-8c5e-2d1f0b9a8e7c', 'admin');

-- Si ese correo ya inició sesión alguna vez, dale la membresía ya:
select public.claim_invitations();
