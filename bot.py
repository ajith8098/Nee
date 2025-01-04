import os
from pyrogram import Client, filters
from pyrogram.errors import ChatAdminRequired, RPCError
from datetime import datetime
import asyncio
from config import BOT_TOKEN, API_ID, API_HASH, CHANNEL_ID, LOGS_CHANNEL_ID, OWNER_ID, BAN_LIST_FILE

# Initialize the bot client
app = Client(
    "autoban_bot",
    bot_token=BOT_TOKEN,
    api_id=API_ID,
    api_hash=API_HASH,
)

# Load or create the ban list
if not os.path.exists(BAN_LIST_FILE):
    with open(BAN_LIST_FILE, "w") as f:
        pass  # Create an empty file

def load_ban_list():
    with open(BAN_LIST_FILE, "r") as f:
        return set(line.strip() for line in f if line.strip())

def save_ban_list(ban_list):
    with open(BAN_LIST_FILE, "w") as f:
        f.write("\n".join(ban_list))

# Load ban list into memory
ban_list = load_ban_list()

# --- Ban Users on Join ---
@app.on_message(filters.chat(CHANNEL_ID) & filters.new_chat_members)
async def autoban(client, message):
    global ban_list
    for member in message.new_chat_members:
        user_id = str(member.id)
        user_name = member.first_name
        join_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        
        if user_id in ban_list:
            try:
                await client.kick_chat_member(CHANNEL_ID, user_id)
                log_message = (
                    f"🚫 **User Banned (Preemptive)**\n"
                    f"**Name:** {user_name}\n"
                    f"**User ID:** `{user_id}`\n"
                    f"**Joined At:** {join_time}\n"
                )
                await client.send_message(LOGS_CHANNEL_ID, log_message)
                print(log_message)
            except ChatAdminRequired:
                error_message = "Bot lacks permissions to ban users!"
                await client.send_message(OWNER_ID, error_message)
                print(error_message)
            except RPCError as e:
                print(f"Error banning user: {e}")

# --- Periodic Member Scan ---
async def periodic_member_scan():
    global ban_list
    while True:
        try:
            # Get list of channel members
            async for member in app.get_chat_members(CHANNEL_ID):
                user_id = str(member.user.id)
                if user_id in ban_list:
                    try:
                        await app.kick_chat_member(CHANNEL_ID, user_id)
                        log_message = (
                            f"🚫 **User Banned (Periodic Check)**\n"
                            f"**User ID:** `{user_id}`\n"
                        )
                        await app.send_message(LOGS_CHANNEL_ID, log_message)
                        print(log_message)
                    except ChatAdminRequired:
                        error_message = "Bot lacks permissions to ban users during periodic scan!"
                        await app.send_message(OWNER_ID, error_message)
                        print(error_message)
                    except RPCError as e:
                        print(f"Error banning user during periodic scan: {e}")
        except Exception as e:
            print(f"Error during periodic scan: {e}")
        
        # Wait 60 seconds before next scan
        await asyncio.sleep(60)

# --- Admin Commands ---
@app.on_message(filters.command(["addban", "removeban", "banlist"]) & filters.user(OWNER_ID))
async def manage_ban_list(client, message):
    global ban_list
    command = message.command
    
    if command[0] == "addban":
        if len(command) == 2:
            user_id = command[1]
            ban_list.add(user_id)
            save_ban_list(ban_list)
            await message.reply(f"✅ User `{user_id}` added to the ban list.")
        else:
            await message.reply("Usage: /addban [user_id]")
    
    elif command[0] == "removeban":
        if len(command) == 2:
            user_id = command[1]
            if user_id in ban_list:
                ban_list.remove(user_id)
                save_ban_list(ban_list)
                await message.reply(f"✅ User `{user_id}` removed from the ban list.")
            else:
                await message.reply(f"❌ User `{user_id}` is not in the ban list.")
        else:
            await message.reply("Usage: /removeban [user_id]")
    
    elif command[0] == "banlist":
        if ban_list:
            ban_list_str = "\n".join(ban_list)
            await message.reply(f"📝 **Ban List:**\n{ban_list_str}")
        else:
            await message.reply("❌ The ban list is currently empty.")

# Start the bot and periodic task
if __name__ == "__main__":
    print("Starting Autoban Bot with Periodic Scan feature...")
    app.start()
    app.loop.create_task(periodic_member_scan())
    app.idle()

