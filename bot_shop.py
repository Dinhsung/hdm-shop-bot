# ============================================================
# HDM SHOP BOT - Full Admin + Auto Duyệt Chính Xác
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
            'products': {},
            'inventory': {},
            'pending': {},
            'orders': [],
            'users': {},
            'tips': []
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
    try:
        commands = [
            BotCommand('start', '🏠 Menu chính'),
            BotCommand('help', '📖 Hướng dẫn'),
            BotCommand('shop', '🛒 Cửa hàng'),
            BotCommand('tips', '💡 Mẹo Free'),
            BotCommand('support', '📞 Hỗ trợ'),
        ]
        bot.set_my_commands(commands)
    except Exception as e:
        print(f"Set commands error: {e}")

set_bot_commands()

# ===== MENU =====
def main_menu():
    db = load_db()
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    # Nhóm sản phẩm theo loại
    for pid, p in db['products'].items():
        stock = f"✅{p['stock']}" if p['stock'] > 0 else "❌Hết"
        markup.add(types.InlineKeyboardButton(
            f"{p['name']} - {p['price']:,}đ ({stock})",
            callback_data=f'product_{pid}'
        ))
    
    markup.add(
        types.InlineKeyboardButton('💡 Mẹo Free', callback_data='cat_tips'),
        types.InlineKeyboardButton('📞 Hỗ trợ', url=f'https://t.me/{TELEGRAM_SUPPORT[1:]}')
    )
    return markup

# ===== LỆNH /start =====
@bot.message_handler(commands=['start'])
def cmd_start(msg):
    chat_id = msg.chat.id
    name = msg.from_user.first_name or 'bạn'
    db = load_db()
    if str(chat_id) not in db['users']:
        db['users'][str(chat_id)] = {'name': name, 'joined': datetime.now().isoformat()}
        save_db(db)
    
    if not db['products']:
        bot.send_message(chat_id,
            f"👋 Xin chào *{name}*!\n\n"
            f"🛒 *HDM SHOP*\n"
            f"⏳ Shop đang cập nhật sản phẩm...\n"
            f"Vui lòng quay lại sau!",
            parse_mode='Markdown')
        return
    
    bot.send_message(chat_id,
        f"👋 Xin chào *{name}*!\n\n"
        f"🛒 *HDM SHOP - Cửa hàng số*\n"
        f"⚡ Tự động duyệt - Giao hàng ngay\n\n"
        f"👇 Chọn sản phẩm bên dưới:",
        parse_mode='Markdown', reply_markup=main_menu())

# ===== LỆNH /help =====
@bot.message_handler(commands=['help'])
def cmd_help(msg):
    bot.send_message(msg.chat.id,
        "📖 *HƯỚNG DẪN MUA HÀNG*\n\n"
        "1️⃣ Chọn sản phẩm từ menu\n"
        "2️⃣ Bot hiện STK + mã đơn\n"
        "3️⃣ Chuyển ĐÚNG số tiền + ĐÚNG nội dung\n"
        "4️⃣ Bot tự động gửi hàng\n\n"
        "⚠️ *Lưu ý:*\n"
        "• Chuyển thiếu tiền → bot KHÔNG giao\n"
        "• Sai nội dung → bot KHÔNG giao\n"
        "• Liên hệ admin nếu có vấn đề\n\n"
        f"📱 Hỗ trợ: {TELEGRAM_SUPPORT}",
        parse_mode='Markdown')

# ===== LỆNH /shop =====
@bot.message_handler(commands=['shop'])
def cmd_shop(msg):
    db = load_db()
    if not db['products']:
        bot.send_message(msg.chat.id, "⏳ Shop đang cập nhật sản phẩm!")
        return
    bot.send_message(msg.chat.id,
        "🛒 *HDM SHOP*\n\n👇 Chọn sản phẩm:",
        parse_mode='Markdown', reply_markup=main_menu())

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

