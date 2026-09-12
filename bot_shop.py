import telebot
from telebot import types
from telebot.types import BotCommand
import json, os, random, string
from datetime import datetime
from flask import Flask, request

BOT_TOKEN = os.environ.get('BOT_TOKEN', '8962422980:AAERSCHiswb_rb6PzRSZ094EVdwnJQ0YPdw')
ADMIN_ID = 6780308119
TELEGRAM_SUPPORT = '@spmxhhdm'
BANK_INFO = {'bank': 'VPBank', 'account': '6566221227', 'owner': 'DO HAI DANG'}
DB_FILE = 'shop_data.json'

def load_db():
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, 'w', encoding='utf-8') as f:
            json.dump({'products': {}, 'inventory': {}, 'pending': {}, 'orders': [], 'users': {}, 'tips': []}, f, ensure_ascii=False, indent=2)
    try:
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {'products': {}, 'inventory': {}, 'pending': {}, 'orders': [], 'users': {}, 'tips': []}

def save_db(data):
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

try:
    bot.set_my_commands([
        BotCommand('start', 'Menu chinh'),
        BotCommand('help', 'Huong dan'),
        BotCommand('shop', 'Cua hang'),
        BotCommand('tips', 'Meo Free'),
        BotCommand('support', 'Ho tro'),
    ])
except Exception as e:
    print(f"Set commands error: {e}")

def main_menu():
    db = load_db()
    markup = types.InlineKeyboardMarkup(row_width=2)
    for pid, p in db['products'].items():
        stock = f"[{p['stock']}]" if p['stock'] > 0 else "[Het]"
        markup.add(types.InlineKeyboardButton(f"{p['name']} - {p['price']:,}d {stock}", callback_data=f'product_{pid}'))
    markup.add(
        types.InlineKeyboardButton('Meo Free', callback_data='cat_tips'),
        types.InlineKeyboardButton('Ho tro', url=f'https://t.me/{TELEGRAM_SUPPORT[1:]}')
    )
    return markup

@bot.message_handler(commands=['start'])
def cmd_start(msg):
    chat_id = msg.chat.id
    name = msg.from_user.first_name or 'ban'
    db = load_db()
    if str(chat_id) not in db['users']:
        db['users'][str(chat_id)] = {'name': name, 'joined': datetime.now().isoformat()}
        save_db(db)
    if not db['products']:
        bot.send_message(chat_id, f"Chao *{name}*!\n\nHDM SHOP\nShop dang cap nhat san pham...", parse_mode='Markdown')
        return
    bot.send_message(chat_id, f"Chao *{name}*!\n\nHDM SHOP - Cua hang so\nTu dong duyet - Giao hang ngay\n\nChon san pham:", parse_mode='Markdown', reply_markup=main_menu())

@bot.message_handler(commands=['help'])
def cmd_help(msg):
    bot.send_message(msg.chat.id, "HUONG DAN MUA HANG\n\n1. Chon san pham\n2. Bot hien STK + ma don\n3. Chuyen DUNG so tien + DUNG noi dung\n4. Bot tu dong gui hang\n\nHo tro: " + TELEGRAM_SUPPORT, parse_mode='Markdown')

@bot.message_handler(commands=['shop'])
def cmd_shop(msg):
    db = load_db()
    if not db['products']:
        bot.send_message(msg.chat.id, "Shop dang cap nhat!")
        return
    bot.send_message(msg.chat.id, "HDM SHOP\n\nChon san pham:", parse_mode='Markdown', reply_markup=main_menu())

@bot.message_handler(commands=['support'])
def cmd_support(msg):
    bot.send_message(msg.chat.id, f"HO TRO\n\nAdmin: {TELEGRAM_SUPPORT}", parse_mode='Markdown', reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton('Nhan Admin', url=f'https://t.me/{TELEGRAM_SUPPORT[1:]}')))

