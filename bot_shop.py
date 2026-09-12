# ============================================================
# HDM SHOP BOT - Full Menu + Auto Duyệt SePay
# Bot: @shop_tai_nguyen_mmo_hdm_bot
# Author: HDM
# ============================================================

import telebot
from telebot import types
from telebot.types import BotCommand, MenuButtonCommands
import json
import os
import random
import string
from datetime import datetime
from flask import Flask, request

# ===== CẤU HÌNH =====
BOT_TOKEN = '8962422980:AAGco6lrf1kytlAGCdpoNeQylUL-qbFwaQM'
ADMIN_ID = 6780308119
TELEGRAM_SUPPORT = '@spmxhhdm'
BANK_INFO = {
    'bank': 'VPBank',
    'account': '6566221227',
    'owner': 'DO HAI DANG'
}

DB_FILE = 'shop_data.json'

# ===== DATABASE =====
def load_db():
    if not os.path.exists(DB_FILE):
        default = {
            'products': {
                'spam_sms': {'name': '💥 Spam SMS', 'price': 50000, 'stock': 999, 'type': 'tool', 'desc': 'Tool spam SMS 50+ dịch vụ', 'delivery': 'Link tool'},
                'via_fb_tuimun': {'name': '📱 Túi mù Via FB 2k', 'price': 2000, 'stock': 100, 'type': 'account', 'desc': 'Via FB random K9-K12', 'delivery': 'Auto kho'},
                'via_fb_k9_2fa': {'name': '🔐 Via FB K9-K12 2FA', 'price': 10000, 'stock': 50, 'type': 'account', 'desc': 'Via K9-K12 có 2FA + cookie', 'delivery': 'Auto kho'},
                'clone_fb': {'name': '👥 Clone Facebook', 'price': 15000, 'stock': 30, 'type': 'account', 'desc': 'Clone FB reg 2020-2022', 'delivery': 'Auto kho'},
                'tut_dame_ig': {'name': '📸 Tut Dame IG', 'price': 30000, 'stock': 999, 'type': 'tut', 'desc': 'Hướng dẫn dame Instagram', 'delivery': 'Google Drive'},
                'tut_dame_fb': {'name': '📘 Tut Dame FB', 'price': 30000, 'stock': 999, 'type': 'tut', 'desc': 'Hướng dẫn dame Facebook', 'delivery': 'Google Drive'},
                'tut_dame_tt_video': {'name': '🎬 Tut Dame Video TikTok', 'price': 30000, 'stock': 999, 'type': 'tut', 'desc': 'Dame video TikTok', 'delivery': 'Google Drive'},
                'tut_dame_tt_13t': {'name': '🎵 Tut Dame TikTok 13T', 'price': 40000, 'stock': 999, 'type': 'tut', 'desc': 'Dame TikTok 13 tuổi', 'delivery': 'Google Drive'},
                'form_dame_fb': {'name': '📋 Form Dame FB', 'price': 25000, 'stock': 999, 'type': 'tool', 'desc': 'Form báo cáo Facebook', 'delivery': 'File HTML'},
                'tool_dame_fb': {'name': '🔧 Tool Dame FB', 'price': 100000, 'stock': 999, 'type': 'tool', 'desc': 'Tool auto dame Facebook', 'delivery': 'Link tool'},
                'tool_dame_tt': {'name': '🔧 Tool Dame TikTok', 'price': 100000, 'stock': 999, 'type': 'tool', 'desc': 'Tool auto dame TikTok', 'delivery': 'Link tool'}
            },
            'inventory': {'via_fb_tuimun': [], 'via_fb_k9_2fa': [], 'clone_fb': []},
            'pending': {}, 'orders': [], 'users': {}, 'tips': [
                {'title': 'Cách dame FB hiệu quả', 'content': 'Bước 1: Chọn nick uy tín\nBước 2: Report đúng loại\nBước 3: Kiên nhẫn', 'author': 'admin', 'time': '12/09/2026 20:00'}
            ]
        }
        with open(DB_FILE, 'w', encoding='utf-8') as f:
            json.dump(default, f, ensure_ascii=False, indent=2)
    with open(DB_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_db(data):
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ===== KHỞI TẠO =====
bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# ===== SET MENU =====
def set_bot_commands():
    commands = [
        BotCommand('start', '🏠 Menu chính'),
        BotCommand('help', '📖 Hướng dẫn'),
        BotCommand('shop', '🛒 Cửa hàng'),
        BotCommand('spamsms', '💥 Spam SMS'),
        BotCommand('via', '📱 Via/Clone FB'),
        BotCommand('tut', '📚 Tut Dame'),
        BotCommand('tool', '🔧 Tool Dame'),
        BotCommand('tips', '💡 Mẹo Free'),
        BotCommand('support', '📞 Hỗ trợ'),
    ]
    bot.set_my_commands(commands)

def set_menu_button():
    bot.set_chat_menu_button(menu_button=MenuButtonCommands())

set_bot_commands()
set_menu_button()

# ===== MENU CHÍNH =====
def main_menu():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton('💥 Spam SMS', callback_data='cat_spam_sms'),
        types.InlineKeyboardButton('📱 Via/Clone FB', callback_data='cat_via_fb'),
        types.InlineKeyboardButton('📚 Tut Dame', callback_data='cat_tut'),
        types.InlineKeyboardButton('🔧 Tool Dame', callback_data='cat_tool'),
        types.InlineKeyboardButton('💡 Mẹo Free', callback_data='cat_tips'),
        types.InlineKeyboardButton('📞 Hỗ trợ', url=f'https://t.me/{TELEGRAM_SUPPORT[1:]}')
    )
    return markup

