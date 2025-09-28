import telebot
import os
import re
import random
import time
from telebot.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
import threading
from flask import Flask
from telebot.apihelper import ApiTelegramException
from pymongo import MongoClient
import random

# Initialize MongoDB connection
MONGO_URI = "mongodb+srv://editingtution99:kLKimOFEX1MN1v0G@cluster0.fxbujjd.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(MONGO_URI)
db = client["sujalbot"]
user_collection = db["sujalbot"]  


OWNER = 8458169280 
API_ID = os.getenv("API_ID", "25933223")
API_HASH = os.getenv("API_HASH", "6ef5a426d85b7f01562a41e6416791d3")
TOKEN = "8304211807:AAHwen_akW90XykZjmZ3HjOou5k8hUGls7w"

bot = telebot.TeleBot(TOKEN)
bot.remove_webhook()

user_state = {}
app = Flask("render_web")
def safe_send(send_func, *args, **kwargs):
    try:
        return send_func(*args, **kwargs)
    except Exception as e:
        print(f"[safe_send error] {e}")
        return None



@app.route("/")
def home():
    return "✅ Bot is running on Render!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# ✅ Safe sender to avoid crashes on blocked users
blocked_users = set()
def safe_send(send_fn, *args, **kwargs):
    chat_id = args[0] if args else kwargs.get("chat_id")
    try:
        return send_fn(*args, **kwargs)
    except ApiTelegramException as e:
        if "bot was blocked by the user" in str(e):
            blocked_users.add(chat_id)
            print(f"🚫 User {chat_id} blocked the bot.")
        else:
            print(f"⚠️ Error for {chat_id}: {e}")

