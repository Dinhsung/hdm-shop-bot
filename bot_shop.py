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
    print(f"[WARN] Không tìm thấy sms_tool.py — spam SMS sẽ tắt ({e})")

# ========== CẤU HÌNH ==========
BOT_TOKEN = os.environ.get('BOT_TOKEN', '8962422980:AAERSCHiswb_rb6PzRSZ094EVdwnJQ0YPdw')
ADMIN_ID = 6780308119
TELEGRAM_SUPPORT = '@spmxhhdm'
BANK_INFO = {'bank': 'TPBank', 'account': '10005490787', 'owner': 'DO HAI DANG'}
BOT_USERNAME = 'hdm_shop_bot'
REF_BONUS = 400
DB_FILE = 'shop_data.json'

# ========== STATE ==========
sms_waiting = {}              # {chat_id: {...}}
nap_waiting = {}              # {chat_id: {...}}
admin_content_waiting = {}    # {admin_id: {'pid': 'xxx', 'type': 'tut'/'tool'}}

# ========== HELPER ==========
def esc(s):
    return html.escape(str(s), quote=False)

def load_db():
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, 'w', encoding='utf-8') as f:
            json.dump({
                'products': {}, 'inventory': {}, 'pending': {}, 'orders': [],
                'users': {}, 'tips': [], 'nap_history': []
            }, f, ensure_ascii=False, indent=2)
    try:
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            db = json.load(f)
            db.setdefault('products', {})
            db.setdefault('inventory', {})
            db.setdefault('pending', {})
            db.setdefault('orders', [])
            db.setdefault('users', {})
            db.setdefault('tips', [])
            db.setdefault('nap_history', [])
            return db
    except:
        return {'products': {}, 'inventory': {}, 'pending': {}, 'orders': [], 'users': {}, 'tips': [], 'nap_history': []}

def save_db(data):
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def find_user_id(query):
    db = load_db()
    query = query.strip().lstrip('@')
    if query.isdigit():
        return query if query in db['users'] else None
    for uid, u in db['users'].items():
        if u.get('name', '').lower() == query.lower():
            return uid
    return None

def stock_text(p):
    if p.get('type') == 'account':
        s = p.get('stock', 0)
        return f"[Còn {s}]" if s > 0 else "[Hết]"
    return "[∞]"

def stock_text_full(p):
    if p.get('type') == 'account':
        s = p.get('stock', 0)
        return f"✅ Còn {s} acc" if s > 0 else "❌ Hết hàng"
    return "♾ Vô hạn (mua bao nhiêu cũng được)"

def can_buy(p, balance=0):
    if p.get('type') == 'account':
        return p.get('stock', 0) > 0 and balance >= p['price']
    return balance >= p['price']

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# ========== SET COMMANDS ==========
try:
    bot.set_my_commands([
        BotCommand('start', '🏠 Menu chính'),
        BotCommand('help', '📖 Hướng dẫn'),
        BotCommand('shop', '🛒 Cửa hàng'),
        BotCommand('nap', '💰 Nạp tiền vào ví'),
        BotCommand('balance', '💵 Số dư'),
        BotCommand('history', '📜 Lịch sử'),
        BotCommand('tips', '🎁 Mẹo Free'),
        BotCommand('ref', '🔗 Giới thiệu +400đ'),
        BotCommand('support', '💬 Hỗ trợ'),
    ])
except Exception as e:
    print(f"Set commands error: {e}")

# ========== MENU ==========
def main_menu():
    db = load_db()
    markup = types.InlineKeyboardMarkup(row_width=2)
    for pid, p in db['products'].items():
        markup.add(types.InlineKeyboardButton(
            f"🛒 {p['name']} - {p['price']:,}đ {stock_text(p)}",
            callback_data=f'product_{pid}'
        ))
    markup.add(
        types.InlineKeyboardButton('💰 Nạp tiền', callback_data='nap_tien'),
        types.InlineKeyboardButton('💵 Số dư', callback_data='show_balance')
    )
    markup.add(
        types.InlineKeyboardButton('📜 Lịch sử', callback_data='history'),
        types.InlineKeyboardButton('🎁 Mẹo Free', callback_data='cat_tips')
    )
    markup.add(
        types.InlineKeyboardButton(f'🔗 Giới thiệu +{REF_BONUS}đ', callback_data='show_ref'),
        types.InlineKeyboardButton('💬 Hỗ trợ', url=f'https://t.me/{TELEGRAM_SUPPORT[1:]}')
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
        bot.send_message(chat_id, f"👋 Chào <b>{esc(name)}</b>!\n\n🏪 <b>HDM SHOP</b>\n⏳ Shop đang cập nhật...", parse_mode='HTML')
        return
    balance = db['users'][uid].get('balance', 0)
    bot.send_message(
        chat_id,
        f"👋 Chào <b>{esc(name)}</b>!\n\n"
        f"🏪 <b>HDM SHOP - Cửa hàng số</b>\n"
        f"⚡ Tự động duyệt - Giao hàng ngay\n"
        f"💵 Số dư: <b>{balance:,}đ</b>\n\n"
        f"👇 Chọn thao tác:",
        parse_mode='HTML',
        reply_markup=main_menu()
    )

# ========== HELP ==========
@bot.message_handler(commands=['help'])
def cmd_help(msg):
    bot.send_message(
        msg.chat.id,
        "📖 <b>HƯỚNG DẪN</b>\n\n"
        "1️⃣ <b>Nạp tiền:</b> Bấm 💰 Nạp tiền → nhập số → CK\n"
        "2️⃣ <b>Mua hàng:</b> Bấm SP → MUA BẰNG SỐ DƯ\n"
        "3️⃣ <b>Nhận hàng:</b> Bot gửi ngay lập tức\n\n"
        "🎁 <b>GIỚI THIỆU BẠN BÈ</b>\n"
        f"• Mỗi người mới qua link → <b>+{REF_BONUS:,}đ</b>\n"
        "• Gõ /ref để lấy link\n\n"
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
    balance = db['users'].get(str(msg.chat.id), {}).get('balance', 0)
    bot.send_message(
        msg.chat.id,
        f"🏪 <b>HDM SHOP</b>\n💵 Số dư: <b>{balance:,}đ</b>\n\n👇 Chọn sản phẩm:",
        parse_mode='HTML',
        reply_markup=main_menu()
    )

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
        bot.send_message(chat_id, "⚠️ Gõ /start trước!")
        return
    ref_link = f"https://t.me/{BOT_USERNAME}?start=ref_{uid}"
    balance = db['users'][uid].get('balance', 0)
    count = sum(1 for u in db['users'].values() if u.get('referred_by') == uid)
    bot.send_message(
        chat_id,
        f"🎁 <b>GIỚI THIỆU BẠN BÈ</b>\n\n"
        f"🔗 Link:\n<code>{ref_link}</code>\n\n"
        f"💰 Mỗi người → <b>+{REF_BONUS:,}đ</b>\n"
        f"👥 Đã giới thiệu: <b>{count}</b> người\n"
        f"💵 Số dư: <b>{balance:,}đ</b>",
        parse_mode='HTML'
    )

# ========== BALANCE ==========
@bot.message_handler(commands=['balance'])
def cmd_balance(msg):
    chat_id = msg.chat.id
    db = load_db()
    uid = str(chat_id)
    if uid not in db['users']:
        bot.send_message(chat_id, "⚠️ Gõ /start trước!")
        return
    balance = db['users'][uid].get('balance', 0)
    count = sum(1 for u in db['users'].values() if u.get('referred_by') == uid)
    bot.send_message(
        chat_id,
        f"💵 <b>SỐ DƯ CỦA BẠN</b>\n\n"
        f"💰 Số dư: <b>{balance:,}đ</b>\n"
        f"👥 Đã giới thiệu: <b>{count}</b> người\n\n"
        f"📌 Nạp tiền: /nap",
        parse_mode='HTML'
    )

# ========== NẠP TIỀN ==========
@bot.message_handler(commands=['nap'])
def cmd_nap(msg):
    chat_id = msg.chat.id
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton('20,000đ', callback_data='nap_20000'),
        types.InlineKeyboardButton('50,000đ', callback_data='nap_50000'),
        types.InlineKeyboardButton('100,000đ', callback_data='nap_100000'),
        types.InlineKeyboardButton('200,000đ', callback_data='nap_200000'),
        types.InlineKeyboardButton('500,000đ', callback_data='nap_500000'),
        types.InlineKeyboardButton('1,000,000đ', callback_data='nap_1000000'),
    )
    markup.add(
        types.InlineKeyboardButton('✏️ Nhập số khác', callback_data='nap_custom'),
        types.InlineKeyboardButton('⬅️ Quay lại', callback_data='back_menu')
    )
    bot.send_message(chat_id, "💰 <b>NẠP TIỀN VÀO VÍ</b>\n\n👇 Chọn số tiền muốn nạp:", parse_mode='HTML', reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data == 'nap_tien')
def cb_nap_tien(call):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton('20,000đ', callback_data='nap_20000'),
        types.InlineKeyboardButton('50,000đ', callback_data='nap_50000'),
        types.InlineKeyboardButton('100,000đ', callback_data='nap_100000'),
        types.InlineKeyboardButton('200,000đ', callback_data='nap_200000'),
        types.InlineKeyboardButton('500,000đ', callback_data='nap_500000'),
        types.InlineKeyboardButton('1,000,000đ', callback_data='nap_1000000'),
    )
    markup.add(
        types.InlineKeyboardButton('✏️ Nhập số khác', callback_data='nap_custom'),
        types.InlineKeyboardButton('⬅️ Quay lại', callback_data='back_menu')
    )
    try:
        bot.edit_message_text("💰 <b>NẠP TIỀN VÀO VÍ</b>\n\n👇 Chọn số tiền muốn nạp:", call.message.chat.id, call.message.message_id, parse_mode='HTML', reply_markup=markup)
    except Exception as e:
        print(f"nap_tien error: {e}")