CATEGORIES = {
    'cat_spam_sms': {'title': '💥 SPAM SMS', 'products': ['spam_sms']},
    'cat_via_fb': {'title': '📱 VIA / CLONE FACEBOOK', 'products': ['via_fb_tuimun', 'via_fb_k9_2fa', 'clone_fb']},
    'cat_tut': {'title': '📚 TUT DAME', 'products': ['tut_dame_ig', 'tut_dame_fb', 'tut_dame_tt_video', 'tut_dame_tt_13t']},
    'cat_tool': {'title': '🔧 TOOL DAME', 'products': ['form_dame_fb', 'tool_dame_fb', 'tool_dame_tt']},
}

# ===== LỆNH /start =====
@bot.message_handler(commands=['start'])
def cmd_start(msg):
    chat_id = msg.chat.id
    name = msg.from_user.first_name or 'bạn'
    db = load_db()
    if str(chat_id) not in db['users']:
        db['users'][str(chat_id)] = {'name': name, 'joined': datetime.now().isoformat()}
        save_db(db)
    bot.send_message(chat_id,
        f"👋 Xin chào *{name}*!\n\n"
        f"🛒 *HDM SHOP - Cửa hàng số*\n"
        f"⚡ Tự động duyệt - Giao hàng ngay\n\n"
        f"📌 *Gõ / để xem menu lệnh*\n"
        f"📌 *Hoặc bấm nút ☰ góc trái dưới*\n\n"
        f"👇 Hoặc chọn danh mục:",
        parse_mode='Markdown', reply_markup=main_menu())

# ===== LỆNH /help =====
@bot.message_handler(commands=['help'])
def cmd_help(msg):
    bot.send_message(msg.chat.id,
        "📖 *HƯỚNG DẪN MUA HÀNG*\n\n"
        "1️⃣ Chọn danh mục (gõ / hoặc bấm nút)\n"
        "2️⃣ Chọn sản phẩm\n"
        "3️⃣ Chuyển khoản đúng nội dung\n"
        "4️⃣ Bot tự động gửi hàng\n\n"
        f"📱 Hỗ trợ: {TELEGRAM_SUPPORT}",
        parse_mode='Markdown')

# ===== LỆNH /shop =====
@bot.message_handler(commands=['shop'])
def cmd_shop(msg):
    bot.send_message(msg.chat.id,
        "🛒 *HDM SHOP*\n\n👇 Chọn danh mục:",
        parse_mode='Markdown', reply_markup=main_menu())

