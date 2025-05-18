import asyncio
from pyrogram import Client, filters
from pytgcalls import PyTgCalls
from pytgcalls.types.input_stream import InputAudioStream
from yt_dlp import YoutubeDL
import os

API_ID = YOUR_API_ID          # Replace with your actual Telegram API ID
API_HASH = "YOUR_API_HASH"    # Replace with your API hash
BOT_TOKEN = "YOUR_BOT_TOKEN"  # Replace with your bot token

app = Client("music_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
pytgcalls = PyTgCalls(app)

ydl_opts = {
    'format': 'bestaudio',
    'quiet': True,
    'noplaylist': True,
    'cookiefile': 'cookies.txt'
}

queues = {}

@app.on_message(filters.command("start"))
async def start(_, message):
    await message.reply("✅ I am ready to play music. Use /play <song name or URL>")

@app.on_message(filters.command("play"))
async def play(_, message):
    chat_id = message.chat.id
    if len(message.command) < 2:
        return await message.reply("❌ Song name missing.")
    query = " ".join(message.command[1:])

    msg = await message.reply("🔍 Searching...")

    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(f"ytsearch:{query}", download=False)['entries'][0]
        url = info['url']
        title = info['title']

    audio_stream = InputAudioStream(url)

    if chat_id not in queues:
        await pytgcalls.join_group_call(chat_id, audio_stream)
        queues[chat_id] = [url]
        await msg.edit(f"▶️ Playing: **{title}**")
    else:
        queues[chat_id].append(url)
        await msg.edit(f"➕ Added to queue: **{title}**")

@app.on_message(filters.command("skip"))
async def skip(_, message):
    chat_id = message.chat.id
    if chat_id in queues and len(queues[chat_id]) > 1:
        queues[chat_id].pop(0)
        next_url = queues[chat_id][0]
        await pytgcalls.change_stream(chat_id, InputAudioStream(next_url))
        await message.reply("⏭ Skipped to next song.")
    else:
        await message.reply("❌ No more songs in queue.")

@app.on_message(filters.command("stop"))
async def end(_, message):
    chat_id = message.chat.id
    if chat_id in queues:
        await pytgcalls.leave_group_call(chat_id)
        queues.pop(chat_id)
        await message.reply("⏹ Stopped playback.")
    else:
        await message.reply("⚠️ Nothing is playing.")

@app.on_message(filters.command("pause"))
async def pause(_, message):
    await pytgcalls.pause_stream(message.chat.id)
    await message.reply("⏸ Paused.")

@app.on_message(filters.command("resume"))
async def resume(_, message):
    await pytgcalls.resume_stream(message.chat.id)
    await message.reply("▶️ Resumed.")

@app.on_message(filters.command("help"))
async def help_cmd(_, message):
    await message.reply("""
🎵 **Music Bot Commands:**
/play <song> - Play song by name or link
/skip - Skip to next
/pause - Pause music
/resume - Resume music
/stop - Stop and leave VC
""")

@app.on_message(filters.command("restart"))
async def restart(_, message):
    await message.reply("♻️ Restarting...")
    os.execl(sys.executable, sys.executable, *sys.argv)

# Start everything
pytgcalls.start()
app.run()
