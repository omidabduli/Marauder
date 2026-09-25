"""
MARAUDER AVAILABILITY MANAGEMENT - 16 WEEK DATABASE
Main server module for the Marauder project.

Written / Maintained by: OA (Omid Abduli)
This script orchestrates the Flask API endpoints, loads/saves CSV data,
configures application parameters, and serves static files.
"""

from flask import Flask, send_file, request, jsonify, redirect
from flask_cors import CORS
import csv
import os
import socket
import webbrowser
from datetime import datetime, timedelta
from pathlib import Path

# Initialize Flask web application
app = Flask(__name__)
# Enable CORS support for local network access
CORS(app)

# Configuration settings
CSV_FILE = 'users.csv'
MAX_WEEKS = 16  # Database limit (current 2 weeks + 14 historical weeks)
HOST = '0.0.0.0' # Listen on all network interfaces
PORT = int(os.environ.get('PORT', 5005))

def get_current_week_id():
    """Returns the current week ID in YYYY-WXX format and the date of Monday"""
    today = datetime.now()
    # Find Monday of current week
    monday = today - timedelta(days=today.weekday())
    # Format: 2025-W46
    week_id = monday.strftime('%Y-W%V')
    return week_id, monday.strftime('%Y-%m-%d')

def get_week_column_name():
    """Generate current week column name"""
    week_id, monday_date = get_current_week_id()
    return f"Week_{week_id}_{monday_date}"