# ===== LỆNH /spamsms =====
@bot.message_handler(commands=['spamsms'])
def cmd_spamsms(msg):
    bot.send_message(msg.chat.id,
        "💥 *SPAM SMS*\n\n👇 Chọn sản phẩm:",
        parse_mode='Markdown',
        reply_markup=types.InlineKeyboardMarkup().add(
            types.InlineKeyboardButton('💥 Tool Spam SMS - 50.000đ', callback_data='product_spam_sms')))

# ===== LỆNH /via =====
@bot.message_handler(commands=['via'])
def cmd_via(msg):
    bot.send_message(msg.chat.id,
        "📱 *VIA / CLONE FACEBOOK*\n\n👇 Chọn sản phẩm:",
        parse_mode='Markdown',
        reply_markup=types.InlineKeyboardMarkup(row_width=1).add(
            types.InlineKeyboardButton('📱 Túi mù Via FB 2k - 2.000đ', callback_data='product_via_fb_tuimun'),
            types.InlineKeyboardButton('🔐 Via FB K9-K12 2FA - 10.000đ', callback_data='product_via_fb_k9_2fa'),
            types.InlineKeyboardButton('👥 Clone Facebook - 15.000đ', callback_data='product_clone_fb')))

# ===== LỆNH /tut =====
@bot.message_handler(commands=['tut'])
def cmd_tut(msg):
    bot.send_message(msg.chat.id,
        "📚 *TUT DAME*\n\n👇 Chọn sản phẩm:",
        parse_mode='Markdown',
        reply_markup=types.InlineKeyboardMarkup(row_width=1).add(
            types.InlineKeyboardButton('📸 Tut Dame IG - 30.000đ', callback_data='product_tut_dame_ig'),
            types.InlineKeyboardButton('📘 Tut Dame FB - 30.000đ', callback_data='product_tut_dame_fb'),
            types.InlineKeyboardButton('🎬 Tut Dame Video TikTok - 30.000đ', callback_data='product_tut_dame_tt_video'),
            types.InlineKeyboardButton('🎵 Tut Dame TikTok 13T - 40.000đ', callback_data='product_tut_dame_tt_13t')))

# ===== LỆNH /tool =====
@bot.message_handler(commands=['tool'])
def cmd_tool(msg):
    bot.send_message(msg.chat.id,
        "🔧 *TOOL DAME*\n\n👇 Chọn sản phẩm:",
        parse_mode='Markdown',
        reply_markup=types.InlineKeyboardMarkup(row_width=1).add(
            types.InlineKeyboardButton('📋 Form Dame FB - 25.000đ', callback_data='product_form_dame_fb'),
            types.InlineKeyboardButton('🔧 Tool Dame FB - 100.000đ', callback_data='product_tool_dame_fb'),
            types.InlineKeyboardButton('🔧 Tool Dame TikTok - 100.000đ', callback_data='product_tool_dame_tt')))

# ===== LỆNH /tips =====
@bot.message_handler(commands=['tips'])
def cmd_tips(msg):
    db = load_db()
    tips = db.get('tips', [])
    markup = types.InlineKeyboardMarkup(row_width=1)
    for i, tip in enumerate(tips):
        markup.add(types.InlineKeyboardButton(f"📖 {tip['title']}", callback_data=f'tip_{i}'))
    markup.add(
        types.InlineKeyboardButton('➕ Đăng bài', callback_data='post_tip'),
        types.InlineKeyboardButton('🔙 Quay lại', callback_data='back_menu'))
    bot.send_message(msg.chat.id,
        "💡 *MẸO FREE*\n\n👇 Chọn bài viết:",
        parse_mode='Markdown', reply_markup=markup)

# ===== LỆNH /support =====
@bot.message_handler(commands=['support'])
def cmd_support(msg):
    bot.send_message(msg.chat.id,
        f"📞 *HỖ TRỢ*\n\n"
        f"👤 Admin: {TELEGRAM_SUPPORT}\n"
        f"💬 Nhắn tin trực tiếp để được hỗ trợ\n"
        f"⏰ Thời gian: 8h - 23h hàng ngày",
        parse_mode='Markdown',
        reply_markup=types.InlineKeyboardMarkup().add(
            types.InlineKeyboardButton('📱 Nhắn Admin', url=f'https://t.me/{TELEGRAM_SUPPORT[1:]}')))

