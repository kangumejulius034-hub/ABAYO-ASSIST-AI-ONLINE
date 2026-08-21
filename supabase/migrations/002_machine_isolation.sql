-- ABAYO multi-machine isolation
-- Run after 001_launch_persistence.sql.
-- Adds machine_id where the legacy relational tables already exist.

do $$
begin
    if to_regclass('public.faults') is not null then
        alter table public.faults add column if not exists machine_id text;
        alter table public.faults add column if not exists machine_model text;
        create index if not exists faults_machine_id_idx on public.faults (machine_id);
    end if;

    if to_regclass('public.maintenance_history') is not null then
        alter table public.maintenance_history add column if not exists machine_id text;
        create index if not exists maintenance_history_machine_id_idx on public.maintenance_history (machine_id);
    end if;

    if to_regclass('public.recipes') is not null then
        alter table public.recipes add column if not exists machine_id text;
        create index if not exists recipes_machine_id_idx on public.recipes (machine_id);
    end if;

    if to_regclass('public.machine_components') is not null then
        alter table public.machine_components add column if not exists machine_id text;
        create index if not exists machine_components_machine_id_idx on public.machine_components (machine_id);
    end if;
end
$$;

-- Existing knowledge_documents payloads remain compatible. New records written
-- by ABAYO include machine_id inside each JSON record. Legacy records without a
-- machine_id are exposed only to the original Pakona profile by application logic.
