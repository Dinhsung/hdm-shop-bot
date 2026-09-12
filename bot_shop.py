import telebot
from telebot import types
from telebot.types import BotCommand
import json, os, random, string, html, time, threading
from datetime import datetime
from flask import Flask, request

# ========== IMPORT TOOL SPAM SMS ==========
try:
    import sms_tool
    SMS_TOOL_AVAILABLE = True
    print("[OK] Đã load sms_tool.py")
except ImportError as e:
    SMS_TOOL_AVAILABLE = False
    print(f"[WARN] Không tìm thấy sms_tool.py — tính năng spam SMS sẽ bị tắt ({e})")

# ========== CẤU HÌNH ==========
BOT_TOKEN = os.environ.get('BOT_TOKEN', '8962422980:AAERSCHiswb_rb6PzRSZ094EVdwnJQ0YPdw')
ADMIN_ID = 6780308119
TELEGRAM_SUPPORT = '@spmxhhdm'
BANK_INFO = {'bank': 'TPBank', 'account': '10005490787', 'owner': 'DO HAI DANG'}
BOT_USERNAME = 'hdm_shop_bot'  # ⚠️ ĐỔI thành username bot thật (không có @)
REF_BONUS = 400
DB_FILE = 'shop_data.json'

# ========== STATE CHO SPAM SMS ==========
sms_waiting = {}

# ========== HELPER ==========
def esc(s):
    return html.escape(str(s), quote=False)

def load_db():
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, 'w', encoding='utf-8') as f:
            json.dump({'products': {}, 'inventory': {}, 'pending': {}, 'orders': [], 'users': {}, 'tips': []}, f, ensure_ascii=False, indent=2)
    try:
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            db = json.load(f)
            db.setdefault('products', {})
            db.setdefault('inventory', {})
            db.setdefault('pending', {})
            db.setdefault('orders', [])
            db.setdefault('users', {})
            db.setdefault('tips', [])
            return db
    except:
        return {'products': {}, 'inventory': {}, 'pending': {}, 'orders': [], 'users': {}, 'tips': []}

def save_db(data):
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def find_user_id(query):
    """Tìm user_id từ username hoặc ID. Trả về str(uid) hoặc None"""
    db = load_db()
    query = query.strip().lstrip('@')
    # Nếu là số → tìm trực tiếp
    if query.isdigit():
        return query if query in db['users'] else None
    # Nếu là username → tìm trong users
    for uid, u in db['users'].items():
        # So khớp name hoặc username (nếu lưu)
        if u.get('name', '').lower() == query.lower():
            return uid
    return None

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# ========== SET COMMANDS ==========
try:
    bot.set_my_commands([
        BotCommand('start', '🏠 Menu chính'),
        BotCommand('help', '📖 Hướng dẫn'),
        BotCommand('shop', '🛒 Cửa hàng'),
        BotCommand('tips', '🎁 Mẹo Free'),
        BotCommand('ref', '🔗 Giới thiệu +400đ'),
        BotCommand('balance', '💵 Số dư'),
        BotCommand('support', '💬 Hỗ trợ'),
    ])
except Exception as e:
    print(f"Set commands error: {e}")

# ========== MENU ==========
def main_menu():
    db = load_db()
    markup = types.InlineKeyboardMarkup(row_width=2)
    for pid, p in db['products'].items():
        stock = f"[Còn {p['stock']}]" if p['stock'] > 0 else "[Hết]"
        markup.add(types.InlineKeyboardButton(f"🛒 {p['name']} - {p['price']:,}đ {stock}", callback_data=f'product_{pid}'))
    markup.add(
        types.InlineKeyboardButton('🎁 Mẹo Free', callback_data='cat_tips'),
        types.InlineKeyboardButton('💬 Hỗ trợ', url=f'https://t.me/{TELEGRAM_SUPPORT[1:]}')
    )
    markup.add(
        types.InlineKeyboardButton(f'🔗 Giới thiệu +{REF_BONUS}đ', callback_data='show_ref'),
        types.InlineKeyboardButton('💵 Số dư', callback_data='show_balance')
    )
    return markup

# ========== START ==========
@bot.message_handler(commands=['start'])
def cmd_start(msg):
    chat_id = msg.chat.id
    name = msg.from_user.first_name or 'bạn'
    db = load_db()
    uid = str(chat_id)

    args = msg.text.split()
    ref_by = None
    if len(args) > 1 and args[1].startswith('ref_'):
        ref_by = args[1].replace('ref_', '').strip()

    is_new = uid not in db['users']

    if is_new:
        db['users'][uid] = {
            'name': name,
            'joined': datetime.now().isoformat(),
            'balance': 0,
            'referred_by': ref_by if ref_by else None
        }

        if ref_by and ref_by != uid and ref_by in db['users']:
            db['users'][ref_by]['balance'] = db['users'][ref_by].get('balance', 0) + REF_BONUS
            new_balance = db['users'][ref_by]['balance']
            total_ref = sum(1 for u in db['users'].values() if u.get('referred_by') == ref_by)
            try:
                bot.send_message(
                    int(ref_by),
                    f"🎉 <b>CHÚC MỪNG!</b>\n\n"
                    f"👤 <b>{esc(name)}</b> đã tham gia qua link của bạn!\n"
                    f"💰 Bạn được cộng <b>+{REF_BONUS:,}đ</b>\n"
                    f"👥 Tổng đã giới thiệu: <b>{total_ref}</b> người\n"
                    f"💵 Số dư hiện tại: <b>{new_balance:,}đ</b>",
                    parse_mode='HTML'
                )
            except Exception as e:
                print(f"Noti ref error: {e}")

        save_db(db)

    if not db['products']:
        bot.send_message(chat_id, f"👋 Chào <b>{esc(name)}</b>!\n\n🏪 <b>HDM SHOP</b>\n⏳ Shop đang cập nhật sản phẩm...", parse_mode='HTML')
        return

    bot.send_message(
        chat_id,
        f"👋 Chào <b>{esc(name)}</b>!\n\n"
        f"🏪 <b>HDM SHOP - Cửa hàng số</b>\n"
        f"⚡ Tự động duyệt - Giao hàng ngay\n\n"
        f"👇 Chọn sản phẩm:",
        parse_mode='HTML',
        reply_markup=main_menu()
    )

# ========== HELP ==========
@bot.message_handler(commands=['help'])
def cmd_help(msg):
    bot.send_message(
        msg.chat.id,
        "📖 <b>HƯỚNG DẪN MUA HÀNG</b>\n\n"
        "1️⃣ Chọn sản phẩm\n"
        "2️⃣ Bot hiện STK + mã đơn\n"
        "3️⃣ Chuyển ĐÚNG số tiền + ĐÚNG nội dung\n"
        "4️⃣ Bot tự động gửi hàng\n\n"
        "🎁 <b>GIỚI THIỆU BẠN BÈ</b>\n"
        f"• Mỗi người mới qua link → <b>+{REF_BONUS:,}đ</b>\n"
        "• Gõ /ref để lấy link giới thiệu\n"
        "• Gõ /balance để xem số dư\n\n"
        f"💬 Hỗ trợ: {esc(TELEGRAM_SUPPORT)}",
        parse_mode='HTML'
    )