# ===== DANH MỤC =====
@bot.callback_query_handler(func=lambda c: c.data.startswith('cat_'))
def show_category(call):
    if call.data == 'cat_tips':
        return show_tips(call)
    cat = CATEGORIES.get(call.data)
    if not cat:
        return
    db = load_db()
    markup = types.InlineKeyboardMarkup(row_width=1)
    for pid in cat['products']:
        if pid in db['products']:
            p = db['products'][pid]
            stock = f"✅{p['stock']}" if p['stock'] > 0 else "❌Hết"
            markup.add(types.InlineKeyboardButton(
                f"{p['name']} - {p['price']:,}đ ({stock})",
                callback_data=f'product_{pid}'))
    markup.add(types.InlineKeyboardButton('🔙 Quay lại', callback_data='back_menu'))
    bot.edit_message_text(f"{cat['title']}\n\n👇 Chọn sản phẩm:",
        call.message.chat.id, call.message.message_id, reply_markup=markup)

# ===== CHI TIẾT SP =====
@bot.callback_query_handler(func=lambda c: c.data.startswith('product_'))
def show_product(call):
    pid = call.data.replace('product_', '')
    db = load_db()
    if pid not in db['products']:
        return
    p = db['products'][pid]
    stock = f"✅ Còn {p['stock']}" if p['stock'] > 0 else "❌ Hết hàng"
    text = (f"🛍️ *{p['name']}*\n\n"
            f"📝 {p['desc']}\n"
            f"💰 Giá: *{p['price']:,}đ*\n"
            f"📦 Kho: {stock}\n"
            f"🚚 Giao: {p['delivery']}\n\n"
            f"👇 Bấm MUA:")
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton('🛒 MUA NGAY', callback_data=f'buy_{pid}'),
        types.InlineKeyboardButton('🔙 Quay lại', callback_data='back_menu'))
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id,
        parse_mode='Markdown', reply_markup=markup)

# ===== MUA HÀNG =====
@bot.callback_query_handler(func=lambda c: c.data.startswith('buy_'))
def buy_product(call):
    pid = call.data.replace('buy_', '')
    db = load_db()
    if pid not in db['products']:
        return
    p = db['products'][pid]
    if p['stock'] <= 0:
        bot.answer_callback_query(call.id, '❌ Hết hàng!')
        return
    order_code = 'HDM' + ''.join(random.choices(string.digits, k=6))
    db['pending'][order_code] = {
        'chat_id': call.from_user.id,
        'username': call.from_user.username or call.from_user.first_name,
        'product_id': pid, 'product_name': p['name'],
        'price': p['price'], 'status': 'awaiting_payment',
        'time': datetime.now().isoformat()
    }
    save_db(db)
    text = (f"🛒 *ĐƠN HÀNG ĐÃ TẠO*\n\n"
            f"📦 SP: *{p['name']}*\n"
            f"💰 Tiền: *{p['price']:,}đ*\n"
            f"🆔 Mã đơn: `{order_code}`\n\n"
            f"💳 *THANH TOÁN*\n"
            f"🏦 {BANK_INFO['bank']}\n"
            f"🔢 STK: `{BANK_INFO['account']}`\n"
            f"👤 {BANK_INFO['owner']}\n"
            f"💵 Nội dung CK: `{order_code}`\n\n"
            f"⚡ *TỰ ĐỘNG DUYỆT*\n"
            f"→ CK đúng nội dung → bot gửi hàng ngay\n\n"
            f"⏰ Đơn hết hạn sau 30 phút")
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton('✅ Tôi đã CK', callback_data=f'paid_{order_code}'),
        types.InlineKeyboardButton('🔙 Quay lại', callback_data='back_menu'))
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id,
        parse_mode='Markdown', reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data.startswith('paid_'))
