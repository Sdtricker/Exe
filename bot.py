import os
import zipfile
import rarfile
import py7zr
import pandas as pd
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from telegram.error import Forbidden
from PyPDF2 import PdfReader
from io import BytesIO

# Replace with your actual BOT_TOKEN and CHANNEL_ID
BOT_TOKEN = '7930776122:AAGtn0YUQ0cDlvudPRrYUGxKBKJkG1IuMlw'
CHANNEL_ID = '@yyyaoqkka'

# Initialize the Application object
app = Application.builder().token(BOT_TOKEN).build()

# File Extraction Function
def extract_file(file_path):
    extracted_text = []

    if file_path.endswith(".zip"):
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            zip_ref.extractall("extracted")
            for file_name in zip_ref.namelist():
                extracted_text.extend(extract_text_from_file(f"extracted/{file_name}"))
    
    elif file_path.endswith(".rar"):
        with rarfile.RarFile(file_path) as rar_ref:
            rar_ref.extractall("extracted")
            for file_name in rar_ref.namelist():
                extracted_text.extend(extract_text_from_file(f"extracted/{file_name}"))
    
    elif file_path.endswith(".7z"):
        with py7zr.SevenZipFile(file_path, mode='r') as archive:
            archive.extractall(path="extracted")
            for file_name in os.listdir("extracted"):
                extracted_text.extend(extract_text_from_file(f"extracted/{file_name}"))
    
    elif file_path.endswith(".txt"):
        extracted_text.extend(extract_text_from_file(file_path))
    
    elif file_path.endswith(".pdf"):
        extracted_text.extend(extract_text_from_pdf(file_path))
    
    elif file_path.endswith(".xlsx"):
        extracted_text.extend(extract_text_from_xlsx(file_path))
    
    return extracted_text

# Helper functions for extracting text from files

def extract_text_from_file(file_path):
    text = []
    try:
        if file_path.endswith('.txt'):
            with open(file_path, 'r', encoding='utf-8') as f:
                text.append(f.read())
        elif file_path.endswith('.xlsx'):
            df = pd.read_excel(file_path)
            text.append(df.to_string())
    except Exception as e:
        print(f"Error extracting from {file_path}: {e}")
    return text

def extract_text_from_pdf(file_path):
    text = []
    try:
        reader = PdfReader(file_path)
        for page in reader.pages:
            text.append(page.extract_text())
    except Exception as e:
        print(f"Error extracting from PDF {file_path}: {e}")
    return text

# Function to send extracted text in chunks
async def send_text_in_chunks(text, update):
    chunks = [text[i:i + 300] for i in range(0, len(text), 300)]
    for chunk in chunks:
        try:
            await app.bot.send_message(CHANNEL_ID, chunk)
        except Forbidden:
            print(f"Bot was blocked by user {update.message.chat_id}")
            break

# Command to start the bot
async def start(update: Update, context):
    await update.message.reply_text("Please send a file (zip, rar, 7z, txt, pdf, xlsx). I will extract and send its contents.")

# Handler to process the file
async def handle_file(update: Update, context):
    file = update.message.document
    file_path = f"./{file.file_name}"
    
    # Download the file
    file_info = await app.bot.get_file(file.file_id)
    await file_info.download_to_drive(file_path)

    extracted_text = extract_file(file_path)

    # Send extracted text in chunks
    for text_chunk in extracted_text:
        await send_text_in_chunks(text_chunk, update)

    # Clean up by deleting the file
    os.remove(file_path)

# Main function to add handlers and start the bot
def main():
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_file))

    # Run the bot
    app.run_polling()

if __name__ == '__main__':
    main()
                
