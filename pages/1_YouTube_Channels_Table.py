import streamlit as st
import pandas as pd
from io import BytesIO
from datetime import datetime
from db.db_helpers import (
    init_channels_table,
    fetch_youtube_channels,
    delete_youtube_channel,
)
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

st.set_page_config(page_title="YouTube Channels Table", page_icon="📺", layout="wide")

with st.sidebar:
    render_authenticated_sidebar("youtube_channels")
    st.header(f"{username}")
    st.caption(f"User ID: {current_user_id}")
    if st.button("🔄 Refresh Data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    if st.button("Logout", use_container_width=True):
        logout_user()
        st.rerun()

st.title("All YouTube Channels (Database Table)")
st.info(f"**Logged in as:** {username} | Showing only your channels")

# Initialize database tables if they don't exist
try:
    init_channels_table()
except Exception as e:
    st.error(f"Error initializing database: {e}")
    st.stop()

def dataframe_to_xlsx_bytes(df: pd.DataFrame) -> bytes:
    """Convert DataFrame to Excel bytes."""
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Channels')
    return output.getvalue()

def render_filters(df: pd.DataFrame) -> dict:
    """Render filter UI and return filter values."""
    filters = {}
    
    with st.sidebar:
        st.header("🔍 Filters")
        
        # Search keyword filter
        if 'search_keyword' in df.columns:
            unique_keywords = [''] + sorted(df['search_keyword'].dropna().unique().tolist())
            selected_keyword = st.selectbox(
                "Search Keyword",
                options=unique_keywords,
                format_func=lambda x: "All" if x == '' else x
            )
            filters['search_keyword'] = selected_keyword if selected_keyword else None
        
        # Channel name search
        channel_name_filter = st.text_input(
            "Channel Name (contains)",
            value="",
            placeholder="Search channel names..."
        )
        filters['channel_name'] = channel_name_filter if channel_name_filter else None
        
        # Subscriber range
        st.subheader("Subscriber Range")
        min_subs = st.number_input(
            "Min Subscribers",
            min_value=0,
            value=0,
            step=1000,
            key="min_subs_filter"
        )
        max_subs = st.number_input(
            "Max Subscribers",
            min_value=0,
            value=10_000_000,
            step=10000,
            key="max_subs_filter"
        )
        filters['min_subscribers'] = min_subs if min_subs > 0 else None
        filters['max_subscribers'] = max_subs if max_subs < 10_000_000 else None
        
        # Country filter
        if 'country' in df.columns:
            unique_countries = [''] + sorted(df['country'].dropna().unique().tolist())
            selected_country = st.selectbox(
                "Country",
                options=unique_countries,
                format_func=lambda x: "All" if x == '' else x
            )
            filters['country'] = selected_country if selected_country else None
    
    return filters

def apply_filters(df: pd.DataFrame, filters: dict) -> pd.DataFrame:
    """Apply filters to DataFrame."""
    filtered_df = df.copy()
    
    if filters.get('search_keyword'):
        filtered_df = filtered_df[
            filtered_df['search_keyword'].str.contains(
                filters['search_keyword'], 
                case=False, 
                na=False
            )
        ]
    
    if filters.get('channel_name'):
        filtered_df = filtered_df[
            filtered_df['channel_name'].str.contains(
                filters['channel_name'], 
                case=False, 
                na=False
            )
        ]
    
    if filters.get('min_subscribers') is not None:
        filtered_df = filtered_df[
            filtered_df['subscribers'] >= filters['min_subscribers']
        ]
    
    if filters.get('max_subscribers') is not None:
        filtered_df = filtered_df[
            filtered_df['subscribers'] <= filters['max_subscribers']
        ]
    
    if filters.get('country'):
        filtered_df = filtered_df[
            filtered_df['country'].str.contains(
                filters['country'], 
                case=False, 
                na=False
            )
        ]
    
    return filtered_df

@st.cache_data
def load_youtube_channels(user_id: str):
    """Load YouTube channels from database for the current user only."""
    try:
        # Ensure user_id is a string
        user_id_str = str(user_id).strip() if user_id else None
        if not user_id_str:
            return pd.DataFrame()
        
        records = fetch_youtube_channels(user_id=user_id_str)
        if not records:
            return pd.DataFrame()
        df = pd.DataFrame(records)
        return df
    except Exception as e:
        st.error(f"Error loading YouTube channels: {e}")
        import traceback
        st.error(traceback.format_exc())
        return pd.DataFrame()

def delete_record(channel_id: int, user_id: str):
    """Delete a channel record only if it belongs to the current user."""
    try:
        return delete_youtube_channel(channel_id, user_id=user_id)
    except Exception as e:
        st.error(f"Error deleting record: {e}")
        return False

try:
    df = load_youtube_channels(current_user_id)
    
    if df.empty:
        st.info(f"No YouTube channels found for your account (User ID: {current_user_id}). Go to the Dashboard and scrape channels to collect data.")
        # Show debug info
        with st.expander("Debug Information"):
            st.write(f"Current User ID: {current_user_id}")
            st.write(f"User ID Type: {type(current_user_id)}")
            # Try to fetch all channels to see what's in DB
            try:
                from db.db_helpers import fetch_youtube_channels
                all_channels = fetch_youtube_channels()
                st.write(f"Total channels in DB (all users): {len(all_channels)}")
                if all_channels:
                    sample = all_channels[0]
                    st.write(f"Sample channel user_id: {sample.get('user_id')} (type: {type(sample.get('user_id'))})")
            except Exception as e:
                st.write(f"Error checking DB: {e}")
        st.stop()
    
    filters = render_filters(df)
    df = apply_filters(df, filters)

    st.subheader(f"Total Channels: {len(df)}")

    # Pagination
    ITEMS_PER_PAGE = 20
    if "channels_page" not in st.session_state:
        st.session_state.channels_page = 1

    total_pages = max(1, (len(df) - 1) // ITEMS_PER_PAGE + 1)
    start_idx = (st.session_state.channels_page - 1) * ITEMS_PER_PAGE
    end_idx = start_idx + ITEMS_PER_PAGE
    page_df = df.iloc[start_idx:end_idx]

    st.write(f"Page {st.session_state.channels_page} of {total_pages}")

    c_prev, c_next = st.columns(2)
    with c_prev:
        if st.button("Previous", disabled=st.session_state.channels_page == 1):
            st.session_state.channels_page -= 1
            st.rerun()
    with c_next:
        if st.button("Next", disabled=st.session_state.channels_page >= total_pages):
            st.session_state.channels_page += 1
            st.rerun()

    # Selection Logic 
    if "selected_channels" not in st.session_state:
        st.session_state.selected_channels = {}

    st.divider()

    # Single Select All checkbox
    select_all = st.checkbox("Select All (This Page)", key="select_all_checkbox")
    if "prev_select_all" not in st.session_state:
        st.session_state.prev_select_all = False

    # Apply select-all changes only when the checkbox state toggles
    if select_all and not st.session_state.prev_select_all:
        for _, row in page_df.iterrows():
            st.session_state.selected_channels[row["id"]] = row.to_dict()
            st.session_state[f"select_{row['id']}"] = True
    elif not select_all and st.session_state.prev_select_all:
        for _, row in page_df.iterrows():
            st.session_state.selected_channels.pop(row["id"], None)
            st.session_state[f"select_{row['id']}"] = False

    st.session_state.prev_select_all = select_all

    # Table Rows 
    for idx, row in page_df.iterrows():
        col_select, col_content, col_delete = st.columns([1, 8, 2])

        with col_select:
            is_selected = st.checkbox(
                "Select row",
                key=f"select_{row['id']}",
                value=row["id"] in st.session_state.selected_channels,
                label_visibility="collapsed",
            )

            if is_selected:
                st.session_state.selected_channels[row["id"]] = row.to_dict()
            else:
                st.session_state.selected_channels.pop(row["id"], None)

        with col_content:
            channel_name = row.get('channel_name', 'N/A')
            subscribers = f"{row.get('subscribers', 0):,}" if row.get('subscribers') else "0"
            
            with st.expander(f"{channel_name} ({subscribers} subscribers)"):
                if row.get("channel_url"):
                    st.write("**Channel URL:**", f"[{row['channel_url']}]({row['channel_url']})")
                if row.get("channel_id"):
                    st.write("**Channel ID:**", row["channel_id"])
                if row.get("subscribers") is not None:
                    st.write("**Subscribers:**", f"{row['subscribers']:,}")
                if row.get("total_videos") is not None:
                    st.write("**Total Videos:**", f"{row['total_videos']:,}")
                if row.get("total_views") is not None:
                    st.write("**Total Views:**", f"{row['total_views']:,}")
                if row.get("country"):
                    st.write("**Country:**", row["country"])
                if row.get("joined_date"):
                    st.write("**Joined Date:**", str(row["joined_date"]))
                if row.get("thumbnail_url"):
                    st.image(row["thumbnail_url"], width=200)
                if row.get("about_section"):
                    st.write("**About:**", row["about_section"][:500] + "..." if len(row.get("about_section", "")) > 500 else row["about_section"])
                if row.get("search_keyword"):
                    st.write("**Search Keyword:**", row["search_keyword"])
                st.write("**Created At:**", str(row.get("created_at", "N/A"))[:19] if row.get("created_at") else "N/A")

        with col_delete:
            if st.button("Delete", key=f"del_{row['id']}"):
                if delete_record(row["id"], current_user_id):
                    st.cache_data.clear()
                    st.success(f"Channel {row['id']} deleted")
                else:
                    st.error("Failed to delete channel. It may not belong to you.")
                st.rerun()

    st.divider()

    # Footer Actions 
    if st.session_state.selected_channels:
        selected_df = pd.DataFrame(st.session_state.selected_channels.values())
        channels_xlsx = dataframe_to_xlsx_bytes(selected_df)

        st.download_button(
            "Download Selected Channels (XLSX)",
            channels_xlsx,
            file_name=f"youtube_channels_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

        if st.button("Delete Selected", use_container_width=True):
            deleted_count = 0
            for rid in list(st.session_state.selected_channels.keys()):
                if delete_record(rid, current_user_id):
                    deleted_count += 1
            st.session_state.selected_channels.clear()
            st.cache_data.clear()
            if deleted_count > 0:
                st.success(f"{deleted_count} channel(s) deleted")
            else:
                st.warning("No channels were deleted.")
            st.rerun()

except Exception as e:
    st.error(f"Error loading YouTube channels: {e}")
    import traceback
    with st.expander("Show Error Details"):
        st.code(traceback.format_exc())
    st.info("Make sure the database is running and accessible.")

