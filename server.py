from flask import Flask, render_template, request, jsonify
import asyncio
import json
from telegram import Bot
from werkzeug.utils import secure_filename
import os
from threading import Thread

# Your bot token and channel username will be provided by the user.
ALLOWED_EXTENSIONS = {'json'}
stop_flag = False  # Global flag to control the process
sending_task = None  # Store the current sending task

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads/'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    global stop_flag, sending_task
    stop_flag = False  # Reset stop flag when a new process starts

    bot_token = request.form.get('bot_token')
    channel_username = request.form.get('channel_username')

    if not bot_token or not channel_username:
        return jsonify({'message': 'Bot Token and Channel Username are required!'}), 400

    file = request.files.get('file')
    if not file or file.filename == '':
        return jsonify({'message': 'No file selected or file missing!'}), 400

    if allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        with open(file_path, 'r') as f:
            polls = json.load(f)

        # Run the task in a separate thread to allow real-time control
        sending_task = Thread(target=lambda: asyncio.run(send_multiple_polls(bot_token, channel_username, polls)))
        sending_task.start()

        return jsonify({'message': 'Polls upload started!'})

    return jsonify({'message': 'Invalid file format. Please upload a JSON file.'}), 400

@app.route('/stop', methods=['POST'])
def stop_process():
    global stop_flag
    stop_flag = True  # Set the stop flag to True to stop the process
    return jsonify({'message': 'Poll sending process has been stopped!'})

async def send_multiple_polls(bot_token, channel_username, polls):
    global stop_flag
    bot = Bot(token=bot_token)

    for poll in polls:
        if stop_flag:  # Check if the process should stop
            print("Poll sending stopped by user.")
            break

        await bot.send_poll(
            chat_id=channel_username,
            question=poll["question"],
            options=poll["options"],
            is_anonymous=True,
            type="quiz",
            correct_option_id=poll["correct_option_id"],
            explanation=poll["explanation"]
        )
        print(f"Poll sent: {poll['question']}")
        await asyncio.sleep(15)

if __name__ == '__main__':
    app.run(debug=True)