@bot.callback_query_handler(func=lambda c: c.data.startswith('nap_') and c.data not in ['nap_tien', 'nap_custom'])
def cb_nap_amount(call):
    chat_id = call.from_user.id
    try:
        amount = int(call.data.replace('nap_', ''))
    except:
        return
    create_nap_qr(chat_id, amount, call.message.chat.id, call.message.message_id)

@bot.callback_query_handler(func=lambda c: c.data == 'nap_custom')
def cb_nap_custom(call):
    chat_id = call.from_user.id
    nap_waiting[chat_id] = {'step': 'amount'}
    bot.send_message(
        chat_id,
        "✏️ <b>NHẬP SỐ TIỀN MUỐN NẠP</b>\n\n"
        "VD: <code>150000</code> (150,000đ)\n"
        "Tối thiểu: 10,000đ\n"
        "Tối đa: 50,000,000đ\n\n"
        "⚠️ Gõ /cancel để huỷ",
        parse_mode='HTML'
    )

@bot.message_handler(func=lambda m: m.chat.id in nap_waiting and nap_waiting[m.chat.id].get('step') == 'amount')
def nap_input_amount(msg):
    chat_id = msg.chat.id
    try:
        amount = int(msg.text.strip().replace(',', '').replace('.', ''))
        if amount < 10000:
            bot.send_message(chat_id, "❌ Tối thiểu 10,000đ! Nhập lại:")
            return
        if amount > 50000000:
            bot.send_message(chat_id, "❌ Tối đa 50,000,000đ! Nhập lại:")
            return
    except:
        bot.send_message(chat_id, "❌ Phải là số! Nhập lại (VD: 150000):")
        return
    del nap_waiting[chat_id]
    create_nap_qr(chat_id, amount, chat_id)

def create_nap_qr(chat_id, amount, send_chat_id, edit_message_id=None):
    db = load_db()
    uid = str(chat_id)
    if uid not in db['users']:
        bot.send_message(send_chat_id, "⚠️ Gõ /start trước!")
        return
    nap_code = 'NAP' + ''.join(random.choices(string.digits, k=6))
    db['pending'][nap_code] = {
        'chat_id': chat_id,
        'username': db['users'][uid].get('name', 'user'),
        'type': 'nap_tien',
        'amount': amount,
        'status': 'awaiting_payment',
        'time': datetime.now().isoformat()
    }
    save_db(db)
    qr_url = (
        f"https://qr.sepay.vn/img"
        f"?acc={BANK_INFO['account']}"
        f"&bank={BANK_INFO['bank']}"
        f"&amount={amount}"
        f"&des={nap_code}"
    )
    caption = (
        f"💰 <b>NẠP TIỀN VÀO VÍ</b>\n\n"
        f"💵 Số tiền: <b>{amount:,}đ</b>\n"
        f"🔖 Mã nạp: <code>{nap_code}</code>\n\n"
        f"🏦 <b>THÔNG TIN CK</b>\n"
        f"NH: <b>{esc(BANK_INFO['bank'])}</b>\n"
        f"STK: <code>{BANK_INFO['account']}</code>\n"
        f"Chủ TK: {esc(BANK_INFO['owner'])}\n"
        f"Số tiền: <b>{amount:,}đ</b>\n"
        f"Nội dung: <code>{nap_code}</code>\n\n"
        f"⚠️ <b>CHUYỂN ĐÚNG SỐ TIỀN + ĐÚNG NỘI DUNG</b>\n"
        f"Bot tự cộng tiền sau 1-2 phút."
    )
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton('✅ Tôi đã CK', callback_data=f'napcheck_{nap_code}'),
        types.InlineKeyboardButton('⬅️ Quay lại', callback_data='back_menu')
    )
    if edit_message_id:
        try:
            bot.delete_message(send_chat_id, edit_message_id)
        except:
            pass
    try:
        bot.send_photo(send_chat_id, qr_url, caption=caption, parse_mode='HTML', reply_markup=markup)
    except Exception as e:
        print(f"Send QR error: {e}")
        bot.send_message(send_chat_id, caption, parse_mode='HTML', reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data.startswith('napcheck_'))
def cb_napcheck(call):
    nap_code = call.data.replace('napcheck_', '')
    db = load_db()
    if nap_code not in db['pending']:
        bot.answer_callback_query(call.id, '❌ Không tìm thấy!')
        return
    order = db['pending'][nap_code]
    order['status'] = 'verifying'
    save_db(db)
    text = (
        f"⏳ <b>ĐANG XÁC MINH</b>\n\n"
        f"🔖 Mã nạp: <code>{nap_code}</code>\n"
        f"💵 Số tiền: {order['amount']:,}đ\n\n"
        f"🔍 Bot đang kiểm tra..."
    )
    try:
        bot.edit_message_caption(text, call.message.chat.id, call.message.message_id, parse_mode='HTML')
    except:
        pass

# ========== REF CALLBACK ==========
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
        f"🔗 Link:\n<code>{ref_link}</code>\n\n"
        f"💰 Mỗi người → <b>+{REF_BONUS:,}đ</b>\n"
        f"👥 Đã giới thiệu: <b>{count}</b> người\n"
        f"💵 Số dư: <b>{balance:,}đ</b>"
    )
    markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton('⬅️ Quay lại', callback_data='back_menu'))
    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode='HTML', reply_markup=markup)
    except Exception as e:
        print(f"cb_show_ref error: {e}")

# ========== BALANCE CALLBACK ==========
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
        f"📌 Nạp tiền để mua hàng!"
    )
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton('💰 Nạp tiền', callback_data='nap_tien'),
        types.InlineKeyboardButton('⬅️ Quay lại', callback_data='back_menu')
    )
    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode='HTML', reply_markup=markup)
    except Exception as e:
        print(f"cb_show_balance error: {e}")

# ========== LỊCH SỬ ==========
@bot.message_handler(commands=['history'])
def cmd_history(msg):
    show_history(msg.chat.id, None, None)

@bot.callback_query_handler(func=lambda c: c.data == 'history')
def cb_history(call):
    show_history(call.from_user.id, call.message.chat.id, call.message.message_id)

def show_history(user_id, chat_id, message_id):
    uid = str(user_id)
    db = load_db()
    my_orders = [o for o in db['orders'] if str(o.get('chat_id')) == uid]
    my_naps = [n for n in db.get('nap_history', []) if str(n.get('chat_id')) == uid]
    text = f"📜 <b>LỊCH SỬ GIAO DỊCH</b>\n\n"
    text += f"🛒 <b>Mua hàng ({len(my_orders)}):</b>\n"
    for o in my_orders[-10:][::-1]:
        text += f"• {esc(o.get('product_name', 'N/A'))} - {o.get('price', 0):,}đ\n"
    if not my_orders:
        text += "• Chưa có\n"
    text += f"\n💰 <b>Nạp tiền ({len(my_naps)}):</b>\n"
    for n in my_naps[-10:][::-1]:
        text += f"• +{n.get('amount', 0):,}đ - {n.get('time', '')[:10]}\n"
    if not my_naps:
        text += "• Chưa có\n"
    markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton('⬅️ Quay lại', callback_data='back_menu'))
    if chat_id and message_id:
        try:
            bot.edit_message_text(text, chat_id, message_id, parse_mode='HTML', reply_markup=markup)
        except Exception as e:
            print(f"history error: {e}")
    else:
        bot.send_message(user_id, text, parse_mode='HTML', reply_markup=markup)