# ========== SHOP ==========
@bot.message_handler(commands=['shop'])
def cmd_shop(msg):
    db = load_db()
    if not db['products']:
        bot.send_message(msg.chat.id, "⏳ Shop đang cập nhật!")
        return
    bot.send_message(msg.chat.id, "🏪 <b>HDM SHOP</b>\n\n👇 Chọn sản phẩm:", parse_mode='HTML', reply_markup=main_menu())

# ========== SUPPORT ==========
@bot.message_handler(commands=['support'])
def cmd_support(msg):
    bot.send_message(
        msg.chat.id,
        f"💬 <b>HỖ TRỢ</b>\n\nAdmin: {esc(TELEGRAM_SUPPORT)}",
        parse_mode='HTML',
        reply_markup=types.InlineKeyboardMarkup().add(
            types.InlineKeyboardButton('💬 Nhắn Admin', url=f'https://t.me/{TELEGRAM_SUPPORT[1:]}')
        )
    )

# ========== REF ==========
@bot.message_handler(commands=['ref'])
def cmd_ref(msg):
    chat_id = msg.chat.id
    db = load_db()
    uid = str(chat_id)
    if uid not in db['users']:
        bot.send_message(chat_id, "⚠️ Bạn chưa đăng ký. Gõ /start trước!")
        return
    ref_link = f"https://t.me/{BOT_USERNAME}?start=ref_{uid}"
    balance = db['users'][uid].get('balance', 0)
    count = sum(1 for u in db['users'].values() if u.get('referred_by') == uid)
    bot.send_message(
        chat_id,
        f"🎁 <b>GIỚI THIỆU BẠN BÈ</b>\n\n"
        f"🔗 Link của bạn:\n<code>{ref_link}</code>\n\n"
        f"💰 Mỗi người mới tham gia qua link → <b>+{REF_BONUS:,}đ</b>\n"
        f"👥 Đã giới thiệu: <b>{count}</b> người\n"
        f"💵 Số dư: <b>{balance:,}đ</b>\n\n"
        f"📌 Chia sẻ link cho bạn bè ngay!",
        parse_mode='HTML'
    )

# ========== BALANCE ==========
@bot.message_handler(commands=['balance'])
def cmd_balance(msg):
    chat_id = msg.chat.id
    db = load_db()
    uid = str(chat_id)
    if uid not in db['users']:
        bot.send_message(chat_id, "⚠️ Bạn chưa đăng ký. Gõ /start trước!")
        return
    balance = db['users'][uid].get('balance', 0)
    count = sum(1 for u in db['users'].values() if u.get('referred_by') == uid)
    bot.send_message(
        chat_id,
        f"💵 <b>SỐ DƯ CỦA BẠN</b>\n\n"
        f"💰 Số dư: <b>{balance:,}đ</b>\n"
        f"👥 Đã giới thiệu: <b>{count}</b> người\n\n"
        f"📌 Dùng /ref để lấy link giới thiệu!",
        parse_mode='HTML'
    )

# ========== CALLBACK: SHOW REF ==========
@bot.callback_query_handler(func=lambda c: c.data == 'show_ref')
def cb_show_ref(call):
    db = load_db()
    uid = str(call.from_user.id)
    if uid not in db['users']:
        bot.answer_callback_query(call.id, '⚠️ Gõ /start trước!')
        return
    ref_link = f"https://t.me/{BOT_USERNAME}?start=ref_{uid}"
    balance = db['users'][uid].get('balance', 0)
    count = sum(1 for u in db['users'].values() if u.get('referred_by') == uid)
    text = (
        f"🎁 <b>GIỚI THIỆU BẠN BÈ</b>\n\n"
        f"🔗 Link của bạn:\n<code>{ref_link}</code>\n\n"
        f"💰 Mỗi người mới tham gia qua link → <b>+{REF_BONUS:,}đ</b>\n"
        f"👥 Đã giới thiệu: <b>{count}</b> người\n"
        f"💵 Số dư: <b>{balance:,}đ</b>\n\n"
        f"📌 Chia sẻ link cho bạn bè ngay!"
    )
    markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton('⬅️ Quay lại', callback_data='back_menu'))
    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode='HTML', reply_markup=markup)
    except Exception as e:
        print(f"cb_show_ref error: {e}")

# ========== CALLBACK: SHOW BALANCE ==========
@bot.callback_query_handler(func=lambda c: c.data == 'show_balance')
def cb_show_balance(call):
    db = load_db()
    uid = str(call.from_user.id)
    if uid not in db['users']:
        bot.answer_callback_query(call.id, '⚠️ Gõ /start trước!')
        return
    balance = db['users'][uid].get('balance', 0)
    count = sum(1 for u in db['users'].values() if u.get('referred_by') == uid)
    text = (
        f"💵 <b>SỐ DƯ CỦA BẠN</b>\n\n"
        f"💰 Số dư: <b>{balance:,}đ</b>\n"
        f"👥 Đã giới thiệu: <b>{count}</b> người\n\n"
        f"📌 Dùng nút Giới thiệu để lấy link!"
    )
    markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton('⬅️ Quay lại', callback_data='back_menu'))
    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode='HTML', reply_markup=markup)
    except Exception as e:
        print(f"cb_show_balance error: {e}")

# ========== CALLBACK: SHOW PRODUCT ==========
@bot.callback_query_handler(func=lambda c: c.data.startswith('product_'))
def show_product(call):
    pid = call.data.replace('product_', '')
    db = load_db()
    if pid not in db['products']:
        bot.answer_callback_query(call.id, '❌ SP không tồn tại!')
        return
    p = db['products'][pid]
    stock = f"✅ Còn {p['stock']}" if p['stock'] > 0 else "❌ Hết hàng"
    text = (
        f"🛍 <b>{esc(p['name'])}</b>\n\n"
        f"📝 {esc(p['desc'])}\n"
        f"💰 Giá: <b>{p['price']:,}đ</b>\n"
        f"📦 Kho: {stock}\n\n"
        f"👇 Bấm MUA:"
    )
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton('✅ MUA NGAY', callback_data=f'buy_{pid}'),
        types.InlineKeyboardButton('⬅️ Quay lại', callback_data='back_menu')
    )
    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode='HTML', reply_markup=markup)
    except Exception as e:
        print(f"Edit error: {e}")

# ========== CALLBACK: BUY ==========
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

    qr_url = (
        f"https://qr.sepay.vn/img"
        f"?acc={BANK_INFO['account']}"
        f"&bank={BANK_INFO['bank']}"
        f"&amount={p['price']}"
        f"&des={order_code}"
    )

    caption = (
        f"🧾 <b>ĐƠN HÀNG ĐÃ TẠO</b>\n\n"
        f"🛍 SP: <b>{esc(p['name'])}</b>\n"
        f"💰 Tiền: <b>{p['price']:,}đ</b>\n"
        f"🔖 Mã đơn: <code>{order_code}</code>\n\n"
        f"🏦 <b>THANH TOÁN</b>\n"
        f"Ngân hàng: <b>{esc(BANK_INFO['bank'])}</b>\n"
        f"STK: <code>{BANK_INFO['account']}</code>\n"
        f"Chủ TK: {esc(BANK_INFO['owner'])}\n"
        f"Nội dung CK: <code>{order_code}</code>\n"
        f"Số tiền: <b>{p['price']:,}đ</b>\n\n"
        f"⚠️ <b>CHUYỂN ĐÚNG SỐ TIỀN + ĐÚNG NỘI DUNG</b>"
    )

    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton('✅ Tôi đã CK', callback_data=f'paid_{order_code}'),
        types.InlineKeyboardButton('⬅️ Quay lại', callback_data='back_menu')
    )

    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except Exception as e:
        print(f"Delete error: {e}")

    try:
        bot.send_photo(call.message.chat.id, qr_url, caption=caption, parse_mode='HTML', reply_markup=markup)
    except Exception as e:
        print(f"Send photo error: {e}")
        bot.send_message(call.message.chat.id, caption, parse_mode='HTML', reply_markup=markup)

