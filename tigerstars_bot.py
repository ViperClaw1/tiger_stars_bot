from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
    CallbackQueryHandler
)

TOKEN = '7617600052:AAFm4LqGNv64lsvlknfKqFaumyO1U_9D1H8'

RATE = 1.69

STAR_OPTIONS = {
    100: f"{round(100 * RATE)}₽",
    200: f"{round(200 * RATE)}₽",
    300: f"{round(300 * RATE)}₽",
    500: f"{round(500 * RATE)}₽",
    800: f"{round(800 * RATE)}₽",
    1000: f"{round(1000 * RATE)}₽",
    1500: f"{round(1500 * RATE)}₽",
    3000: f"{round(3000 * RATE)}₽",
    5000: f"{round(5000 * RATE)}₽"
}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await show_stars_options(update, context)


async def show_stars_options(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query:
        await query.answer()

    context.user_data.clear()

    link = "https://tiger-stars.com"

    text = f"""Это TIGER-STARS бот, с помощью которого ты можешь получить Звёзды.
Также вы можете приобрести Звёзды на [нашем сайте]({link}).

Telegram Stars 🌟 по выгодной цене!

Выберите количество звёзд ниже или просто отправьте цифру в чат, чтобы приобрести нужное количество! 
"""

    keyboard = []
    row = []
    for i, (amount, price) in enumerate(STAR_OPTIONS.items()):
        button = InlineKeyboardButton(f"🌟{amount} - {price}", callback_data=f'select_{amount}')
        row.append(button)
        if (i + 1) % 2 == 0:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)

    keyboard.append([InlineKeyboardButton("✏️ Ввести свой вариант", callback_data='custom_amount')])

    keyboard.append([
        InlineKeyboardButton("📢 Отзывы", url='https://t.me/tiger_stars1/20'),
        InlineKeyboardButton("🆘 Помощь", url='https://t.me/Starstiger')
    ])
    keyboard.append([InlineKeyboardButton("📢 TG Канал", url='https://t.me/tiger_stars1')])

    reply_markup = InlineKeyboardMarkup(keyboard)

    if query:
        await query.edit_message_text(
            text,
            reply_markup=reply_markup,
            parse_mode='Markdown',
            disable_web_page_preview=True
        )
    else:
        await update.message.reply_text(
            text,
            reply_markup=reply_markup,
            parse_mode='Markdown',
            disable_web_page_preview=True
        )


