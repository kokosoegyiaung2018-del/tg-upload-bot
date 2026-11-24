import os
import io
import zipfile
import telebot
from github import Github, Auth

BOT_TOKEN = os.environ.get("BOT_TOKEN") or "9167671951:AAHRQ03bZiOv_pgermbFSlqsBeyLJ3t-RJk"
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN") or "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"
TARGET_REPO = os.environ.get("TARGET_REPO") or "kokosoegyiaung2018-del/my-website"
ADMIN_ID = int(os.environ.get("ADMIN_ID") or "7217813072")

bot = telebot.TeleBot(BOT_TOKEN)
gh = Github(auth=Auth.Token(GITHUB_TOKEN))
repo = gh.get_repo(TARGET_REPO)

user_target_folder = {}

ALLOWED_EXTENSIONS = (
    ".html", ".htm", ".css", ".js", ".json",
    ".svg", ".png", ".jpg", ".jpeg", ".webp", ".zip"
)

GUIDE_TEXT = (
    "📖 <b>GitHub Upload Bot လမ်းညွှန်</b>\n\n"
    "<b>၁. စာသားနဲ့ ဖိုင်အသစ်ဆောက် / ပြင်ရန်</b>\n"
    "<code>/save index.html\n&lt;h1&gt;Hello&lt;/h1&gt;</code>\n"
    "• <code>/newfile</code> ဟုလည်း သုံးနိုင်သည်။\n"
    "• ဖိုင်မရှိသေးရင် အသစ်ဆောက်ပြီး ရှိပြီးသားဆို Update လုပ်ပေးသည်။\n\n"
    "<b>၂. Folder ပြောင်းရန်</b>\n"
    "• <code>/folder pages</code> — နောက်တင်မယ့် ဖိုင်များကို <code>pages/</code> ထဲ ထည့်မည်။\n"
    "• <code>/folder root</code> — Root folder သို့ ပြန်ထားမည်။\n\n"
    "<b>၃. ဖိုင်စာရင်း ကြည့်ရန်</b>\n"
    "• <code>/files</code> — လက်ရှိ folder / root ထဲက ဖိုင်စာရင်း\n"
    "• <code>/files pages</code> — သတ်မှတ် folder ထဲက ဖိုင်စာရင်း\n"
    "• <code>/files all</code> — Repo ထဲက ဖိုင်အားလုံး\n\n"
    "<b>၄. ဖိုင် (Document / ZIP) တိုက်ရိုက်တင်ရန်</b>\n"
    "• <code>.html</code>, <code>.css</code>, <code>.js</code>, <code>.json</code>, ပုံဖိုင် သို့မဟုတ် <code>.zip</code> ဖိုင်များကို Bot ဆီ တိုက်ရိုက် ပို့နိုင်သည်။\n\n"
    "<b>၅. လမ်းညွှန်ပြန်ကြည့်ရန်</b>\n"
    "• <code>/help</code> သို့မဟုတ် <code>/guide</code>"
)

def push_file(path_in_repo, content_bytes):
    clean_path = path_in_repo.lstrip("/")
    try:
        existing = repo.get_contents(clean_path)
        repo.update_file(
            existing.path,
            f"Update {clean_path} via Telegram Bot",
            content_bytes,
            existing.sha
        )
    except Exception:
        repo.create_file(
            clean_path,
            f"Upload {clean_path} via Telegram Bot",
            content_bytes
        )

def list_repo_files(target_path="", recursive=False):
    clean_path = target_path.strip("/")
    if recursive:
        branch = repo.get_branch(repo.default_branch)
        tree = repo.get_git_tree(branch.commit.sha, recursive=True).tree
        blobs = [item.path for item in tree if item.type == "blob"]
        if clean_path:
            prefix = clean_path + "/"
            blobs = [p for p in blobs if p.startswith(prefix)]
        return blobs

    contents = repo.get_contents(clean_path) if clean_path else repo.get_contents("")
    if not isinstance(contents, list):
        contents = [contents]

    items = []
    for c in contents:
        if c.type == "dir":
            items.append(f"📁 {c.path}/")
        else:
            items.append(f"📄 {c.path}")
    return items

@bot.message_handler(commands=["start", "help", "guide"])
def cmd_guide(message):
    if message.from_user.id != ADMIN_ID:
        return bot.reply_to(message, "ခွင့်ပြုချက်မရှိပါ။")
    bot.reply_to(message, GUIDE_TEXT, parse_mode="HTML")

@bot.message_handler(commands=["folder"])
def cmd_folder(message):
    if message.from_user.id != ADMIN_ID:
        return
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2 or parts[1].strip().lower() in ("root", "/", "none"):
        user_target_folder[message.chat.id] = ""
        return bot.reply_to(message, "Target folder ကို Root (/) သို့ ပြန်ထားပြီးပါပြီ။")

    folder = parts[1].strip().strip("/") + "/"
    user_target_folder[message.chat.id] = folder
    bot.reply_to(message, f"နောက်တင်မယ့် ဖိုင်များကို <code>{folder}</code> ထဲ ထည့်တင်ပါမည်။", parse_mode="HTML")