@bot.callback_query_handler(func=lambda c: c.data.startswith('product_'))
def show_product(call):
    pid = call.data.replace('product_', '')
    db = load_db()
    if pid not in db['products']:
        bot.answer_callback_query(call.id, 'SP khong ton tai!')
        return
    p = db['products'][pid]
    stock = f"Con {p['stock']}" if p['stock'] > 0 else "Het hang"
    text = f"{p['name']}\n\n{p['desc']}\nGia: {p['price']:,}d\nKho: {stock}\n\nBam MUA:"
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(types.InlineKeyboardButton('MUA NGAY', callback_data=f'buy_{pid}'), types.InlineKeyboardButton('Quay lai', callback_data='back_menu'))
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data.startswith('buy_'))
def buy_product(call):
    pid = call.data.replace('buy_', '')
    db = load_db()
    if pid not in db['products']:
        return
    p = db['products'][pid]
    if p['stock'] <= 0:
        bot.answer_callback_query(call.id, 'Het hang!')
        return
    order_code = 'HDM' + ''.join(random.choices(string.digits, k=6))
    db['pending'][order_code] = {'chat_id': call.from_user.id, 'username': call.from_user.username or call.from_user.first_name, 'product_id': pid, 'product_name': p['name'], 'price': p['price'], 'status': 'awaiting_payment', 'time': datetime.now().isoformat()}
    save_db(db)
    text = f"DON HANG DA TAO\n\nSP: {p['name']}\nTien: {p['price']:,}d\nMa don: {order_code}\n\nTHANH TOAN\n{BANK_INFO['bank']}\nSTK: {BANK_INFO['account']}\n{BANK_INFO['owner']}\nNoi dung CK: {order_code}\nSo tien: {p['price']:,}d\n\nCHUYEN DUNG SO TIEN + DUNG NOI DUNG"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('Toi da CK', callback_data=f'paid_{order_code}'), types.InlineKeyboardButton('Quay lai', callback_data='back_menu'))
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data.startswith('paid_'))
def user_paid(call):
    order_code = call.data.replace('paid_', '')
    db = load_db()
    if order_code not in db['pending']:
        return
    order = db['pending'][order_code]
    order['status'] = 'verifying'
    save_db(db)
    bot.edit_message_text(f"DANG XAC MINH\n\nMa: {order_code}\nTien: {order['price']:,}d\n\nHe thong kiem tra giao dich...", call.message.chat.id, call.message.message_id)

@app.route('/webhook/payment', methods=['POST'])
def payment_webhook():
    try:
        data = request.json
        print(f"Webhook: {data}")
        amount = data.get('transferAmount', 0) or data.get('amount', 0)
        description = data.get('content', '') or data.get('description', '')
        print(f"So tien: {amount}, Noi dung: {description}")
        db = load_db()
        for order_code, order in list(db['pending'].items()):
            if order_code in description and order['status'] in ['awaiting_payment', 'verifying']:
                if amount == order['price']:
                    auto_deliver(order_code, order)
                    break
                elif amount > order['price']:
                    auto_deliver(order_code, order)
                    bot.send_message(ADMIN_ID, f"CHUYEN DU\nDon: {order_code}\nGia: {order['price']:,}d\nDa CK: {amount:,}d\nDu: {amount - order['price']:,}d")
                    break
                elif amount < order['price']:
                    bot.send_message(order['chat_id'], f"CHUYEN THIEU TIEN\n\nDon: {order_code}\nGia: {order['price']:,}d\nDa CK: {amount:,}d\nCon thieu: {order['price'] - amount:,}d\n\nVui long chuyen them!")
                    bot.send_message(ADMIN_ID, f"CHUYEN THIEU\nDon: {order_code}\n@{order['username']}\nThieu: {order['price'] - amount:,}d")
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
                bot.send_message(chat_id, 'Het kho. Admin gui sau!')
                bot.send_message(ADMIN_ID, f'HET KHO: {p["name"]} - {order_code}')
                return
            acc = inventory.pop(0)
            db['inventory'][pid] = inventory
            p['stock'] = len(inventory)
            bot.send_message(chat_id, f"GIAO HANG THANH CONG\n\nSP: {p['name']}\nMa: {order_code}\n\nTAI KHOAN:\n{acc}\n\nDoi pass ngay!")
        elif p['type'] == 'tool':
            bot.send_message(chat_id, f"GIAO HANG THANH CONG\n\nSP: {p['name']}\nMa: {order_code}\n\nLink tool:\n{p.get('link', 'https://github.com/hdm-shop/tools')}")
        elif p['type'] == 'tut':
            bot.send_message(chat_id, f"GIAO HANG THANH CONG\n\nSP: {p['name']}\nMa: {order_code}\n\nLink tai lieu:\n{p.get('link', 'https://drive.google.com/hdm-tuts')}")
        order['status'] = 'completed'
        order['completed_at'] = datetime.now().isoformat()
        db['orders'].append(order)
        del db['pending'][order_code]
        save_db(db)
        bot.send_message(ADMIN_ID, f"DON TU DONG DUYET\n\nMa: {order_code}\n@{order['username']}\nSP: {p['name']}\nTien: {order['price']:,}d")
    except Exception as e:
        print(f'Auto deliver error: {e}')
        bot.send_message(ADMIN_ID, f'Loi don {order_code}: {e}')

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
        bot.send_message(chat_id, 'Khong co don cho!')
        return
    oid, order = user_order
    bot.send_photo(ADMIN_ID, photo_id, caption=f"BILL\n\nMa: {oid}\n@{order['username']}\nSP: {order['product_name']}\nTien: {order['price']:,}d", reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton('GUI HANG', callback_data=f'manual_{oid}'), types.InlineKeyboardButton('TU CHOI', callback_data=f'reject_{oid}')))
    bot.send_message(chat_id, 'Da gui bill!')