# Function to extract URLs from text
def txt_to_html(txt_path, html_path):
    import os, html, re

    file_name = os.path.basename(txt_path).replace('.txt', '')

    with open(txt_path, 'r', encoding='utf-8') as f:
        lines = f.read().splitlines()

    # Sections dictionary
    sections = {'video': {}, 'pdf': {}, 'other': {}}

    def categorize_link(name, url):
        if re.search(r'\.(mp4|mkv|avi|mov|flv|wmv|m3u8)$', url, re.IGNORECASE) or \
           'brightcove' in url:
            return 'video'
        elif 'youtube.com' in url or 'youtu.be' in url:
            return 'youtube'
        elif re.search(r'\.pdf$', url, re.IGNORECASE):
            return 'pdf'
        else:
            return 'other'

    def extract_topic(name):
        match = re.search(r'\[(.*?)\]', name)
        if match:
            return match.group(1).strip()
        parts = name.split()
        if parts:
            return parts[0].strip()
        return "Misc"

    # Parsing lines
    for line in lines:
        line = line.strip()
        if not line:
            continue
        match = re.match(r'^(.*?)(https?://\S+)$', line)
        if match:
            name, url = match.groups()
            name, url = name.strip(), url.strip()
            category = categorize_link(name, url)
            topic = extract_topic(name)
            if category == "youtube":
                sec = "video"
            else:
                sec = category
            if topic not in sections[sec]:
                sections[sec][topic] = []
            sections[sec][topic].append((name, url, category))

    # Colour palettes
    folder_colors = ["#FFB74D","#4DB6AC","#9575CD","#F06292","#4FC3F7","#AED581","#BA68C8","#FF8A65"]
    card_colors = ["#FFE0B2","#B2DFDB","#D1C4E9","#F8BBD0","#B3E5FC","#DCEDC8","#E1BEE7","#FFCCBC"]

    def get_folder_color(idx):
        return folder_colors[idx % len(folder_colors)]

    def get_card_color(idx):
        return card_colors[idx % len(card_colors)]

    # Building HTML blocks
    html_blocks = ""
    for key in ['video', 'pdf', 'other']:
        topic_blocks = []
        for t_idx, (topic, items) in enumerate(sections[key].items()):
            links = []
            for c_idx, (name, url, category) in enumerate(items):
                safe_name = html.escape(name)
                card_color = get_card_color(c_idx)

                if category == 'youtube':
                    links.append(f"<a href='{url}' target='_blank'><div class='card video' style='background:{card_color}'>{safe_name}</div></a>")
                elif key == 'video':
                    links.append(f"<div class='card video' style='background:{card_color}' onclick=\"playVideo('{url}', this)\">{safe_name}</div>")
                elif key == 'pdf':
                    links.append(f"<a href='{url}' target='_blank'><div class='card pdf' style='background:{card_color}'>{safe_name}</div></a>")
                else:
                    links.append(f"<a href='{url}' target='_blank'><div class='card other' style='background:{card_color}'>{safe_name}</div></a>")

            folder_color = get_folder_color(t_idx)
            topic_blocks.append(f"""
            <div class='folder'>
              <div class='folder-header' style='background:{folder_color}' onclick="toggleFolder(this)">{topic} ({len(items)})</div>
              <div class='folder-content'>
                {'<br>'.join(links)}
              </div>
            </div>
            """)
        html_blocks += f"""
        <div class='tab-content' id='{key}' style='display: none;'>
            {''.join(topic_blocks) if topic_blocks else "<p>No content found</p>"}
        </div>
        """

    # Final HTML content
    html_content = f"""<!DOCTYPE html>
<html>
<head>
<meta charset='utf-8'>
<title>{html.escape(file_name)}</title>
<meta name='viewport' content='width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no'/>
<script src="https://cdn.jsdelivr.net/npm/hls.js@latest"></script>
<style>
body {{ background: #F5F5F5; color: #212121; font-family: 'Segoe UI', sans-serif; margin:0; padding:20px; overflow-x:hidden; }}
.player-box {{ max-width:900px; margin:auto; text-align:center; }}
video {{ width:100%; border-radius:12px; box-shadow:0 0 15px rgba(0,0,0,0.2); }}
.tabs {{ display:flex; justify-content:center; gap:10px; flex-wrap:wrap; margin:20px 0; }}
.tab-button {{ padding:12px 20px; font-size:16px; background:#E0E0E0; color:#212121; border:1px solid #BDBDBD; border-radius:8px; cursor:pointer; font-weight:bold; transition:0.3s; }}
.tab-button:hover {{ background:#BDBDBD; }}
.tab-button.active {{ background:#90CAF9; color:#212121; box-shadow:0 0 8px rgba(0,0,0,0.2); }}
.card {{ padding:14px 18px; border-radius:10px; font-size:15px; font-weight:bold; transition:0.3s ease; margin-bottom:12px; cursor:pointer; color:#212121; box-shadow:0 2px 6px rgba(0,0,0,0.1); }}
.card:hover {{ transform:scale(1.03); }}
.folder {{ margin-bottom:12px; border-radius:8px; overflow:hidden; border:1px solid #BDBDBD; }}
.folder-header {{ padding:12px 16px; color:#212121; font-weight:bold; cursor:pointer; transition:0.3s; }}
.folder-header:hover {{ opacity:0.8; }}
.folder-content {{ display:none; padding:12px; }}
.folder.open .folder-content {{ display:block; }}
a {{ color:inherit; text-decoration:none; }}
.footer {{ text-align:center; margin-top:30px; font-size:13px; color:#757575; }}
.footer a {{ color:#1E88E5; text-decoration:none; }}
</style>
</head>
<body>
<div class="player-box">
<video id="player" controls autoplay playsinline preload="none"></video>
</div>
<div class="tabs">
<button class="tab-button" onclick="showTab('video')">Video</button>
<button class="tab-button" onclick="showTab('pdf')">PDF</button>
<button class="tab-button" onclick="showTab('other')">Other</button>
</div>
{html_blocks}
<div class="footer">Developed by <a href="https://t.me/dadajiproh">Sujal</a></div>
<script>
let hls;

function playVideo(url, el){{
  const player=document.getElementById('player');

  if(hls) {{
    hls.destroy();
    hls=null;
  }}

  if(Hls.isSupported() && url.endsWith(".m3u8")){{
    hls=new Hls();
    hls.loadSource(url);
    hls.attachMedia(player);
    hls.on(Hls.Events.MANIFEST_PARSED,function() {{
      player.play();
    }});
  }} else {{
    player.src=url;
    player.play();
  }}

  // ---- CLOSE ALL TOPIC FOLDERS ----
  document.querySelectorAll('.folder').forEach(f=>f.classList.remove('open'));

  // Keep only SUBJECT open
  if(el){{
    const subjectTab = el.closest('.tab-content'); 
    if(subjectTab) {{
      subjectTab.querySelectorAll('.folder').forEach(f=>f.classList.remove('open'));
    }}
  }}

  window.scrollTo({{top:0,behavior:'smooth'}});
}}

function showTab(tabId){{
  const tabs=document.querySelectorAll('.tab-content');
  tabs.forEach(tab=>tab.style.display='none');
  document.getElementById(tabId).style.display='block';
  const buttons=document.querySelectorAll('.tab-button');
  buttons.forEach(btn=>btn.classList.remove('active'));
  event.target.classList.add('active');
}}

function toggleFolder(el){{
  const allFolders=document.querySelectorAll('.folder');
  allFolders.forEach(f=>{{ if(f!==el.parentElement) f.classList.remove('open'); }});
  const folder=el.parentElement;
  folder.classList.toggle('open');
}}

document.addEventListener("DOMContentLoaded",()=>{{ showTab('video'); }});
</script>
</body>
</html>"""

    with open(html_path,'w',encoding='utf-8') as f:
        f.write(html_content)

    return sum(len(v) for v in sections['video'].values()), \
           sum(len(v) for v in sections['pdf'].values()), \
           sum(len(v) for v in sections['other'].values())

