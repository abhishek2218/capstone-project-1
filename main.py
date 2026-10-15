"""
Daily Habit Tracker & Analytics
Person 5: ARMAN - Master Assembly, Routing & QA Testing
"""

import streamlit as st

# PAGE CONFIGURATION
st.set_page_config(page_title="Habit Tracker", layout="wide")

import database
import ui_layout
import analytics
import visuals

# Initialize the database on startup
database.init_db()

# SESSION MANAGEMENT
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_id = None
    st.session_state.username = None

def app_router():
    if not st.session_state.logged_in:
        username, password, login_btn, register_btn = ui_layout.render_login_screen()
        
        if login_btn:
            user_id = database.check_password(username, password)
            if user_id:
                st.session_state.logged_in = True
                st.session_state.user_id = user_id
                st.session_state.username = username
                st.rerun()
            else:
                st.error("Invalid username or password.")
                
        if register_btn:
            try:
                user_id = database.register_user(username, password)
                if user_id:
                    st.success("Account created! Please click Login.")
                else:
                    st.error("Username already exists.")
            except ValueError as e:
                st.error(str(e))
    
    else:
        try:
            ui_layout.render_sidebar()
            
            stats = database.get_user_stats(st.session_state.user_id)
            ui_layout.render_user_profile(
                st.session_state.username, 
                stats["total_xp"], 
                stats["level"]
            )
            
            current_page = st.session_state.get("current_page", "Dashboard")
            
            if current_page == "Dashboard":
                st.title("Daily Check-In")
                user_habits = database.get_habits(st.session_state.user_id)
                
                if not ui_layout.render_empty_state_message(user_habits):
                    for habit in user_habits:
                        col1, col2, col3, col4 = st.columns([3, 2, 2, 2])
                        with col1:
                            st.write(f"**{habit['habit_name']}** ({habit['category']})")
                        with col2:
                            streak = database.get_streak(habit['habit_id'])
                            st.write(f"Streak: {streak}")
                        with col3:
                            prediction = analytics.predict_tomorrow(habit['habit_id'])
                            st.caption(f"Trend: {prediction}")
                        with col4:
                            status = st.selectbox(
                                "Status", 
                                ["Pending", "Completed", "Skipped", "Missed"], 
                                key=f"status_{habit['habit_id']}"
                            )
                            if status != "Pending" and st.button("Save", key=f"btn_{habit['habit_id']}"):
                                earned = database.log_habit_status(habit['habit_id'], status)
                                st.success(f"Logged! Earned {earned} XP.")
                                st.rerun()
                                
            elif current_page == "Manage Habits":
                habit_name, category, submit_btn = ui_layout.render_add_habit_form()
                
                if submit_btn:
                    try:
                        result = database.add_habit(st.session_state.user_id, habit_name, category)
                        if result:
                            st.success(f"Habit '{habit_name}' added!")
                        else:
                            st.error("You already have a habit with this name.")
                    except ValueError as e:
                        st.error(str(e))
                        
            elif current_page == "Achievements":
                st.title("Analytics & Visuals")
                
                all_logs_df = analytics.get_all_user_logs(st.session_state.user_id)
                
                st.subheader("Your Progress Over Time")
                visuals.show_momentum_chart(all_logs_df)
                
                st.markdown("---")
                st.subheader("Category Mastery")
                visuals.show_category_bar_chart(all_logs_df)

        except Exception as e:
            st.error(f"Error details: {e}")
            st.stop()

if __name__ == "__main__":
    app_router()