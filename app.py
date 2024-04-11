import os
import datetime
import streamlit as st
import psycopg2
from dotenv import load_dotenv
from dataclasses import dataclass

load_dotenv()

@dataclass
class Prompt:
    title: str
    prompt: str
    is_favorite: bool
    id: int = None  # Added ID field for easier reference
    created_at: datetime.datetime = None
    updated_at: datetime.datetime = None

def setup_database():
    con = psycopg2.connect(os.getenv("DATABASE_URL"))
    cur = con.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS prompts (
            id SERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            prompt TEXT NOT NULL,
            is_favorite BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    con.commit()
    return con, cur

def prompt_form(prompt=None):
    default = Prompt("", "", False) if prompt is None else prompt
    with st.form(key=f"prompt_form_{default.id}", clear_on_submit=True):
        title = st.text_input("Title", value=default.title)
        prompt_content = st.text_area("Prompt", height=200, value=default.prompt)
        is_favorite = st.checkbox("❤️Favorite", value=default.is_favorite)

        submitted = st.form_submit_button("Submit")
        if submitted:
            if not title or not prompt_content:
                st.error('Please fill in both the title and prompt fields.')
                return
            return Prompt(title, prompt_content, is_favorite, default.id)

def display_prompts(cur, con):
    # Search and sort functionality
    search_query = st.text_input("Search prompts")
    sort_order = st.selectbox("Sort by", ["Newest First", "Oldest First"])

    order_by = "created_at DESC" if sort_order == "Newest First" else "created_at ASC"
    cur.execute(f"SELECT * FROM prompts WHERE title ILIKE %s OR prompt ILIKE %s ORDER BY {order_by}", (f"%{search_query}%", f"%{search_query}%"))
    prompts = [Prompt(title=p[1], prompt=p[2], is_favorite=p[3], id=p[0]) for p in cur.fetchall()]

    for prompt in prompts:
        with st.expander(prompt.title):
            st.code(prompt.prompt)
            st.write(f"❤️Favorite: {'Yes' if prompt.is_favorite else 'No'}")

            # Edit function
            edit = st.button("Edit", key=f"edit_{prompt.id}")
            if edit:
                edited_prompt = prompt_form(prompt)
                if edited_prompt:
                    cur.execute(
                        "UPDATE prompts SET title = %s, prompt = %s, is_favorite = %s WHERE id = %s",
                        (edited_prompt.title, edited_prompt.prompt, edited_prompt.is_favorite, edited_prompt.id)
                    )
                    con.commit()
                    st.success("Prompt updated successfully!")
                    st.experimental_rerun()

            # Favorite button
            if st.button("Toggle Favorite", key=f"fav_{prompt.id}"):
                cur.execute("UPDATE prompts SET is_favorite = NOT is_favorite WHERE id = %s", (prompt.id,))
                con.commit()
                st.experimental_rerun()

            # Delete function
            if st.button("Delete", key=prompt.id):
                cur.execute("DELETE FROM prompts WHERE id = %s", (prompt.id,))
                con.commit()
                st.experimental_rerun()


if __name__ == "__main__":
    st.title("🍎 Promptbase")
    st.subheader("A simple app to store and retrieve prompts")

    con, cur = setup_database()

    new_prompt = prompt_form()
    if new_prompt:
        try: 
            cur.execute(
                "INSERT INTO prompts (title, prompt, is_favorite) VALUES (%s, %s, %s)",
                (new_prompt.title, new_prompt.prompt, new_prompt.is_favorite)
            )
            con.commit()
            st.success("Prompt added successfully!")
        except psycopg2.Error as e:
            st.error(f"Database error: {e}")

    display_prompts(cur, con)
    con.close()
