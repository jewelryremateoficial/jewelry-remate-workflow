-- Invitar miembros del equipo (correr en Supabase → SQL Editor).
-- Agrega/edita los correos y corre. Roles: 'admin' | 'editor' | 'viewer'.

insert into public.invitations (email, org_id, role) values
  ('correo1@ejemplo.com', '4a7c2e10-9b3d-4f6a-8c5e-2d1f0b9a8e7c', 'editor'),
  ('correo2@ejemplo.com', '4a7c2e10-9b3d-4f6a-8c5e-2d1f0b9a8e7c', 'editor')
on conflict (email) do update set role = excluded.role;

-- Por si alguno ya había iniciado sesión antes de ser invitado:
select public.claim_invitations();
