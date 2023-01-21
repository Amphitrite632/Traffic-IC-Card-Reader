import nfc
import time
import math
import struct
import datetime
import pandas as pd

SEPARATOR = "==================#=================="

CSV_KEYS = ("kind", "lineID", "stationID",
            "companyName", "lineName",  "stationName")

EXCEPTIONAL_LINE = [
    "ゆりかもめ",
    "つくばエクスプレス",
    "アストラムライン",
    "金沢シーサイドライン",
    "東京モノレール",
    "東部丘陵リニモ",
    "ディズニーリゾートライン",
    "日暮里・舎人ライナー",
    "生駒ケーブル",
    "西信貴ケーブル",
]

SERVICE_CODE = 0x090f

def timestamp():
    now = datetime.datetime.now()
    timestamp = datetime.datetime(
        now.year, now.month, now.day, now.hour, now.minute, now.second)
    return (f"[Timestamp] {timestamp}")


def procTime(begin):
    proc_time = (math.floor((time.perf_counter_ns() - begin) / 10000)) / 100
    return (f"{proc_time}ms")


def getConsole(num):
    console = {
        0x03: "精算機",
        0x04: "携帯型端末",
        0x05: "車載端末",
        0x07: "券売機",
        0x08: "券売機",
        0x09: "入金機",
        0x12: "券売機",
        0x14: "券売機等",
        0x15: "券売機等",
        0x16: "改札機",
        0x17: "簡易改札機",
        0x18: "窓口端末",
        0x19: "窓口端末",
        0x1A: "改札端末",
        0x1B: "携帯電話",
        0x1C: "乗継精算機",
        0x1D: "連絡改札機",
        0x1F: "簡易入金機",
        0x23: "不明（改札機？）",
        0x46: "VIEW ALTTE",
        0x47: "VIEW ALTTE",
        0xC7: "物販端末",
        0xC8: "自販機",
    }.get(num)

    if console == None:
        console = (f"不明（{hex(num)}）")

    return console


def getCategory(num):
    category = {
        0x01: "運賃支払",
        0x02: "チャージ",
        0x03: "乗車券購入",
        0x04: "清算",
        0x05: "入場清算",
        0x06: "窓口処理",
        0x07: "新規発行",
        0x08: "窓口控除",
        0x0D: "バス",
        0x0F: "バス",
        0x11: "再発行",
        0x13: "新幹線利用",
        0x14: "自動チャージ",
        0x15: "自動チャージ",
        0x1F: "入金（バス）",
        0x46: "物販",
        0x48: "特典チャージ",
        0x49: "入金（レジ）",
        0x4A: "物販取り消し",
        0x4B: "入場物販",
        0xC6: "現金併用物販",
        0x84: "他社清算",
        0x85: "他社入場清算",
    }.get(num)

    if category == None:
        category = (f"不明（{hex(num)}）")

    return category


def getPaymentDate(date):
    payment_year = (date >> 9) & 0x7f
    payment_month = (date >> 5) & 0x0f
    payment_day = (date >> 0) & 0x1f

    this_year = str(datetime.datetime.now().year)
    payment_year = this_year[0] + this_year[1] + str(payment_year)

    return (f"{payment_year}/{payment_month}/{payment_day}")


def getStation(lineID, stationID):
    try:
        station = STATIONLIST.query(
            "lineID==@lineID and stationID==@stationID").stationName.values[0] + "駅"
    except IndexError:
        station = "駅名不明"
        
    try:
        line = STATIONLIST.query(
            "lineID==@lineID and stationID==@stationID").lineName.values[0]
        if not line in EXCEPTIONAL_LINE:
            line += "線"
    except IndexError:
        line = "路線不明"

    return (f"{station}（{line}）")


def printLog(texts):
    log: str = ""
    for text in texts:
        log += (f"{text}\n")
    print(f"\033[32m{SEPARATOR}\n{log}{timestamp()}\n{SEPARATOR}\n\033[0m")


def initialize():
    global STATIONLIST

    printLog(["[System] Initializing..."])

    proc_begin = time.perf_counter_ns()
    STATIONLIST = pd.read_csv("StationCode.csv", names=CSV_KEYS)

    try:
        clf = nfc.ContactlessFrontend("usb")
    except OSError:
        printLog(["[System] Error: Device not found.", "[System] Terminating program..."])
        exit(1)

    printLog([f"[System] Initialize: done({procTime(proc_begin)})",
              "[System] Please touch card."])

    clf.connect(rdwr={"targets": ["212F"], "on-connect": onConnect})


def onConnect(tag):
    global history_length

    printLog(["[System] Card detected.", "[System] Loading card information..."])

    system_code = (tag.dump()[0]).removeprefix("System ")

    if "0003" in system_code:
        pass
    elif system_code == "This is not an NFC Forum Tag.":
        printLog(["[System] Unknown card detected.", "[System] Terminating program..."])
        exit(1)
    else:
        printLog(["[System] Incompatible card detected.", f"[Info] System-code:{system_code}", "[System] Terminating program..."])
        exit(1)

    proc_begin = time.perf_counter_ns()
    datas = []

    for i in range(20):
        sc = nfc.tag.tt3.ServiceCode(SERVICE_CODE >> 6, SERVICE_CODE & 0x3f)
        bc = nfc.tag.tt3.BlockCode(i, service=0)
        datas += [tag.read_without_encryption([sc], [bc])]

    printLog(
        [f"[System] Read data: done({procTime(proc_begin)})", "[System] Please release card."])

    history_length = len(datas) - 1
    showHistory(datas, 0)


def showHistory(datas, index):
    global history_length

    no_gate_flag = False
    data = datas[index]
    row_be = struct.unpack(">2B2H4BH4B", bytes(data))
    row_le = struct.unpack("<2B2H4BH4B", data)

    iteration_number = (f"[System] 表示中の履歴情報: {index + 1}件目")
    for i, v in enumerate(data):
        if i == 0:
            console_info = getConsole(v)
            payment_console = (f"[Info] 端末種別:{console_info}")
            if console_info in ["車載端末", "物販端末", "自販機"]:
                no_gate_flag = True
        elif i == 1:
            payment_category = (f"[Info] 決済種別:{getCategory(v)}")
            if ("チャージ" in payment_category) | ("入金" in payment_category):
                no_gate_flag = True
        elif i == 4:
            payment_date = (f"[Info] 決済日　:{getPaymentDate(row_be[3])}")
        elif i == 6:
            if no_gate_flag:
                station_enter = ("[Info] 乗車駅　:----")
            else:
                station_enter = (
                    f"[Info] 乗車駅　:{getStation(row_be[4], row_be[5])}")
        elif i == 8:
            if no_gate_flag:
                station_exit = ("[Info] 降車駅　:----")
            else:
                station_exit = (
                    f"[Info] 降車駅　:{getStation(row_be[6], row_be[7])}")
        elif i == 10:
            card_balance = (f"[Info] 残高　　:{row_le[8]}円")
        
    printLog([iteration_number, payment_console, payment_category, payment_date, station_enter, station_exit, card_balance])
    if index < 19:
        print("Press Enter to display the previous payment")
        input()
        showHistory(datas, index + 1)
    else:
        print("Press Enter to exit program")
        input()
        exit(0)
    

if __name__ == "__main__":
    initialize()
