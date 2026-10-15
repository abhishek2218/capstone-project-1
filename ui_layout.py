"""
Daily Habit Tracker & Analytics
Moksh: Frontend Screens & UI Elements
"""

import streamlit as st

def render_login_screen():
    st.title("🎯 Daily Habit Tracker")
    st.subheader("Login to your account")
    
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        
        col1, col2 = st.columns(2)
        with col1:
            login_btn = st.form_submit_button("Login")
        with col2:
            register_btn = st.form_submit_button("Register New Account")
            
    return username, password, login_btn, register_btn

def render_sidebar():
    st.sidebar.title("Navigation")
    
    if "current_page" not in st.session_state:
        st.session_state.current_page = "Dashboard"
        
    if st.sidebar.button("🏠 Dashboard", use_container_width=True):
        st.session_state.current_page = "Dashboard"
    if st.sidebar.button("➕ Manage Habits", use_container_width=True):
        st.session_state.current_page = "Manage Habits"
    if st.sidebar.button("🏆 Achievements", use_container_width=True):
        st.session_state.current_page = "Achievements"
        
    st.sidebar.markdown("---")
    if st.sidebar.button("Logout", use_container_width=True):
        st.session_state.clear()
        st.rerun()

def render_user_profile(username, total_xp, level):
    st.sidebar.markdown("---")
    st.sidebar.subheader(f"Player: {username}")
    st.sidebar.write(f"**Level {level}**")
    
    xp_in_current_level = total_xp % 100
    st.sidebar.progress(xp_in_current_level / 100.0, text=f"{xp_in_current_level} / 100 XP")

def render_add_habit_form():
    st.header("➕ Add a New Habit")
    
    with st.form("new_habit_form"):
        habit_name = st.text_input("Habit Name")
        category = st.selectbox("Category", ["Health", "Work", "Focus"]) 
        submit_btn = st.form_submit_button("Save Habit")
        
    return habit_name, category, submit_btn

def render_empty_state_message(user_habits):
    if not user_habits:
        st.info("You haven't added any habits yet! Go to 'Manage Habits' to get started.")
        return True
    return False