# ========== CALLBACK: USER PAID ==========
@bot.callback_query_handler(func=lambda c: c.data.startswith('paid_'))
def user_paid(call):
    order_code = call.data.replace('paid_', '')
    db = load_db()
    if order_code not in db['pending']:
        return
    order = db['pending'][order_code]
    order['status'] = 'verifying'
    save_db(db)
    text = (
        f"⏳ <b>ĐANG XÁC MINH</b>\n\n"
        f"🔖 Mã: <code>{order_code}</code>\n"
        f"💰 Tiền: {order['price']:,}đ\n\n"
        f"🔍 Hệ thống đang kiểm tra giao dịch..."
    )
    try:
        bot.edit_message_caption(text, call.message.chat.id, call.message.message_id, parse_mode='HTML')
    except Exception:
        try:
            bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode='HTML')
        except Exception as e:
            print(f"Edit paid error: {e}")

# ========== WEBHOOK ==========
@app.route('/webhook/payment', methods=['POST'])
def payment_webhook():
    try:
        data = request.json
        print(f"Webhook: {data}")
        amount = data.get('transferAmount', 0) or data.get('amount', 0)
        description = data.get('content', '') or data.get('description', '')
        print(f"Số tiền: {amount}, Nội dung: {description}")
        db = load_db()
        for order_code, order in list(db['pending'].items()):
            if order_code in description and order['status'] in ['awaiting_payment', 'verifying']:
                if amount == order['price']:
                    auto_deliver(order_code, order)
                    break
                elif amount > order['price']:
                    auto_deliver(order_code, order)
                    bot.send_message(ADMIN_ID, f"⚠️ <b>CHUYỂN DƯ</b>\nĐơn: {order_code}\nGiá: {order['price']:,}đ\nĐã CK: {amount:,}đ\nDư: {amount - order['price']:,}đ", parse_mode='HTML')
                    break
                elif amount < order['price']:
                    bot.send_message(order['chat_id'], f"⚠️ <b>CHUYỂN THIẾU TIỀN</b>\n\n🔖 Đơn: {order_code}\n💰 Giá: {order['price']:,}đ\n📥 Đã CK: {amount:,}đ\n❗ Còn thiếu: <b>{order['price'] - amount:,}đ</b>\n\nVui lòng chuyển thêm!", parse_mode='HTML')
                    bot.send_message(ADMIN_ID, f"⚠️ CHUYỂN THIẾU\nĐơn: {order_code}\n@{order['username']}\nThiếu: {order['price'] - amount:,}đ")
                    break
        return {'success': True}
    except Exception as e:
        print(f'Webhook error: {e}')
        return {'error': str(e)}, 500

# ========== AUTO DELIVER ==========
def auto_deliver(order_code, order):
    db = load_db()
    pid = order['product_id']
    p = db['products'][pid]
    chat_id = order['chat_id']
    try:
        if p['type'] == 'account':
            inventory = db['inventory'].get(pid, [])
            if not inventory:
                bot.send_message(chat_id, '❌ Hết kho. Admin gửi sau!')
                bot.send_message(ADMIN_ID, f'❌ HẾT KHO: {p["name"]} - {order_code}')
                return
            acc = inventory.pop(0)
            db['inventory'][pid] = inventory
            p['stock'] = len(inventory)
            bot.send_message(
                chat_id,
                f"✅ <b>GIAO HÀNG THÀNH CÔNG</b>\n\n"
                f"🛍 SP: {esc(p['name'])}\n"
                f"🔖 Mã: <code>{order_code}</code>\n\n"
                f"🔑 <b>TÀI KHOẢN:</b>\n<code>{esc(acc)}</code>\n\n"
                f"🍀🍀🍀 <b>CHÚC ANH EM MAY MẮN</b>🍀🍀🍀",
                parse_mode='HTML'
            )
        elif p['type'] == 'tool':
            bot.send_message(
                chat_id,
                f"✅ <b>GIAO HÀNG THÀNH CÔNG</b>\n\n"
                f"🛍 SP: {esc(p['name'])}\n"
                f"🔖 Mã: <code>{order_code}</code>\n\n"
                f"🔗 Link tool:\n{p.get('link', 'https://github.com/hdm-shop/tools')}\n\n"
                f"🍀🍀🍀 <b>CHÚC ANH EM MAY MẮN</b>🍀🍀🍀",
                parse_mode='HTML'
            )
        elif p['type'] == 'tut':
            bot.send_message(
                chat_id,
                f"✅ <b>GIAO HÀNG THÀNH CÔNG</b>\n\n"
                f"🛍 SP: {esc(p['name'])}\n"
                f"🔖 Mã: <code>{order_code}</code>\n\n"
                f"🔗 Link tài liệu:\n{p.get('link', 'https://drive.google.com/hdm-tuts')}\n\n"
                f"🍀🍀🍀 <b>CHÚC ANH EM MAY MẮN</b>🍀🍀🍀",
                parse_mode='HTML'
            )
        elif p['type'] == 'tool_sms':
            if not SMS_TOOL_AVAILABLE:
                bot.send_message(chat_id, "❌ Tool spam SMS đang bảo trì. Admin sẽ liên hệ!")
                bot.send_message(ADMIN_ID, f"⚠️ Tool SMS không có sẵn cho đơn {order_code}")
                return
            sms_waiting[chat_id] = {
                'order_code': order_code,
                'step': 'phone',
                'phone': None,
                'count': None
            }
            bot.send_message(
                chat_id,
                f"✅ <b>THANH TOÁN THÀNH CÔNG</b>\n\n"
                f"🛍 SP: {esc(p['name'])}\n"
                f"🔖 Mã: <code>{order_code}</code>\n\n"
                f"📱 <b>Nhập số điện thoại muốn spam:</b>\n"
                f"(VD: 0987654321)\n\n"
                f"⚠️ Gõ /cancel để huỷ",
                parse_mode='HTML'
            )

        order['status'] = 'completed'
        order['completed_at'] = datetime.now().isoformat()
        db['orders'].append(order)
        del db['pending'][order_code]
        save_db(db)
        bot.send_message(ADMIN_ID, f"✅ <b>ĐƠN TỰ ĐỘNG DUYỆT</b>\n\n🔖 Mã: {order_code}\n@{order['username']}\n🛍 SP: {esc(p['name'])}\n💰 Tiền: {order['price']:,}đ", parse_mode='HTML')
    except Exception as e:
        print(f'Auto deliver error: {e}')
        bot.send_message(ADMIN_ID, f'❌ Lỗi đơn {order_code}: {e}')

