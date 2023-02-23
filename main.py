import os
import telegram
from pymongo import MongoClient
from telegram import Update
from queue import Queue
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, ConversationHandler

# try:
#   client = MongoClient(
#      os.environ.get("mongodb+srv://sanzharik03:skyisthelimit77@sssky.hrkea6e.mongodb.net/?retryWrites=true&w=majority"))
# db = client.get_database('notes')
# notes_collection = db.get_collection('notes_collection')
# note = {"title": "Test Note", "content": "This is a test note."}
# result = notes_collection.insert_one(note)
# print("Note inserted with id:", result.inserted_id)
# except Exception as e:
#   print("Error:", e)
client = MongoClient(
    os.environ.get("mongodb+srv://sanzharik03:skyisthelimit77@sssky.hrkea6e.mongodb.net/?retryWrites=true&w=majority"))
db = client.get_database('notes')
notes_collection = db.get_collection('notes_collection')

TOKEN = "6252010953:AAELtx_Ubdc8m5DAZHVtr7mbmTGZGAPnzUo"
bot = telegram.Bot(TOKEN)

update_queue = Queue()


def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Hi there! I can help you take notes. Type /help and you get list of commands')


def help(update, context: CallbackContext) -> None:
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text="Available commands:\n/add_note - Add a note\n/view_notes - "
                                  "View all notes\n/edit_note - Edit note\n/delete_note - Delete note")


def add_note_command(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("Please enter your note.")
    return "GET_NOTE"


def get_note_text(update: Update, context: CallbackContext) -> None:
    note_text = update.message.text

    note = {"note_text": note_text}
    notes_collection.insert_one(note)

    confirmation_message = "Note added successfully."
    context.bot.send_message(chat_id=update.effective_chat.id, text=confirmation_message)

    return -1


def view_notes_command(update: Update, context: CallbackContext) -> None:
    notes = list(notes_collection.find())
    if len(notes) == 0:
        update.message.reply_text("You haven't added any notes yet.")
    else:
        message = "Here are your notes:\n\n"
        for i, note in enumerate(notes):
            message += f"{i + 1}. {note['note_text']}\n"
        context.bot.send_message(chat_id=update.effective_chat.id, text=message)


def edit_note_command(update: Update, context: CallbackContext) -> None:
    notes = list(notes_collection.find())
    if len(notes) == 0:
        update.message.reply_text("You haven't added any notes yet.")
        return

    message = "Which note would you like to edit? Please enter the number of the note you want to edit.\n\n"
    for i, note in enumerate(notes):
        message += f"{i + 1}. {note['note_text']}\n"
    update.message.reply_text(message)

    return "GET_NOTE_NUMBER"


def get_note_number(update: Update, context: CallbackContext) -> None:
    note_number = int(update.message.text)

    notes = list(notes_collection.find())
    if note_number < 1 or note_number > len(notes):
        update.message.reply_text("Invalid note number.")
        return "GET_NOTE_NUMBER"

    context.user_data["note_number"] = note_number
    update.message.reply_text("Please enter the new note text.")
    return "GET_NOTE_TEXT"


def get_note_text_for_edit(update: Update, context: CallbackContext) -> None:
    new_note_text = update.message.text

    note_number = context.user_data["note_number"]
    notes = list(notes_collection.find())
    note_id = notes[note_number - 1]["_id"]
    notes_collection.update_one({"_id": note_id}, {"$set": {"note_text": new_note_text}})

    confirmation_message = "Note edited successfully."
    context.bot.send_message(chat_id=update.effective_chat.id, text=confirmation_message)

    return -1


def delete_note_command(update: Update, context: CallbackContext) -> None:
    notes = list(notes_collection.find())
    if len(notes) == 0:
        update.message.reply_text("You haven't added any notes yet.")
        return

    message = "Which note would you like to delete? Please enter the number of the note you want to delete.\n\n"
    for i, note in enumerate(notes):
        message += f"{i + 1}. {note['note_text']}\n"
    update.message.reply_text(message)

    return "GET_NOTE_NUMBER_FOR_DELETION"


def get_note_number_for_deletion(update: Update, context: CallbackContext) -> None:
    note_number = int(update.message.text)

    notes = list(notes_collection.find())
    if note_number < 1 or note_number > len(notes):
        update.message.reply_text("Invalid note number.")
        return "GET_NOTE_NUMBER_FOR_DELETION"

    note_id = notes[note_number - 1]["_id"]
    notes_collection.delete_one({"_id": note_id})

    confirmation_message = "Note deleted successfully."
    context.bot.send_message(chat_id=update.effective_chat.id, text=confirmation_message)


def cancel(update: Update, context: CallbackContext) -> None:
    context.user_data.clear()
    update.message.reply_text('Action canceled.')


add_note_conv_handler = ConversationHandler(
    entry_points=[CommandHandler('add_note', add_note_command)],
    states={
        "GET_NOTE": [MessageHandler(Filters.text & ~Filters.command, get_note_text)],
    },
    fallbacks=[CommandHandler('cancel', cancel)]
)

edit_note_conv_handler = ConversationHandler(
    entry_points=[CommandHandler('edit_note', edit_note_command)],
    states={
        "GET_NOTE_NUMBER": [MessageHandler(Filters.text, get_note_number)],
        "GET_NOTE_TEXT": [MessageHandler(Filters.text, get_note_text_for_edit)],
    },
    fallbacks=[CommandHandler('cancel', cancel)],
    allow_reentry=True
)

delete_note_conv_handler = ConversationHandler(
    entry_points=[CommandHandler('delete_note', delete_note_command)],
    states={
        "GET_NOTE_NUMBER_FOR_DELETION": [MessageHandler(Filters.text, get_note_number_for_deletion)]
    },
    fallbacks=[CommandHandler('cancel', cancel)],
    allow_reentry=True
)

updater = Updater(TOKEN, use_context=True)

dispatcher = updater.dispatcher

dispatcher.add_handler(CommandHandler("start", start))

dispatcher.add_handler(add_note_conv_handler)

dispatcher.add_handler(CommandHandler("view_notes", view_notes_command))
dispatcher.add_handler(CommandHandler("help", help))
dispatcher.add_handler(delete_note_conv_handler)
dispatcher.add_handler(edit_note_conv_handler)

updater.start_polling()

updater.idle()