# ========== SHOW PRODUCT ==========
@bot.callback_query_handler(func=lambda c: c.data.startswith('product_'))
def show_product(call):
    pid = call.data.replace('product_', '')
    db = load_db()
    if pid not in db['products']:
        bot.answer_callback_query(call.id, '❌ SP không tồn tại!')
        return
    p = db['products'][pid]
    uid = str(call.from_user.id)
    balance = db['users'].get(uid, {}).get('balance', 0)

    text = (
        f"🛍 <b>{esc(p['name'])}</b>\n\n"
        f"📝 {esc(p['desc'])}\n"
        f"💰 Giá: <b>{p['price']:,}đ</b>\n"
        f"📦 Kho: {stock_text_full(p)}\n"
        f"💵 Số dư của bạn: <b>{balance:,}đ</b>\n\n"
        f"👇 Chọn cách thanh toán:"
    )
    markup = types.InlineKeyboardMarkup(row_width=2)
    if can_buy(p, balance):
        markup.add(types.InlineKeyboardButton('💵 MUA BẰNG SỐ DƯ', callback_data=f'buywallet_{pid}'))
    markup.add(
        types.InlineKeyboardButton('💳 MUA QUA QR', callback_data=f'buy_{pid}'),
        types.InlineKeyboardButton('⬅️ Quay lại', callback_data='back_menu')
    )
    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode='HTML', reply_markup=markup)
    except Exception as e:
        print(f"Edit error: {e}")

# ========== MUA BẰNG VÍ ==========
@bot.callback_query_handler(func=lambda c: c.data.startswith('buywallet_'))
def buy_with_wallet(call):
    pid = call.data.replace('buywallet_', '')
    uid = str(call.from_user.id)
    db = load_db()
    if pid not in db['products']:
        bot.answer_callback_query(call.id, '❌ SP không tồn tại!')
        return
    p = db['products'][pid]
    if p['type'] == 'account' and p.get('stock', 0) <= 0:
        bot.answer_callback_query(call.id, '❌ Hết hàng!')
        return
    if uid not in db['users']:
        bot.answer_callback_query(call.id, '⚠️ Gõ /start trước!')
        return
    balance = db['users'][uid].get('balance', 0)
    if balance < p['price']:
        bot.answer_callback_query(call.id, f'❌ Thiếu {p["price"] - balance:,}đ!')
        return

    db['users'][uid]['balance'] = balance - p['price']
    new_balance = db['users'][uid]['balance']

    order_code = 'HDM' + ''.join(random.choices(string.digits, k=6))
    order = {
        'chat_id': call.from_user.id,
        'username': call.from_user.username or call.from_user.first_name,
        'product_id': pid,
        'product_name': p['name'],
        'price': p['price'],
        'status': 'paid_wallet',
        'time': datetime.now().isoformat(),
        'payment_method': 'wallet'
    }
    db['pending'][order_code] = order
    save_db(db)

    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except:
        pass

    bot.send_message(
        call.message.chat.id,
        f"✅ <b>ĐÃ THANH TOÁN BẰNG SỐ DƯ</b>\n\n"
        f"🛍 SP: {esc(p['name'])}\n"
        f"💰 Đã trừ: <b>{p['price']:,}đ</b>\n"
        f"💵 Số dư còn: <b>{new_balance:,}đ</b>\n"
        f"🔖 Mã đơn: <code>{order_code}</code>\n\n"
        f"⏳ Đang giao hàng...",
        parse_mode='HTML'
    )
    auto_deliver(order_code, order)

# ========== MUA QUA QR ==========
@bot.callback_query_handler(func=lambda c: c.data.startswith('buy_'))
def buy_product(call):
    pid = call.data.replace('buy_', '')
    db = load_db()
    if pid not in db['products']:
        return
    p = db['products'][pid]
    if p['type'] == 'account' and p.get('stock', 0) <= 0:
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
        f"🧾 <b>ĐƠN HÀNG</b>\n\n"
        f"🛍 SP: <b>{esc(p['name'])}</b>\n"
        f"💰 Tiền: <b>{p['price']:,}đ</b>\n"
        f"🔖 Mã đơn: <code>{order_code}</code>\n\n"
        f"🏦 <b>THANH TOÁN</b>\n"
        f"NH: <b>{esc(BANK_INFO['bank'])}</b>\n"
        f"STK: <code>{BANK_INFO['account']}</code>\n"
        f"Chủ TK: {esc(BANK_INFO['owner'])}\n"
        f"ND: <code>{order_code}</code>\n"
        f"Tiền: <b>{p['price']:,}đ</b>\n\n"
        f"⚠️ <b>ĐÚNG SỐ TIỀN + ĐÚNG NỘI DUNG</b>"
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

# ========== USER PAID ==========
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
        f"🔍 Bot đang kiểm tra..."
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
                # NẠP TIỀN
                if order.get('type') == 'nap_tien':
                    if amount >= order['amount']:
                        uid = str(order['chat_id'])
                        if uid in db['users']:
                            old_bal = db['users'][uid].get('balance', 0)
                            db['users'][uid]['balance'] = old_bal + amount
                            new_bal = db['users'][uid]['balance']
                            db.setdefault('nap_history', []).append({
                                'chat_id': order['chat_id'],
                                'amount': amount,
                                'code': order_code,
                                'time': datetime.now().isoformat()
                            })
                            del db['pending'][order_code]
                            save_db(db)
                            try:
                                bot.send_message(
                                    order['chat_id'],
                                    f"✅ <b>NẠP TIỀN THÀNH CÔNG</b>\n\n"
                                    f"💵 Số tiền nạp: <b>+{amount:,}đ</b>\n"
                                    f"💰 Số dư mới: <b>{new_bal:,}đ</b>\n"
                                    f"🔖 Mã: <code>{order_code}</code>\n\n"
                                    f"📌 Dùng số dư để mua hàng!",
                                    parse_mode='HTML'
                                )
                            except Exception as e:
                                print(f"Noti user error: {e}")
                            bot.send_message(ADMIN_ID, f"💰 <b>USER NẠP TIỀN</b>\n\n👤 @{order['username']}\n💵 +{amount:,}đ\n🔖 {order_code}", parse_mode='HTML')
                        break
                    else:
                        bot.send_message(
                            order['chat_id'],
                            f"⚠️ <b>NẠP THIẾU TIỀN</b>\n\n"
                            f"🔖 Mã: {order_code}\n"
                            f"💰 Cần: {order['amount']:,}đ\n"
                            f"📥 Đã CK: {amount:,}đ\n"
                            f"❗ Còn thiếu: <b>{order['amount'] - amount:,}đ</b>",
                            parse_mode='HTML'
                        )
                        break
                # MUA HÀNG
                else:
                    if amount == order['price']:
                        auto_deliver(order_code, order)
                        break
                    elif amount > order['price']:
                        auto_deliver(order_code, order)
                        bot.send_message(ADMIN_ID, f"⚠️ <b>CHUYỂN DƯ</b>\nĐơn: {order_code}\nDư: {amount - order['price']:,}đ", parse_mode='HTML')
                        break
                    elif amount < order['price']:
                        bot.send_message(order['chat_id'], f"⚠️ <b>CHUYỂN THIẾU</b>\n\n🔖 {order_code}\n💰 Giá: {order['price']:,}đ\n📥 Đã CK: {amount:,}đ\n❗ Thiếu: <b>{order['price'] - amount:,}đ</b>", parse_mode='HTML')
                        bot.send_message(ADMIN_ID, f"⚠️ CHUYỂN THIẾU\nĐơn: {order_code}\nThiếu: {order['price'] - amount:,}đ")
                        break
        return {'success': True}
    except Exception as e:
        print(f'Webhook error: {e}')
        return {'error': str(e)}, 500