def get_database_stats():
    """Get basic stats about the CSV file"""
    if not os.path.exists(CSV_FILE):
        return {'error': 'Database file not found'}
    
    try:
        with open(CSV_FILE, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            headers = next(reader)
            rows = list(reader)
            
        week_cols = [h for h in headers if h.startswith('Week_')]
        
        return {
            'total_users': len(rows),
            'total_weeks': len(week_cols),
            'weeks': week_cols,
            'max_weeks': MAX_WEEKS
        }
    except Exception as e:
        return {'error': str(e)}

def manage_week_columns():
    """Automatically add new weeks and prune old ones to maintain the 16-week limit"""
    if not os.path.exists(CSV_FILE):
        return

    try:
        # Read current data
        with open(CSV_FILE, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            headers = next(reader)
            rows = list(reader)

        current_week_col = get_week_column_name()
        
        # 1. Add current week if missing
        if current_week_col not in headers:
            headers.append(current_week_col)
            # Add empty values for all rows
            for row in rows:
                row.append('')
            print(f"Added new week column: {current_week_col}")

        # 2. Add next week for foresight
        today = datetime.now()
        next_monday = today + timedelta(days=(7 - today.weekday()))
        next_week_id = next_monday.strftime('%Y-W%V')
        next_week_col = f"Week_{next_week_id}_{next_monday.strftime('%Y-%m-%d')}"
        
        if next_week_col not in headers:
            headers.append(next_week_col)
            for row in rows:
                row.append('')
            print(f"Added future week column: {next_week_col}")

        # 3. Prune old weeks if we exceed MAX_WEEKS
        week_cols = [h for h in headers if h.startswith('Week_')]
        if len(week_cols) > MAX_WEEKS:
            # Columns to keep are ID, Name, and the most recent 16 weeks
            num_to_remove = len(week_cols) - MAX_WEEKS
            cols_to_remove = week_cols[:num_to_remove]
            
            # Find indices to remove
            indices_to_remove = [headers.index(c) for h, c in enumerate(cols_to_remove)]
            
            # Create new headers and rows
            new_headers = [h for i, h in enumerate(headers) if i not in indices_to_remove]
            new_rows = []
            for row in rows:
                new_rows.append([val for i, val in enumerate(row) if i not in indices_to_remove])
            
            headers = new_headers
            rows = new_rows
            print(f"Pruned {num_to_remove} old week(s)")

        # Save updated data
        with open(CSV_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            writer.writerows(rows)

    except Exception as e:
        print(f"Error managing weeks: {e}")

import json

SETTINGS_FILE = 'settings.json'
DEFAULT_SETTINGS = {
    "language": "de",
    "allowPastChanges": True,
    "pastWeeksLimit": 8,
    "futurePeriods": 1,
    "adminPassword": "admin"
}

def load_settings():
    if not os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
                json.dump(DEFAULT_SETTINGS, f, indent=4)
        except Exception as e:
            print(f"Error writing default settings: {e}")
        return DEFAULT_SETTINGS.copy()
    try:
        with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
            settings = json.load(f)
        
        # Auto-populate any missing keys from defaults
        updated = False
        for k, v in DEFAULT_SETTINGS.items():
            if k not in settings:
                settings[k] = v
                updated = True
        
        if updated:
            save_settings(settings)
            
        return settings
    except Exception as e:
        print(f"Error loading settings: {e}")
        return DEFAULT_SETTINGS.copy()

def save_settings(settings):
    try:
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=4)
        return True
    except Exception as e:
        print(f"Error saving settings: {e}")
        return False

# --- ROUTES ---

# Route for getting settings (public, stripped of sensitive data)
@app.route('/api/settings', methods=['GET'])
def get_settings():
    """Get the current settings without sensitive password information"""
    settings = load_settings()
    public_settings = {k: v for k, v in settings.items() if k != 'adminPassword'}
    return jsonify(public_settings)

# Route for admin login authentication
@app.route('/api/admin-login', methods=['POST'])
def admin_login():
    """Verify admin login password"""
    try:
        data = request.get_json()
        if not data or 'password' not in data:
            return jsonify({'error': 'Missing password'}), 400
        
        settings = load_settings()
        saved_password = settings.get('adminPassword', 'admin')
        
        if data['password'] == saved_password:
            return jsonify({'success': True, 'message': 'Authentication successful'})
        else:
            return jsonify({'error': 'Unauthorized', 'message': 'Incorrect password'}), 401
    except Exception as e:
        return jsonify({'error': 'Internal server error', 'message': str(e)}), 500

# Route for saving settings
@app.route('/api/settings', methods=['POST'])
def update_settings():
    """Update settings on the server"""
    try:
        new_settings = request.get_json()
        if not new_settings:
            return jsonify({'error': 'Invalid request format'}), 400
        
        settings = load_settings()
        saved_password = settings.get('adminPassword', 'admin')
        
        # Verify admin password
        password = new_settings.get('password')
        if password != saved_password:
            return jsonify({'error': 'Unauthorized', 'message': 'Incorrect admin password'}), 401
            
        # Update allowed settings keys
        for key in DEFAULT_SETTINGS.keys():
            if key in new_settings and key != 'adminPassword':
                settings[key] = new_settings[key]
        
        # Update password if requested
        new_password = new_settings.get('newPassword')
        if new_password:
            settings['adminPassword'] = new_password
                
        if save_settings(settings):
            return jsonify({
                'success': True,
                'message': 'Settings saved successfully'
            })
        else:
            return jsonify({'error': 'Failed to save settings'}), 500
    except Exception as e:
        return jsonify({'error': 'Internal server error', 'message': str(e)}), 500

# Route for the admin page
@app.route('/admin')
def admin_page():
    """Serve the admin configuration page"""
    try:
        return send_file('admin.html')
    except FileNotFoundError:
        return jsonify({
            'error': 'admin.html not found',
            'message': 'Please ensure admin.html is in the same directory as server.py'
        }), 404

# Route for the main application at /
@app.route('/')
def index():
    """Serve the main interface page"""
    
    # Manage weeks before serving the page
    manage_week_columns()
    
    try:
        return send_file('Interface.html')
    except FileNotFoundError:
        print("ERROR: Interface.html not found in current directory")
        return jsonify({
            'error': 'Interface.html not found',
            'message': 'Please ensure Interface.html is in the same directory as server.py'
        }), 404

# Route for serving CSV file
@app.route('/users.csv')
def users_csv():
    """Serve the CSV data file"""
    try:
        return send_file(CSV_FILE, mimetype='text/csv')
    except FileNotFoundError:
        return jsonify({
            'error': 'users.csv not found',
            'message': 'Please ensure users.csv is in the same directory as server.py'
        }), 404

# API endpoint for saving CSV data
@app.route('/save-csv', methods=['POST'])
def save_csv():
    """Save CSV data with user changes"""
    try:
        # Ensure weeks are managed before saving
        manage_week_columns()
        
        data = request.get_json()
        if not data or 'csvData' not in data:
            return jsonify({'error': 'Invalid data format'}), 400

        csv_data = data['csvData']

        # Write to CSV file
        with open(CSV_FILE, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            for row in csv_data:
                writer.writerow(row)

        db_stats = get_database_stats()
        
        return jsonify({
            'success': True,
            'message': 'CSV data saved successfully',
            'timestamp': datetime.now().isoformat(),
            'database_stats': db_stats
        })

    except Exception as e:
        app.logger.error(f"Error saving CSV: {str(e)}")
        return jsonify({
            'error': 'Failed to save CSV data',
            'message': str(e)
        }), 500

# Health check endpoint
@app.route('/health')
def health_check():
    """Health check endpoint"""
    db_stats = get_database_stats()
    return jsonify({
        'status': 'healthy',
        'service': 'MARAUDER Availability Management',
        'version': '1.2.0',
        'database_stats': db_stats
    })

# API endpoint for loading FAQ from ampel_faq.csv
@app.route('/api/faq', methods=['GET'])
def get_faq():
    """Load FAQ from ampel_faq.csv and return as JSON list"""
    faq_file = 'ampel_faq.csv'
    if not os.path.exists(faq_file):
        return jsonify([])
    try:
        faqs = []
        with open(faq_file, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            # Skip header
            next(reader, None)
            for row in reader:
                if len(row) >= 2:
                    faqs.append({
                        'question': row[0].strip(),
                        'answer': row[1].strip()
                    })
        return jsonify(faqs)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# API endpoint to get current week info and database stats
@app.route('/current-week', methods=['GET'])
def get_current_week_info():
    """Get current week information and database statistics"""
    try:
        week_id, monday_date = get_current_week_id()
        current_week_col = get_week_column_name()
        db_stats = get_database_stats()
        
        return jsonify({
            'success': True,
            'current_week_id': week_id,
            'monday_date': monday_date,
            'column_name': current_week_col,
            'database_stats': db_stats,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'error': 'Failed to get current week info',
            'message': str(e)
        }), 500

# API endpoint to get database statistics
@app.route('/database-stats', methods=['GET'])
def get_database_statistics():
    """Get detailed database statistics"""
    try:
        stats = get_database_stats()
        return jsonify({
            'success': True,
            'statistics': stats,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'error': 'Failed to get database statistics',
            'message': str(e)
        }), 500

@app.errorhandler(404)
def not_found_error(error):
    """Handle 404 errors"""
    return jsonify({
        'error': 'Not Found',
        'message': 'The requested resource was not found on this server.'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({
        'error': 'Internal Server Error',
        'message': 'An internal server error occurred.'
    }), 500

def get_local_ip():
    """Get the local IP address for network access"""
    try:
        # Connect to a remote address to find local IP
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except:
        return "localhost"

def main():
    """Main function to start the Flask server"""
    # Change to the directory containing this script
    script_dir = Path(__file__).parent.absolute()
    os.chdir(script_dir)

    # Check if required files exist
    if not os.path.exists('Interface.html'):
        print("Error: Interface.html not found in current directory!")
        print(f"Current directory: {script_dir}")
        return

    if not os.path.exists('users.csv'):
        print("Warning: users.csv not found. The application may not function properly.")
        print("Please ensure users.csv is in the current directory.")

    try:
        print("=" * 70)
        print("MARAUDER AVAILABILITY MANAGEMENT - 16 WEEK DATABASE")
        print("=" * 70)
        print(f"Local access:   http://localhost:{PORT}/")
        print(f"Network access: http://{get_local_ip()}:{PORT}/")
        print(f"Directory:      {script_dir}")
        print(f"Health check:   http://localhost:{PORT}/health")
        print(f"Week API:       http://localhost:{PORT}/current-week")
        print("-" * 70)
        
        # Show current week info and database stats
        try:
            current_week_col = get_week_column_name()
            week_id, monday_date = get_current_week_id()
            print(f"Current Week:   {week_id} (starts {monday_date})")
            
            # Initialize week management and get stats
            manage_week_columns()
            db_stats = get_database_stats()
            
            print(f"Database:       {db_stats.get('total_users', 0)} users, {db_stats.get('total_weeks', 0)}/{MAX_WEEKS} weeks")
            print(f"Week Management: Active (16 Week Limit)")
            
            # Print Admin password status
            settings = load_settings()
            admin_pwd = settings.get('adminPassword', 'admin')
            if admin_pwd == 'admin':
                print(f"Admin Password: 'admin' (default - change via Admin Panel or settings.json)")
            else:
                print(f"Admin Password: [Customized] (Check/reset in settings.json if forgotten)")
            
            if db_stats.get('weeks'):
                recent_weeks = db_stats['weeks'][-3:]  # Show last 3 weeks
                week_display = [w.replace('Week_', '').replace('2025-', '') for w in recent_weeks]
                print(f"Recent Weeks:   {', '.join(week_display)}")
                
        except Exception as e:
            print(f"Week Management: Error - {e}")
        
        print("-" * 70)
        print("Database Features:")
        print("  • Automatic week creation (Monday-based)")
        print("  • 16 week limit (2 current + 14 historical)")
        print("  • Automatic removal of oldest weeks")
        print("  • Empty status for new weeks")
        print("-" * 70)
        print("Press Ctrl+C to stop the server")
        print("=" * 70)

        # Try to open the browser automatically
        try:
            webbrowser.open(f'http://127.0.0.1:{PORT}/')
        except:
            print("Note: Could not auto-open browser. Please navigate manually.")

        # Start the Flask development server
        app.run(
            host=HOST,
            port=PORT,
            debug=False,
            use_reloader=False
        )

    except KeyboardInterrupt:
        print("\n" + "=" * 70)
        print("Server stopped by user")
        print("=" * 70)
    except OSError as e:
        if e.errno == 98 or 'Address already in use' in str(e):
            print(f"Error: Port {PORT} is already in use!")
            print("Try stopping other processes using this port or use a different port.")
        else:
            print(f"Error starting server: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    main()
