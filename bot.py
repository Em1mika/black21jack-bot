import logging
import random
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor

# 🔒 ТВОИ ДАННЫЕ
API_TOKEN = "7689697850:AAFeDtgekHM6bsOT7B0A1rdsaTRCcp59VqY"
ADMIN_TG_ID = "5520224616"

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)
logging.basicConfig(level=logging.INFO)

user_balances = {}
last_daily_claim = {}

# 🎴 Игровая логика
def draw_card():
    return random.choice(['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A'])

def card_value(card):
    if card in ['J', 'Q', 'K']:
        return 10
    elif card == 'A':
        return 11
    return int(card)

def total(hand):
    result = sum(card_value(c) for c in hand)
    aces = hand.count('A')
    while result > 21 and aces:
        result -= 10
        aces -= 1
    return result

# 🟢 /start
@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    user_id = message.from_user.id
    user_balances.setdefault(user_id, 100)

    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("🎮 Играть", callback_data="play"))
    kb.add(InlineKeyboardButton("🎁 Ежедневная награда", callback_data="daily"))
    kb.add(InlineKeyboardButton("💸 Поддержать", callback_data="donate"))

    await message.answer("Добро пожаловать в Blackjack-бот!\nВыберите действие:", reply_markup=kb)

# 🕹 Кнопки
@dp.callback_query_handler(lambda c: True)
async def handle(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    data = callback_query.data

    if data == "daily":
        today = datetime.utcnow().date()
        if last_daily_claim.get(user_id) == today:
            await callback_query.message.edit_text("Ты уже получал награду сегодня!")
        else:
            user_balances[user_id] = user_balances.get(user_id, 100) + 10
            last_daily_claim[user_id] = today
            await callback_query.message.edit_text(f"Получено +10 монет! Баланс: {user_balances[user_id]}")
        return

    if data == "play":
        if user_balances.get(user_id, 100) < 10:
            await callback_query.message.edit_text("Недостаточно монет! Минимум 10.")
            return

        player = [draw_card(), draw_card()]
        dealer = [draw_card()]
        text = f"Твои карты: {player} (сумма: {total(player)})\nКарта дилера: {dealer}"

        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("Взять", callback_data=f"hit|{','.join(player)}|{dealer[0]}"))
        kb.add(InlineKeyboardButton("Хватит", callback_data=f"stand|{','.join(player)}|{dealer[0]}"))

        await callback_query.message.edit_text(text, reply_markup=kb)

    elif data.startswith("hit") or data.startswith("stand"):
        parts = data.split("|")
        action = parts[0]
        player = parts[1].split(",")
        dealer = [parts[2]]

        if action == "hit":
            player.append(draw_card())
            if total(player) > 21:
                user_balances[user_id] -= 10
                await callback_query.message.edit_text(
                    f"Проигрыш! Твои карты: {player} ({total(player)}). Баланс: {user_balances[user_id]}"
                )
                return
            kb = InlineKeyboardMarkup()
            kb.add(InlineKeyboardButton("Взять", callback_data=f"hit|{','.join(player)}|{dealer[0]}"))
            kb.add(InlineKeyboardButton("Хватит", callback_data=f"stand|{','.join(player)}|{dealer[0]}"))
            await callback_query.message.edit_text(
                f"Твои карты: {player} ({total(player)})\nКарта дилера: {dealer}", reply_markup=kb
            )

        elif action == "stand":
            while total(dealer) < 17:
                dealer.append(draw_card())

            text = f"Твои карты: {player} ({total(player)})\nКарты дилера: {dealer} ({total(dealer)})\n"
            if total(dealer) > 21 or total(player) > total(dealer):
                user_balances[user_id] += 10
                text += "Ты выиграл! +10 монет"
            elif total(player) < total(dealer):
                user_balances[user_id] -= 10
                text += "Ты проиграл. -10 монет"
            else:
                text += "Ничья."
            text += f"\nБаланс: {user_balances[user_id]}"
            await callback_query.message.edit_text(text)

    elif data == "donate":
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("TON перевод", url=f"https://t.me/crypto?start=send-{ADMIN_TG_ID}"))
        await callback_query.message.edit_text("Поддержи разработчика:", reply_markup=kb)

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