@bot.callback_query_handler(func=lambda c: c.data.startswith('manual_'))
def admin_manual(call):
    if call.from_user.id != ADMIN_ID:
        return
    oid = call.data.replace('manual_', '')
    db = load_db()
    if oid in db['pending']:
        auto_deliver(oid, db['pending'][oid])
        bot.answer_callback_query(call.id, 'Da gui!')

@bot.callback_query_handler(func=lambda c: c.data.startswith('reject_'))
def admin_reject(call):
    if call.from_user.id != ADMIN_ID:
        return
    oid = call.data.replace('reject_', '')
    db = load_db()
    if oid in db['pending']:
        order = db['pending'][oid]
        bot.send_message(order['chat_id'], 'Don bi tu choi!')
        order['status'] = 'rejected'
        db['orders'].append(order)
        del db['pending'][oid]
        save_db(db)
        bot.answer_callback_query(call.id, 'Da tu choi!')

@bot.message_handler(commands=['tips'])
def cmd_tips(msg):
    db = load_db()
    tips = db.get('tips', [])
    markup = types.InlineKeyboardMarkup(row_width=1)
    for i, tip in enumerate(tips):
        markup.add(types.InlineKeyboardButton(tip['title'], callback_data=f'tip_{i}'))
    markup.add(types.InlineKeyboardButton('Dang bai', callback_data='post_tip'), types.InlineKeyboardButton('Quay lai', callback_data='back_menu'))
    bot.send_message(msg.chat.id, "MEO FREE\n\nChon bai viet:", reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data == 'cat_tips')
def cat_tips_cb(call):
    db = load_db()
    tips = db.get('tips', [])
    markup = types.InlineKeyboardMarkup(row_width=1)
    for i, tip in enumerate(tips):
        markup.add(types.InlineKeyboardButton(tip['title'], callback_data=f'tip_{i}'))
    markup.add(types.InlineKeyboardButton('Dang bai', callback_data='post_tip'), types.InlineKeyboardButton('Quay lai', callback_data='back_menu'))
    bot.edit_message_text("MEO FREE\n\nChon bai viet:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data.startswith('tip_'))
def show_tip(call):
    idx = int(call.data.replace('tip_', ''))
    db = load_db()
    tips = db.get('tips', [])
    if idx >= len(tips):
        return
    tip = tips[idx]
    bot.edit_message_text(f"{tip['title']}\n\n{tip['content']}\n\n@{tip['author']} - {tip['time']}", call.message.chat.id, call.message.message_id, reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton('Quay lai', callback_data='cat_tips')))

@bot.callback_query_handler(func=lambda c: c.data == 'post_tip')
def post_tip(call):
    bot.send_message(call.from_user.id, "DANG MEO\n\nFormat: Tieu de | Noi dung")