# ========== BILL PHOTO ==========
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
        bot.send_message(chat_id, '❌ Không có đơn chờ!')
        return
    oid, order = user_order
    bot.send_photo(
        ADMIN_ID, photo_id,
        caption=f"🧾 <b>BILL</b>\n\n🔖 Mã: {oid}\n@{esc(order['username'])}\n🛍 SP: {esc(order['product_name'])}\n💰 Tiền: {order['price']:,}đ",
        parse_mode='HTML',
        reply_markup=types.InlineKeyboardMarkup().add(
            types.InlineKeyboardButton('📤 GỬI HÀNG', callback_data=f'manual_{oid}'),
            types.InlineKeyboardButton('❌ TỪ CHỐI', callback_data=f'reject_{oid}')
        )
    )
    bot.send_message(chat_id, '✅ Đã gửi bill!')

# ========== ADMIN MANUAL ==========
@bot.callback_query_handler(func=lambda c: c.data.startswith('manual_'))
def admin_manual(call):
    if call.from_user.id != ADMIN_ID:
        return
    oid = call.data.replace('manual_', '')
    db = load_db()
    if oid in db['pending']:
        auto_deliver(oid, db['pending'][oid])
        bot.answer_callback_query(call.id, '✅ Đã gửi!')

# ========== ADMIN REJECT ==========
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
        bot.answer_callback_query(call.id, '✅ Đã từ chối!')

# ========== SMS: NHẬP SĐT ==========
@bot.message_handler(func=lambda m: m.chat.id in sms_waiting and sms_waiting[m.chat.id]['step'] == 'phone')
def sms_input_phone(msg):
    chat_id = msg.chat.id
    phone = msg.text.strip().replace(' ', '').replace('-', '')
    if not phone.isdigit() or len(phone) < 10 or len(phone) > 11:
        bot.send_message(chat_id, "❌ SĐT không hợp lệ! Nhập lại (VD: 0987654321):")
        return
    sms_waiting[chat_id]['phone'] = phone
    sms_waiting[chat_id]['step'] = 'count'
    bot.send_message(
        chat_id,
        f"📱 SĐT: <code>{phone}</code>\n\n"
        f"🔁 <b>Nhập số lần spam:</b>\n"
        f"(VD: 10 — tối đa 50)\n\n"
        f"⚠️ Gõ /cancel để huỷ",
        parse_mode='HTML'
    )

# ========== SMS: NHẬP SỐ LẦN ==========
@bot.message_handler(func=lambda m: m.chat.id in sms_waiting and sms_waiting[m.chat.id]['step'] == 'count')
def sms_input_count(msg):
    chat_id = msg.chat.id
    try:
        count = int(msg.text.strip())
        if count < 1 or count > 50:
            bot.send_message(chat_id, "❌ Số lần phải từ 1 đến 50! Nhập lại:")
            return
    except:
        bot.send_message(chat_id, "❌ Phải là số! Nhập lại:")
        return

    data = sms_waiting[chat_id]
    phone = data['phone']
    order_code = data['order_code']
    del sms_waiting[chat_id]

    bot.send_message(
        chat_id,
        f"🚀 <b>ĐANG CHẠY TOOL SPAM SMS</b>\n\n"
        f"📱 SĐT: <code>{phone}</code>\n"
        f"🔁 Số lần: <b>{count}</b>\n"
        f"⏳ Vui lòng đợi... (có thể mất 1–5 phút)\n\n"
        f"Bot sẽ thông báo khi xong!",
        parse_mode='HTML'
    )

    def run_tool():
        try:
            start = time.time()
            if hasattr(sms_tool, 'run_multi'):
                sms_tool.run_multi(phone, count)
            elif hasattr(sms_tool, 'run'):
                for i in range(1, count + 1):
                    sms_tool.run(phone, i)
            else:
                raise Exception("sms_tool.py không có hàm run hoặc run_multi")

            elapsed = time.time() - start
            bot.send_message(
                chat_id,
                f"✅ <b>SPAM SMS HOÀN THÀNH</b>\n\n"
                f"📱 SĐT: <code>{phone}</code>\n"
                f"🔁 Số lần: <b>{count}</b>\n"
                f"⏱ Thời gian: {elapsed:.1f}s\n\n"
                f"🍀🍀🍀 <b>CHÚC ANH EM MAY MẮN</b>🍀🍀🍀",
                parse_mode='HTML'
            )
            bot.send_message(ADMIN_ID, f"✅ Đơn {order_code} chạy xong: {phone} x{count}")
        except Exception as e:
            print(f"[SMS TOOL ERROR] {e}")
            bot.send_message(
                chat_id,
                f"❌ <b>LỖI KHI CHẠY TOOL</b>\n\n"
                f"📱 SĐT: <code>{phone}</code>\n"
                f"🔁 Số lần: <b>{count}</b>\n"
                f"❗ Lỗi: {esc(str(e))}\n\n"
                f"Vui lòng liên hệ admin: {esc(TELEGRAM_SUPPORT)}",
                parse_mode='HTML'
            )
            bot.send_message(ADMIN_ID, f"❌ Lỗi đơn {order_code}: {e}")

    threading.Thread(target=run_tool, daemon=True).start()

# ========== CANCEL ==========
@bot.message_handler(commands=['cancel'])
def cmd_cancel(msg):
    chat_id = msg.chat.id
    if chat_id in sms_waiting:
        del sms_waiting[chat_id]
        bot.send_message(chat_id, "✅ Đã huỷ. Gõ /shop để quay lại.")
    else:
        bot.send_message(chat_id, "⚠️ Không có gì để huỷ.")

# ========== TIPS ==========
@bot.message_handler(commands=['tips'])
def cmd_tips(msg):
    db = load_db()
    tips = db.get('tips', [])
    markup = types.InlineKeyboardMarkup(row_width=1)
    for i, tip in enumerate(tips):
        markup.add(types.InlineKeyboardButton(f"📄 {tip['title']}", callback_data=f'tip_{i}'))
    markup.add(
        types.InlineKeyboardButton('✍️ Đăng bài', callback_data='post_tip'),
        types.InlineKeyboardButton('⬅️ Quay lại', callback_data='back_menu')
    )
    bot.send_message(msg.chat.id, "🎁 <b>MẸO FREE</b>\n\n👇 Chọn bài viết:", parse_mode='HTML', reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data == 'cat_tips')
def cat_tips_cb(call):
    db = load_db()
    tips = db.get('tips', [])
    markup = types.InlineKeyboardMarkup(row_width=1)
    for i, tip in enumerate(tips):
        markup.add(types.InlineKeyboardButton(f"📄 {tip['title']}", callback_data=f'tip_{i}'))
    markup.add(
        types.InlineKeyboardButton('✍️ Đăng bài', callback_data='post_tip'),
        types.InlineKeyboardButton('⬅️ Quay lại', callback_data='back_menu')
    )
    bot.edit_message_text("🎁 <b>MẸO FREE</b>\n\n👇 Chọn bài viết:", call.message.chat.id, call.message.message_id, parse_mode='HTML', reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data.startswith('tip_'))
def show_tip(call):
    idx = int(call.data.replace('tip_', ''))
    db = load_db()
    tips = db.get('tips', [])
    if idx >= len(tips):
        return
    tip = tips[idx]
    text = f"📄 <b>{esc(tip['title'])}</b>\n\n{esc(tip['content'])}\n\n👤 @{esc(tip['author'])} - {esc(tip['time'])}"
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode='HTML', reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton('⬅️ Quay lại', callback_data='cat_tips')))

@bot.callback_query_handler(func=lambda c: c.data == 'post_tip')
def post_tip(call):
    bot.send_message(call.from_user.id, "✍️ <b>ĐĂNG MẸO</b>\n\nFormat: <code>Tiêu đề | Nội dung</code>", parse_mode='HTML')

