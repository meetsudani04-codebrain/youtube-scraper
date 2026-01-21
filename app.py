import streamlit as st
import pandas as pd
from youtube_scraper import search_channels_by_keyword
# --------------------------
# PAGE CONFIG
# --------------------------
st.set_page_config(
    page_title="YouTube Channel Scraper",
    layout="wide"
)

st.title("YouTube Channel Scraper")
st.write("Search YouTube channels by keyword and filter by subscriber range")

# --------------------------
# SIDEBAR INPUTS
# --------------------------
st.sidebar.header("🔍 Search Filters")

keyword = st.sidebar.text_input(
    "Keyword",
    placeholder="e.g. tech, education, gaming"
)

max_channels = st.sidebar.number_input(
    "Max Channels",
    min_value=1,
    max_value=500,
    value=50,
    step=1
)

min_subs = st.sidebar.number_input(
    "Min Subscribers",
    min_value=0,
    value=0,
    step=100
)

max_subs = st.sidebar.number_input(
    "Max Subscribers",
    min_value=0,
    value=1_000_000,
    step=1000
)

# --------------------------
# ACTION BUTTON
# --------------------------
if st.sidebar.button("Start Scraping"):
    if not keyword:
        st.error("Please enter a keyword")
    else:
        with st.spinner("Fetching channels from YouTube..."):
            channels = search_channels_by_keyword(
                keyword=keyword,
                max_channels=max_channels,
                min_subs=min_subs,
                max_subs=max_subs
            )

        if not channels:
            st.warning("No channels found with the given filters.")
        else:
            df = pd.DataFrame(channels)

            st.success(f"✅ Found {len(df)} channels")
            st.dataframe(df, use_container_width=True)

            # Save Excel
            excel_file = f"youtube_channels_{keyword}.xlsx"
            df.to_excel(excel_file, index=False)

            with open(excel_file, "rb") as file:
                st.download_button(
                    label="⬇ Download Excel",
                    data=file,
                    file_name=excel_file,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

# --------------------------
# FOOTER
# --------------------------
st.markdown("---")
st.caption("Powered by YouTube Data API v3")
