import telebot
from telebot import types
from telebot.types import BotCommand
import json, os, random, string, html
from datetime import datetime
from flask import Flask, request

BOT_TOKEN = os.environ.get('BOT_TOKEN', '8962422980:AAERSCHiswb_rb6PzRSZ094EVdwnJQ0YPdw')
ADMIN_ID = 6780308119
TELEGRAM_SUPPORT = '@spmxhhdm'
BANK_INFO = {'bank': 'TPBank', 'account': '10005490787', 'owner': 'DO HAI DANG'}
BOT_USERNAME = 'hdm_shop_bot'  # ⚠️ ĐỔI thành username bot thật của bạn (không có @)
REF_BONUS = 400  # Số tiền cộng cho mỗi người đăng ký qua link
DB_FILE = 'shop_data.json'

def esc(s):
    """Escape ký tự đặc biệt cho HTML parse_mode"""
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

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

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

@bot.message_handler(commands=['start'])
def cmd_start(msg):
    chat_id = msg.chat.id
    name = msg.from_user.first_name or 'bạn'
    db = load_db()
    uid = str(chat_id)

    # Xử lý referral: /start ref_<id>
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

        # Cộng tiền cho người giới thiệu (mỗi người +400đ)
        if ref_by and ref_by != uid and ref_by in db['users']:
            db['users'][ref_by]['balance'] = db['users'][ref_by].get('balance', 0) + REF_BONUS
            new_balance = db['users'][ref_by]['balance']
            # Đếm tổng số người đã giới thiệu
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
        "• Càng nhiều người → càng nhiều tiền\n"
        "• Gõ /ref để lấy link giới thiệu\n"
        "• Gõ /balance để xem số dư\n\n"
        f"💬 Hỗ trợ: {esc(TELEGRAM_SUPPORT)}",
        parse_mode='HTML'
    )

@bot.message_handler(commands=['shop'])
def cmd_shop(msg):
    db = load_db()
    if not db['products']:
        bot.send_message(msg.chat.id, "⏳ Shop đang cập nhật!")
        return
    bot.send_message(msg.chat.id, "🏪 <b>HDM SHOP</b>\n\n👇 Chọn sản phẩm:", parse_mode='HTML', reply_markup=main_menu())

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
        order['status'] = 'completed'
        order['completed_at'] = datetime.now().isoformat()
        db['orders'].append(order)
        del db['pending'][order_code]
        save_db(db)
        bot.send_message(ADMIN_ID, f"✅ <b>ĐƠN TỰ ĐỘNG DUYỆT</b>\n\n🔖 Mã: {order_code}\n@{order['username']}\n🛍 SP: {esc(p['name'])}\n💰 Tiền: {order['price']:,}đ", parse_mode='HTML')
    except Exception as e:
        print(f'Auto deliver error: {e}')
        bot.send_message(ADMIN_ID, f'❌ Lỗi đơn {order_code}: {e}')

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
        bot.answer_callback_query(call.id, '✅ Đã từ chối!')

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

@bot.message_handler(commands=['admin'])
def admin_panel(msg):
    if msg.chat.id != ADMIN_ID:
        return
    db = load_db()
    total = sum(o['price'] for o in db['orders'] if o['status'] == 'completed')
    total_balance = sum(u.get('balance', 0) for u in db['users'].values())
    bot.send_message(
        ADMIN_ID,
        f"👑 <b>ADMIN PANEL</b>\n\n"
        f"👥 Users: {len(db['users'])}\n"
        f"🛍 SP: {len(db['products'])}\n"
        f"✅ Đơn xong: {len(db['orders'])}\n"
        f"⏳ Chờ: {len(db['pending'])}\n"
        f"💰 Doanh thu: <b>{total:,}đ</b>\n"
        f"💵 Tổng số dư ref: <b>{total_balance:,}đ</b>\n\n"
        f"📌 <b>LỆNH:</b>\n"
        f"<code>/addproduct |pid|ten|gia|loai|mo_ta|link|</code>\n"
        f"<code>/setprice &lt;pid&gt; &lt;gia&gt;</code>\n"
        f"<code>/delproduct &lt;pid&gt;</code>\n"
        f"<code>/delall confirm</code> - xoá tất cả SP\n"
        f"<code>/addacc &lt;pid&gt; &lt;acc&gt;</code>\n"
        f"<code>/addlist &lt;pid&gt;</code> + list\n"
        f"<code>/kho</code> hoặc <code>/kho &lt;pid&gt;</code>\n"
        f"<code>/deltip</code> - xem DS mẹo\n"
        f"<code>/deltip &lt;số&gt;</code> - xoá 1 mẹo\n"
        f"<code>/deltip all confirm</code> - xoá tất cả mẹo\n"
        f"<code>/broadcast &lt;text&gt;</code>\n"
        f"<code>/stats</code>",
        parse_mode='HTML'
    )

@bot.message_handler(commands=['addproduct'])
def admin_addproduct(msg):
    if msg.chat.id != ADMIN_ID:
        return
    try:
        content = msg.text.replace('/addproduct', '').strip()
        parts = [p.strip() for p in content.split('|') if p.strip()]
        if len(parts) < 5:
            bot.send_message(ADMIN_ID, "📌 Dùng: <code>/addproduct |pid|ten|gia|loai|mo_ta|link|</code>\nLoại: account / tool / tut", parse_mode='HTML')
            return
        pid = parts[0]
        name = parts[1]
        price = int(parts[2])
        ptype = parts[3].lower()
        desc = parts[4]
        link = parts[5] if len(parts) > 5 else ''
        if ptype not in ['account', 'tool', 'tut']:
            bot.send_message(ADMIN_ID, "❌ Loại phải là: account / tool / tut")
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
        f"⚠️ Đơn đã hoàn thành trong <code>orders</code> vẫn giữ nguyên.",
        parse_mode='HTML'
    )

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

@bot.callback_query_handler(func=lambda c: c.data == 'back_menu')
def back_menu(call):
    try:
        bot.edit_message_text("🏪 <b>HDM SHOP</b>\n\n👇 Chọn sản phẩm:", call.message.chat.id, call.message.message_id, parse_mode='HTML', reply_markup=main_menu())
    except Exception as e:
        print(f"Back menu error: {e}")

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
    print("🏪 HDM SHOP BOT đang chạy...")
    print(f"👑 Admin: {ADMIN_ID}")
    print(f"🏦 Bank: {BANK_INFO['bank']} - {BANK_INFO['account']}")
    print(f"🔗 Ref bonus: +{REF_BONUS}đ/người")
    port = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=port)