@bot.message_handler(func=lambda m: '|' in m.text and len(m.text) < 1000 and m.chat.id != ADMIN_ID)
def receive_tip(msg):
    parts = msg.text.split('|', 1)
    if len(parts) != 2:
        return
    title = parts[0].strip()
    content = parts[1].strip()
    db = load_db()
    db['tips'].append({'title': title, 'content': content, 'author': msg.from_user.username or msg.from_user.first_name, 'time': datetime.now().strftime('%d/%m/%Y %H:%M')})
    save_db(db)
    bot.send_message(msg.chat.id, f"Da dang: {title}")
    bot.send_message(ADMIN_ID, f"Bai moi: {title}")

@bot.message_handler(commands=['admin'])
def admin_panel(msg):
    if msg.chat.id != ADMIN_ID:
        return
    db = load_db()
    total = sum(o['price'] for o in db['orders'] if o['status'] == 'completed')
    bot.send_message(ADMIN_ID, f"ADMIN PANEL\n\nUsers: {len(db['users'])}\nSP: {len(db['products'])}\nDon xong: {len(db['orders'])}\nCho: {len(db['pending'])}\nDoanh thu: {total:,}d\n\nLENH:\n/addproduct |pid|ten|gia|loai|mo_ta|link|\n/setprice <pid> <gia>\n/delproduct <pid>\n/addacc <pid> <acc>\n/addlist <pid> + list\n/kho hoac /kho <pid>\n/broadcast <text>\n/stats")

@bot.message_handler(commands=['addproduct'])
def admin_addproduct(msg):
    if msg.chat.id != ADMIN_ID:
        return
    try:
        content = msg.text.replace('/addproduct', '').strip()
        parts = [p.strip() for p in content.split('|') if p.strip()]
        if len(parts) < 5:
            bot.send_message(ADMIN_ID, "Dung: /addproduct |pid|ten|gia|loai|mo_ta|link|\nLoai: account / tool / tut")
            return
        pid = parts[0]
        name = parts[1]
        price = int(parts[2])
        ptype = parts[3].lower()
        desc = parts[4]
        link = parts[5] if len(parts) > 5 else ''
        if ptype not in ['account', 'tool', 'tut']:
            bot.send_message(ADMIN_ID, "Loai phai la: account / tool / tut")
            return
        db = load_db()
        if pid in db['products']:
            bot.send_message(ADMIN_ID, f"PID {pid} da ton tai!")
            return
        db['products'][pid] = {'name': name, 'price': price, 'stock': 0 if ptype == 'account' else 999, 'type': ptype, 'desc': desc, 'link': link}
        if ptype == 'account':
            db['inventory'][pid] = []
        save_db(db)
        bot.send_message(ADMIN_ID, f"DA THEM SP\n\nPID: {pid}\nTen: {name}\nGia: {price:,}d\nLoai: {ptype}")
    except Exception as e:
        bot.send_message(ADMIN_ID, f"Loi: {e}")

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
            bot.send_message(ADMIN_ID, f"Doi gia {pid}: {old:,}d -> {new_price:,}d")
        else:
            bot.send_message(ADMIN_ID, f"Khong tim thay {pid}")
    except:
        bot.send_message(ADMIN_ID, "Dung: /setprice <pid> <gia>")

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
            bot.send_message(ADMIN_ID, f"Da xoa: {name}")
        else:
            bot.send_message(ADMIN_ID, f"Khong tim thay {pid}")
    except:
        bot.send_message(ADMIN_ID, "Dung: /delproduct <pid>")

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
            bot.send_message(ADMIN_ID, f"SP {pid} khong ton tai!")
            return
        if pid not in db['inventory']:
            db['inventory'][pid] = []
        db['inventory'][pid].append(acc)
        db['products'][pid]['stock'] = len(db['inventory'][pid])
        save_db(db)
        bot.send_message(ADMIN_ID, f"Da them acc vao {pid}\nKho: {db['products'][pid]['stock']}")
    except:
        bot.send_message(ADMIN_ID, "Dung: /addacc <pid> <acc>")

