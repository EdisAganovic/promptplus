import streamlit as st
import json
import os
from typing import Dict, List

# File to store prompts
PROMPTS_FILE = "prompts.json"

def load_prompts() -> Dict[str, str]:
    """Load prompts from a JSON file."""
    if os.path.exists(PROMPTS_FILE):
        with open(PROMPTS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_prompts(prompts: Dict[str, str]) -> None:
    """Save prompts to a JSON file."""
    with open(PROMPTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(prompts, f, ensure_ascii=False, indent=2)

def main():
    st.set_page_config(page_title="Prompt Manager", layout="wide")
    st.title("🌍 GPT Plus")
    
    # Initialize session state
    if 'prompts' not in st.session_state:
        st.session_state.prompts = load_prompts()
    
    # Sidebar for managing prompts
    st.sidebar.header("Dodaj novi prompt")
    
    # Form to add new prompt in sidebar
    with st.sidebar.form("add_prompt_form"):
        new_keyword = st.text_input("Ključna riječ (npr. `:lektor`)", placeholder=":ime_prompta")
        new_content = st.text_area("Sadržaj prompta", height=100)
        submitted = st.form_submit_button("Dodaj Prompt")
        
        if submitted:
            if new_keyword and new_content:
                st.session_state.prompts[new_keyword] = new_content
                save_prompts(st.session_state.prompts)
                st.success(f"Prompt '{new_keyword}' je dodan!")
                st.rerun()
            else:
                st.error("Molim Vas unesite ključnu riječ i sadržaj prompta!")
    
    # Display and edit existing prompts in main area
    st.header("Aktivni Prompti")
    if st.session_state.prompts:
        st.write("Sljedeći prompti su trenutno aktivni:")
        for i, (keyword, content) in enumerate(st.session_state.prompts.items()):
            # Format the keyword for proper display in Streamlit, especially for keywords starting with ':'
            display_keyword = f"`{keyword}`"
            with st.expander(display_keyword):
                # Display keyword prominently at the top when expanded
                # Edit form for each prompt
                edit_form_key = f"edit_form_{i}"
                with st.form(edit_form_key):
                    edited_keyword = st.text_input("Ključna riječ", value=keyword, key=f"edit_keyword_{i}")
                    edited_content = st.text_area("Sadržaj prompta", value=content, height=150, key=f"edit_content_{i}")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        update_btn = st.form_submit_button("Ažuriraj", type="primary")
                    with col2:
                        delete_btn = st.form_submit_button("Obriši", type="secondary")
                    
                    if update_btn:
                        if edited_keyword and edited_content:
                            # Remove old key and add new one
                            del st.session_state.prompts[keyword]
                            st.session_state.prompts[edited_keyword] = edited_content
                            save_prompts(st.session_state.prompts)
                            st.success(f"Prompt '{edited_keyword}' ažuriran!")
                            st.rerun()
                        else:
                            st.error("Molim Vas unesite ključnu riječ i sadržaj prompta!")
                    
                    if delete_btn:
                        del st.session_state.prompts[keyword]
                        save_prompts(st.session_state.prompts)
                        st.success(f"Prompt '{keyword}' obrisan!")
                        st.rerun()
    else:
        st.info("Nema dodanih prompta. Dodajte prompt u sidebaru!")

if __name__ == "__main__":
    main()