def user_paid(call):
    order_code = call.data.replace('paid_', '')
    db = load_db()
    if order_code not in db['pending']:
        return
    order = db['pending'][order_code]
    order['status'] = 'verifying'
    save_db(db)
    bot.edit_message_text(
        f"⏳ *ĐANG XÁC MINH*\n\n"
        f"🆔 Mã: `{order_code}`\n"
        f"💰 Tiền: *{order['price']:,}đ*\n\n"
        f"⚡ Hệ thống kiểm tra giao dịch...\n"
        f"⏰ Chờ 1-5 phút\n\n"
        f"📸 Hoặc gửi bill để duyệt nhanh:",
        call.message.chat.id, call.message.message_id, parse_mode='Markdown')

# ===== WEBHOOK SEPAY =====
@app.route('/webhook/payment', methods=['POST'])
def payment_webhook():
    try:
        data = request.json
        print(f"Webhook: {data}")
        amount = data.get('transferAmount', 0) or data.get('amount', 0)
        description = data.get('content', '') or data.get('description', '')
        db = load_db()
        for order_code, order in list(db['pending'].items()):
            if order_code in description and order['status'] in ['awaiting_payment', 'verifying']:
                if amount >= order['price']:
                    auto_deliver(order_code, order)
                    break
        return {'success': True}
    except Exception as e:
        print(f'Webhook error: {e}')
        return {'error': str(e)}, 500

def auto_deliver(order_code, order):
    db = load_db()
    pid = order['product_id']
    p = db['products'][pid]
    chat_id = order['chat_id']
    try:
        if p['type'] == 'account':
            inventory = db['inventory'].get(pid, [])
            if not inventory:
                bot.send_message(chat_id, '⚠️ Hết kho. Admin gửi sau!')
                bot.send_message(ADMIN_ID, f'⚠️ HẾT KHO: {p["name"]} - {order_code}')
                return
            acc = inventory.pop(0)
            db['inventory'][pid] = inventory
            p['stock'] = len(inventory)
            bot.send_message(chat_id,
                f"✅ *GIAO HÀNG THÀNH CÔNG*\n\n"
                f"📦 SP: *{p['name']}*\n"
                f"🆔 Mã: `{order_code}`\n\n"
                f"📩 *TÀI KHOẢN:*\n```\n{acc}\n```\n\n"
                f"⚠️ Đổi pass ngay!",
                parse_mode='Markdown')
        elif p['type'] == 'tool':
            bot.send_message(chat_id,
                f"✅ *GIAO HÀNG THÀNH CÔNG*\n\n"
                f"📦 SP: *{p['name']}*\n"
                f"🆔 Mã: `{order_code}`\n\n"
                f"📎 *Link tool:*\n`https://github.com/hdm-shop/tools`\n\n"
                f"📱 Hỗ trợ: {TELEGRAM_SUPPORT}",
                parse_mode='Markdown')
        elif p['type'] == 'tut':
            bot.send_message(chat_id,
                f"✅ *GIAO HÀNG THÀNH CÔNG*\n\n"
                f"📦 SP: *{p['name']}*\n"
                f"🆔 Mã: `{order_code}`\n\n"
                f"📎 *Link tài liệu:*\n`https://drive.google.com/hdm-tuts`\n\n"
                f"⚠️ Không chia sẻ!",
                parse_mode='Markdown')
        order['status'] = 'completed'
        order['completed_at'] = datetime.now().isoformat()
        db['orders'].append(order)
        del db['pending'][order_code]
        save_db(db)
        bot.send_message(ADMIN_ID,
            f"✅ *ĐƠN TỰ ĐỘNG DUYỆT*\n\n"
            f"🆔 `{order_code}`\n"
            f"👤 @{order['username']}\n"
            f"📦 {p['name']}\n"
            f"💰 {order['price']:,}đ",
            parse_mode='Markdown')
    except Exception as e:
        print(f'Auto deliver error: {e}')
        bot.send_message(ADMIN_ID, f'❌ Lỗi đơn {order_code}: {e}')