@bot.message_handler(func=lambda m: m.text and '|' in m.text and len(m.text) < 1000 and m.chat.id != ADMIN_ID)
def receive_tip(msg):
    parts = msg.text.split('|', 1)
    if len(parts) != 2:
        return
    title = parts[0].strip()
    content = parts[1].strip()
    db = load_db()
    db['tips'].append({
        'title': title,
        'content': content,
        'author': msg.from_user.username or msg.from_user.first_name,
        'time': datetime.now().strftime('%d/%m/%Y %H:%M')
    })
    save_db(db)
    bot.send_message(msg.chat.id, f"✅ Đã đăng: <b>{esc(title)}</b>", parse_mode='HTML')
    bot.send_message(ADMIN_ID, f"📝 Bài mới: <b>{esc(title)}</b>", parse_mode='HTML')

# ============================================================
# ============== ADMIN PANEL ============
# ============================================================
@bot.message_handler(commands=['admin'])
def admin_panel(msg):
    if msg.chat.id != ADMIN_ID:
        return
    db = load_db()
    total = sum(o['price'] for o in db['orders'] if o['status'] == 'completed')
    total_balance = sum(u.get('balance', 0) for u in db['users'].values())
    sms_status = "✅ ONLINE" if SMS_TOOL_AVAILABLE else "❌ OFFLINE"
    bot.send_message(
        ADMIN_ID,
        f"👑 <b>ADMIN PANEL</b>\n\n"
        f"👥 Users: {len(db['users'])}\n"
        f"🛍 SP: {len(db['products'])}\n"
        f"✅ Đơn xong: {len(db['orders'])}\n"
        f"⏳ Chờ: {len(db['pending'])}\n"
        f"💰 Doanh thu: <b>{total:,}đ</b>\n"
        f"💵 Tổng số dư ref: <b>{total_balance:,}đ</b>\n"
        f"📱 Tool SMS: {sms_status}\n\n"
        f"📌 <b>LỆNH SẢN PHẨM:</b>\n"
        f"<code>/addproduct |pid|ten|gia|loai|mo_ta|link|</code>\n"
        f"<code>/setprice &lt;pid&gt; &lt;gia&gt;</code>\n"
        f"<code>/delproduct &lt;pid&gt;</code>\n"
        f"<code>/delall confirm</code>\n"
        f"<code>/addacc &lt;pid&gt; &lt;acc&gt;</code>\n"
        f"<code>/addlist &lt;pid&gt;</code> + list\n"
        f"<code>/kho</code> hoặc <code>/kho &lt;pid&gt;</code>\n\n"
        f"📌 <b>LỆNH TIỀN / USER:</b>\n"
        f"<code>/addmoney &lt;user_id&gt; &lt;số_tiền&gt;</code>\n"
        f"<code>/submoney &lt;user_id&gt; &lt;số_tiền&gt;</code>\n"
        f"<code>/setmoney &lt;user_id&gt; &lt;số_tiền&gt;</code>\n"
        f"<code>/checkmoney &lt;user_id&gt;</code>\n"
        f"<code>/allusers</code> - DS toàn bộ user\n"
        f"<code>/finduser &lt;tên&gt;</code> - tìm user\n\n"
        f"📌 <b>KHÁC:</b>\n"
        f"<code>/deltip</code> - xem DS mẹo\n"
        f"<code>/deltip &lt;số&gt;</code> - xoá 1 mẹo\n"
        f"<code>/deltip all confirm</code>\n"
        f"<code>/broadcast &lt;text&gt;</code>\n"
        f"<code>/stats</code>",
        parse_mode='HTML'
    )

# ========== ADD PRODUCT ==========
@bot.message_handler(commands=['addproduct'])
def admin_addproduct(msg):
    if msg.chat.id != ADMIN_ID:
        return
    try:
        content = msg.text.replace('/addproduct', '').strip()
        parts = [p.strip() for p in content.split('|') if p.strip()]
        if len(parts) < 5:
            bot.send_message(ADMIN_ID, "📌 Dùng: <code>/addproduct |pid|ten|gia|loai|mo_ta|link|</code>\nLoại: account / tool / tut / tool_sms", parse_mode='HTML')
            return
        pid = parts[0]
        name = parts[1]
        price = int(parts[2])
        ptype = parts[3].lower()
        desc = parts[4]
        link = parts[5] if len(parts) > 5 else ''
        if ptype not in ['account', 'tool', 'tut', 'tool_sms']:
            bot.send_message(ADMIN_ID, "❌ Loại phải là: account / tool / tut / tool_sms")
            return
        db = load_db()
        if pid in db['products']:
            bot.send_message(ADMIN_ID, f"❌ PID <code>{esc(pid)}</code> đã tồn tại!", parse_mode='HTML')
            return
        db['products'][pid] = {'name': name, 'price': price, 'stock': 0 if ptype == 'account' else 999, 'type': ptype, 'desc': desc, 'link': link}
        if ptype == 'account':
            db['inventory'][pid] = []
        save_db(db)
        bot.send_message(ADMIN_ID, f"✅ <b>ĐÃ THÊM SP</b>\n\nPID: <code>{esc(pid)}</code>\nTên: {esc(name)}\nGiá: {price:,}đ\nLoại: {ptype}", parse_mode='HTML')
    except Exception as e:
        bot.send_message(ADMIN_ID, f"❌ Lỗi: {e}")

# ========== SET PRICE ==========
@bot.message_handler(commands=['setprice'])
def admin_setprice(msg):
    if msg.chat.id != ADMIN_ID:
        return
    try:
        parts = msg.text.split()
        pid = parts[1]
        new_price = int(parts[2])
        db = load_db()
        if pid in db['products']:
            old = db['products'][pid]['price']
            db['products'][pid]['price'] = new_price
            save_db(db)
            bot.send_message(ADMIN_ID, f"✅ Đổi giá <code>{esc(pid)}</code>: {old:,}đ → <b>{new_price:,}đ</b>", parse_mode='HTML')
        else:
            bot.send_message(ADMIN_ID, f"❌ Không tìm thấy <code>{esc(pid)}</code>", parse_mode='HTML')
    except:
        bot.send_message(ADMIN_ID, "📌 Dùng: <code>/setprice &lt;pid&gt; &lt;gia&gt;</code>", parse_mode='HTML')

# ========== DEL PRODUCT ==========
@bot.message_handler(commands=['delproduct'])
def admin_delproduct(msg):
    if msg.chat.id != ADMIN_ID:
        return
    try:
        pid = msg.text.split()[1]
        db = load_db()
        if pid in db['products']:
            name = db['products'][pid]['name']
            del db['products'][pid]
            if pid in db['inventory']:
                del db['inventory'][pid]
            save_db(db)
            bot.send_message(ADMIN_ID, f"✅ Đã xoá: <b>{esc(name)}</b>", parse_mode='HTML')
        else:
            bot.send_message(ADMIN_ID, f"❌ Không tìm thấy <code>{esc(pid)}</code>", parse_mode='HTML')
    except:
        bot.send_message(ADMIN_ID, "📌 Dùng: <code>/delproduct &lt;pid&gt;</code>", parse_mode='HTML')