# ===== CHI TIẾT SP =====
@bot.callback_query_handler(func=lambda c: c.data.startswith('product_'))
def show_product(call):
    pid = call.data.replace('product_', '')
    db = load_db()
    if pid not in db['products']:
        bot.answer_callback_query(call.id, '❌ SP không tồn tại!')
        return
    p = db['products'][pid]
    stock = f"✅ Còn {p['stock']}" if p['stock'] > 0 else "❌ Hết hàng"
    text = (f"🛍️ *{p['name']}*\n\n"
            f"📝 {p['desc']}\n"
            f"💰 Giá: *{p['price']:,}đ*\n"
            f"📦 Kho: {stock}\n\n"
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
        'product_id': pid,
        'product_name': p['name'],
        'price': p['price'],
        'status': 'awaiting_payment',
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
            f"💵 Nội dung CK: `{order_code}`\n"
            f"💰 Số tiền: *{p['price']:,}đ* (ĐÚNG SỐ NÀY)\n\n"
            f"⚠️ *CHUYỂN ĐÚNG SỐ TIỀN + ĐÚNG NỘI DUNG*\n"
            f"→ Bot mới tự động giao hàng\n\n"
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
        f"⚠️ Chuyển đúng số tiền mới được duyệt!",
        call.message.chat.id, call.message.message_id, parse_mode='Markdown')

