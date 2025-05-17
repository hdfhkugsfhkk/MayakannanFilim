from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

FUB_TEXT =

@Client.on_message(filters.command("help"))
async def generate_link(client, message):
    command_text = message.text.split(maxsplit=1)
    if len(command_text) < 2:
        await message.reply("FUB_TEXT")
        return
