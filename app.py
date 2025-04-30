from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file
from visualization import generate_visualizations, load_data
import csv
import subprocess
import os
import time
import traceback

app = Flask(__name__)
app.secret_key = 'ILOVEANNEHATHAWAY'

UPLOADS_DIR = './uploads'
CSV_FILE = './structured_data.csv'

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        if 'file' not in request.files or request.files['file'].filename == '':
            flash('No file selected.', 'error')
            return redirect(url_for('upload'))
        uploaded_file = request.files['file']
        if not uploaded_file.filename.endswith('.log'):
            flash('Invalid file type. Please upload a .log file.', 'error')
            return redirect(url_for('upload'))
        os.makedirs(UPLOADS_DIR, exist_ok=True)
        filepath = os.path.join(UPLOADS_DIR, uploaded_file.filename)
        uploaded_file.save(filepath)
        filter_level = request.form.get('filter_level', '')
        filter_event = request.form.get('filter_event', '')
        sort_field = request.form.get('sort_field', 'line')
        sort_order = request.form.get('sort_order', 'asc')
        if sort_field not in ('line', 'event'):
            sort_field = 'line'
        progress_id = f"{os.getpid()}_{int(time.time() * 1e6)}"
        progress_file = f"/tmp/progress_{progress_id}.txt"
        cmd_args = ['bash', './scripts/process_logs.sh']
        if filter_level:
            cmd_args += ['-l', filter_level]
        if filter_event:
            cmd_args += ['-e', filter_event]
        cmd_args += ['-s', sort_field, '-o', sort_order]
        cmd_args += [filepath, progress_file]
        subprocess.Popen(cmd_args)
        query = f"?sort={sort_field}&order={sort_order}&level={filter_level}&event={filter_event}"
        redirect_url = url_for('display') + query
        return render_template(
            'processing.html',
            progress_id=progress_id,
            redirect_url=redirect_url
        )
    return render_template('upload.html')

@app.route('/progress/<progress_id>')
def progress(progress_id):
    progress_file = f"/tmp/progress_{progress_id}.txt"
    try:
        with open(progress_file, 'r') as f:
            content = f.read().strip()
            if '|' in content:
                progress, error = content.split('|', 1)
            else:
                progress, error = content, ''
    except FileNotFoundError:
        progress, error = "0/1", ""
    return jsonify({'progress': progress, 'error': error})

@app.route('/display')
def display():
    logs = []
    try:
        with open(CSV_FILE, 'r') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                logs.append(row)
    except FileNotFoundError:
        logs = []

    # Read skipped lines
    skipped_lines = ""
    if os.path.exists("skipped_lines.txt"):
        with open("skipped_lines.txt", "r") as f:
            skipped_lines = f.read().strip()

    sort_field = request.args.get('sort', 'line')
    sort_order = request.args.get('order', 'asc')
    level_filter = request.args.get('level', '')
    event_filter = request.args.get('event', '')

    return render_template(
        'display.html',
        logs=logs,
        current_sort=sort_field,
        current_order=sort_order,
        current_level=level_filter,
        current_event=event_filter,
        skipped_lines=skipped_lines
    )

@app.route('/resort', methods=['POST'])
def resort():
    filter_level = request.form.get('filter_level', '')
    filter_event = request.form.get('filter_event', '')
    sort_field = request.form.get('sort_field', 'line')
    sort_order = request.form.get('sort_order', 'asc')
    if sort_field not in ('line', 'event'):
        sort_field = 'line'
    files = sorted(
        [os.path.join(UPLOADS_DIR, f) for f in os.listdir(UPLOADS_DIR)],
        key=os.path.getmtime,
        reverse=True
    )
    if not files:
        flash('No log file found to re-process.', 'error')
        return redirect(url_for('upload'))
    filepath = files[0]
    progress_id = f"{os.getpid()}_{int(time.time() * 1e6)}"
    progress_file = f"/tmp/progress_{progress_id}.txt"
    cmd_args = ['bash', './scripts/process_logs.sh']
    if filter_level:
        cmd_args += ['-l', filter_level]
    if filter_event:
        cmd_args += ['-e', filter_event]
    cmd_args += ['-s', sort_field, '-o', sort_order]
    cmd_args += [filepath, progress_file]
    subprocess.Popen(cmd_args)
    query = f"?sort={sort_field}&order={sort_order}&level={filter_level}&event={filter_event}"
    redirect_url = url_for('display') + query
    return render_template(
        'processing.html',
        progress_id=progress_id,
        redirect_url=redirect_url
    )

@app.route('/download/csv')
def download_csv():
    return send_file(CSV_FILE, as_attachment=True, download_name='structured_data.csv')

@app.route('/graph', methods=['GET', 'POST'])
def graph():
    generate_visualizations(CSV_FILE)
    # For custom code execution
    custom_code = ''
    custom_plot_url = None
    error = None
    if request.method == 'POST':
        custom_code = request.form.get('custom_code', '')
        # Save user plot to a fixed filename
        custom_plot_path = os.path.join('static', 'images', 'custom_plot.png')
        try:
            # Prepare safe exec environment
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
            import pandas as pd
            import numpy as np
            df = load_data(CSV_FILE)
            # Clear previous plot
            plt.close('all')
            # Provide a globals dict with only safe objects
            safe_globals = {
                '__builtins__': {
                    'abs': abs, 'min': min, 'max': max, 'len': len, 'range': range, 'sum': sum, 'float': float, 'int': int, 'str': str, 'print': print
                },
                'df': df,
                'plt': plt,
                'pd': pd,
                'np': np
            }
            exec(custom_code, safe_globals)
            plt.tight_layout()
            plt.savefig(custom_plot_path, facecolor='#18181a')
            plt.close()
            custom_plot_url = '/static/images/custom_plot.png'
        except Exception as e:
            error = traceback.format_exc()
    return render_template(
        'graph.html',
        line_plot_url="/static/images/line_plot.png",
        pie_chart_url="/static/images/pie_chart.png",
        bar_chart_url="/static/images/bar_chart.png",
        stacked_bar_url="/static/images/stacked_bar_chart.png",
        heatmap_url="/static/images/heatmap.png",
        histogram_url="/static/images/histogram.png",
        scatter_plot_url="/static/images/scatter_plot.png",
        area_chart_url="/static/images/area_chart.png",
        custom_code=custom_code,
        custom_plot_url=custom_plot_url,
        error=error
    )

@app.route('/download/image/<img>')
def download_image(img):
    img_path = os.path.join('static', 'images', img)
    if os.path.exists(img_path):
        return send_file(img_path, as_attachment=True)
    else:
        flash('Image not found.', 'error')
        return redirect(url_for('graph'))

@app.route('/')
def home():
    return render_template('home.html')

if __name__ == '__main__':
    app.run(debug=True)