# ===== BILL THỦ CÔNG =====
@bot.message_handler(content_types=['photo'])
def handle_bill_photo(msg):
    chat_id = msg.chat.id
    photo_id = msg.photo[-1].file_id
    db = load_db()
    user_order = None
    for oid, o in db['pending'].items():
        if o['chat_id'] == chat_id and o['status'] in ['awaiting_payment', 'verifying']:
            user_order = (oid, o)
            break
    if not user_order:
        bot.send_message(chat_id, '⚠️ Không có đơn chờ!')
        return
    oid, order = user_order
    bot.send_photo(ADMIN_ID, photo_id,
        caption=f"🔔 *BILL THỦ CÔNG*\n\n"
                f"🆔 `{oid}`\n"
                f"👤 @{order['username']}\n"
                f"📦 {order['product_name']}\n"
                f"💰 {order['price']:,}đ",
        parse_mode='Markdown',
        reply_markup=types.InlineKeyboardMarkup().add(
            types.InlineKeyboardButton('✅ GỬI HÀNG', callback_data=f'manual_{oid}'),
            types.InlineKeyboardButton('❌ TỪ CHỐI', callback_data=f'reject_{oid}')))
    bot.send_message(chat_id, '✅ Đã gửi bill cho admin!')

@bot.callback_query_handler(func=lambda c: c.data.startswith('manual_'))
def admin_manual(call):
    if call.from_user.id != ADMIN_ID:
        return
    oid = call.data.replace('manual_', '')
    db = load_db()
    if oid in db['pending']:
        auto_deliver(oid, db['pending'][oid])
        bot.answer_callback_query(call.id, '✅ Đã gửi!')

@bot.callback_query_handler(func=lambda c: c.data.startswith('reject_'))
def admin_reject(call):
    if call.from_user.id != ADMIN_ID:
        return
    oid = call.data.replace('reject_', '')
    db = load_db()
    if oid in db['pending']:
        order = db['pending'][oid]
        bot.send_message(order['chat_id'], '❌ Đơn bị từ chối!')
        order['status'] = 'rejected'
        db['orders'].append(order)
        del db['pending'][oid]
        save_db(db)
        bot.answer_callback_query(call.id, '❌ Đã từ chối!')

# ===== MẸO FREE =====
def show_tips(call):
    db = load_db()
    tips = db.get('tips', [])
    markup = types.InlineKeyboardMarkup(row_width=1)
    for i, tip in enumerate(tips):
        markup.add(types.InlineKeyboardButton(f"📖 {tip['title']}", callback_data=f'tip_{i}'))
    markup.add(
        types.InlineKeyboardButton('➕ Đăng bài', callback_data='post_tip'),
        types.InlineKeyboardButton('🔙 Quay lại', callback_data='back_menu'))
    bot.edit_message_text(
        "💡 *MẸO FREE*\n\n👇 Chọn bài viết:",
        call.message.chat.id, call.message.message_id,
        parse_mode='Markdown', reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data.startswith('tip_'))
def show_tip(call):
    idx = int(call.data.replace('tip_', ''))
    db = load_db()
    tips = db.get('tips', [])
    if idx >= len(tips):
        return
    tip = tips[idx]
    bot.edit_message_text(
        f"📖 *{tip['title']}*\n\n{tip['content']}\n\n"
        f"👤 @{tip['author']}\n⏰ {tip['time']}",
        call.message.chat.id, call.message.message_id,
        parse_mode='Markdown',
        reply_markup=types.InlineKeyboardMarkup().add(
            types.InlineKeyboardButton('🔙 Quay lại', callback_data='cat_tips')))

@bot.callback_query_handler(func=lambda c: c.data == 'post_tip')
def post_tip(call):
    bot.send_message(call.from_user.id,
        "📝 *ĐĂNG MẸO*\n\nFormat:\n`Tiêu đề | Nội dung`\n\nVD: `Cách dame FB | Bước 1...`",
        parse_mode='Markdown')

@bot.message_handler(func=lambda m: '|' in m.text and len(m.text) < 1000 and m.chat.id != ADMIN_ID)
def receive_tip(msg):
    parts = msg.text.split('|', 1)
    if len(parts) != 2:
        return
    title = parts[0].strip()
    content = parts[1].strip()
    db = load_db()
    db['tips'].append({'title': title, 'content': content,
        'author': msg.from_user.username or msg.from_user.first_name,
        'time': datetime.now().strftime('%d/%m/%Y %H:%M')})
    save_db(db)
    bot.send_message(msg.chat.id, f"✅ Đã đăng: *{title}*", parse_mode='Markdown')
    bot.send_message(ADMIN_ID, f"📝 Bài mới từ @{msg.from_user.username}: {title}")

