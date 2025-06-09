import asyncio
import time
from pyrogram.enums import ChatType
from pyrogram.types import Message
from database.ia_filterdb import check_file, save_file

# Async batch processor
async def save_batch(batch, chat_id, msg):
    tasks = [process_media(media, chat_id, msg) for media in batch]
    await asyncio.gather(*tasks)

# Each file check/save logic
async def process_media(media, chat_id, msg):
    try:
        result = await check_file(media)
        if result == "okda":
            success, status = await save_file(media)
            if success:
                print(f"[✅] Indexed: {media.file_name} - {media.file_id}")
            else:
                print(f"[⚠️] Duplicate Skipped: {media.file_name}")
    except Exception as e:
        print(f"[❌] Error saving file: {e}")

# Main Indexer
async def index_files_to_db(bot, message: Message):
    try:
        chat = message.reply_to_message.forward_from_chat or message.reply_to_message.chat
    except Exception:
        await message.reply_text("Reply to a message from the channel or forward one.")
        return

    if chat.type != ChatType.CHANNEL:
        await message.reply_text("This only works with channels.")
        return

    status_msg = await message.reply_text(f"📂 Started Indexing from **{chat.title}**...")
    success = 0
    skipped = 0
    batch = []
    batch_size = 50  # Customize this

    # Get latest message ID
    try:
        current = 0
        async for _ in bot.get_chat_history(chat.id, limit=1):
            current = _.id
    except Exception as e:
        await status_msg.edit(f"Couldn't fetch latest message ID: `{e}`")
        return

    await status_msg.edit("🔍 Scanning messages...")

    last_log_time = time.time()

    async for msg in bot.iter_messages(chat.id, reverse=True):
        if msg.empty or not msg.media:
            continue

        media = None
        if msg.document:
            media = msg.document
        elif msg.video:
            media = msg.video
        elif msg.audio:
            media = msg.audio

        if not media or not getattr(media, 'file_name', None):
            skipped += 1
            continue

        media.chat_id = chat.id
        media.message_id = msg.id

        batch.append(media)

        if len(batch) >= batch_size:
            await save_batch(batch, chat.id, status_msg)
            success += len(batch)
            batch.clear()

        if time.time() - last_log_time > 3:
            await status_msg.edit(f"⚡ Indexing... ✅ `{success}` | ❌ `{skipped}`")
            last_log_time = time.time()

    # Final remaining files
    if batch:
        await save_batch(batch, chat.id, status_msg)
        success += len(batch)

    await status_msg.edit(
        f"✅ Indexing Finished from **{chat.title}**!\n\nTotal Saved: `{success}`\nSkipped: `{skipped}`"
    )
