import logging
import random
import requests
from telegram import Update, ParseMode
from telegram.ext import Updater, CommandHandler, CallbackContext
from telegram.error import TelegramError, BadRequest

# Global variables
OWNER_ID = 6663845789  # Owner ID
LOG_GROUP_ID = -1002035333875
PINTEREST_API_URL = "https://api.pinterest.com/v1/pins/"  # Example Pinterest API endpoint

leaderboard = {}

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Function to fetch a random Pinterest image
def get_random_pinterest_image():
    try:
        random_id = random.randint(1, 1000)  # Simulate fetching random images
        response = requests.get(f"{PINTEREST_API_URL}{random_id}")
        if response.status_code == 200:
            # Here we assume the response returns an image URL
            return response.json().get('url')
        return None
    except requests.RequestException as e:
        logger.error(f"Failed to fetch Pinterest image: {e}")
        return None

# Function to format user details
def format_user_details(user, chat=None):
    username = f"@{user.username}" if user.username else "No username"
    profile_link = f"[Profile Link](tg://user?id={user.id})"
    name = user.full_name
    user_details = f" *Name*: {name}\n"
    user_details += f" *Username*: {username}\n"
    user_details += f" *User ID*: {user.id}\n"
    user_details += f" *Profile*: {profile_link}\n"

    if chat:
        if chat.type == "private":
            user_details += "💬 *Chat Type*: Private (DM)\n"
        else:
            chat_name = chat.title
            chat_link = f" [Group Link](https://t.me/{chat.username})" if chat.username else "No public link"
            user_details += f" *Group*: {chat_name}\n{chat_link}\n"
    
    return user_details

# Function to log user who started the bot
def log_user_start(update: Update, context: CallbackContext):
    user = update.message.from_user
    chat = update.message.chat

    # Format user details
    user_details = format_user_details(user, chat)
    log_message = f" *Bot Started by:*\n{user_details}"

    # Send log to the log group
    context.bot.send_message(
        chat_id=LOG_GROUP_ID,
        text=log_message,
        parse_mode=ParseMode.MARKDOWN
    )

# Error handler to log exceptions
def error_handler(update: Update, context: CallbackContext) -> None:
    """Log the error and send a friendly message to the log group."""
    logger.error(msg="Exception while handling an update:", exc_info=context.error)
    
    if update and update.message:
        user = update.message.from_user
        chat = update.message.chat
        error_details = format_user_details(user, chat)
        error_message = f" *Error occurred:*\n{error_details}\n\nException: `{context.error}`"
        
        # Send the error log to the log group
        context.bot.send_message(
            chat_id=LOG_GROUP_ID,
            text=error_message,
            parse_mode=ParseMode.MARKDOWN
        )

# Start command
def start(update: Update, context: CallbackContext) -> None:
    chat_id = update.message.chat_id
    context.bot.send_message(chat_id=chat_id, text="Welcome to the Memory Game bot!")
    
    # Log user details when they start the bot
    log_user_start(update, context)

# Help command
def help_command(update: Update, context: CallbackContext) -> None:
    help_text = (
        " *Game Bot*\n\n"
        "Commands:\n"
        "/start - Start the bot\n"
        "/game - Start a new game\n"
        "/mode - Change the game mode\n"
        "/leaderboard - Show the leaderboard\n"
        "/restart - Restart the current game"
    )
    update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)

# Broadcast command (only accessible by the owner)
def broadcast(update: Update, context: CallbackContext) -> None:
    if update.message.from_user.id == OWNER_ID:
        message = " ".join(context.args)
        for chat_id in get_all_users():  # Assuming get_all_users fetches all chat IDs
            context.bot.send_message(chat_id=chat_id, text=message)
    else:
        update.message.reply_text("You don't have permission to use this command.")

# Game start command
def game(update: Update, context: CallbackContext) -> None:
    image_url = get_random_pinterest_image()
    if image_url:
        update.message.reply_photo(photo=image_url, caption="Can you remember the sequence?")
    else:
        update.message.reply_text("Failed to fetch a random Pinterest image. Try again later.")

# Restart game command
def restart(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("Game restarted! Start a new one with /game.")

# Leaderboard command
def leaderboard_command(update: Update, context: CallbackContext) -> None:
    # Sort the leaderboard by score and display the top 10 players
    sorted_leaderboard = sorted(leaderboard.items(), key=lambda x: x[1], reverse=True)[:10]
    if sorted_leaderboard:
        leaderboard_text = " *Top 10 Players:*\n\n"
        for i, (user_id, score) in enumerate(sorted_leaderboard, start=1):
            user = context.bot.get_chat(user_id)
            leaderboard_text += f"{i}. {user.full_name} - {score} points\n"
        update.message.reply_text(leaderboard_text, parse_mode=ParseMode.MARKDOWN)
    else:
        update.message.reply_text("No players in the leaderboard yet.")

# Update the score for a user (dummy function, should be called when the user wins the game)
def update_leaderboard(user_id, score):
    if user_id in leaderboard:
        leaderboard[user_id] += score
    else:
        leaderboard[user_id] = score

# Main function
def main():
    updater = Updater("7814682859:AAESP76mUBBLgjBkJNCKQNZpZXHjysoHs2g", use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help_command))
    dp.add_handler(CommandHandler("broadcast", broadcast))
    dp.add_handler(CommandHandler("game", game))
    dp.add_handler(CommandHandler("restart", restart))
    dp.add_handler(CommandHandler("leaderboard", leaderboard_command))

    # Log all errors
    dp.add_error_handler(error_handler)

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
