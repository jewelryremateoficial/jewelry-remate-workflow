-- Tabla de precios nuevos — Jewelry Remate MX
-- La persona de calidad escribe aqui el precio que decidio; Eduardo y las demas lideres lo ven.
-- Solo entra quien tenga usuario y contrasena (rol authenticated). Nunca 'anon': el sitio es
-- publico y cualquiera con el link podria mover precios.

create table if not exists public.precios_nuevos (
  sku           text primary key,
  producto      text,
  precio_nuevo  numeric(10,2) not null,
  nota          text,
  autor         text not null,
  actualizado   timestamptz not null default now()
);

alter table public.precios_nuevos enable row level security;

grant select, insert, update, delete on public.precios_nuevos to authenticated;

drop policy if exists pn_leer       on public.precios_nuevos;
drop policy if exists pn_insertar   on public.precios_nuevos;
drop policy if exists pn_actualizar on public.precios_nuevos;
drop policy if exists pn_borrar     on public.precios_nuevos;

create policy pn_leer       on public.precios_nuevos for select to authenticated using (true);
create policy pn_insertar   on public.precios_nuevos for insert to authenticated with check (true);
create policy pn_actualizar on public.precios_nuevos for update to authenticated using (true) with check (true);
create policy pn_borrar     on public.precios_nuevos for delete to authenticated using (true);

-- Deja constancia de cada cambio, para que se pueda ver el historial completo.
create table if not exists public.precios_nuevos_log (
  id           bigserial primary key,
  sku          text not null,
  precio_nuevo numeric(10,2),
  autor        text,
  momento      timestamptz not null default now()
);

alter table public.precios_nuevos_log enable row level security;
grant select, insert on public.precios_nuevos_log to authenticated;

drop policy if exists pnl_leer     on public.precios_nuevos_log;
drop policy if exists pnl_insertar on public.precios_nuevos_log;
create policy pnl_leer     on public.precios_nuevos_log for select to authenticated using (true);
create policy pnl_insertar on public.precios_nuevos_log for insert to authenticated with check (true);

create or replace function public.pn_log() returns trigger
language plpgsql security definer set search_path = public as $$
begin
  insert into public.precios_nuevos_log (sku, precio_nuevo, autor)
  values (new.sku, new.precio_nuevo, new.autor);
  return new;
end $$;

drop trigger if exists pn_log_trg on public.precios_nuevos;
create trigger pn_log_trg after insert or update on public.precios_nuevos
for each row execute function public.pn_log();