# ========== DEL ALL ==========
@bot.message_handler(commands=['delall'])
def admin_delall(msg):
    if msg.chat.id != ADMIN_ID:
        return
    parts = msg.text.split()
    if len(parts) < 2 or parts[1] != 'confirm':
        bot.send_message(
            ADMIN_ID,
            "⚠️ <b>CẢNH BÁO</b>\n\n"
            "Lệnh này sẽ XOÁ TOÀN BỘ sản phẩm + kho hàng + đơn chờ.\n"
            "Không thể hoàn tác!\n\n"
            "Nếu chắc chắn, gõ:\n"
            "<code>/delall confirm</code>",
            parse_mode='HTML'
        )
        return
    db = load_db()
    n_prod = len(db['products'])
    n_inv = sum(len(v) for v in db['inventory'].values())
    n_pending = len(db['pending'])
    db['products'] = {}
    db['inventory'] = {}
    db['pending'] = {}
    save_db(db)
    bot.send_message(
        ADMIN_ID,
        f"✅ <b>ĐÃ XOÁ TOÀN BỘ</b>\n\n"
        f"🗑 Sản phẩm: {n_prod}\n"
        f"🗑 Acc trong kho: {n_inv}\n"
        f"🗑 Đơn chờ: {n_pending}\n\n"
        f"⚠️ Đơn đã hoàn thành vẫn giữ nguyên.",
        parse_mode='HTML'
    )

# ============================================================
# ============== 💰 LỆNH TIỀN / USER MỚI ==============
# ============================================================

# ========== /addmoney ==========
@bot.message_handler(commands=['addmoney'])
def admin_addmoney(msg):
    if msg.chat.id != ADMIN_ID:
        return
    try:
        parts = msg.text.split()
        if len(parts) < 3:
            bot.send_message(ADMIN_ID, "📌 Dùng: <code>/addmoney &lt;user_id&gt; &lt;số_tiền&gt;</code>\nVD: <code>/addmoney 6780308119 50000</code>", parse_mode='HTML')
            return
        target = parts[1].strip()
        amount = int(parts[2])
        if amount <= 0:
            bot.send_message(ADMIN_ID, "❌ Số tiền phải > 0!")
            return

        uid = find_user_id(target)
        if not uid:
            bot.send_message(ADMIN_ID, f"❌ Không tìm thấy user: <code>{esc(target)}</code>\n\n💡 Dùng /allusers để xem DS", parse_mode='HTML')
            return

        db = load_db()
        old_balance = db['users'][uid].get('balance', 0)
        db['users'][uid]['balance'] = old_balance + amount
        new_balance = db['users'][uid]['balance']
        save_db(db)

        # Thông báo cho user
        try:
            bot.send_message(
                int(uid),
                f"💰 <b>BẠN ĐƯỢC CỘNG TIỀN</b>\n\n"
                f"💵 Số tiền: <b>+{amount:,}đ</b>\n"
                f"💰 Số dư mới: <b>{new_balance:,}đ</b>\n\n"
                f"📌 Cảm ơn bạn đã ủng hộ shop!",
                parse_mode='HTML'
            )
        except Exception as e:
            print(f"Noti user error: {e}")

        bot.send_message(
            ADMIN_ID,
            f"✅ <b>ĐÃ CỘNG TIỀN</b>\n\n"
            f"👤 User: <code>{uid}</code> ({esc(db['users'][uid].get('name', 'N/A'))})\n"
            f"💰 Trước: {old_balance:,}đ\n"
            f"➕ Cộng: <b>+{amount:,}đ</b>\n"
            f"💵 Sau: <b>{new_balance:,}đ</b>",
            parse_mode='HTML'
        )
    except ValueError:
        bot.send_message(ADMIN_ID, "❌ Số tiền phải là số nguyên!")
    except Exception as e:
        bot.send_message(ADMIN_ID, f"❌ Lỗi: {e}")

# ========== /submoney ==========
@bot.message_handler(commands=['submoney'])
def admin_submoney(msg):
    if msg.chat.id != ADMIN_ID:
        return
    try:
        parts = msg.text.split()
        if len(parts) < 3:
            bot.send_message(ADMIN_ID, "📌 Dùng: <code>/submoney &lt;user_id&gt; &lt;số_tiền&gt;</code>", parse_mode='HTML')
            return
        target = parts[1].strip()
        amount = int(parts[2])
        if amount <= 0:
            bot.send_message(ADMIN_ID, "❌ Số tiền phải > 0!")
            return

        uid = find_user_id(target)
        if not uid:
            bot.send_message(ADMIN_ID, f"❌ Không tìm thấy user: <code>{esc(target)}</code>", parse_mode='HTML')
            return

        db = load_db()
        old_balance = db['users'][uid].get('balance', 0)
        if old_balance < amount:
            bot.send_message(ADMIN_ID, f"⚠️ User chỉ có {old_balance:,}đ, không đủ để trừ {amount:,}đ!")
            return
        db['users'][uid]['balance'] = old_balance - amount
        new_balance = db['users'][uid]['balance']
        save_db(db)

        try:
            bot.send_message(
                int(uid),
                f"⚠️ <b>SỐ DƯ BỊ TRỪ</b>\n\n"
                f"💵 Số tiền: <b>-{amount:,}đ</b>\n"
                f"💰 Số dư mới: <b>{new_balance:,}đ</b>\n\n"
                f"📌 Liên hệ admin nếu có thắc mắc!",
                parse_mode='HTML'
            )
        except Exception as e:
            print(f"Noti user error: {e}")

        bot.send_message(
            ADMIN_ID,
            f"✅ <b>ĐÃ TRỪ TIỀN</b>\n\n"
            f"👤 User: <code>{uid}</code>\n"
            f"💰 Trước: {old_balance:,}đ\n"
            f"➖ Trừ: <b>-{amount:,}đ</b>\n"
            f"💵 Sau: <b>{new_balance:,}đ</b>",
            parse_mode='HTML'
        )
    except ValueError:
        bot.send_message(ADMIN_ID, "❌ Số tiền phải là số nguyên!")
    except Exception as e:
        bot.send_message(ADMIN_ID, f"❌ Lỗi: {e}")

# ========== /setmoney ==========
@bot.message_handler(commands=['setmoney'])
def admin_setmoney(msg):
    if msg.chat.id != ADMIN_ID:
        return
    try:
        parts = msg.text.split()
        if len(parts) < 3:
            bot.send_message(ADMIN_ID, "📌 Dùng: <code>/setmoney &lt;user_id&gt; &lt;số_tiền&gt;</code>", parse_mode='HTML')
            return
        target = parts[1].strip()
        amount = int(parts[2])
        if amount < 0:
            bot.send_message(ADMIN_ID, "❌ Số tiền phải >= 0!")
            return

        uid = find_user_id(target)
        if not uid:
            bot.send_message(ADMIN_ID, f"❌ Không tìm thấy user: <code>{esc(target)}</code>", parse_mode='HTML')
            return

        db = load_db()
        old_balance = db['users'][uid].get('balance', 0)
        db['users'][uid]['balance'] = amount
        save_db(db)

        try:
            bot.send_message(
                int(uid),
                f"⚙️ <b>SỐ DƯ ĐÃ ĐƯỢC CẬP NHẬT</b>\n\n"
                f"💰 Số dư mới: <b>{amount:,}đ</b>",
                parse_mode='HTML'
            )
        except Exception as e:
            print(f"Noti user error: {e}")

        bot.send_message(
            ADMIN_ID,
            f"✅ <b>ĐÃ SET SỐ DƯ</b>\n\n"
            f"👤 User: <code>{uid}</code>\n"
            f"💰 Trước: {old_balance:,}đ\n"
            f"💵 Sau: <b>{amount:,}đ</b>",
            parse_mode='HTML'
        )
    except ValueError:
        bot.send_message(ADMIN_ID, "❌ Số tiền phải là số nguyên!")
    except Exception as e:
        bot.send_message(ADMIN_ID, f"❌ Lỗi: {e}")

