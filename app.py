import os
import streamlit as st
from supabase import create_client
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

supabase = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"])
openai   = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

st.set_page_config(page_title="Baptist Press Archive Search", layout="wide")
st.title("Baptist Press Archive Search")
st.caption("Semantic search across thousands of press releases, 1948–1996")

query = st.text_input(
    "What are you looking for?",
    placeholder="e.g. a time a seminary president resigned over controversy"
)

col1, col2, col3 = st.columns(3)
with col1:
    year_from = st.number_input("From year", min_value=1948, max_value=1996, value=1948)
with col2:
    year_to = st.number_input("To year", min_value=1948, max_value=1996, value=1996)
with col3:
    num_results = st.select_slider("Results to show", options=[5, 10, 20, 30], value=10)

search_btn = st.button("Search", type="primary")

def search(query_text, from_year, to_year, top_k=10):
    response = openai.embeddings.create(
        model="text-embedding-3-small",
        input=query_text
    )
    query_embedding = response.data[0].embedding
    result = supabase.rpc("search_articles", {
        "query_embedding": query_embedding,
        "from_year":       from_year,
        "to_year":         to_year,
        "match_count":     top_k
    }).execute()
    return result.data

if search_btn and query:
    with st.spinner("Searching..."):
        results = search(query, year_from, year_to, num_results)
    if not results:
        st.warning("No results found. Try different search terms.")
    else:
        st.success(f"Found {len(results)} relevant articles")
        for row in results:
            date_str   = row.get("pub_date", "Unknown date")
            headline   = row.get("headline", "Untitled")
            body       = row.get("body", "")
            similarity = row.get("similarity", 0)
            with st.expander(f"{date_str} — {headline} (relevance: {similarity:.0%})"):
                st.write(body)
                st.caption(f"Source file: {row.get('file_name', '')}")
elif search_btn and not query:
    st.warning("Please enter a search query.")

with st.sidebar:
    st.header("Search Tips")
    st.markdown("""
    This is semantic search — search by concept, not just keywords.

    Try searches like:

    - a seminary president fired or forced out
    - church and state controversy over schools
    - missionary killed or died
    - college desegregation first Black student
    - large donation gift to a Baptist college
    - Southern Baptist Convention annual meeting controversy

    Use the date filters to narrow results to a specific era.
    """)