from flask import Flask, request, jsonify, send_file, render_template, session
from flask_socketio import SocketIO, emit, join_room, leave_room, disconnect
from flask_cors import CORS
import os
import threading
import time
import random
from datetime import datetime
import qrcode
from PIL import Image, ImageDraw, ImageFont, ImageOps
import gspread
from gspread.utils import rowcol_to_a1
from oauth2client.service_account import ServiceAccountCredentials
from collections import deque
from threading import Lock

app = Flask(__name__)
CORS(app, origins='https://172.104.41.186')
socketio = SocketIO(app, cors_allowed_origins="*")  # Allow CORS for all origins

app.secret_key = 'helloworld'

# Google Sheets Configuration
SCOPE = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
SERVICE_ACCOUNT_FILE = 'service_account.json'  # Path to your service account JSON file

credentials = ServiceAccountCredentials.from_json_keyfile_name(SERVICE_ACCOUNT_FILE, SCOPE)
gc = gspread.authorize(credentials)

# Open the Google Sheet
SHEET_NAME = 'DATA KURSI WORSHIP NIGHT'  # Replace with your Google Sheet name

try:
    sh = gc.open(SHEET_NAME)
    monitoring_ws = sh.worksheet('MONITORING 1')  # Replace with your worksheet name
except Exception as e:
    print(f"Error accessing Google Sheet: {e}")
    exit(1)

# Global variables for caching and batching
sheet_data = []  # List of dictionaries representing each row
ket_index = {}   # Index for quick lookup based on 'KET' column
headers = {}     # Column headers
write_queue = deque()  # Queue for write updates
data_lock = Lock()     # Lock for thread-safe operations

# Function to load sheet data into memory
def load_sheet_data():
    global sheet_data, headers
    with data_lock:
        # Read all values from the sheet
        all_values = monitoring_ws.get_all_values()
        header_row = 3  # Headers are in row 3
        header_values = all_values[header_row - 1]  # Zero-based indexing
        headers.clear()
        for idx, cell_value in enumerate(header_values, start=1):
            if cell_value:
                header_name = cell_value.strip().upper()
                headers[header_name] = idx  # 1-based index

        data_rows = all_values[header_row:]
        sheet_data.clear()
        for row in data_rows:
            record = {}
            for idx, value in enumerate(row):
                if idx < len(header_values):
                    header = header_values[idx].strip().upper()
                    record[header] = value
            sheet_data.append(record)
        index_sheet_data()

# Function to index sheet data based on 'KET' column
def index_sheet_data():
    global sheet_data, ket_index
    ket_index.clear()
    for idx, record in enumerate(sheet_data):
        ket_value = record.get('KET', '').strip()
        if ket_value:
            if ket_value not in ket_index:
                ket_index[ket_value] = []
            ket_index[ket_value].append(idx)  # Store index in sheet_data

# Function to periodically refresh sheet data
def refresh_sheet_data():
    while True:
        load_sheet_data()
        time.sleep(5)  # Refresh every 60 seconds

# Start the sheet data refresh thread
refresh_thread = threading.Thread(target=refresh_sheet_data)
refresh_thread.daemon = True
refresh_thread.start()

# Function to process write queue and perform batch updates
def process_write_queue():
    MAX_BATCH_SIZE = 100  # Adjust based on your needs
    while True:
        batch_updates = []
        with data_lock:
            while write_queue and len(batch_updates) < MAX_BATCH_SIZE:
                update = write_queue.popleft()
                batch_updates.append(update)
        if batch_updates:
            try:
                monitoring_ws.batch_update(batch_updates)
            except Exception as e:
                print(f"Error processing write queue: {e}")
        time.sleep(2)  # Process every 1 second

# Start the write queue processing thread
write_thread = threading.Thread(target=process_write_queue)
write_thread.daemon = True
write_thread.start()

@app.route('/verify-transaction', methods=['POST'])
def verify_transaction():
    data = request.get_json()
    transaction_id = data.get('transaction_id', '').strip()

    if not transaction_id:
        return jsonify({'success': False, 'message': 'No transaction ID provided.'}), 400

    try:
        with data_lock:
            if transaction_id in ket_index:
                indices = ket_index[transaction_id]
                transaction_details = []
                for idx in indices:
                    record = sheet_data[idx]
                    transaction = {}
                    fields_to_include = ['WARNA', 'BARIS', 'NO KURSI', 'NAMA', 'NO HP', 
                                         'PIC', 'GELANG', 'KET']
                    for field in fields_to_include:
                        transaction[field] = record.get(field, '')
                    transaction_details.append(transaction)
                return jsonify({
                    'success': True, 
                    'message': f'Found {len(transaction_details)} transaction(s) with ID {transaction_id}.', 
                    'details': transaction_details
                })
            else:
                return jsonify({'success': False, 'message': 'Transaction ID not found.'}), 404
    except Exception as e:
        print(f"Error verifying transaction: {e}")
        return jsonify({'success': False, 'message': 'An error occurred during verification.'}), 500

@app.route('/give-gelang', methods=['POST'])
def give_gelang():
    data = request.get_json()
    transaction_id = data.get('transaction_id', '').strip()

    if not transaction_id:
        return jsonify({'success': False, 'message': 'No transaction ID provided.'}), 400

    try:
        with data_lock:
            if 'KET' not in headers or 'GELANG' not in headers:
                return jsonify({'success': False, 'message': 'Required columns not found in the sheet.'}), 500

            if transaction_id not in ket_index:
                return jsonify({'success': False, 'message': 'Transaction ID not found.'}), 404

            indices = ket_index[transaction_id]
            batch_updates = []
            updated_count = 0
            for idx in indices:
                record = sheet_data[idx]
                current_gelang = record.get('GELANG', '').strip().upper()
                if current_gelang != 'YES':
                    # Update in-memory data
                    record['GELANG'] = 'Yes'
                    # Prepare batch update
                    row_num = idx + 4  # Data starts from row 4
                    gelang_col_index = headers['GELANG']
                    cell_address = rowcol_to_a1(row_num, gelang_col_index)
                    batch_updates.append({
                        'range': cell_address,
                        'values': [['Yes']]
                    })
                    updated_count += 1
            if not batch_updates:
                return jsonify({'success': False, 'message': 'GELANG is already marked as Yes for all matching transactions.'}), 400

            # Add updates to the write queue
            write_queue.extend(batch_updates)
        return jsonify({
            'success': True,
            'message': f'GELANG has been marked as Yes for {updated_count} transaction(s).'
        }), 200
    except Exception as e:
        print(f"Error giving Gelang: {e}")
        return jsonify({'success': False, 'message': 'An error occurred while updating GELANG.'}), 500

# Rest of your code remains unchanged...

if __name__ == "__main__":
    socketio.run(app, host='0.0.0.0', port=5000, ssl_context=('/etc/ssl/private/selfsigned.crt', '/etc/ssl/private/selfsigned.key'))
