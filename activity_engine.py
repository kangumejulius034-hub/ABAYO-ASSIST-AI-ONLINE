from supabase_engine import get_supabase_client


def log_activity(
    machine_id,
    activity_type,
    description,
    status="Completed",
):
    try:
        supabase = get_supabase_client()

        supabase.table("machine_activity").insert(
            {
                "machine_id": machine_id,
                "activity_type": activity_type,
                "description": description,
                "status": status,
            }
        ).execute()

        return True

    except Exception as error:
        print(f"Activity logging failed: {error}")
        return False