# ========== /checkmoney ==========
@bot.message_handler(commands=['checkmoney'])
def admin_checkmoney(msg):
    if msg.chat.id != ADMIN_ID:
        return
    try:
        parts = msg.text.split()
        if len(parts) < 2:
            bot.send_message(ADMIN_ID, "📌 Dùng: <code>/checkmoney &lt;user_id&gt;</code>", parse_mode='HTML')
            return
        target = parts[1].strip()
        uid = find_user_id(target)
        if not uid:
            bot.send_message(ADMIN_ID, f"❌ Không tìm thấy user: <code>{esc(target)}</code>", parse_mode='HTML')
            return
        db = load_db()
        u = db['users'][uid]
        ref_count = sum(1 for x in db['users'].values() if x.get('referred_by') == uid)
        total_spent = sum(o['price'] for o in db['orders'] if str(o.get('chat_id')) == uid and o['status'] == 'completed')
        bot.send_message(
            ADMIN_ID,
            f"👤 <b>THÔNG TIN USER</b>\n\n"
            f"🆔 ID: <code>{uid}</code>\n"
            f"📛 Tên: {esc(u.get('name', 'N/A'))}\n"
            f"💰 Số dư: <b>{u.get('balance', 0):,}đ</b>\n"
            f"👥 Đã giới thiệu: <b>{ref_count}</b> người\n"
            f"🛍 Tổng chi tiêu: <b>{total_spent:,}đ</b>\n"
            f"📅 Tham gia: {esc(u.get('joined', 'N/A')[:19])}",
            parse_mode='HTML'
        )
    except Exception as e:
        bot.send_message(ADMIN_ID, f"❌ Lỗi: {e}")

# ========== /allusers ==========
@bot.message_handler(commands=['allusers'])
def admin_allusers(msg):
    if msg.chat.id != ADMIN_ID:
        return
    db = load_db()
    users = db['users']
    if not users:
        bot.send_message(ADMIN_ID, "📭 Chưa có user nào!")
        return

    # Sắp xếp theo số dư giảm dần
    sorted_users = sorted(users.items(), key=lambda x: x[1].get('balance', 0), reverse=True)

    text = f"👥 <b>DANH SÁCH USERS</b> ({len(sorted_users)})\n\n"
    for i, (uid, u) in enumerate(sorted_users[:50], 1):
        bal = u.get('balance', 0)
        name = u.get('name', 'N/A')
        text += f"{i}. <code>{uid}</code> - {esc(name)} - <b>{bal:,}đ</b>\n"
    if len(sorted_users) > 50:
        text += f"\n... và {len(sorted_users) - 50} user khác"
    text += f"\n\n💡 Dùng /checkmoney &lt;id&gt; để xem chi tiết"

    bot.send_message(ADMIN_ID, text, parse_mode='HTML')

# ========== /finduser ==========
@bot.message_handler(commands=['finduser'])
def admin_finduser(msg):
    if msg.chat.id != ADMIN_ID:
        return
    try:
        parts = msg.text.split(maxsplit=1)
        if len(parts) < 2:
            bot.send_message(ADMIN_ID, "📌 Dùng: <code>/finduser &lt;tên&gt;</code>", parse_mode='HTML')
            return
        query = parts[1].strip()
        db = load_db()
        results = []
        for uid, u in db['users'].items():
            name = u.get('name', '')
            if query.lower() in name.lower() or query == uid:
                results.append((uid, u))
        if not results:
            bot.send_message(ADMIN_ID, f"❌ Không tìm thấy user nào khớp: <code>{esc(query)}</code>", parse_mode='HTML')
            return
        text = f"🔍 <b>KẾT QUẢ TÌM KIẾM</b> ({len(results)})\n\n"
        for uid, u in results[:20]:
            bal = u.get('balance', 0)
            name = u.get('name', 'N/A')
            text += f"🆔 <code>{uid}</code>\n📛 {esc(name)}\n💰 <b>{bal:,}đ</b>\n\n"
        bot.send_message(ADMIN_ID, text, parse_mode='HTML')
    except Exception as e:
        bot.send_message(ADMIN_ID, f"❌ Lỗi: {e}")

# ============================================================
# ============== CÁC LỆNH ADMIN KHÁC ==============
# ============================================================

# ========== DEL TIP ==========
@bot.message_handler(commands=['deltip'])
def admin_deltip(msg):
    if msg.chat.id != ADMIN_ID:
        return
    parts = msg.text.split()
    if len(parts) < 2:
        db = load_db()
        tips = db.get('tips', [])
        if not tips:
            bot.send_message(ADMIN_ID, "📭 Không có mẹo nào để xoá!")
            return
        text = "📋 <b>DANH SÁCH MẸO</b>\n\n"
        for i, tip in enumerate(tips):
            text += f"{i}. {esc(tip['title'])}\n"
        text += "\n📌 Xoá 1 mẹo: <code>/deltip &lt;số&gt;</code>\n"
        text += "📌 Xoá tất cả: <code>/deltip all confirm</code>"
        bot.send_message(ADMIN_ID, text, parse_mode='HTML')
        return

    if parts[1] == 'all':
        if len(parts) < 3 or parts[2] != 'confirm':
            bot.send_message(ADMIN_ID, "⚠️ Gõ <code>/deltip all confirm</code> để xoá TẤT CẢ mẹo.", parse_mode='HTML')
            return
        db = load_db()
        n = len(db.get('tips', []))
        db['tips'] = []
        save_db(db)
        bot.send_message(ADMIN_ID, f"✅ Đã xoá <b>{n}</b> mẹo!", parse_mode='HTML')
        return

    try:
        idx = int(parts[1])
        db = load_db()
        tips = db.get('tips', [])
        if idx < 0 or idx >= len(tips):
            bot.send_message(ADMIN_ID, f"❌ Số không hợp lệ! Có {len(tips)} mẹo (0 → {len(tips)-1}).")
            return
        removed = tips.pop(idx)
        db['tips'] = tips
        save_db(db)
        bot.send_message(ADMIN_ID, f"✅ Đã xoá mẹo: <b>{esc(removed['title'])}</b>", parse_mode='HTML')
    except:
        bot.send_message(ADMIN_ID, "📌 Dùng: <code>/deltip &lt;số&gt;</code> hoặc <code>/deltip all confirm</code>", parse_mode='HTML')

# ========== ADD ACC ==========
@bot.message_handler(commands=['addacc'])
def admin_addacc(msg):
    if msg.chat.id != ADMIN_ID:
        return
    try:
        parts = msg.text.split(' ', 2)
        pid = parts[1]
        acc = parts[2]
        db = load_db()
        if pid not in db['products']:
            bot.send_message(ADMIN_ID, f"❌ SP <code>{esc(pid)}</code> không tồn tại!", parse_mode='HTML')
            return
        if pid not in db['inventory']:
            db['inventory'][pid] = []
        db['inventory'][pid].append(acc)
        db['products'][pid]['stock'] = len(db['inventory'][pid])
        save_db(db)
        bot.send_message(ADMIN_ID, f"✅ Đã thêm acc vào <code>{esc(pid)}</code>\n📦 Kho: <b>{db['products'][pid]['stock']}</b>", parse_mode='HTML')
    except:
        bot.send_message(ADMIN_ID, "📌 Dùng: <code>/addacc &lt;pid&gt; &lt;acc&gt;</code>", parse_mode='HTML')