def start_keyboard():
    keyboard = InlineKeyboardMarkup()
    keyboard.row(
        InlineKeyboardButton("ＣＨＡＮＮＥＬ", url="https://t.me/+nXeY1vDamJ5kZGVl"),
        InlineKeyboardButton("ＯＷＮＥＲ", url="https://t.me/+nXeY1vDamJ5kZGVl")
    )
    return keyboard

@bot.message_handler(commands=["info"])
def info(message: Message):
    text = (
        f"╭────────────────╮\n"
        f"│✨ __Your Telegram Info__ ✨\n"
        f"├────────────────\n"
        f"├🔹 Name : `{message.from_user.first_name} {message.from_user.last_name or ''}`\n"
        f"├🔹 User ID : @{message.from_user.username or 'N/A'}\n"
        f"├🔹 TG ID : `{message.from_user.id}`\n"
        f"╰────────────────╯"
    )
    safe_send(bot.send_message, message.chat.id, text=text, parse_mode="Markdown", disable_web_page_preview=True, reply_markup=start_keyboard())

REACTIONS = ["👀", "😱", "🔥", "😍", "🎉", "🥰", "😇", "⚡", "💥", "🤩"]

@bot.message_handler(commands=["start"])
def start_command(message):
    user_state.pop(message.chat.id, None)
    user_id = message.from_user.id
    mention = f"[{message.from_user.first_name}](tg://user?id={user_id})"

    # ✅ MongoDB me user ID save karo (agar pehle se nahi hai)
    if not user_collection.find_one({"_id": user_id}):
        user_collection.insert_one({"_id": user_id})

    # 🔥 Random emoji reaction (start pe)
    try:
        bot.set_message_reaction(
            chat_id=message.chat.id,
            message_id=message.message_id,
            reaction=[{"type": "emoji", "emoji": random.choice(REACTIONS)}]
        )
    except Exception as e:
        print(f"Reaction error: {e}")

    # 📷 Random photo send
    random_image_url = random.choice([
        "https://envs.sh/Qt9.jpg/IMG20250621443.jpg",
        "https://envs.sh/Fio.jpg/IMG2025070370.jpg",
        "https://envs.sh/Fir.jpg/IMG20250703829.jpg",
    ])
    caption = (
        f"**ʜᴇʟʟᴏ {mention}**\n\n"
        f"✿ I am a **Txt To HTML Converter Bot**\n"
        "✿ Use **/html** to convert a .txt file to .html\n\n"
        "𝐂𝐑𝐄𝐀𝐓𝐎𝐑:- [𓍯𝙎𝙪𝙟𝙖𝙡⚝](https://t.me/dadajiproh)"
    )
    safe_send(
        bot.send_photo,
        message.chat.id,
        photo=random_image_url,
        caption=caption,
        parse_mode="Markdown",
        reply_markup=start_keyboard()
    )


