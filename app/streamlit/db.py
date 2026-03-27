import streamlit as st
from supabase import create_client
from dotenv import load_dotenv
import os

load_dotenv()

@st.cache_resource
def get_client():
    return create_client(
        os.getenv("SUPABASE_URL"),
        os.getenv("SUPABASE_KEY")
    )