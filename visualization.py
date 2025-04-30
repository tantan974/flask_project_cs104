import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# Load CSV as DataFrame (returns None on failure)
def load_data(csv_file):
    try:
        return pd.read_csv(csv_file, parse_dates=['Timestamp'])
    except Exception as e:
        print(f"Error loading CSV: {e}")
        return None

# Set dark theme for plots
def set_dark_theme():
    plt.gca().set_facecolor('#18181a')
    plt.gcf().patch.set_facecolor('#18181a')
    plt.tick_params(colors='white')

# Save and close current plot
def save_and_close(path):
    plt.tight_layout()
    plt.savefig(path, facecolor='#18181a')
    plt.close()

# Line plot: events over time
def generate_line_plot(data, output_path):
    plt.figure(figsize=(12, 6))
    data['Timestamp'] = pd.to_datetime(data['Timestamp'], errors='coerce')
    counts = data.groupby('Timestamp').size()
    counts.plot(kind='line', marker='o', color='#ffb347')
    plt.title('Events Over Time', color='white')
    plt.xlabel('Timestamp', color='white')
    plt.ylabel('Number of Events', color='white')
    plt.grid(True, linestyle='--', alpha=0.6)
    set_dark_theme()
    save_and_close(output_path)

# Pie chart: log level distribution
def generate_pie_chart(data, output_path):
    plt.figure(figsize=(7, 7))
    counts = data['Level'].value_counts()
    colors = ['#ffb347', '#ff6961', '#77dd77', '#aec6cf', '#f49ac2']
    counts.plot(kind='pie', autopct='%1.1f%%', startangle=140, colors=colors, shadow=True, textprops={'color':"white"})
    plt.title('Log Level Distribution', color='white')
    plt.gcf().patch.set_facecolor('#18181a')
    save_and_close(output_path)

# Bar chart: event ID distribution
def generate_bar_chart(data, output_path):
    plt.figure(figsize=(10, 6))
    counts = data['Event ID'].value_counts().sort_index()
    colors = ['#ffb347', '#ff6961', '#77dd77', '#aec6cf', '#f49ac2', '#fdfd96']
    counts.plot(kind='bar', color=colors)
    plt.title('Event ID Distribution', color='white')
    plt.xlabel('Event ID', color='white')
    plt.ylabel('Count', color='white')
    plt.grid(axis='y', linestyle='--', alpha=0.6)
    set_dark_theme()
    save_and_close(output_path)

# Stacked bar: log levels by day
def generate_stacked_bar_chart(data, output_path):
    plt.figure(figsize=(12, 7))
    if not np.issubdtype(data['Timestamp'].dtype, np.datetime64):
        data['Timestamp'] = pd.to_datetime(data['Timestamp'], errors='coerce')
    cross_tab = pd.crosstab(data['Timestamp'].dt.date, data['Level'])
    cross_tab.plot(kind='bar', stacked=True, colormap='plasma')
    plt.title('Daily Log Level Counts (Stacked)', color='white')
    plt.xlabel('Date', color='white')
    plt.ylabel('Count', color='white')
    plt.xticks(rotation=45, color='white')
    plt.yticks(color='white')
    set_dark_theme()
    save_and_close(output_path)

# Heatmap: log levels by hour
def generate_heatmap(data, output_path):
    data['Hour'] = pd.to_datetime(data['Timestamp'], errors='coerce').dt.hour
    pivot = pd.pivot_table(data, index='Hour', columns='Level', aggfunc='size', fill_value=0)
    plt.figure(figsize=(10, 6))
    plt.imshow(pivot, aspect='auto', cmap='viridis', interpolation='nearest')
    plt.colorbar(label='Count')
    plt.title('Heatmap of Log Levels by Hour', color='white')
    plt.xlabel('Level', color='white')
    plt.ylabel('Hour of Day', color='white')
    plt.xticks(ticks=range(len(pivot.columns)), labels=pivot.columns, color='white')
    plt.yticks(ticks=range(24), color='white')
    set_dark_theme()
    save_and_close(output_path)

# Histogram: events per hour
def generate_histogram(data, output_path):
    data['Hour'] = pd.to_datetime(data['Timestamp'], errors='coerce').dt.hour
    plt.figure(figsize=(10, 6))
    data['Hour'].dropna().plot(kind='hist', bins=24, color='#ffb347', alpha=0.8)
    plt.title('Histogram of Events per Hour', color='white')
    plt.xlabel('Hour of Day', color='white')
    plt.ylabel('Number of Events', color='white')
    set_dark_theme()
    save_and_close(output_path)

# Scatter plot: Line ID vs Hour
def generate_scatter_plot(data, output_path):
    data['Hour'] = pd.to_datetime(data['Timestamp'], errors='coerce').dt.hour
    plt.figure(figsize=(10, 6))
    plt.scatter(data['Line ID'], data['Hour'], c='#77dd77', alpha=0.8)
    plt.title('Scatter Plot: Line ID vs. Hour', color='white')
    plt.xlabel('Line ID', color='white')
    plt.ylabel('Hour of Day', color='white')
    set_dark_theme()
    save_and_close(output_path)

# Area chart: cumulative events
def generate_area_chart(data, output_path):
    data['Timestamp'] = pd.to_datetime(data['Timestamp'], errors='coerce')
    counts = data.groupby('Timestamp').size().cumsum()
    plt.figure(figsize=(12, 6))
    counts.plot(kind='area', color='#aec6cf', alpha=0.7)
    plt.title('Cumulative Events Over Time', color='white')
    plt.xlabel('Timestamp', color='white')
    plt.ylabel('Cumulative Events', color='white')
    set_dark_theme()
    save_and_close(output_path)

# Generate all plots (if data is present)
def generate_visualizations(csv_file):
    data = load_data(csv_file)
    if data is not None and not data.empty:
        os.makedirs('./static/images', exist_ok=True)
        generate_line_plot(data, './static/images/line_plot.png')
        generate_pie_chart(data, './static/images/pie_chart.png')
        generate_bar_chart(data, './static/images/bar_chart.png')
        generate_stacked_bar_chart(data, './static/images/stacked_bar_chart.png')
        generate_heatmap(data, './static/images/heatmap.png')
        generate_histogram(data, './static/images/histogram.png')
        generate_scatter_plot(data, './static/images/scatter_plot.png')
        generate_area_chart(data, './static/images/area_chart.png')
    else:
        print("No data to plot.")

if __name__ == '__main__':
    generate_visualizations('./structured_data.csv')