async def handle_custom_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    context.user_data['awaiting_custom_amount'] = True
    context.user_data['action'] = 'buy_for_self'  # Default action

    text = "✏️ Введите количество звёзд (от 50 до 5000):"

    keyboard = [
        [InlineKeyboardButton("← Назад", callback_data='show_stars')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    message = await query.edit_message_text(
        text,
        reply_markup=reply_markup
    )

    context.user_data['custom_amount_message_id'] = message.message_id


async def confirm_purchase(update: Update, context: ContextTypes.DEFAULT_TYPE, amount: int):
    query = update.callback_query
    if query:
        await query.answer()

    # Store amount in user_data for later use
    context.user_data['amount'] = amount
    context.user_data['action'] = 'buy_for_self'  # Default action

    nickname = update.effective_user.username or "пользователь"
    cost = round(amount * RATE)

    text = f"Вы собираетесь купить *{amount}* Telegram Stars 🌟 на аккаунт *@{nickname}* за *{cost}₽*"
    link = f"https://tiger-stars.com?amount={amount}&username={nickname}"

    keyboard = [
        [InlineKeyboardButton("💳 Оплатить", url=link)],
        [InlineKeyboardButton("📤 Отправить другому пользователю", callback_data='send_to_other')],
        [InlineKeyboardButton("← Назад", callback_data='show_stars')]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    if query:
        await query.edit_message_text(
            text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )


async def ask_for_username(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    context.user_data['action'] = 'buy_for_other'
    context.user_data['awaiting_username'] = True

    text = "✏️ Введите @username пользователя в чат"

    keyboard = [
        [InlineKeyboardButton("← Назад", callback_data='show_stars')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    message = await query.edit_message_text(
        text,
        reply_markup=reply_markup
    )
    context.user_data['username_prompt_message_id'] = message.message_id


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('awaiting_custom_amount'):
        try:
            amount = int(update.message.text)

            if amount < 50:
                await update.message.reply_text("Минимальное количество звёзд - 50")
                return
            if amount > 5000:
                await update.message.reply_text("Максимальное количество звёзд - 5000")
                return

            message_id = context.user_data.pop('custom_amount_message_id', None)
            if message_id:
                try:
                    await update.message.chat.delete_message(message_id)
                except:
                    pass

            context.user_data['awaiting_custom_amount'] = False
            context.user_data['amount'] = amount

            await confirm_purchase(update, context, amount)
            await update.message.delete()

        except ValueError:
            await update.message.reply_text(
                "Пожалуйста, введите корректное количество звёзд (целое число от 50 до 5000)."
            )
    elif context.user_data.get('awaiting_username'):
        message_id = context.user_data.pop('username_prompt_message_id', None)
        if message_id:
            try:
                await update.message.chat.delete_message(message_id)
            except:
                pass

        recipient_username = update.message.text.strip()

        if not recipient_username:
            await update.message.reply_text("Пожалуйста, введите @username или ID получателя")
            return

        amount = context.user_data.get('amount')
        cost = round(amount * RATE)
        if not amount:
            await update.message.reply_text("Ошибка: количество звёзд не указано")
            return

        link = f"https://tiger-stars.com/?amount={amount}&username={recipient_username}"
        text = f"Вы собираетесь купить *{amount}* Telegram Stars 🌟 на аккаунт *@{recipient_username}* за *{cost}₽*\n"

        keyboard = [
            [InlineKeyboardButton("💳 Перейти к оплате", url=link)],
            [InlineKeyboardButton("📤 Отправить другому пользователю", callback_data='send_to_other')],
            [InlineKeyboardButton("← Назад", callback_data='show_stars')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            text,
            reply_markup=reply_markup,
            parse_mode='Markdown',
            disable_web_page_preview=True
        )
        await update.message.delete()
    else:
        try:
            amount = int(update.message.text)

            if amount < 50:
                await update.message.reply_text("Минимальное количество звёзд - 50")
                return
            if amount > 5000:
                await update.message.reply_text("Максимальное количество звёзд - 5000")
                return

            context.user_data['amount'] = amount
            await confirm_purchase(update, context, amount)

        except ValueError:
            await update.message.reply_text(
                "Пожалуйста, введите корректное количество звёзд (целое число от 50 до 5000)."
            )


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == 'show_stars':
        context.user_data.clear()
        await show_stars_options(update, context)
    elif query.data == 'back_to_main':
        await start(update, context)
    elif query.data == 'custom_amount':
        await handle_custom_amount(update, context)
    elif query.data == 'send_to_other':
        await ask_for_username(update, context)
    elif query.data.startswith('select_'):
        amount = int(query.data.split('_')[1])
        await confirm_purchase(update, context, amount)
    elif query.data.startswith('buy_'):
        amount = int(query.data.split('_')[1])
        cost = round(amount * RATE)
        nickname = query.from_user.username or query.from_user.first_name or "пользователь"
        link = f"https://tiger-stars.com/?amount={amount}&username={nickname}"

        keyboard = [
            [InlineKeyboardButton("💳 Перейти к оплате", url=link)],
            [InlineKeyboardButton("← Назад", callback_data='show_stars')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        text = f"Вы собираетесь купить *{amount}* Telegram Stars 🌟 на аккаунт *@{nickname}* за *{cost}₽*"

        await query.edit_message_text(
            text,
            reply_markup=reply_markup,
            parse_mode='Markdown',
            disable_web_page_preview=True
        )


if __name__ == '__main__':
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(button_callback))

    app.run_polling()