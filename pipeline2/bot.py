import os
import uuid
import shutil
import re
import asyncio
import subprocess
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, ContextTypes, filters
import os

BOT_TOKEN = os.getenv("BOT_TOKEN")
bar_width = 20

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hi! Send me a file and I’ll return a processed ZIP file and compiled PDF.")

async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    document = update.message.document
    if not document:
        await update.message.reply_text("Please send a document file.")
        return

    input_ext = os.path.splitext(document.file_name)[1]
    input_path = f"input_{uuid.uuid4().hex}{input_ext}"
    output_folder = f"output_{uuid.uuid4().hex}"

    telegram_file = await context.bot.get_file(document.file_id)
    await telegram_file.download_to_drive(input_path)

    status_msg = await update.message.reply_text("Starting processing…")
    chat_id = status_msg.chat_id
    msg_id = status_msg.message_id

    in_step5 = False
    total_fragments = None

    try:
        proc = await asyncio.create_subprocess_exec(
            "python", "-u", "main.py", input_path, output_folder,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT
        )

        while True:
            raw = await proc.stdout.readline()
            if not raw:
                break
            line = raw.decode().rstrip()

            m_step = re.match(r"^\[Step\s+(\d+)\]", line)
            if m_step:
                step_num = int(m_step.group(1))
                if step_num == 5:
                    in_step5 = True
                    # Show Step 5 header + empty code‐bar
                    await context.bot.edit_message_text(
                        chat_id=chat_id,
                        message_id=msg_id,
                        text=(
                            "[Step 5] Proofreading LaTeX file with LLM...\n"
                            "Progress: <code>[" + "-" * bar_width + "]</code> 0/?? (0%)"
                        ),
                        parse_mode="HTML"
                    )
                    continue
                else:
                    in_step5 = False
                    await context.bot.edit_message_text(
                        chat_id=chat_id,
                        message_id=msg_id,
                        text=line
                    )
                    continue

            if in_step5:
                m_total = re.search(r"Total fragments:\s*(\d+)", line)
                if m_total:
                    total_fragments = int(m_total.group(1))
                    if total_fragments:
                        empty_code_bar = "<code>[" + "-" * bar_width + "]</code>"
                        await context.bot.edit_message_text(
                            chat_id=chat_id,
                            message_id=msg_id,
                            text=(
                                "Proofreading LaTeX file with LLM...\n"
                                f"Progress: {empty_code_bar} 0/{total_fragments} (0%)"
                            ),
                            parse_mode="HTML"
                        )
                    continue

                m_frag = re.search(r"Correcting fragment\s+(\d+)/(\d+)", line)
                if m_frag and total_fragments:
                    current = int(m_frag.group(1))
                    total = int(m_frag.group(2))
                    done_chars = int((current / total) * bar_width)
                    bar_inside = "#" * done_chars + "-" * (bar_width - done_chars)
                    pct = int((current / total) * 100)
                    code_bar = "<code>[" + bar_inside + "]</code>"
                    await context.bot.edit_message_text(
                        chat_id=chat_id,
                        message_id=msg_id,
                        text=(
                            "Proofreading LaTeX file with LLM...\n"
                            f"Progress: {code_bar} {current}/{total} ({pct}%)"
                        ),
                        parse_mode="HTML"
                    )
                    continue


        await proc.wait()

        zip_name = f"{output_folder}.zip"
        shutil.make_archive(base_name=output_folder, format="zip", root_dir=output_folder)

        with open(zip_name, "rb") as f_zip:
            await update.message.reply_document(document=f_zip)

        tex_path = None
        for root, dirs, files in os.walk(output_folder):
            for fname in files:
                if fname.endswith(".tex"):
                    tex_path = os.path.join(root, fname)
                    break
            if tex_path:
                break

        if tex_path:
            tex_dir = os.path.dirname(tex_path)
            tex_file = os.path.basename(tex_path)
            pdf_name = tex_file.rsplit(".", 1)[0] + ".pdf"
            pdf_path = os.path.join(tex_dir, pdf_name)

            xelatexelog = os.path.join(tex_dir, tex_file.rsplit(".", 1)[0] + "_xelatex.log")
            try:
                with open(xelatexelog, "w", encoding="utf-8", errors="ignore") as logf:
                    subprocess.run(
                        [
                            "xelatex",
                            "-interaction=nonstopmode",
                            "-halt-on-error",
                            tex_file
                        ],
                        cwd=tex_dir,
                        stdout=logf,
                        stderr=subprocess.STDOUT,
                        check=True
                    )
                pdf_name = tex_file.rsplit(".", 1)[0] + ".pdf"
                pdf_path = os.path.join(tex_dir, pdf_name)
                if os.path.isfile(pdf_path):
                    with open(pdf_path, "rb") as f_pdf:
                        await update.message.reply_document(document=f_pdf)
                else:
                    await update.message.reply_text("❗ PDF was not created. Here is the xelatex log:")
                    with open(xelatexelog, "rb") as f_log:
                        await update.message.reply_document(document=f_log, filename=os.path.basename(xelatexelog))

            except subprocess.CalledProcessError:
                await update.message.reply_text("❗ PDF compilation failed. See log:")
                with open(xelatexelog, "rb") as f_log:
                    await update.message.reply_document(document=f_log, filename=os.path.basename(xelatexelog))

        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=msg_id,
            text="✓ Processing complete. ZIP and PDF (if compiled) have been sent."
        )

    except Exception as e:
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=msg_id,
            text=f"⛔ Error during processing:\n{e}"
        )
        return

    finally:
        shutil.rmtree(output_folder, ignore_errors=True)

        try:
            os.remove(f"{output_folder}.zip")
        except:
            pass

        try:
            os.remove(input_path)
        except:
            pass

        if tex_path:
            pdf_path = os.path.join(os.path.dirname(tex_path),
                                     os.path.basename(tex_path).rsplit(".", 1)[0] + ".pdf")
            try:
                os.remove(pdf_path)
            except:
                pass

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_file))
    app.run_polling()

if __name__ == "__main__":
    main()