@bot.message_handler(commands=["files"])
def cmd_files(message):
    if message.from_user.id != ADMIN_ID:
        return bot.reply_to(message, "ခွင့်ပြုချက်မရှိပါ။")

    parts = message.text.split(maxsplit=1)
    arg = parts[1].strip() if len(parts) > 1 else ""

    recursive = False
    if arg.lower() == "all":
        recursive = True
        target_path = user_target_folder.get(message.chat.id, "")
    elif arg:
        target_path = arg
    else:
        target_path = user_target_folder.get(message.chat.id, "")

    bot.reply_to(message, "GitHub Repo ထဲမှ ဖိုင်စာရင်း ယူနေပါသည်...")

    try:
        items = list_repo_files(target_path=target_path, recursive=recursive)
        if not items:
            loc_label = target_path.strip("/") or "Root (/)"
            return bot.reply_to(message, f"<code>{loc_label}</code> ထဲတွင် ဖိုင်မရှိသေးပါ။", parse_mode="HTML")

        header_loc = target_path.strip("/") or "Root (/)"
        mode_note = " (All files)" if recursive else ""
        header = f"📂 <b>Repo:</b> <code>{TARGET_REPO}</code>\n📍 <b>Path:</b> <code>{header_loc}</code>{mode_note}\n\n"

        chunk = header
        for entry in items:
            line = f"<code>{entry}</code>\n" if recursive else f"{entry}\n"
            if len(chunk) + len(line) > 3900:
                bot.send_message(message.chat.id, chunk, parse_mode="HTML")
                chunk = ""
            chunk += line

        if chunk.strip():
            bot.send_message(message.chat.id, chunk, parse_mode="HTML")

    except Exception as e:
        bot.send_message(message.chat.id, f"Files error: {e}")

@bot.message_handler(commands=["save", "newfile"])
def cmd_save_text_file(message):
    if message.from_user.id != ADMIN_ID:
        return bot.reply_to(message, "ခွင့်ပြုချက်မရှိပါ။")

    lines = message.text.split("\n", 1)
    header_parts = lines[0].split(maxsplit=1)

    if len(header_parts) < 2 or len(lines) < 2 or not lines[1].strip():
        return bot.reply_to(
            message,
            "အသုံးပြုပုံ မှားယွင်းနေပါသည်။\n\n"
            "<code>/save index.html\n&lt;!DOCTYPE html&gt;\n&lt;html&gt;...&lt;/html&gt;</code>",
            parse_mode="HTML"
        )

    raw_filename = header_parts[1].strip()
    code_text = lines[1]

    cleaned_code = code_text.strip()
    if cleaned_code.startswith("```"):
        first_nl = cleaned_code.find("\n")
        if first_nl != -1:
            cleaned_code = cleaned_code[first_nl + 1:]
        if cleaned_code.endswith("```"):
            cleaned_code = cleaned_code[:-3].rstrip()

    prefix = user_target_folder.get(message.chat.id, "")
    final_path = prefix + raw_filename.lstrip("/")

    bot.reply_to(message, f"<code>{final_path}</code> ကို GitHub ထဲ သိမ်းနေပါသည်...", parse_mode="HTML")

    try:
        push_file(final_path, cleaned_code.encode("utf-8"))
        bot.send_message(message.chat.id, f"<code>{final_path}</code> ကို GitHub ထဲ တင်ပြီးပါပြီ။", parse_mode="HTML")
    except Exception as e:
        bot.send_message(message.chat.id, f"Save error: {e}")

@bot.message_handler(content_types=["document"])
def handle_document(message):
    if message.from_user.id != ADMIN_ID:
        return bot.reply_to(message, "ခွင့်ပြုချက်မရှိပါ။")

    file_name = message.document.file_name
    if not file_name.lower().endswith(ALLOWED_EXTENSIONS):
        return bot.reply_to(
            message,
            f"<code>{file_name}</code> ကို ခွင့်မပြုပါ။ HTML, CSS, JS သို့မဟုတ် ZIP ဖိုင်ပို့ပါ။",
            parse_mode="HTML"
        )

    bot.reply_to(message, f"<code>{file_name}</code> ကို GitHub ထဲ တင်နေပါသည်...", parse_mode="HTML")

    file_info = bot.get_file(message.document.file_id)
    file_bytes = bot.download_file(file_info.file_path)
    prefix = user_target_folder.get(message.chat.id, "")

    try:
        if file_name.lower().endswith(".zip"):
            uploaded_count = 0
            with zipfile.ZipFile(io.BytesIO(file_bytes)) as zf:
                for member in zf.namelist():
                    if member.endswith("/") or "__MACOSX" in member:
                        continue
                    push_file(prefix + member, zf.read(member))
                    uploaded_count += 1
            bot.send_message(message.chat.id, f"ZIP ထဲမှ ဖိုင် {uploaded_count} ခုကို GitHub ထဲ တင်ပြီးပါပြီ။")
        else:
            push_file(prefix + file_name, file_bytes)
            bot.send_message(message.chat.id, f"<code>{prefix + file_name}</code> ကို GitHub ထဲ တင်ပြီးပါပြီ။", parse_mode="HTML")
    except Exception as e:
        bot.send_message(message.chat.id, f"Upload error: {e}")

bot.infinity_polling(none_stop=True)