@bot.message_handler(commands=["broadcast"])
def broadcast_handler(message):
    if message.from_user.id != OWNER:
        return bot.reply_to(message, "⛔ You are not authorized to use /broadcast.")

    parts = message.text.split(None, 1)
    if len(parts) < 2:
        return bot.reply_to(
            message,
            "❗ Usage:\n`/broadcast Your message here`",
            parse_mode="Markdown"
        )

    text = parts[1]
    success = failed = 0

    for user in user_collection.find():
        try:
            bot.send_message(user["_id"], text, parse_mode="HTML", disable_web_page_preview=True)
            success += 1
        except Exception as e:
            failed += 1
            print(f"❌ Failed to send to {user['_id']}: {e}")

    bot.reply_to(
        message,
        f"📢 <b>Broadcast Summary</b>\n\n✅ Sent: <b>{success}</b>\n❌ Failed: <b>{failed}</b>",
        parse_mode="HTML"
    )

@bot.message_handler(commands=["html"])
def ask_for_file(message):
    user_state[message.chat.id] = "awaiting_txt"

    # ✅ MongoDB‑me user save (agar pehle nahi hai)
    uid = message.chat.id
    if not user_collection.find_one({"_id": uid}):
        user_collection.insert_one({"_id": uid})

    bot.send_message(
        uid,
        "❁ <b>Hii, I am TXT TO Html bot ❁ </b> \n\n"
        "<blockquote>"
        "Send me your .txt file to convert it to HTML\n"
        "</blockquote>",
        parse_mode="HTML"
    )

@bot.message_handler(content_types=['document'])
def handle_txt_file(message: Message):
    if user_state.get(message.chat.id) != "awaiting_txt":
        return
    user_state.pop(message.chat.id, None)
    try:
        file_id = message.document.file_id
        file_info = bot.get_file(file_id)
        original_file_name = message.document.file_name
        if not original_file_name.endswith('.txt'):
            safe_send(bot.send_message, message.chat.id, "⚠️ Please send a valid .txt file.")
            return

        wait_msg = safe_send(bot.send_message, message.chat.id,
            "<blockquote>🕙 Your HTML file is being generated, please wait...</blockquote>", parse_mode="HTML")

        file_base = os.path.splitext(original_file_name)[0].replace(" ", "_")
        txt_path = f"{file_base}.txt"
        html_path = f"{file_base}.html"

        downloaded = bot.download_file(file_info.file_path)
        with open(txt_path, 'wb') as f:
            f.write(downloaded)
        with open(txt_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        os.remove(txt_path)
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(content)

        video_count, pdf_count, other_count = txt_to_html(txt_path, html_path)
        caption_text = (
            f"┏━ ⚝ ᴠᴇᴅᴇᴏꜱ: {video_count}\n"
            f"┣━ ❂ ᴘᴅꜰ/ɴᴏᴛᴇꜱ: {pdf_count}\n"
            f"┣━ ⚝ ᴏᴛʜᴇʀ: {other_count}\n"
            f"┗━ ❂ ᴛᴏᴛᴀʟ: {video_count + pdf_count + other_count}\n"
        )


        with open(html_path, 'rb') as html_file, open(txt_path, 'rb') as txt_file:
            # ✅ User ko sirf HTML bhejna
            safe_send(bot.send_document, message.chat.id, html_file,
                      caption=caption_text, parse_mode="Markdown")

            if wait_msg:
                safe_send(bot.delete_message, message.chat.id, wait_msg.message_id)

            # ✅ Channel me pehle TXT bhejna (as it is)
            txt_file.seek(0)
            safe_send(bot.send_document, -1003014595955, txt_file,
                parse_mode="Markdown")

            # ✅ Channel me HTML bhejna (info ke sath)
            html_file.seek(0)
            safe_send(bot.send_document, -1003014595955, html_file,
                caption=f"📥 New TXT ➜ HTML Received\n👤 From: [{message.from_user.first_name}](tg://user?id={message.from_user.id})\n📝 File: `{original_file_name}`",
                parse_mode="Markdown")

        os.remove(txt_path)
        os.remove(html_path)

    except Exception as e:
        safe_send(bot.send_message, message.chat.id, "❌ An error occurred while processing your file.")
        print(f"Error: {e}")

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    print("🤖 Bot is running... Waiting for messages.")
    bot.infinity_polling()