@bot.message_handler(commands=['addlist'])
def admin_addlist(msg):
    if msg.chat.id != ADMIN_ID:
        return
    try:
        lines = msg.text.split('\n')
        first = lines[0].strip().split()
        if len(first) < 2:
            bot.send_message(ADMIN_ID, "Dung:\n/addlist <pid>\ntk1|mk1|nam1|2fa1|cookie1\ntk2|mk2|nam2|2fa2|cookie2")
            return
        pid = first[1].strip()
        acc_lines = [l.strip() for l in lines[1:] if l.strip()]
        if not acc_lines:
            bot.send_message(ADMIN_ID, "Khong co acc!")
            return
        db = load_db()
        if pid not in db['products']:
            bot.send_message(ADMIN_ID, f"SP {pid} khong ton tai!")
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
        bot.send_message(ADMIN_ID, f"DA THEM {added} ACC\n\nSP: {db['products'][pid]['name']}\nTong kho: {db['products'][pid]['stock']}")
    except Exception as e:
        bot.send_message(ADMIN_ID, f"Loi: {e}")

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
                bot.send_message(ADMIN_ID, f"Khong co kho {pid}")
                return
            inv = db['inventory'][pid]
            if not inv:
                bot.send_message(ADMIN_ID, f"Kho {pid} trong")
                return
            text = f"KHO: {pid} ({len(inv)})\n\n"
            for i, acc in enumerate(inv[:30], 1):
                p = acc.split('|')
                tk = p[0] if len(p) > 0 else ''
                nam = p[2] if len(p) > 2 else ''
                has2fa = 'Y' if len(p) > 3 and p[3] else 'N'
                hasck = 'Y' if len(p) > 4 and p[4] else 'N'
                text += f"{i}. {tk} | {nam} | 2FA:{has2fa} | CK:{hasck}\n"
            if len(inv) > 30:
                text += f"\n... va {len(inv) - 30} acc khac"
            bot.send_message(ADMIN_ID, text)
        else:
            text = "TAT CA KHO\n\n"
            total = 0
            for pid, inv in db['inventory'].items():
                name = db['products'].get(pid, {}).get('name', pid)
                text += f"- {name}: {len(inv)} acc\n"
                total += len(inv)
            text += f"\nTONG: {total} acc"
            bot.send_message(ADMIN_ID, text)
    except Exception as e:
        bot.send_message(ADMIN_ID, f"Loi: {e}")

@bot.message_handler(commands=['broadcast'])
def admin_broadcast(msg):
    if msg.chat.id != ADMIN_ID:
        return
    content = msg.text.replace('/broadcast', '').strip()
    if not content:
        bot.send_message(ADMIN_ID, "Dung: /broadcast <noi dung>")
        return
    db = load_db()
    users = list(db['users'].keys())
    success = 0
    for uid in users:
        try:
            bot.send_message(int(uid), f"THONG BAO\n\n{content}")
            success += 1
        except:
            pass
    bot.send_message(ADMIN_ID, f"Da gui den {success}/{len(users)}")

@bot.message_handler(commands=['stats'])
def admin_stats(msg):
    if msg.chat.id != ADMIN_ID:
        return
    db = load_db()
    text = "THONG KE\n\n"
    for pid, p in db['products'].items():
        sold = sum(1 for o in db['orders'] if o['product_id'] == pid and o['status'] == 'completed')
        text += f"{p['name']}\n   {p['price']:,}d | Ban: {sold} | Kho: {p['stock']}\n"
    total = sum(o['price'] for o in db['orders'] if o['status'] == 'completed')
    text += f"\nTONG: {total:,}d\nUsers: {len(db['users'])}"
    bot.send_message(ADMIN_ID, text)

@bot.callback_query_handler(func=lambda c: c.data == 'back_menu')
def back_menu(call):
    bot.edit_message_text("HDM SHOP\n\nChon san pham:", call.message.chat.id, call.message.message_id, reply_markup=main_menu())

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
    print("HDM SHOP BOT dang chay...")
    print(f"Admin: {ADMIN_ID}")
    print(f"Bank: {BANK_INFO['bank']} - {BANK_INFO['account']}")
    port = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=port)
