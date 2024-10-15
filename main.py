import random
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackContext, CallbackQueryHandler, Filters

# Global variables
sequence = []
user_attempts = {}
global_leaderboard = {}
group_leaderboards = {}
current_mode = "easy"  #default game mode hai
game_in_progress = False

OWNER_ID = 6663845789 

game_modes = {
    "easy": {"pics": 4, "timer": 3},
    "medium": {"pics": 6, "timer": 4},
    "hard": {"pics": 8, "timer": 4},
}

def get_random_images_from_pinterest(search_query, num_images=5):
    url = f"https://www.pinterest.com/search/pins/?q={search_query}"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    images = []
    for img_tag in soup.find_all('img', limit=num_images):
        img_url = img_tag['src']
        images.append(img_url)
    return images

def start(update: Update, context: CallbackContext) -> None:
    chat_id = update.message.chat_id
    context.bot.send_message(chat_id=chat_id, text="Welcome to the Memory Game bot!")
    show_mode_buttons(update, context)

def help_command(update: Update, context: CallbackContext) -> None:
    chat_id = update.message.chat_id
    help_text = (
        " *Memory Game Bot* \n\n"
        "Commands:\n"
        "/start - Start the bot\n"
        "/leaderboard - Show the leaderboard\n"
        "/mode - Change game mode (Admin only)\n"
        "/game - Start a new game\n"
        "/restart - Restart the current game\n"
        "To win the game, you must guess the correct sequence of images!"
    )
    context.bot.send_message(chat_id=chat_id, text=help_text, parse_mode="Markdown")

def broadcast(update: Update, context: CallbackContext) -> None:
    if update.message.from_user.id != OWNER_ID:
        context.bot.send_message(chat_id=update.message.chat_id, text="You are not authorized to use this command.")
        return

    if len(context.args) < 1:
        context.bot.send_message(chat_id=update.message.chat_id, text="Usage: /broadcast <message>")
        return

    message = " ".join(context.args)
    for chat_id in global_leaderboard.keys():
        context.bot.send_message(chat_id=chat_id, text=message)

def mode(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    chat_id = update.message.chat_id
    user_status = context.bot.get_chat_member(chat_id, user_id).status

    if user_status in ['administrator', 'creator']:
        show_mode_buttons(update, context)
    else:
        context.bot.send_message(chat_id=chat_id, text="Only admins can change the game mode.")

def show_mode_buttons(update: Update, context: CallbackContext) -> None:
    buttons = [
        [InlineKeyboardButton("Easy", callback_data="easy"), InlineKeyboardButton("Medium", callback_data="medium")],
        [InlineKeyboardButton("Hard", callback_data="hard")]
    ]
    reply_markup = InlineKeyboardMarkup(buttons)
    context.bot.send_message(chat_id=update.message.chat_id, text="Select a game mode:", reply_markup=reply_markup)

def mode_callback(update: Update, context: CallbackContext) -> None:
    global current_mode
    query = update.callback_query
    current_mode = query.data
    query.answer(f"Selected mode: {current_mode.capitalize()}")
    query.message.edit_text(f"Game mode changed to {current_mode.capitalize()}.")

def game(update: Update, context: CallbackContext) -> None:
    global game_in_progress
    if game_in_progress:
        context.bot.send_message(chat_id=update.message.chat_id, text="A game is already in progress!")
    else:
        start_game(update, context)

def start_game(update: Update, context: CallbackContext) -> None:
    global game_in_progress, sequence
    game_in_progress = True

    num_pics = game_modes[current_mode]["pics"]
    sequence = get_random_images_from_pinterest("nature", num_pics)
    
    context.bot.send_message(chat_id=update.message.chat_id, text=f"Starting a new game in {current_mode} mode!")
    
    for img in sequence:
        context.bot.send_photo(chat_id=update.message.chat_id, photo=img)

    context.job_queue.run_once(show_sequence, game_modes[current_mode]["timer"], context=update.message.chat_id)

def show_sequence(context: CallbackContext) -> None:
    context.bot.send_message(chat_id=context.job.context, text="Time's up! Now send the correct sequence of image numbers (e.g., 1 3 2 4).")

def restart_game(update: Update, context: CallbackContext) -> None:
    global game_in_progress, sequence
    chat_id = update.message.chat_id

    if game_in_progress:
        game_in_progress = False
        sequence = []
        context.bot.send_message(chat_id=chat_id, text="Game has been restarted! You can start a new game using /game.")
    else:
        context.bot.send_message(chat_id=chat_id, text="No game is currently in progress. Start a new game with /game.")

def main():
    updater = Updater("7814682859:AAESP76mUBBLgjBkJNCKQNZpZXHjysoHs2g", use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help_command))
    dp.add_handler(CommandHandler("broadcast", broadcast, Filters.user(user_id=OWNER_ID)))
    dp.add_handler(CommandHandler("mode", mode))
    dp.add_handler(CommandHandler("game", game))
    dp.add_handler(CommandHandler("restart", restart_game))
    dp.add_handler(CallbackQueryHandler(mode_callback))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