# ========== GỬI NỘI DUNG TUT/TOOL ==========
def send_content_to_user(chat_id, p, order_code, header):
    """Gửi nội dung tut/tool cho user"""
    content_type = p.get('content_type', 'text')
    link = p.get('link', '')

    # Chưa có nội dung / liên hệ admin
    if not link or content_type == 'contact':
        bot.send_message(
            chat_id,
            f"✅ <b>GIAO HÀNG THÀNH CÔNG</b>\n\n"
            f"🛍 SP: {esc(p['name'])}\n"
            f"🔖 Mã: <code>{order_code}</code>\n\n"
            f"📞 <b>VUI LÒNG LIÊN HỆ ADMIN ĐỂ LẤY {p['type'].upper()}:</b>\n"
            f"👤 Admin: {esc(TELEGRAM_SUPPORT)}\n\n"
            f"📌 Nhắn kèm <b>mã đơn</b> và <b>tên SP</b> để được hỗ trợ!\n\n"
            f"🍀🍀🍀 <b>CHÚC ANH EM MAY MẮN</b>🍀🍀🍀",
            parse_mode='HTML'
        )
        try:
            bot.send_message(
                ADMIN_ID,
                f"🔔 <b>CẦN GỬI {p['type'].upper()} THỦ CÔNG</b>\n\n"
                f"🛍 SP: {esc(p['name'])}\n"
                f"🔖 Mã: <code>{order_code}</code>\n"
                f"👤 User ID: <code>{chat_id}</code>",
                parse_mode='HTML'
            )
        except:
            pass
        return

    # FILE
    if content_type == 'file' and p.get('file_id'):
        caption = (
            f"✅ <b>GIAO HÀNG THÀNH CÔNG</b>\n\n"
            f"🛍 SP: {esc(p['name'])}\n"
            f"🔖 Mã: <code>{order_code}</code>\n\n"
            f"{header}\n"
            f"📁 File: {esc(p.get('file_name', 'file'))}\n\n"
            f"🍀🍀🍀 <b>CHÚC ANH EM MAY MẮN</b>🍀🍀🍀"
        )
        try:
            bot.send_document(chat_id, p['file_id'], caption=caption, parse_mode='HTML')
            return
        except Exception as e:
            print(f"Send file error: {e}")
            bot.send_message(chat_id, "❌ Lỗi gửi file. Liên hệ admin!")

    # PHOTO
    if content_type == 'photo' and p.get('file_id'):
        caption = (
            f"✅ <b>GIAO HÀNG THÀNH CÔNG</b>\n\n"
            f"🛍 SP: {esc(p['name'])}\n"
            f"🔖 Mã: <code>{order_code}</code>\n\n"
            f"🍀🍀🍀 <b>CHÚC ANH EM MAY MẮN</b>🍀🍀🍀"
        )
        try:
            bot.send_photo(chat_id, p['file_id'], caption=caption, parse_mode='HTML')
            return
        except Exception as e:
            print(f"Send photo error: {e}")

    # VIDEO
    if content_type == 'video' and p.get('file_id'):
        try:
            bot.send_video(chat_id, p['file_id'], caption=header, parse_mode='HTML')
            return
        except Exception as e:
            print(f"Send video error: {e}")

    # AUDIO
    if content_type == 'audio' and p.get('file_id'):
        try:
            bot.send_audio(chat_id, p['file_id'], caption=header, parse_mode='HTML')
            return
        except Exception as e:
            print(f"Send audio error: {e}")

    # TEXT/LINK mặc định
    bot.send_message(
        chat_id,
        f"✅ <b>GIAO HÀNG THÀNH CÔNG</b>\n\n"
        f"🛍 SP: {esc(p['name'])}\n"
        f"🔖 Mã: <code>{order_code}</code>\n\n"
        f"{header}\n"
        f"{esc(link)}\n\n"
        f"🍀🍀🍀 <b>CHÚC ANH EM MAY MẮN</b>🍀🍀🍀",
        parse_mode='HTML'
    )

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
            send_content_to_user(chat_id, p, order_code, "🔧 <b>TOOL CỦA BẠN</b>")
        elif p['type'] == 'tut':
            send_content_to_user(chat_id, p, order_code, "📚 <b>TÀI LIỆU CỦA BẠN</b>")
        elif p['type'] == 'tool_sms':
            if not SMS_TOOL_AVAILABLE:
                bot.send_message(chat_id, "❌ Tool spam SMS đang bảo trì!")
                bot.send_message(ADMIN_ID, f"⚠️ Tool SMS không có cho đơn {order_code}")
                return
            sms_waiting[chat_id] = {
                'order_code': order_code,
                'product_id': pid,
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
        if order_code in db['pending']:
            del db['pending'][order_code]
        save_db(db)
        bot.send_message(ADMIN_ID, f"✅ <b>ĐƠN TỰ ĐỘNG DUYỆT</b>\n\n🔖 Mã: {order_code}\n@{order['username']}\n🛍 SP: {esc(p['name'])}\n💰 {order['price']:,}đ", parse_mode='HTML')
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
    title = order.get('product_name', order.get('type', 'N/A'))
    price = order.get('price', order.get('amount', 0))
    bot.send_photo(
        ADMIN_ID, photo_id,
        caption=f"🧾 <b>BILL</b>\n\n🔖 Mã: {oid}\n@{esc(order['username'])}\n🛍 {esc(title)}\n💰 {price:,}đ",
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
        order = db['pending'][oid]
        if order.get('type') == 'nap_tien':
            uid = str(order['chat_id'])
            if uid in db['users']:
                db['users'][uid]['balance'] = db['users'][uid].get('balance', 0) + order['amount']
                db.setdefault('nap_history', []).append({
                    'chat_id': order['chat_id'], 'amount': order['amount'],
                    'code': oid, 'time': datetime.now().isoformat()
                })
                del db['pending'][oid]
                save_db(db)
                bot.send_message(order['chat_id'], f"✅ Đã cộng {order['amount']:,}đ vào ví!", parse_mode='HTML')
        else:
            auto_deliver(oid, order)
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

# ========== SMS INPUT ==========
@bot.message_handler(func=lambda m: m.chat.id in sms_waiting and sms_waiting[m.chat.id]['step'] == 'phone')
def sms_input_phone(msg):
    chat_id = msg.chat.id
    phone = msg.text.strip().replace(' ', '').replace('-', '')
    if not phone.isdigit() or len(phone) < 10 or len(phone) > 11:
        bot.send_message(chat_id, "❌ SĐT không hợp lệ! Nhập lại:")
        return
    sms_waiting[chat_id]['phone'] = phone
    sms_waiting[chat_id]['step'] = 'count'
    bot.send_message(
        chat_id,
        f"📱 SĐT: <code>{phone}</code>\n\n"
        f"🔁 <b>Nhập số lần spam:</b> (1-50)\n\n"
        f"⚠️ Gõ /cancel để huỷ",
        parse_mode='HTML'
    )

@bot.message_handler(func=lambda m: m.chat.id in sms_waiting and sms_waiting[m.chat.id]['step'] == 'count')
def sms_input_count(msg):
    chat_id = msg.chat.id
    try:
        count = int(msg.text.strip())
        if count < 1 or count > 50:
            bot.send_message(chat_id, "❌ Số lần phải từ 1-50! Nhập lại:")
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
        f"⏳ Đợi 1-5 phút...",
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
                raise Exception("sms_tool.py không có hàm run/run_multi")
            elapsed = time.time() - start
            bot.send_message(
                chat_id,
                f"✅ <b>SPAM SMS HOÀN THÀNH</b>\n\n"
                f"📱 SĐT: <code>{phone}</code>\n"
                f"🔁 Số lần: <b>{count}</b>\n"
                f"⏱ {elapsed:.1f}s\n\n"
                f"🍀🍀🍀 <b>CHÚC MAY MẮN</b>🍀🍀🍀",
                parse_mode='HTML'
            )
            bot.send_message(ADMIN_ID, f"✅ Đơn {order_code}: {phone} x{count}")
        except Exception as e:
            print(f"[SMS TOOL ERROR] {e}")
            bot.send_message(chat_id, f"❌ <b>LỖI TOOL</b>\n\n❗ {esc(str(e))}\n\nLH: {esc(TELEGRAM_SUPPORT)}", parse_mode='HTML')
            bot.send_message(ADMIN_ID, f"❌ Lỗi đơn {order_code}: {e}")
    threading.Thread(target=run_tool, daemon=True).start()

# ========== CANCEL ==========
@bot.message_handler(commands=['cancel'])
def cmd_cancel(msg):
    chat_id = msg.chat.id
    cancelled = False
    if chat_id in sms_waiting:
        del sms_waiting[chat_id]
        cancelled = True
    if chat_id in nap_waiting:
        del nap_waiting[chat_id]
        cancelled = True
    if chat_id == ADMIN_ID and ADMIN_ID in admin_content_waiting:
        del admin_content_waiting[ADMIN_ID]
        cancelled = True
    if cancelled:
        bot.send_message(chat_id, "✅ Đã huỷ.")
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
    bot.send_message(msg.chat.id, "🎁 <b>MẸO FREE</b>\n\n👇 Chọn bài:", parse_mode='HTML', reply_markup=markup)

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
    bot.edit_message_text("🎁 <b>MẸO FREE</b>\n\n👇 Chọn bài:", call.message.chat.id, call.message.message_id, parse_mode='HTML', reply_markup=markup)

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

@bot.message_handler(func=lambda m: m.text and '|' in m.text and len(m.text) < 1000 and m.chat.id != ADMIN_ID and m.chat.id not in nap_waiting and m.chat.id not in sms_waiting)
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
# ============== ADMIN PANEL ==============
# ============================================================
@bot.message_handler(commands=['admin'])
def admin_panel(msg):
    if msg.chat.id != ADMIN_ID:
        return
    db = load_db()
    total = sum(o.get('price', 0) for o in db['orders'] if o.get('status') == 'completed')
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
        f"💵 Tổng số dư user: <b>{total_balance:,}đ</b>\n"
        f"📱 Tool SMS: {sms_status}\n\n"
        f"📌 <b>SP:</b>\n"
        f"<code>/addproduct |pid|ten|gia|loai|mo_ta|link|</code>\n"
        f"Loại: <code>account</code> / <code>tool</code> / <code>tut</code> / <code>tool_sms</code>\n"
        f"<code>/addtut &lt;pid&gt;</code> — thêm nội dung TUT ⭐\n"
        f"<code>/addtool &lt;pid&gt;</code> — thêm file/link TOOL ⭐\n"
        f"<code>/setprice &lt;pid&gt; &lt;gia&gt;</code>\n"
        f"<code>/setlink &lt;pid&gt; &lt;link&gt;</code>\n"
        f"<code>/settut &lt;pid&gt; &lt;link&gt;</code>\n"
        f"<code>/settool &lt;pid&gt; &lt;link&gt;</code>\n"
        f"<code>/info &lt;pid&gt;</code>\n"
        f"<code>/delproduct &lt;pid&gt;</code>\n"
        f"<code>/delall confirm</code>\n\n"
        f"📌 <b>ACC:</b>\n"
        f"<code>/addacc &lt;pid&gt; &lt;acc&gt;</code>\n"
        f"<code>/addlist &lt;pid&gt;</code> + list\n"
        f"<code>/genacc &lt;pid&gt; &lt;so_luong&gt;</code>\n"
        f"<code>/kho</code> hoặc <code>/kho &lt;pid&gt;</code>\n\n"
        f"📌 <b>TIỀN / USER:</b>\n"
        f"<code>/addmoney &lt;id&gt; &lt;tien&gt;</code>\n"
        f"<code>/submoney &lt;id&gt; &lt;tien&gt;</code>\n"
        f"<code>/setmoney &lt;id&gt; &lt;tien&gt;</code>\n"
        f"<code>/checkmoney &lt;id&gt;</code>\n"
        f"<code>/allusers</code>\n"
        f"<code>/finduser &lt;ten&gt;</code>\n\n"
        f"📌 <b>KHÁC:</b>\n"
        f"<code>/deltip</code>\n"
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
            bot.send_message(ADMIN_ID, "📌 <code>/addproduct |pid|ten|gia|loai|mo_ta|link|</code>\nLoại: account / tool / tut / tool_sms", parse_mode='HTML')
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
        stock = 0 if ptype == 'account' else -1
        db['products'][pid] = {
            'name': name,
            'price': price,
            'stock': stock,
            'type': ptype,
            'desc': desc,
            'link': link
        }
        if ptype == 'account':
            db['inventory'][pid] = []
        save_db(db)
        stock_display = "Vô hạn" if stock == -1 else stock

        next_hint = ""
        if ptype == 'tut':
            next_hint = f"\n\n📌 <b>Bước tiếp:</b> Gõ <code>/addtut {esc(pid)}</code> để thêm nội dung tut"
        elif ptype == 'tool':
            next_hint = f"\n\n📌 <b>Bước tiếp:</b> Gõ <code>/addtool {esc(pid)}</code> để thêm file/link tool\n💡 Hoặc gõ <code>skip</code> để set 'Liên hệ admin'"
        elif ptype == 'account':
            next_hint = f"\n\n📌 <b>Bước tiếp:</b> Gõ <code>/addacc {esc(pid)} &lt;acc&gt;</code> hoặc <code>/addlist {esc(pid)}</code>"

        bot.send_message(
            ADMIN_ID,
            f"✅ <b>ĐÃ THÊM SP</b>\n\n"
            f"PID: <code>{esc(pid)}</code>\n"
            f"Tên: {esc(name)}\n"
            f"Giá: {price:,}đ\n"
            f"Loại: {ptype}\n"
            f"Stock: {stock_display}"
            f"{next_hint}",
            parse_mode='HTML'
        )
    except Exception as e:
        bot.send_message(ADMIN_ID, f"❌ Lỗi: {e}")

# ========== ADD TUT ==========
@bot.message_handler(commands=['addtut'])
def admin_addtut(msg):
    if msg.chat.id != ADMIN_ID:
        return
    try:
        parts = msg.text.split(maxsplit=1)
        if len(parts) < 2:
            bot.send_message(
                ADMIN_ID,
                "📌 <b>Dùng:</b> <code>/addtut &lt;pid&gt;</code>\n\n"
                "Sau đó bot sẽ hỏi nội dung, bạn gửi:\n"
                "• Text (link, hướng dẫn)\n"
                "• Hoặc file (PDF, DOCX, ZIP...)\n\n"
                "<b>VD:</b> <code>/addtut tut1</code>",
                parse_mode='HTML'
            )
            return
        pid = parts[1].strip()
        db = load_db()
        if pid not in db['products']:
            bot.send_message(ADMIN_ID, f"❌ SP <code>{esc(pid)}</code> không tồn tại!", parse_mode='HTML')
            return
        p = db['products'][pid]
        if p['type'] != 'tut':
            bot.send_message(ADMIN_ID, f"❌ SP <code>{esc(pid)}</code> không phải loại <b>tut</b>!\nLoại: {p['type']}", parse_mode='HTML')
            return
        admin_content_waiting[ADMIN_ID] = {'pid': pid, 'type': 'tut'}
        bot.send_message(
            ADMIN_ID,
            f"📚 <b>THÊM NỘI DUNG TUT</b>\n\n"
            f"🛍 SP: <b>{esc(p['name'])}</b>\n"
            f"🆔 PID: <code>{esc(pid)}</code>\n\n"
            f"👇 Gửi nội dung tut (text, link, file...):\n"
            f"⚠️ Gõ /cancel để huỷ",
            parse_mode='HTML'
        )
    except Exception as e:
        bot.send_message(ADMIN_ID, f"❌ Lỗi: {e}")

# ========== ADD TOOL ==========
@bot.message_handler(commands=['addtool'])
def admin_addtool(msg):
    if msg.chat.id != ADMIN_ID:
        return
    try:
        parts = msg.text.split(maxsplit=1)
        if len(parts) < 2:
            bot.send_message(
                ADMIN_ID,
                "📌 <b>Dùng:</b> <code>/addtool &lt;pid&gt;</code>\n\n"
                "Sau đó bot sẽ hỏi nội dung, bạn có thể:\n"
                "• Gửi <b>file</b> (ZIP, EXE, APK...)\n"
                "• Gửi <b>link</b> tải tool\n"
                "• Gõ <code>skip</code> → Bot tự ghi 'Liên hệ admin'\n\n"
                "<b>VD:</b> <code>/addtool tool1</code>",
                parse_mode='HTML'
            )
            return
        pid = parts[1].strip()
        db = load_db()
        if pid not in db['products']:
            bot.send_message(ADMIN_ID, f"❌ SP <code>{esc(pid)}</code> không tồn tại!", parse_mode='HTML')
            return
        p = db['products'][pid]
        if p['type'] != 'tool':
            bot.send_message(ADMIN_ID, f"❌ SP <code>{esc(pid)}</code> không phải loại <b>tool</b>!\nLoại: {p['type']}", parse_mode='HTML')
            return
        admin_content_waiting[ADMIN_ID] = {'pid': pid, 'type': 'tool'}
        bot.send_message(
            ADMIN_ID,
            f"🔧 <b>THÊM NỘI DUNG TOOL</b>\n\n"
            f"🛍 SP: <b>{esc(p['name'])}</b>\n"
            f"🆔 PID: <code>{esc(pid)}</code>\n\n"
            f"👇 Gửi file tool HOẶC link tải:\n"
            f"• Gửi file (ZIP, RAR, EXE...)\n"
            f"• Hoặc gửi link\n"
            f"• Hoặc gõ <code>skip</code> → Bot ghi 'Liên hệ admin {esc(TELEGRAM_SUPPORT)}'\n\n"
            f"⚠️ Gõ /cancel để huỷ",
            parse_mode='HTML'
        )
    except Exception as e:
        bot.send_message(ADMIN_ID, f"❌ Lỗi: {e}")

# ========== HANDLER NHẬN NỘI DUNG TUT/TOOL ==========
@bot.message_handler(
    func=lambda m: m.chat.id == ADMIN_ID and ADMIN_ID in admin_content_waiting,
    content_types=['text', 'document', 'photo', 'video', 'audio']
)
def admin_receive_content(msg):
    state = admin_content_waiting[ADMIN_ID]
    pid = state['pid']
    ctype = state['type']
    db = load_db()
    if pid not in db['products']:
        bot.send_message(ADMIN_ID, f"❌ SP <code>{esc(pid)}</code> không tồn tại!", parse_mode='HTML')
        del admin_content_waiting[ADMIN_ID]
        return
    p = db['products'][pid]

    # SKIP
    if msg.content_type == 'text' and msg.text.strip().lower() == 'skip':
        p['link'] = f"CONTACT_ADMIN:{TELEGRAM_SUPPORT}"
        p['content_type'] = 'contact'
        save_db(db)
        del admin_content_waiting[ADMIN_ID]
        bot.send_message(
            ADMIN_ID,
            f"✅ <b>ĐÃ SET 'LIÊN HỆ ADMIN'</b>\n\n"
            f"🛍 SP: {esc(p['name'])}\n"
            f"🆔 PID: <code>{esc(pid)}</code>\n"
            f"📌 User mua sẽ thấy: 'Liên hệ admin {esc(TELEGRAM_SUPPORT)}'",
            parse_mode='HTML'
        )
        return

    # TEXT
    if msg.content_type == 'text':
        content = msg.text.strip()
        p['link'] = content
        p['content_type'] = 'text'
        save_db(db)
        del admin_content_waiting[ADMIN_ID]
        bot.send_message(
            ADMIN_ID,
            f"✅ <b>ĐÃ LƯU NỘI DUNG {ctype.upper()}</b>\n\n"
            f"🛍 SP: {esc(p['name'])}\n"
            f"📝 Nội dung: <code>{esc(content[:100])}</code>",
            parse_mode='HTML'
        )
        return

    # FILE
    if msg.content_type == 'document':
        file_id = msg.document.file_id
        file_name = msg.document.file_name or 'file'
        p['link'] = f"FILE:{file_id}:{file_name}"
        p['content_type'] = 'file'
        p['file_id'] = file_id
        p['file_name'] = file_name
        save_db(db)
        del admin_content_waiting[ADMIN_ID]
        bot.send_message(
            ADMIN_ID,
            f"✅ <b>ĐÃ LƯU FILE {ctype.upper()}</b>\n\n"
            f"🛍 SP: {esc(p['name'])}\n"
            f"📁 File: <code>{esc(file_name)}</code>",
            parse_mode='HTML'
        )
        return

    # PHOTO
    if msg.content_type == 'photo':
        file_id = msg.photo[-1].file_id
        p['link'] = f"PHOTO:{file_id}"
        p['content_type'] = 'photo'
        p['file_id'] = file_id
        save_db(db)
        del admin_content_waiting[ADMIN_ID]
        bot.send_message(ADMIN_ID, f"✅ Đã lưu ảnh cho <b>{esc(p['name'])}</b>", parse_mode='HTML')
        return

    # VIDEO
    if msg.content_type == 'video':
        file_id = msg.video.file_id
        p['link'] = f"VIDEO:{file_id}"
        p['content_type'] = 'video'
        p['file_id'] = file_id
        save_db(db)
        del admin_content_waiting[ADMIN_ID]
        bot.send_message(ADMIN_ID, f"✅ Đã lưu video cho <b>{esc(p['name'])}</b>", parse_mode='HTML')
        return

    # AUDIO
    if msg.content_type == 'audio':
        file_id = msg.audio.file_id
        p['link'] = f"AUDIO:{file_id}"
        p['content_type'] = 'audio'
        p['file_id'] = file_id
        save_db(db)
        del admin_content_waiting[ADMIN_ID]
        bot.send_message(ADMIN_ID, f"✅ Đã lưu audio cho <b>{esc(p['name'])}</b>", parse_mode='HTML')
        return

    bot.send_message(ADMIN_ID, "❌ Loại nội dung không hỗ trợ. Gửi text/file/ảnh hoặc /cancel.")

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
        bot.send_message(ADMIN_ID, "📌 <code>/setprice &lt;pid&gt; &lt;gia&gt;</code>", parse_mode='HTML')

# ========== SET LINK ==========
@bot.message_handler(commands=['setlink'])
def admin_setlink(msg):
    if msg.chat.id != ADMIN_ID:
        return
    try:
        parts = msg.text.split(maxsplit=2)
        if len(parts) < 3:
            bot.send_message(ADMIN_ID, "📌 <code>/setlink &lt;pid&gt; &lt;link&gt;</code>", parse_mode='HTML')
            return
        pid = parts[1].strip()
        link = parts[2].strip()
        db = load_db()
        if pid not in db['products']:
            bot.send_message(ADMIN_ID, f"❌ SP <code>{esc(pid)}</code> không tồn tại!", parse_mode='HTML')
            return
        p = db['products'][pid]
        if p['type'] == 'account':
            bot.send_message(ADMIN_ID, f"❌ SP là account! Dùng /addacc hoặc /addlist", parse_mode='HTML')
            return
        p['link'] = link
        p['content_type'] = 'text'
        save_db(db)
        bot.send_message(ADMIN_ID, f"✅ Đã cập nhật link <code>{esc(pid)}</code>\n🔗 <code>{esc(link[:80])}</code>", parse_mode='HTML')
    except Exception as e:
        bot.send_message(ADMIN_ID, f"❌ Lỗi: {e}")

# ========== SET TUT ==========
@bot.message_handler(commands=['settut'])
def admin_settut(msg):
    if msg.chat.id != ADMIN_ID:
        return
    try:
        parts = msg.text.split(maxsplit=2)
        if len(parts) < 3:
            bot.send_message(ADMIN_ID, "📌 <code>/settut &lt;pid&gt; &lt;link&gt;</code>", parse_mode='HTML')
            return
        pid = parts[1].strip()
        link = parts[2].strip()
        db = load_db()
        if pid not in db['products']:
            bot.send_message(ADMIN_ID, f"❌ SP <code>{esc(pid)}</code> không tồn tại!", parse_mode='HTML')
            return
        p = db['products'][pid]
        if p['type'] != 'tut':
            bot.send_message(ADMIN_ID, f"❌ SP không phải tut! Loại: {p['type']}", parse_mode='HTML')
            return
        p['link'] = link
        p['content_type'] = 'text'
        save_db(db)
        bot.send_message(ADMIN_ID, f"✅ Đã cập nhật link tut <code>{esc(pid)}</code>", parse_mode='HTML')
    except Exception as e:
        bot.send_message(ADMIN_ID, f"❌ Lỗi: {e}")

# ========== SET TOOL ==========
@bot.message_handler(commands=['settool'])
def admin_settool(msg):
    if msg.chat.id != ADMIN_ID:
        return
    try:
        parts = msg.text.split(maxsplit=2)
        if len(parts) < 3:
            bot.send_message(ADMIN_ID, "📌 <code>/settool &lt;pid&gt; &lt;link&gt;</code>", parse_mode='HTML')
            return
        pid = parts[1].strip()
        link = parts[2].strip()
        db = load_db()
        if pid not in db['products']:
            bot.send_message(ADMIN_ID, f"❌ SP <code>{esc(pid)}</code> không tồn tại!", parse_mode='HTML')
            return
        p = db['products'][pid]
        if p['type'] != 'tool':
            bot.send_message(ADMIN_ID, f"❌ SP không phải tool! Loại: {p['type']}", parse_mode='HTML')
            return
        p['link'] = link
        p['content_type'] = 'text'
        save_db(db)
        bot.send_message(ADMIN_ID, f"✅ Đã cập nhật link tool <code>{esc(pid)}</code>", parse_mode='HTML')
    except Exception as e:
        bot.send_message(ADMIN_ID, f"❌ Lỗi: {e}")

# ========== INFO ==========
@bot.message_handler(commands=['info'])
def admin_info(msg):
    if msg.chat.id != ADMIN_ID:
        return
    try:
        parts = msg.text.split()
        if len(parts) < 2:
            bot.send_message(ADMIN_ID, "📌 <code>/info &lt;pid&gt;</code>", parse_mode='HTML')
            return
        pid = parts[1].strip()
        db = load_db()
        if pid not in db['products']:
            bot.send_message(ADMIN_ID, f"❌ Không tìm thấy <code>{esc(pid)}</code>", parse_mode='HTML')
            return
        p = db['products'][pid]
        stock_display = "Vô hạn" if p.get('stock', 0) == -1 else p.get('stock', 0)
        ctype = p.get('content_type', 'text')
        link_display = p.get('link', 'Chưa có')[:80]
        text = (
            f"🛍 <b>{esc(p['name'])}</b>\n\n"
            f"🆔 PID: <code>{esc(pid)}</code>\n"
            f"📦 Loại: <b>{p['type']}</b>\n"
            f"💰 Giá: <b>{p['price']:,}đ</b>\n"
            f"📊 Stock: <b>{stock_display}</b>\n"
            f"📝 Mô tả: {esc(p.get('desc', ''))}\n"
            f"📎 Kiểu nội dung: {ctype}\n"
            f"🔗 Link: <code>{esc(link_display)}</code>"
        )
        bot.send_message(ADMIN_ID, text, parse_mode='HTML')
    except Exception as e:
        bot.send_message(ADMIN_ID, f"❌ Lỗi: {e}")

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
        bot.send_message(ADMIN_ID, "📌 <code>/delproduct &lt;pid&gt;</code>", parse_mode='HTML')

# ========== DEL ALL ==========
@bot.message_handler(commands=['delall'])
def admin_delall(msg):
    if msg.chat.id != ADMIN_ID:
        return
    parts = msg.text.split()
    if len(parts) < 2 or parts[1] != 'confirm':
        bot.send_message(ADMIN_ID, "⚠️ <code>/delall confirm</code> để xoá TẤT CẢ SP", parse_mode='HTML')
        return
    db = load_db()
    n_prod = len(db['products'])
    n_inv = sum(len(v) for v in db['inventory'].values())
    n_pending = len(db['pending'])
    db['products'] = {}
    db['inventory'] = {}
    db['pending'] = {}
    save_db(db)
    bot.send_message(ADMIN_ID, f"✅ Đã xoá: {n_prod} SP, {n_inv} acc, {n_pending} đơn chờ", parse_mode='HTML')

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
        bot.send_message(ADMIN_ID, f"✅ Thêm acc vào <code>{esc(pid)}</code>\n📦 Kho: <b>{db['products'][pid]['stock']}</b>", parse_mode='HTML')
    except:
        bot.send_message(ADMIN_ID, "📌 <code>/addacc &lt;pid&gt; &lt;acc&gt;</code>", parse_mode='HTML')

# ========== ADD LIST ==========
@bot.message_handler(commands=['addlist'])
def admin_addlist(msg):
    if msg.chat.id != ADMIN_ID:
        return
    try:
        lines = msg.text.split('\n')
        first = lines[0].strip().split()
        if len(first) < 2:
            bot.send_message(ADMIN_ID, "📌 <code>/addlist &lt;pid&gt;\ntk1|mk1|nam1|2fa1|cookie1\ntk2|...</code>", parse_mode='HTML')
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
        bot.send_message(ADMIN_ID, f"✅ Thêm {added} acc vào <b>{esc(db['products'][pid]['name'])}</b>\n📦 Kho: <b>{db['products'][pid]['stock']}</b>", parse_mode='HTML')
    except Exception as e:
        bot.send_message(ADMIN_ID, f"❌ Lỗi: {e}")

# ========== GEN ACC ==========
@bot.message_handler(commands=['genacc'])
def admin_genacc(msg):
    if msg.chat.id != ADMIN_ID:
        return
    try:
        parts = msg.text.split()
        if len(parts) < 3:
            bot.send_message(ADMIN_ID, "📌 <code>/genacc &lt;pid&gt; &lt;số_lượng&gt;</code>", parse_mode='HTML')
            return
        pid = parts[1].strip()
        count = int(parts[2])
        if count < 1 or count > 1000:
            bot.send_message(ADMIN_ID, "❌ Số lượng 1-1000!")
            return
        db = load_db()
        if pid not in db['products']:
            bot.send_message(ADMIN_ID, f"❌ SP <code>{esc(pid)}</code> không tồn tại!", parse_mode='HTML')
            return
        if pid not in db['inventory']:
            db['inventory'][pid] = []
        for i in range(count):
            username = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
            password = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
            name = f"User_{''.join(random.choices(string.ascii_uppercase, k=4))}"
            fa2 = ''.join(random.choices(string.digits, k=6))
            db['inventory'][pid].append(f"{username}|{password}|{name}|{fa2}|")
        db['products'][pid]['stock'] = len(db['inventory'][pid])
        save_db(db)
        bot.send_message(ADMIN_ID, f"✅ Tạo {count} acc random vào <b>{esc(db['products'][pid]['name'])}</b>\n📦 Kho: <b>{db['products'][pid]['stock']}</b>", parse_mode='HTML')
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
                text += f"{i}. <code>{esc(tk)}</code> | {esc(nam)}\n"
            if len(inv) > 30:
                text += f"\n... +{len(inv)-30} acc"
            bot.send_message(ADMIN_ID, text, parse_mode='HTML')
        else:
            text = "📦 <b>TẤT CẢ KHO</b>\n\n"
            total = 0
            for pid, inv in db['inventory'].items():
                name = db['products'].get(pid, {}).get('name', pid)
                text += f"• {esc(name)}: <b>{len(inv)}</b>\n"
                total += len(inv)
            text += f"\n🧮 <b>TỔNG: {total}</b>"
            bot.send_message(ADMIN_ID, text, parse_mode='HTML')
    except Exception as e:
        bot.send_message(ADMIN_ID, f"❌ Lỗi: {e}")

# ========== 💰 LỆNH TIỀN ==========
@bot.message_handler(commands=['addmoney'])
def admin_addmoney(msg):
    if msg.chat.id != ADMIN_ID:
        return
    try:
        parts = msg.text.split()
        if len(parts) < 3:
            bot.send_message(ADMIN_ID, "📌 <code>/addmoney &lt;id&gt; &lt;tien&gt;</code>", parse_mode='HTML')
            return
        target = parts[1].strip()
        amount = int(parts[2])
        if amount <= 0:
            bot.send_message(ADMIN_ID, "❌ Số tiền phải > 0!")
            return
        uid = find_user_id(target)
        if not uid:
            bot.send_message(ADMIN_ID, f"❌ Không tìm thấy: <code>{esc(target)}</code>", parse_mode='HTML')
            return
        db = load_db()
        old_balance = db['users'][uid].get('balance', 0)
        db['users'][uid]['balance'] = old_balance + amount
        new_balance = db['users'][uid]['balance']
        save_db(db)
        try:
            bot.send_message(int(uid), f"💰 <b>BẠN ĐƯỢC CỘNG TIỀN</b>\n\n💵 +{amount:,}đ\n💰 Số dư: <b>{new_balance:,}đ</b>", parse_mode='HTML')
        except Exception as e:
            print(f"Noti user error: {e}")
        bot.send_message(ADMIN_ID, f"✅ <b>ĐÃ CỘNG TIỀN</b>\n\n👤 <code>{uid}</code>\n💰 Trước: {old_balance:,}đ\n➕ +{amount:,}đ\n💵 Sau: <b>{new_balance:,}đ</b>", parse_mode='HTML')
    except ValueError:
        bot.send_message(ADMIN_ID, "❌ Số tiền phải là số nguyên!")
    except Exception as e:
        bot.send_message(ADMIN_ID, f"❌ Lỗi: {e}")

@bot.message_handler(commands=['submoney'])
def admin_submoney(msg):
    if msg.chat.id != ADMIN_ID:
        return
    try:
        parts = msg.text.split()
        if len(parts) < 3:
            bot.send_message(ADMIN_ID, "📌 <code>/submoney &lt;id&gt; &lt;tien&gt;</code>", parse_mode='HTML')
            return
        target = parts[1].strip()
        amount = int(parts[2])
        if amount <= 0:
            bot.send_message(ADMIN_ID, "❌ Số tiền phải > 0!")
            return
        uid = find_user_id(target)
        if not uid:
            bot.send_message(ADMIN_ID, f"❌ Không tìm thấy: <code>{esc(target)}</code>", parse_mode='HTML')
            return
        db = load_db()
        old_balance = db['users'][uid].get('balance', 0)
        if old_balance < amount:
            bot.send_message(ADMIN_ID, f"⚠️ User chỉ có {old_balance:,}đ!")
            return
        db['users'][uid]['balance'] = old_balance - amount
        new_balance = db['users'][uid]['balance']
        save_db(db)
        try:
            bot.send_message(int(uid), f"⚠️ <b>SỐ DƯ BỊ TRỪ</b>\n\n💵 -{amount:,}đ\n💰 Còn: <b>{new_balance:,}đ</b>", parse_mode='HTML')
        except:
            pass
        bot.send_message(ADMIN_ID, f"✅ Đã trừ {amount:,}đ của <code>{uid}</code>\n💰 Còn: <b>{new_balance:,}đ</b>", parse_mode='HTML')
    except ValueError:
        bot.send_message(ADMIN_ID, "❌ Số tiền phải là số!")
    except Exception as e:
        bot.send_message(ADMIN_ID, f"❌ Lỗi: {e}")

@bot.message_handler(commands=['setmoney'])
def admin_setmoney(msg):
    if msg.chat.id != ADMIN_ID:
        return
    try:
        parts = msg.text.split()
        if len(parts) < 3:
            bot.send_message(ADMIN_ID, "📌 <code>/setmoney &lt;id&gt; &lt;tien&gt;</code>", parse_mode='HTML')
            return
        target = parts[1].strip()
        amount = int(parts[2])
        if amount < 0:
            bot.send_message(ADMIN_ID, "❌ Số tiền phải >= 0!")
            return
        uid = find_user_id(target)
        if not uid:
            bot.send_message(ADMIN_ID, f"❌ Không tìm thấy: <code>{esc(target)}</code>", parse_mode='HTML')
            return
        db = load_db()
        old_balance = db['users'][uid].get('balance', 0)
        db['users'][uid]['balance'] = amount
        save_db(db)
        try:
            bot.send_message(int(uid), f"⚙️ <b>SỐ DƯ ĐÃ CẬP NHẬT</b>\n\n💰 Số dư mới: <b>{amount:,}đ</b>", parse_mode='HTML')
        except:
            pass
        bot.send_message(ADMIN_ID, f"✅ Set số dư <code>{uid}</code>\n💰 Trước: {old_balance:,}đ → Sau: <b>{amount:,}đ</b>", parse_mode='HTML')
    except ValueError:
        bot.send_message(ADMIN_ID, "❌ Số tiền phải là số!")
    except Exception as e:
        bot.send_message(ADMIN_ID, f"❌ Lỗi: {e}")

@bot.message_handler(commands=['checkmoney'])
def admin_checkmoney(msg):
    if msg.chat.id != ADMIN_ID:
        return
    try:
        parts = msg.text.split()
        if len(parts) < 2:
            bot.send_message(ADMIN_ID, "📌 <code>/checkmoney &lt;id&gt;</code>", parse_mode='HTML')
            return
        target = parts[1].strip()
        uid = find_user_id(target)
        if not uid:
            bot.send_message(ADMIN_ID, f"❌ Không tìm thấy: <code>{esc(target)}</code>", parse_mode='HTML')
            return
        db = load_db()
        u = db['users'][uid]
        ref_count = sum(1 for x in db['users'].values() if x.get('referred_by') == uid)
        total_spent = sum(o.get('price', 0) for o in db['orders'] if str(o.get('chat_id')) == uid)
        bot.send_message(
            ADMIN_ID,
            f"👤 <b>USER INFO</b>\n\n"
            f"🆔 <code>{uid}</code>\n"
            f"📛 {esc(u.get('name', 'N/A'))}\n"
            f"💰 Số dư: <b>{u.get('balance', 0):,}đ</b>\n"
            f"👥 Đã GT: <b>{ref_count}</b>\n"
            f"🛍 Chi tiêu: <b>{total_spent:,}đ</b>\n"
            f"📅 {esc(u.get('joined', 'N/A')[:19])}",
            parse_mode='HTML'
        )
    except Exception as e:
        bot.send_message(ADMIN_ID, f"❌ Lỗi: {e}")

@bot.message_handler(commands=['allusers'])
def admin_allusers(msg):
    if msg.chat.id != ADMIN_ID:
        return
    db = load_db()
    users = db['users']
    if not users:
        bot.send_message(ADMIN_ID, "📭 Chưa có user!")
        return
    sorted_users = sorted(users.items(), key=lambda x: x[1].get('balance', 0), reverse=True)
    text = f"👥 <b>USERS</b> ({len(sorted_users)})\n\n"
    for i, (uid, u) in enumerate(sorted_users[:50], 1):
        bal = u.get('balance', 0)
        name = u.get('name', 'N/A')
        text += f"{i}. <code>{uid}</code> - {esc(name)} - <b>{bal:,}đ</b>\n"
    if len(sorted_users) > 50:
        text += f"\n... +{len(sorted_users)-50}"
    bot.send_message(ADMIN_ID, text, parse_mode='HTML')

@bot.message_handler(commands=['finduser'])
def admin_finduser(msg):
    if msg.chat.id != ADMIN_ID:
        return
    try:
        parts = msg.text.split(maxsplit=1)
        if len(parts) < 2:
            bot.send_message(ADMIN_ID, "📌 <code>/finduser &lt;tên&gt;</code>", parse_mode='HTML')
            return
        query = parts[1].strip()
        db = load_db()
        results = []
        for uid, u in db['users'].items():
            name = u.get('name', '')
            if query.lower() in name.lower() or query == uid:
                results.append((uid, u))
        if not results:
            bot.send_message(ADMIN_ID, f"❌ Không tìm thấy: <code>{esc(query)}</code>", parse_mode='HTML')
            return
        text = f"🔍 <b>KẾT QUẢ</b> ({len(results)})\n\n"
        for uid, u in results[:20]:
            text += f"🆔 <code>{uid}</code>\n📛 {esc(u.get('name', 'N/A'))}\n💰 <b>{u.get('balance', 0):,}đ</b>\n\n"
        bot.send_message(ADMIN_ID, text, parse_mode='HTML')
    except Exception as e:
        bot.send_message(ADMIN_ID, f"❌ Lỗi: {e}")

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
            bot.send_message(ADMIN_ID, "📭 Không có mẹo!")
            return
        text = "📋 <b>DS MẸO</b>\n\n"
        for i, tip in enumerate(tips):
            text += f"{i}. {esc(tip['title'])}\n"
        text += "\n📌 <code>/deltip &lt;số&gt;</code> hoặc <code>/deltip all confirm</code>"
        bot.send_message(ADMIN_ID, text, parse_mode='HTML')
        return
    if parts[1] == 'all':
        if len(parts) < 3 or parts[2] != 'confirm':
            bot.send_message(ADMIN_ID, "⚠️ <code>/deltip all confirm</code>", parse_mode='HTML')
            return
        db = load_db()
        n = len(db.get('tips', []))
        db['tips'] = []
        save_db(db)
        bot.send_message(ADMIN_ID, f"✅ Xoá {n} mẹo!", parse_mode='HTML')
        return
    try:
        idx = int(parts[1])
        db = load_db()
        tips = db.get('tips', [])
        if idx < 0 or idx >= len(tips):
            bot.send_message(ADMIN_ID, f"❌ Số 0 → {len(tips)-1}")
            return
        removed = tips.pop(idx)
        db['tips'] = tips
        save_db(db)
        bot.send_message(ADMIN_ID, f"✅ Xoá: <b>{esc(removed['title'])}</b>", parse_mode='HTML')
    except:
        bot.send_message(ADMIN_ID, "📌 <code>/deltip &lt;số&gt;</code>", parse_mode='HTML')

# ========== BROADCAST ==========
@bot.message_handler(commands=['broadcast'])
def admin_broadcast(msg):
    if msg.chat.id != ADMIN_ID:
        return
    content = msg.text.replace('/broadcast', '').strip()
    if not content:
        bot.send_message(ADMIN_ID, "📌 <code>/broadcast &lt;nội dung&gt;</code>", parse_mode='HTML')
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
    bot.send_message(ADMIN_ID, f"✅ Gửi {success}/{len(users)}", parse_mode='HTML')

# ========== STATS ==========
@bot.message_handler(commands=['stats'])
def admin_stats(msg):
    if msg.chat.id != ADMIN_ID:
        return
    db = load_db()
    text = "📊 <b>THỐNG KÊ</b>\n\n"
    for pid, p in db['products'].items():
        sold = sum(1 for o in db['orders'] if o.get('product_id') == pid and o.get('status') == 'completed')
        stock_display = "∞" if p.get('stock', 0) == -1 else p.get('stock', 0)
        text += f"🛍 <b>{esc(p['name'])}</b>\n   💰 {p['price']:,}đ | ✅ {sold} | 📦 {stock_display}\n"
    total = sum(o.get('price', 0) for o in db['orders'] if o.get('status') == 'completed')
    total_balance = sum(u.get('balance', 0) for u in db['users'].values())
    total_nap = sum(n.get('amount', 0) for n in db.get('nap_history', []))
    text += f"\n💵 <b>TỔNG: {total:,}đ</b>\n👥 Users: {len(db['users'])}\n💰 Số dư user: <b>{total_balance:,}đ</b>\n💳 Tổng nạp: <b>{total_nap:,}đ</b>"
    bot.send_message(ADMIN_ID, text, parse_mode='HTML')

# ========== BACK MENU ==========
@bot.callback_query_handler(func=lambda c: c.data == 'back_menu')
def back_menu(call):
    db = load_db()
    uid = str(call.from_user.id)
    balance = db['users'].get(uid, {}).get('balance', 0)
    try:
        bot.edit_message_text(
            f"🏪 <b>HDM SHOP</b>\n💵 Số dư: <b>{balance:,}đ</b>\n\n👇 Chọn thao tác:",
            call.message.chat.id, call.message.message_id,
            parse_mode='HTML', reply_markup=main_menu()
        )
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
    print(f"🔗 Ref bonus: +{REF_BONUS}đ")
    print(f"📱 Tool SMS: {'✅ ONLINE' if SMS_TOOL_AVAILABLE else '❌ OFFLINE'}")
    port = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=port)
