import os
import zipfile
import rarfile
import py7zr
import shutil
import tempfile
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from pdfminer.high_level import extract_text
import pandas as pd

BOT_TOKEN = '7930776122:AAGtn0YUQ0cDlvudPRrYUGxKBKJkG1IuMlw'
CHANNEL_ID = '@yyyaoqkka'

# Create a temporary directory for file extraction
def extract_file(file_path):
    temp_dir = tempfile.mkdtemp()

    if file_path.endswith('.zip'):
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
    elif file_path.endswith('.rar'):
        with rarfile.RarFile(file_path, 'r') as rar_ref:
            rar_ref.extractall(temp_dir)
    elif file_path.endswith('.7z'):
        with py7zr.SevenZipFile(file_path, mode='r') as zf:
            zf.extractall(temp_dir)
    elif file_path.endswith('.pdf'):
        # Use pdfminer to extract text from PDFs
        return extract_text(file_path)
    elif file_path.endswith('.txt'):
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    elif file_path.endswith('.xlsx'):
        # Use pandas to read Excel file
        df = pd.read_excel(file_path)
        return df.to_string()

    # If no format matches, return empty content
    return None

# Function to send content in chunks to Telegram
def send_chunks(text, chat_id):
    words = text.split()
    chunk_size = 300
    for i in range(0, len(words), chunk_size):
        chunk = ' '.join(words[i:i + chunk_size])
        # Send to channel
        bot.send_message(chat_id=chat_id, text=chunk)

# Command handler for /start command
def start(update: Update, context):
    update.message.reply_text("Please send a file (zip, rar, 7z, txt, pdf, xlsx). I will extract and send its contents.")

# Handler for file messages
def handle_file(update: Update, context):
    file = update.message.document
    file_id = file.file_id
    file_name = file.file_name
    file_path = f'{file_name}'

    # Download the file
    file = context.bot.get_file(file_id)
    file.download(file_path)

    # Extract file content based on its type
    if file_path.endswith(('.zip', '.rar', '.7z')):
        extracted_text = ""
        extracted_text += extract_file(file_path)
        # Check if there are more files inside
        for root, dirs, files in os.walk(file_path):
            for f in files:
                extracted_text += extract_file(os.path.join(root, f))

        # Send the extracted content to Telegram
        send_chunks(extracted_text, CHANNEL_ID)

        # Clean up
        shutil.rmtree(file_path)
    else:
        # For non-archive files like .txt, .pdf, .xlsx
        extracted_text = extract_file(file_path)
        send_chunks(extracted_text, CHANNEL_ID)

        # Clean up
        os.remove(file_path)

# Main function to set up the bot
def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    global bot
    bot = updater.bot

    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.document, handle_file))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
