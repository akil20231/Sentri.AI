import sqlite3
import pandas as pd
import streamlit as st
from db import DB_PATH

st.set_page_config(page_title="AgentGuard Dashboard", layout="wide")
st.title("AgentGuard Dashboard")

conn = sqlite3.connect(DB_PATH)

decisions = pd.read_sql_query(
    "SELECT * FROM decisions ORDER BY ts DESC LIMIT 500",
    conn
)
events = pd.read_sql_query(
    "SELECT * FROM events ORDER BY ts DESC LIMIT 500",
    conn
)

col1, col2 = st.columns(2)

with col1:
    st.subheader("Recent Decisions")
    st.dataframe(decisions, use_container_width=True, height=400)

with col2:
    st.subheader("Recent Events")
    st.dataframe(events[["ts","channel_id","user_id","has_link","mentions_count","content"]], use_container_width=True, height=400)

st.subheader("Flagged Users (top by risk)")
if not decisions.empty:
    agg = (decisions.groupby("user_id")
           .agg(max_risk=("final_risk","max"),
                last_action=("action","last"),
                last_ts=("ts","max"),
                count=("id","count"))
           .reset_index()
           .sort_values("max_risk", ascending=False))
    st.dataframe(agg, use_container_width=True)

st.subheader("Inspect a user")
user_id = st.text_input("Enter user_id")
if user_id:
    try:
        uid = int(user_id)
        ud = decisions[decisions["user_id"] == uid].copy()
        st.write("Decisions for user:", uid)
        st.dataframe(ud, use_container_width=True)
    except ValueError:
        st.warning("user_id must be an integer")
