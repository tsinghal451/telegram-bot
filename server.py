from flask import Flask, render_template, request, jsonify
import asyncio
import json
from telegram import Bot
from werkzeug.utils import secure_filename
import os

# Allowed file extensions
ALLOWED_EXTENSIONS = {'json'}

# Function to check allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

app = Flask(__name__)

# Configure upload folder
app.config['UPLOAD_FOLDER'] = 'uploads/'

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    # Get bot token and channel username from the form
    bot_token = request.form['bot_token']
    channel_username = request.form['channel_username']

    # Check if the request has the file part
    if 'file' not in request.files:
        return jsonify({'message': 'No file part'}), 400

    file = request.files['file']

    # If no file is selected
    if file.filename == '':
        return jsonify({'message': 'No selected file'}), 400

    # If the file is allowed, process it
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        # Read the JSON data
        with open(file_path, 'r') as f:
            polls = json.load(f)

        # Send the polls to the Telegram channel
        asyncio.run(send_multiple_polls(bot_token, channel_username, polls))

        return jsonify({'message': 'Polls sent successfully!'})

    return jsonify({'message': 'Invalid file format. Please upload a JSON file.'}), 400

async def send_multiple_polls(bot_token, channel_username, polls):
    # Initialize the bot
    bot = Bot(token=bot_token)

    # Loop through each poll
    for poll in polls:
        # Send the anonymous poll
        await bot.send_poll(
            chat_id=channel_username,
            question=poll["question"],
            options=poll["options"],
            is_anonymous=True,  # Keep it anonymous
            type="quiz",  # Quiz type poll
            correct_option_id=poll["correct_option_id"],  # Correct answer
            explanation=poll["explanation"]  # Explanation for wrong answers
        )
        print(f"Poll sent: {poll['question']}")

        # Wait for a specified time before sending the next poll
        await asyncio.sleep(15)  # Adjust the time as needed for voting

if __name__ == '__main__':
    app.run(debug=True)