# ========== ADD LIST ==========
@bot.message_handler(commands=['addlist'])
def admin_addlist(msg):
    if msg.chat.id != ADMIN_ID:
        return
    try:
        lines = msg.text.split('\n')
        first = lines[0].strip().split()
        if len(first) < 2:
            bot.send_message(ADMIN_ID, "📌 Dùng:\n<code>/addlist &lt;pid&gt;\ntk1|mk1|nam1|2fa1|cookie1\ntk2|mk2|nam2|2fa2|cookie2</code>", parse_mode='HTML')
            return
        pid = first[1].strip()
        acc_lines = [l.strip() for l in lines[1:] if l.strip()]
        if not acc_lines:
            bot.send_message(ADMIN_ID, "❌ Không có acc!")
            return
        db = load_db()
        if pid not in db['products']:
            bot.send_message(ADMIN_ID, f"❌ SP <code>{esc(pid)}</code> không tồn tại!", parse_mode='HTML')
            return
        if pid not in db['inventory']:
            db['inventory'][pid] = []
        added = 0
        for acc_line in acc_lines:
            parts = acc_line.split('|')
            if len(parts) < 2:
                continue
            tk = parts[0].strip()
            mk = parts[1].strip() if len(parts) > 1 else ''
            nam = parts[2].strip() if len(parts) > 2 else ''
            fa2 = parts[3].strip() if len(parts) > 3 else ''
            cookie = parts[4].strip() if len(parts) > 4 else ''
            db['inventory'][pid].append(f"{tk}|{mk}|{nam}|{fa2}|{cookie}")
            added += 1
        db['products'][pid]['stock'] = len(db['inventory'][pid])
        save_db(db)
        bot.send_message(ADMIN_ID, f"✅ <b>ĐÃ THÊM {added} ACC</b>\n\n🛍 SP: {esc(db['products'][pid]['name'])}\n📦 Tổng kho: <b>{db['products'][pid]['stock']}</b>", parse_mode='HTML')
    except Exception as e:
        bot.send_message(ADMIN_ID, f"❌ Lỗi: {e}")

# ========== KHO ==========
@bot.message_handler(commands=['kho'])
def admin_kho(msg):
    if msg.chat.id != ADMIN_ID:
        return
    try:
        parts = msg.text.split()
        pid = parts[1] if len(parts) > 1 else None
        db = load_db()
        if pid:
            if pid not in db['inventory']:
                bot.send_message(ADMIN_ID, f"❌ Không có kho <code>{esc(pid)}</code>", parse_mode='HTML')
                return
            inv = db['inventory'][pid]
            if not inv:
                bot.send_message(ADMIN_ID, f"📦 Kho <code>{esc(pid)}</code> trống", parse_mode='HTML')
                return
            text = f"📦 <b>KHO: {esc(pid)} ({len(inv)})</b>\n\n"
            for i, acc in enumerate(inv[:30], 1):
                p = acc.split('|')
                tk = p[0] if len(p) > 0 else ''
                nam = p[2] if len(p) > 2 else ''
                has2fa = '✅' if len(p) > 3 and p[3] else '❌'
                hasck = '✅' if len(p) > 4 and p[4] else '❌'
                text += f"{i}. <code>{esc(tk)}</code> | {esc(nam)} | 2FA:{has2fa} | CK:{hasck}\n"
            if len(inv) > 30:
                text += f"\n... và {len(inv) - 30} acc khác"
            bot.send_message(ADMIN_ID, text, parse_mode='HTML')
        else:
            text = "📦 <b>TẤT CẢ KHO</b>\n\n"
            total = 0
            for pid, inv in db['inventory'].items():
                name = db['products'].get(pid, {}).get('name', pid)
                text += f"• {esc(name)}: <b>{len(inv)}</b> acc\n"
                total += len(inv)
            text += f"\n🧮 <b>TỔNG: {total} acc</b>"
            bot.send_message(ADMIN_ID, text, parse_mode='HTML')
    except Exception as e:
        bot.send_message(ADMIN_ID, f"❌ Lỗi: {e}")

# ========== BROADCAST ==========
@bot.message_handler(commands=['broadcast'])
def admin_broadcast(msg):
    if msg.chat.id != ADMIN_ID:
        return
    content = msg.text.replace('/broadcast', '').strip()
    if not content:
        bot.send_message(ADMIN_ID, "📌 Dùng: <code>/broadcast &lt;nội dung&gt;</code>", parse_mode='HTML')
        return
    db = load_db()
    users = list(db['users'].keys())
    success = 0
    for uid in users:
        try:
            bot.send_message(int(uid), f"📢 <b>THÔNG BÁO</b>\n\n{esc(content)}", parse_mode='HTML')
            success += 1
        except:
            pass
    bot.send_message(ADMIN_ID, f"✅ Đã gửi đến {success}/{len(users)}", parse_mode='HTML')

# ========== STATS ==========
@bot.message_handler(commands=['stats'])
def admin_stats(msg):
    if msg.chat.id != ADMIN_ID:
        return
    db = load_db()
    text = "📊 <b>THỐNG KÊ</b>\n\n"
    for pid, p in db['products'].items():
        sold = sum(1 for o in db['orders'] if o['product_id'] == pid and o['status'] == 'completed')
        text += f"🛍 <b>{esc(p['name'])}</b>\n   💰 {p['price']:,}đ | ✅ Bán: {sold} | 📦 Kho: {p['stock']}\n"
    total = sum(o['price'] for o in db['orders'] if o['status'] == 'completed')
    total_balance = sum(u.get('balance', 0) for u in db['users'].values())
    text += f"\n💵 <b>TỔNG: {total:,}đ</b>\n👥 Users: {len(db['users'])}\n💰 Tổng số dư ref: <b>{total_balance:,}đ</b>"
    bot.send_message(ADMIN_ID, text, parse_mode='HTML')

# ========== BACK MENU ==========
@bot.callback_query_handler(func=lambda c: c.data == 'back_menu')
def back_menu(call):
    try:
        bot.edit_message_text("🏪 <b>HDM SHOP</b>\n\n👇 Chọn sản phẩm:", call.message.chat.id, call.message.message_id, parse_mode='HTML', reply_markup=main_menu())
    except Exception as e:
        print(f"Back menu error: {e}")

# ========== MAIN ==========
if __name__ == '__main__':
    def run_bot():
        while True:
            try:
                bot.polling(none_stop=True, timeout=60)
            except Exception as e:
                print(f'Bot error: {e}')
                time.sleep(5)
    threading.Thread(target=run_bot, daemon=True).start()
    print("🏪 HDM SHOP BOT đang chạy...")
    print(f"👑 Admin: {ADMIN_ID}")
    print(f"🏦 Bank: {BANK_INFO['bank']} - {BANK_INFO['account']}")
    print(f"🔗 Ref bonus: +{REF_BONUS}đ/người")
    print(f"📱 Tool SMS: {'✅ ONLINE' if SMS_TOOL_AVAILABLE else '❌ OFFLINE'}")
    port = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=port)
