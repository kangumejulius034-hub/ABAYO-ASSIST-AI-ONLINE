import streamlit as st
from supabase import Client, create_client


@st.cache_resource
def get_supabase_client() -> Client:
    """Create and reuse one Supabase connection."""

    try:
        supabase_url = st.secrets["supabase"]["url"]
        supabase_key = st.secrets["supabase"]["key"]
    except KeyError as exc:
        raise RuntimeError(
            "Supabase secrets are missing from Streamlit settings."
        ) from exc

    return create_client(supabase_url, supabase_key)
