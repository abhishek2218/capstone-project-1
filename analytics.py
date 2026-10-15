"""
Daily Habit Tracker & Analytics
Person 3: Abhishek - Advanced Data Science & Predictions 
"""

import pandas as pd
import database

def get_habit_dataframe(habit_id):
    logs = database.get_habit_logs(habit_id)
    if not logs:
        return pd.DataFrame()
    return pd.DataFrame(logs)

def get_all_user_logs(user_id):
    habits = database.get_habits(user_id)
    all_logs = []
    
    for habit in habits:
        logs = database.get_habit_logs(habit["habit_id"])
        for log in logs:
            log["category"] = habit["category"]
            all_logs.append(log)
            
    if not all_logs:
        return pd.DataFrame()
    return pd.DataFrame(all_logs)

def calculate_completion_rate(habit_id):
    df = get_habit_dataframe(habit_id)
    total_tracked_days = len(df)
    
    if total_tracked_days == 0:
        completion_rate = 0
    else:
        completed_days = len(df[df['status'] == 'Completed'])
        completion_rate = (completed_days / total_tracked_days) * 100
        
    return round(completion_rate, 2)   

def check_mastery_badge(habit_id):
    rate = calculate_completion_rate(habit_id)
    if rate >= 90.0:
        return True
    return False

def predict_tomorrow(habit_id):
    df = get_habit_dataframe(habit_id)
    if len(df) < 3:
        return "Needs more historical data."
    
    recent_7_days = df.head(7)
    total_recent = len(recent_7_days)
    completed_recent = len(recent_7_days[recent_7_days['status'] == 'Completed'])
    
    recent_rate = (completed_recent / total_recent) * 100
    
    if recent_rate > 70:
        return "High probability of completion tomorrow!"
    elif recent_rate < 30:
        return "Focus on this habit - trends are slipping!"
    else:
        return "Moderate probability of completion"