# ===== ADMIN =====
@bot.message_handler(commands=['admin'])
def admin_panel(msg):
    if msg.chat.id != ADMIN_ID:
        return
    db = load_db()
    total = sum(o['price'] for o in db['orders'] if o['status'] == 'completed')
    bot.send_message(ADMIN_ID,
        f"👑 *ADMIN PANEL*\n\n"
        f"👥 Users: {len(db['users'])}\n"
        f"📦 Đơn xong: {len(db['orders'])}\n"
        f"⏳ Chờ: {len(db['pending'])}\n"
        f"💰 Doanh thu: {total:,}đ\n\n"
        f"*Lệnh:*\n"
        f"`/addacc <pid> <acc>` - Thêm acc\n"
        f"`/broadcast <text>` - Thông báo all\n"
        f"`/stats` - Thống kê",
        parse_mode='Markdown')

@bot.message_handler(commands=['addacc'])
def admin_addacc(msg):
    if msg.chat.id != ADMIN_ID:
        return
    try:
        parts = msg.text.split(' ', 2)
        pid = parts[1]
        acc = parts[2]
        db = load_db()
        if pid in db['inventory']:
            db['inventory'][pid].append(acc)
            db['products'][pid]['stock'] = len(db['inventory'][pid])
            save_db(db)
            bot.send_message(ADMIN_ID, f"✅ Đã thêm acc vào {pid}. Kho: {db['products'][pid]['stock']}")
    except:
        bot.send_message(ADMIN_ID, "❌ Dùng: /addacc <pid> <acc>")

@bot.message_handler(commands=['broadcast'])
def admin_broadcast(msg):
    if msg.chat.id != ADMIN_ID:
        return
    content = msg.text.replace('/broadcast', '').strip()
    if not content:
        bot.send_message(ADMIN_ID, "❌ Dùng: /broadcast <nội dung>")
        return
    db = load_db()
    users = list(db['users'].keys())
    success = 0
    for uid in users:
        try:
            bot.send_message(int(uid), f"📢 *THÔNG BÁO*\n\n{content}", parse_mode='Markdown')
            success += 1
        except:
            pass
    bot.send_message(ADMIN_ID, f"✅ Đã gửi đến {success}/{len(users)}")

@bot.message_handler(commands=['stats'])
def admin_stats(msg):
    if msg.chat.id != ADMIN_ID:
        return
    db = load_db()
    text = "📊 *THỐNG KÊ*\n\n"
    for pid, p in db['products'].items():
        sold = sum(1 for o in db['orders'] if o['product_id'] == pid and o['status'] == 'completed')
        text += f"📦 {p['name']}: bán {sold} | kho {p['stock']}\n"
    total = sum(o['price'] for o in db['orders'] if o['status'] == 'completed')
    text += f"\n💰 Tổng: *{total:,}đ*"
    bot.send_message(ADMIN_ID, text, parse_mode='Markdown')

@bot.callback_query_handler(func=lambda c: c.data == 'back_menu')
def back_menu(call):
    bot.edit_message_text(
        "🛒 *HDM SHOP*\n\n👇 Chọn danh mục:",
        call.message.chat.id, call.message.message_id,
        parse_mode='Markdown', reply_markup=main_menu())

# ===== CHẠY BOT + WEBHOOK =====
if __name__ == '__main__':
    import threading
    def run_bot():
        while True:
            try:
                bot.polling(none_stop=True, timeout=60)
            except Exception as e:
                print(f'Bot error: {e}')
                import time
                time.sleep(5)
    threading.Thread(target=run_bot, daemon=True).start()
    print("🤖 HDM SHOP BOT đang chạy...")
    print(f"👑 Admin: {ADMIN_ID}")
    print(f"💳 Bank: {BANK_INFO['bank']} - {BANK_INFO['account']}")
    port = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=port)