"""
Daily Habit Tracker & Analytics
Person 4: SIDDHARTH - Plotly Visualizations & Interactive UI
"""

import streamlit as st
import plotly.express as px
import pandas as pd

def show_momentum_chart(df):
    if df.empty:
        st.warning("Not enough data to render charts yet!")
        return
        
    completed_df = df[df['status'] == 'Completed']
    
    if completed_df.empty:
        st.warning("No completed habits to graph yet. Go check one off!")
        return
        
    daily_totals = completed_df.groupby('log_date').size().reset_index(name='Total Completions')
    
    fig = px.line(
        daily_totals, 
        x='log_date', 
        y='Total Completions',
        title="🔥 Daily Habit Momentum",
        markers=True,
        line_shape="spline"
    )
    st.plotly_chart(fig, use_container_width=True)

def show_category_bar_chart(df):
    if df.empty:
        st.warning("Not enough data to render charts yet!")
        return
        
    category_rates = []
    categories = df['category'].unique()
    
    for cat in categories:
        cat_df = df[df['category'] == cat]
        total_tracked = len(cat_df)
        completed = len(cat_df[cat_df['status'] == 'Completed'])
        
        rate = (completed / total_tracked) * 100 if total_tracked > 0 else 0
        category_rates.append({"Category": cat, "Completion Rate (%)": rate})
        
    cat_summary_df = pd.DataFrame(category_rates)
    
    fig = px.bar(
        cat_summary_df, 
        x='Category', 
        y='Completion Rate (%)',
        title="📊 Completion Rates by Category",
        color='Category',
        color_discrete_map={
            "Health": "#2ecc71", 
            "Work": "#3498db",   
            "Focus": "#9b59b6"   
        }
    )
    st.plotly_chart(fig, use_container_width=True)