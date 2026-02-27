import streamlit as st
import pandas as pd
from youtube_scraper import search_channels_by_keyword
from db.db_helpers import save_youtube_channels
from config.auth import (
    require_auth,
    get_current_user_id,
    redirect_to_login,
    hide_default_sidebar_nav,
    render_authenticated_sidebar,
    logout_user,
)

hide_default_sidebar_nav()

# Check authentication
if not require_auth():
    redirect_to_login()

# Get current user ID
current_user_id = get_current_user_id()
username = st.session_state.get('username', 'User')

# --------------------------
# PAGE CONFIG
# --------------------------
st.set_page_config(
    page_title="YouTube Channel Scraper",
    layout="wide"
)

with st.sidebar:
    render_authenticated_sidebar("dashboard")
    st.header(f"{username}")
    st.caption(f"User ID: {current_user_id}")
    if st.button("Logout", use_container_width=True):
        logout_user()
        st.rerun()

st.title("YouTube Channel Scraper")
st.info(f"**Logged in as:** {username} | Your scraped channels will be saved to your account")
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
            try:
                channels = search_channels_by_keyword(
                    keyword=keyword,
                    max_channels=max_channels,
                    min_subs=min_subs,
                    max_subs=max_subs
                )
            except ValueError as e:
                st.error(f"⚠️  Configuration Error: {str(e)}")
                st.info("**Setup Instructions:**\n1. Get a YouTube API key from [Google Cloud Console](https://console.cloud.google.com/)\n2. Create a `.env` file in the project folder:\n```\nYOUTUBE_API_KEY=your_api_key_here\n```\n3. Restart the app")
                channels = None
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                channels = None

        if channels is None:
            pass
        elif not channels:
            st.warning(f"⚠️  No channels found for '{keyword}' with subscriber range {min_subs:,} - {max_subs:,}")
            st.info("💡 Tips to find channels:\n- Try broader keywords (e.g., 'travel vlog' instead of just 'travel')\n- Adjust the subscriber range - many channels may fall outside your range\n- Check that your API key is valid")
        else:
            df = pd.DataFrame(channels)

            st.success(f"✅ Found {len(df)} channels")
            st.dataframe(df, use_container_width=True)

            # Save to database
            try:
                saved_count = save_youtube_channels(
                    channels=channels,
                    search_keyword=keyword,
                    user_id=current_user_id
                )
                st.info(f"💾 Saved {saved_count} channels to database")
            except Exception as e:
                st.warning(f"⚠️  Database save error: {str(e)}")
                st.info("Channels are still available for download below.")

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