# ===== WEBHOOK SEPAY - CHECK CHÍNH XÁC SỐ TIỀN =====
@app.route('/webhook/payment', methods=['POST'])
def payment_webhook():
    try:
        data = request.json
        print(f"Webhook: {data}")
        
        amount = data.get('transferAmount', 0) or data.get('amount', 0)
        description = data.get('content', '') or data.get('description', '')
        
        print(f"Số tiền: {amount}, Nội dung: {description}")
        
        db = load_db()
        matched = False
        
        for order_code, order in list(db['pending'].items()):
            if order_code in description and order['status'] in ['awaiting_payment', 'verifying']:
                
                # ===== CHECK CHÍNH XÁC SỐ TIỀN =====
                if amount == order['price']:
                    # ĐÚNG SỐ TIỀN → GIAO HÀNG
                    auto_deliver(order_code, order)
                    matched = True
                    break
                    
                elif amount > order['price']:
                    # CHUYỂN DƯ → GIAO HÀNG + BÁO ADMIN
                    auto_deliver(order_code, order)
                    bot.send_message(ADMIN_ID,
                        f"⚠️ *CHUYỂN DƯ*\n\n"
                        f"🆔 Đơn: `{order_code}`\n"
                        f"💰 Giá SP: {order['price']:,}đ\n"
                        f"💰 Đã CK: {amount:,}đ\n"
                        f"💰 Dư: {amount - order['price']:,}đ",
                        parse_mode='Markdown')
                    matched = True
                    break
                    
                elif amount < order['price']:
                    # CHUYỂN THIẾU → KHÔNG GIAO
                    bot.send_message(order['chat_id'],
                        f"⚠️ *CHUYỂN THIẾU TIỀN*\n\n"
                        f"🆔 Đơn: `{order_code}`\n"
                        f"💰 Giá SP: *{order['price']:,}đ*\n"
                        f"💰 Đã CK: *{amount:,}đ*\n"
                        f"💰 Còn thiếu: *{order['price'] - amount:,}đ*\n\n"
                        f"⚠️ Vui lòng chuyển thêm đúng số tiền!\n"
                        f"📱 Hỗ trợ: {TELEGRAM_SUPPORT}",
                        parse_mode='Markdown')
                    
                    bot.send_message(ADMIN_ID,
                        f"⚠️ *CHUYỂN THIẾU*\n\n"
                        f"🆔 Đơn: `{order_code}`\n"
                        f"👤 @{order['username']}\n"
                        f"💰 Giá: {order['price']:,}đ\n"
                        f"💰 Đã CK: {amount:,}đ\n"
                        f"💰 Thiếu: {order['price'] - amount:,}đ",
                        parse_mode='Markdown')
                    matched = True
                    break
        
        if not matched:
            print(f"Không match đơn nào với nội dung: {description}")
        
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
                f"📎 *Link tool:*\n`{p.get('link', 'https://github.com/hdm-shop/tools')}`\n\n"
                f"📱 Hỗ trợ: {TELEGRAM_SUPPORT}",
                parse_mode='Markdown')
        
        elif p['type'] == 'tut':
            bot.send_message(chat_id,
                f"✅ *GIAO HÀNG THÀNH CÔNG*\n\n"
                f"📦 SP: *{p['name']}*\n"
                f"🆔 Mã: `{order_code}`\n\n"
                f"📎 *Link tài liệu:*\n`{p.get('link', 'https://drive.google.com/hdm-tuts')}`\n\n"
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

# ============================================================
# ===== ADMIN COMMANDS =====
# ============================================================

@bot.message_handler(commands=['admin'])
def admin_panel(msg):
    if msg.chat.id != ADMIN_ID:
        return
    db = load_db()
    total = sum(o['price'] for o in db['orders'] if o['status'] == 'completed')
    bot.send_message(ADMIN_ID,
        f"👑 *ADMIN PANEL*\n\n"
        f"👥 Users: {len(db['users'])}\n"
        f"📦 SP: {len(db['products'])}\n"
        f"🛒 Đơn xong: {len(db['orders'])}\n"
        f"⏳ Chờ: {len(db['pending'])}\n"
        f"💰 Doanh thu: {total:,}đ\n\n"
        f"*LỆNH ADMIN:*\n\n"
        f"📦 *Thêm SP:*\n"
        f"`/addproduct |pid|tên|giá|loại|mô_tả|link|`\n"
        f"Loại: `account` / `tool` / `tut`\n\n"
        f"💰 *Đổi giá:*\n"
        f"`/setprice <pid> <giá_mới>`\n\n"
        f"🔑 *Thêm acc:*\n"
        f"`/addacc <pid> <acc>`\n\n"
        f"📢 *Thông báo:*\n"
        f"`/broadcast <nội dung>`\n\n"
        f"📊 *Thống kê:*\n"
        f"`/stats`\n\n"
        f"🗑 *Xóa SP:*\n"
        f"`/delproduct <pid>`",
        parse_mode='Markdown')

# ===== THÊM SẢN PHẨM =====
@bot.message_handler(commands=['addproduct'])
def admin_addproduct(msg):
    """
    Format: /addproduct |pid|tên|giá|loại|mô_tả|link|
    VD: /addproduct |via_moi|Via FB Mới|5000|account|Via xịn 2024|https://link|
    """
    if msg.chat.id != ADMIN_ID:
        return
    
    try:
        content = msg.text.replace('/addproduct', '').strip()
        parts = [p.strip() for p in content.split('|') if p.strip()]
        
        if len(parts) < 5:
            bot.send_message(ADMIN_ID,
                "❌ *THIẾU THÔNG TIN*\n\n"
                "Format:\n`/addproduct |pid|tên|giá|loại|mô_tả|link|`\n\n"
                "VD:\n`/addproduct |via_moi|Via FB Mới|5000|account|Via xịn 2024|`",
                parse_mode='Markdown')
            return
        
        pid = parts[0]
        name = parts[1]
        price = int(parts[2])
        ptype = parts[3].lower()
        desc = parts[4]
        link = parts[5] if len(parts) > 5 else ''
        
        if ptype not in ['account', 'tool', 'tut']:
            bot.send_message(ADMIN_ID, "❌ Loại phải là: `account` / `tool` / `tut`", parse_mode='Markdown')
            return
        
        db = load_db()
        
        if pid in db['products']:
            bot.send_message(ADMIN_ID, f"❌ PID `{pid}` đã tồn tại! Dùng /setprice để đổi giá.", parse_mode='Markdown')
            return
        
        db['products'][pid] = {
            'name': name,
            'price': price,
            'stock': 0 if ptype == 'account' else 999,
            'type': ptype,
            'desc': desc,
            'link': link
        }
        
        if ptype == 'account':
            db['inventory'][pid] = []
        
        save_db(db)
        
        bot.send_message(ADMIN_ID,
            f"✅ *ĐÃ THÊM SẢN PHẨM*\n\n"
            f"🆔 PID: `{pid}`\n"
            f"📦 Tên: *{name}*\n"
            f"💰 Giá: *{price:,}đ*\n"
            f"📂 Loại: `{ptype}`\n"
            f"📝 Mô tả: {desc}\n"
            f"📎 Link: {link if link else '(không có)'}\n\n"
            f"👉 Thêm acc: `/addacc {pid} <acc>`",
            parse_mode='Markdown')
    
    except Exception as e:
        bot.send_message(ADMIN_ID, f"❌ Lỗi: {e}\n\nDùng: `/addproduct |pid|tên|giá|loại|mô_tả|link|`", parse_mode='Markdown')

# ===== ĐỔI GIÁ =====
@bot.message_handler(commands=['setprice'])
def admin_setprice(msg):
    """Admin đổi giá: /setprice <pid> <giá_mới>"""
    if msg.chat.id != ADMIN_ID:
        return
    try:
        parts = msg.text.split()
        pid = parts[1]
        new_price = int(parts[2])
        
        db = load_db()
        if pid in db['products']:
            old_price = db['products'][pid]['price']
            db['products'][pid]['price'] = new_price
            save_db(db)
            bot.send_message(ADMIN_ID,
                f"✅ *ĐÃ ĐỔI GIÁ*\n\n"
                f"📦 SP: *{db['products'][pid]['name']}*\n"
                f"💰 Giá cũ: {old_price:,}đ\n"
                f"💰 Giá mới: *{new_price:,}đ*",
                parse_mode='Markdown')
        else:
            bot.send_message(ADMIN_ID, f"❌ Không tìm thấy SP: `{pid}`", parse_mode='Markdown')
    except:
        bot.send_message(ADMIN_ID, "❌ Dùng: `/setprice <pid> <giá>`", parse_mode='Markdown')

# ===== XÓA SẢN PHẨM =====
@bot.message_handler(commands=['delproduct'])
def admin_delproduct(msg):
    """Xóa SP: /delproduct <pid>"""
    if msg.chat.id != ADMIN_ID:
        return
    try:
        parts = msg.text.split()
        pid = parts[1]
        
        db = load_db()
        if pid in db['products']:
            name = db['products'][pid]['name']
            del db['products'][pid]
            if pid in db['inventory']:
                del db['inventory'][pid]
            save_db(db)
            bot.send_message(ADMIN_ID, f"✅ Đã xóa SP: *{name}*", parse_mode='Markdown')
        else:
            bot.send_message(ADMIN_ID, f"❌ Không tìm thấy SP: `{pid}`", parse_mode='Markdown')
    except:
        bot.send_message(ADMIN_ID, "❌ Dùng: `/delproduct <pid>`", parse_mode='Markdown')

# ===== THÊM ACC VÀO KHO =====
@bot.message_handler(commands=['addacc'])
def admin_addacc(msg):
    """Thêm acc: /addacc <pid> <acc_content>"""
    if msg.chat.id != ADMIN_ID:
        return
    try:
        parts = msg.text.split(' ', 2)
        pid = parts[1]
        acc = parts[2]
        
        db = load_db()
        if pid not in db['products']:
            bot.send_message(ADMIN_ID, f"❌ SP `{pid}` không tồn tại!", parse_mode='Markdown')
            return
        
        if pid not in db['inventory']:
            db['inventory'][pid] = []
        
        db['inventory'][pid].append(acc)
        db['products'][pid]['stock'] = len(db['inventory'][pid])
        save_db(db)
        
        bot.send_message(ADMIN_ID,
            f"✅ *ĐÃ THÊM ACC*\n\n"
            f"📦 SP: *{db['products'][pid]['name']}*\n"
            f"🔑 Acc: `{acc}`\n"
            f"📊 Kho hiện tại: *{db['products'][pid]['stock']}*",
            parse_mode='Markdown')
    except:
        bot.send_message(ADMIN_ID, "❌ Dùng: `/addacc <pid> <acc>`", parse_mode='Markdown')

# ===== XEM KHO =====
@bot.message_handler(commands=['kho'])
def admin_kho(msg):
    """Xem kho: /kho <pid>"""
    if msg.chat.id != ADMIN_ID:
        return
    try:
        parts = msg.text.split()
        pid = parts[1] if len(parts) > 1 else None
        
        db = load_db()
        if pid:
            if pid not in db['inventory']:
                bot.send_message(ADMIN_ID, f"❌ Không có kho cho `{pid}`", parse_mode='Markdown')
                return
            inv = db['inventory'][pid]
            if not inv:
                bot.send_message(ADMIN_ID, f"📭 Kho `{pid}` trống")
                return
            text = f"📦 *KHO: {pid}* ({len(inv)})\n\n"
            for i, acc in enumerate(inv[:20], 1):
                text += f"{i}. `{acc}`\n"
            if len(inv) > 20:
                text += f"\n... và {len(inv) - 20} acc khác"
            bot.send_message(ADMIN_ID, text, parse_mode='Markdown')
        else:
            text = "📦 *TẤT CẢ KHO*\n\n"
            for pid, inv in db['inventory'].items():
                name = db['products'].get(pid, {}).get('name', pid)
                text += f"• {name}: *{len(inv)}* acc\n"
            bot.send_message(ADMIN_ID, text, parse_mode='Markdown')
    except:
        bot.send_message(ADMIN_ID, "❌ Dùng: `/kho` hoặc `/kho <pid>`", parse_mode='Markdown')

# ===== BROADCAST =====
@bot.message_handler(commands=['broadcast'])
def admin_broadcast(msg):
    if msg.chat.id != ADMIN_ID:
        return
    content = msg.text.replace('/broadcast', '').strip()
    if not content:
        bot.send_message(ADMIN_ID, "❌ Dùng: `/broadcast <nội dung>`", parse_mode='Markdown')
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
    bot.send_message(ADMIN_ID, f"✅ Đã gửi đến *{success}/{len(users)}* user", parse_mode='Markdown')

# ===== THỐNG KÊ =====
@bot.message_handler(commands=['stats'])
def admin_stats(msg):
    if msg.chat.id != ADMIN_ID:
        return
    db = load_db()
    text = "📊 *THỐNG KÊ SHOP*\n\n"
    for pid, p in db['products'].items():
        sold = sum(1 for o in db['orders'] if o['product_id'] == pid and o['status'] == 'completed')
        stock = p['stock']
        text += f"📦 *{p['name']}*\n"
        text += f"   💰 {p['price']:,}đ | Bán: {sold} | Kho: {stock}\n"
    total = sum(o['price'] for o in db['orders'] if o['status'] == 'completed')
    text += f"\n💰 *TỔNG DOANH THU: {total:,}đ*"
    text += f"\n👥 Users: {len(db['users'])}"
    bot.send_message(ADMIN_ID, text, parse_mode='Markdown')

@bot.callback_query_handler(func=lambda c: c.data == 'back_menu')
def back_menu(call):
    bot.edit_message_text(
        "🛒 *HDM SHOP*\n\n👇 Chọn sản phẩm:",
        call.message.chat.id, call.message.message_id,
        parse_mode='Markdown', reply_markup=main_menu())

@bot.callback_query_handler(func=lambda c: c.data == 'cat_tips')
def cat_tips_cb(call):
    show_tips(call)

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
