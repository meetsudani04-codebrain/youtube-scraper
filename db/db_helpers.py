"""Database helpers for youtube_scraper and contacts tables."""

from __future__ import annotations

from typing import Iterable, List, Dict

import psycopg2
from psycopg2.extras import execute_values

from . import db

POST_COLUMNS = (
    "id",
    "channel_name",
    "channel_id",
    "channel_url",
    "subscribers",
    "total_videos",
    "total_views",
    "country",
    "joined_date",
    "thumbnail_url",
    "about_section",
    "created_at",
)


def init_job_tables() -> None:
    """Ensure job_posts and contacts tables exist."""
    conn = db.get_connection()
    if not conn:
        raise psycopg2.OperationalError("Unable to connect to database")

    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS scraped_channels (
            id SERIAL PRIMARY KEY,
            channel_name TEXT,
            channel_id TEXT UNIQUE,
            channel_url TEXT,
            subscribers BIGINT,
            total_videos BIGINT,
            total_views BIGINT,
            country TEXT,
            joined_date DATE,
            thumbnail_url TEXT,
            about_section TEXT,
            contact TEXT,
            search_keyword TEXT,
            user_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    conn.commit()
    cur.close()
    conn.close()


def init_channels_table() -> None:
    """Ensure scraped_channels table exists."""
    conn = db.get_connection()
    if not conn:
        raise psycopg2.OperationalError("Unable to connect to database")

    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS scraped_channels (
            id SERIAL PRIMARY KEY,
            channel_name TEXT,
            channel_id TEXT UNIQUE,
            channel_url TEXT,
            subscribers BIGINT,
            total_videos BIGINT,
            total_views BIGINT,
            country TEXT,
            joined_date DATE,
            thumbnail_url TEXT,
            about_section TEXT,
            contact TEXT,
            search_keyword TEXT,
            user_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    conn.commit()
    cur.close()
    conn.close()


def save_youtube_channels(
    channels: Iterable[dict],
    search_keyword: str | None = None,
    user_id: str | None = None,
) -> int:
    """Save YouTube channels to database. Returns number of channels saved."""
    init_channels_table()
    conn = db.get_connection()
    if not conn:
        raise psycopg2.OperationalError("Unable to connect to database")

    # Ensure user_id is a string
    if user_id is not None:
        user_id = str(user_id).strip()

    cur = conn.cursor()

    # Get existing channel_ids to avoid duplicates
    cur.execute(
        """
        SELECT DISTINCT channel_id 
        FROM scraped_channels 
        WHERE channel_id IS NOT NULL AND channel_id != ''
        """
    )
    existing_channel_ids = {row[0] for row in cur.fetchall()}

    # Prepare data for insertion
    channels_data = []
    for channel in channels:
        channel_id = channel.get("Channel ID", "")
        
        # Skip if channel_id already exists
        if channel_id and channel_id in existing_channel_ids:
            continue

        # Convert joined_date string to date if needed
        joined_date = channel.get("Joined Date", "")
        if joined_date and joined_date != "N/A":
            try:
                # Handle date string format
                if isinstance(joined_date, str):
                    # Try parsing the date
                    from datetime import datetime
                    try:
                        joined_date = datetime.strptime(joined_date, "%Y-%m-%d").date()
                    except:
                        joined_date = None
                else:
                    joined_date = None
            except:
                joined_date = None
        else:
            joined_date = None

        channels_data.append((
            channel.get("Channel Name", ""),
            channel_id,
            channel.get("Channel URL", ""),
            channel.get("Subscribers", 0),
            channel.get("Total Videos", 0),
            channel.get("Total Views", 0),
            channel.get("Country", ""),
            joined_date,
            channel.get("Thumbnail URL", ""),
            channel.get("About Section", ""),
            "",  # contact field
            search_keyword,
            user_id,
        ))
        
        # Add to existing set to avoid duplicates in the same batch
        if channel_id:
            existing_channel_ids.add(channel_id)

    saved_count = 0
    if channels_data:
        execute_values(
            cur,
            """
            INSERT INTO scraped_channels
            (channel_name, channel_id, channel_url, subscribers, total_videos, 
             total_views, country, joined_date, thumbnail_url, about_section, 
             contact, search_keyword, user_id)
            VALUES %s
            ON CONFLICT (channel_id) DO UPDATE SET
                channel_name = EXCLUDED.channel_name,
                channel_url = EXCLUDED.channel_url,
                subscribers = EXCLUDED.subscribers,
                total_videos = EXCLUDED.total_videos,
                total_views = EXCLUDED.total_views,
                country = EXCLUDED.country,
                joined_date = EXCLUDED.joined_date,
                thumbnail_url = EXCLUDED.thumbnail_url,
                about_section = EXCLUDED.about_section
            """,
            channels_data,
        )
        saved_count = len(channels_data)

    conn.commit()
    cur.close()
    conn.close()
    
    return saved_count


def fetch_youtube_channels(
    search_keyword: str | None = None,
    user_id: str | None = None,
    limit: int | None = None,
) -> List[Dict]:
    """Fetch YouTube channels from database."""
    conn = db.get_connection()
    if not conn:
        return []

    cur = conn.cursor()
    
    query = """
        SELECT id, channel_name, channel_id, channel_url, subscribers,
               total_videos, total_views, country, joined_date, thumbnail_url,
               about_section, contact, search_keyword, user_id, created_at
        FROM scraped_channels
        WHERE 1=1
    """
    params = []
    
    if search_keyword:
        query += " AND search_keyword = %s"
        params.append(search_keyword)
    
    if user_id:
        # Convert user_id to string to ensure proper comparison with TEXT field
        user_id_str = str(user_id).strip()
        # Use direct comparison - user_id is stored as TEXT in database
        query += " AND user_id = %s"
        params.append(user_id_str)
    
    query += " ORDER BY created_at DESC"
    
    if limit:
        query += " LIMIT %s"
        params.append(limit)
    
    cur.execute(query, params)
    rows = cur.fetchall()
    cur.close()
    conn.close()

    columns = [
        "id", "channel_name", "channel_id", "channel_url", "subscribers",
        "total_videos", "total_views", "country", "joined_date", "thumbnail_url",
        "about_section", "contact", "search_keyword", "user_id", "created_at"
    ]
    
    return [dict(zip(columns, row)) for row in rows]


def delete_youtube_channel(channel_id: int, user_id: str | None = None) -> bool:
    """Delete a YouTube channel from database."""
    conn = db.get_connection()
    if not conn:
        return False

    cur = conn.cursor()
    
    if user_id:
        cur.execute(
            "DELETE FROM scraped_channels WHERE id = %s AND user_id = %s",
            (channel_id, user_id),
        )
    else:
        cur.execute(
            "DELETE FROM scraped_channels WHERE id = %s",
            (channel_id,),
        )
    
    deleted = cur.rowcount > 0
    conn.commit()
    cur.close()
    conn.close()
    return deleted


def fetch_job_posts(user_id: str) -> List[Dict]:
    """Return list of job posts for a user."""
    conn = db.get_connection()
    if not conn:
        return []

    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, author_name, author_profile, content, email,
               contact, search_keyword, user_id, created_at
        FROM job_posts
        WHERE user_id = %s
        ORDER BY created_at DESC
        """,
        (user_id,),
    )

    rows = cur.fetchall()
    cur.close()
    conn.close()

    return [dict(zip(POST_COLUMNS, row)) for row in rows]


def delete_job_post(post_id: int, user_id: str) -> bool:
    conn = db.get_connection()
    if not conn:
        return False

    cur = conn.cursor()
    cur.execute(
        "DELETE FROM job_posts WHERE id = %s AND user_id = %s",
        (post_id, user_id),
    )
    deleted = cur.rowcount > 0
    conn.commit()
    cur.close()
    conn.close()
    return deleted


def add_job_post(
    name: str,
    profile: str,
    content: str,
    email: str,
    phone: str,
    user_id: str,
) -> bool:
    conn = db.get_connection()
    if not conn:
        return False

    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO job_posts (author_name, author_profile, content, email, contact, user_id)
        VALUES (%s, %s, %s, %s, %s, %s)
        """,
        (name, profile, content, email, phone, user_id),
    )
    conn.commit()
    cur.close()
    conn.close()
    return True


def save_scraped_posts(
    posts: Iterable[dict],
    emails: Iterable[str],
    phones: Iterable[str],
    user_id: str | None = None,
    search_keyword: str | None = None,
) -> None:
    """Persist scraped posts plus contact info."""
    init_job_tables()
    conn = db.get_connection()
    if not conn:
        raise psycopg2.OperationalError("Unable to connect to database")

    cur = conn.cursor()

    effective_user_id = user_id
    effective_keyword = search_keyword

    # Check for existing posts to avoid duplicates
    # Get existing author_profile URLs for this user
    if effective_user_id:
        cur.execute(
            """
            SELECT DISTINCT author_profile 
            FROM job_posts 
            WHERE user_id = %s AND author_profile IS NOT NULL AND author_profile != ''
            """,
            (effective_user_id,),
        )
        existing_profiles = {row[0] for row in cur.fetchall()}
    else:
        existing_profiles = set()

    # Filter out duplicates: check if author_profile already exists for this user
    posts_data = []
    for post in posts:
        author_profile = post.get("author", "")
        # Only add if this profile doesn't already exist for this user
        if not author_profile or author_profile not in existing_profiles:
            posts_data.append((
                post.get("author_name", ""),
                author_profile,
                post.get("content", ""),
                post.get("email", ""),
                post.get("contact", ""),
                effective_keyword,
                effective_user_id,
            ))
            # Add to existing_profiles to avoid duplicates in the same batch
            if author_profile:
                existing_profiles.add(author_profile)

    if posts_data:
        execute_values(
            cur,
            """
            INSERT INTO job_posts
            (author_name, author_profile, content, email, contact, search_keyword, user_id)
            VALUES %s
            """,
            posts_data,
        )

    for email in emails:
        if not email:
            continue
        try:
            cur.execute(
                """
                INSERT INTO contacts (email, phone_number)
                VALUES (%s, %s)
                ON CONFLICT (email) DO NOTHING
                """,
                (email, ""),
            )
        except psycopg2.Error:
            pass

    for phone in phones:
        if not phone:
            continue
        try:
            cur.execute(
                """
                SELECT id FROM contacts WHERE phone_number = %s
                """,
                (phone,),
            )
            if not cur.fetchone():
                cur.execute(
                    """
                    INSERT INTO contacts (email, phone_number)
                    VALUES (%s, %s)
                    """,
                    ("", phone),
                )
        except psycopg2.Error:
            pass

    conn.commit()
    cur.close()
    conn.close()

