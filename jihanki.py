import csv
import time
import os
from collections import defaultdict


# ★追加：このPythonファイルが置かれているフォルダを基準にCSVを参照する
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ★追加：CSVファイルのパスを固定
ITEMS_FILE = os.path.join(BASE_DIR, "items.csv")
MONEY_FILE = os.path.join(BASE_DIR, "money.csv")
SALE_FILE = os.path.join(BASE_DIR, "sale.csv")


# ---------- データクラス ----------

class Item:
    def __init__(self, code, name, price, stock):
        self.code = code
        self.name = name
        self.price = price
        self.stock = stock


# ---------- 金銭管理 ----------

class MoneyManager:
    MONEY_KEYS = {
        "1": 10,
        "2": 50,
        "3": 100,
        "4": 500,
        "5": 1000
    }

    def __init__(self):
        self.money_stock = {}
        self.inserted_total = 0
        self.inserted_count = defaultdict(int)
        self.inserted_money = defaultdict(int)
        self.sales_total = 0

    def load_money(self, filepath):
        print("読み込んでいるmoney.csv:", filepath)

        self.money_stock.clear()

        with open(filepath, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)

            for row in reader:
                denomination = int(row["denomination"])
                count = int(row["count"])
                self.money_stock[denomination] = count

        print("読み込み後のmoney_stock:", self.money_stock)

    def save_money(self, filepath):
        with open(filepath, mode="w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)

            writer.writerow(["denomination", "count"])

            for coin in [10, 50, 100, 500, 1000]:
                writer.writerow([coin, self.money_stock.get(coin, 0)])

    def load_sales(self, filepath):
        with open(filepath, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)

            for row in reader:
                self.sales_total = int(row["sales"])

    def save_sales(self, filepath):
        with open(filepath, mode="w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)

            writer.writerow(["sales"])
            writer.writerow([self.sales_total])

    def insert_money(self, key):
        value = self.MONEY_KEYS[key]

        # ★追加：投入可能金額の上限1990円チェック
        if self.inserted_total + value > 1990:
            print("\033[31m 投入可能な金額の上限1990円を超えています。\033[0m")
            time.sleep(2)
            return False

        limit = 2 if value == 1000 else 20

        if self.inserted_count[value] >= limit:
            print("\033[31m 投入枚数が上限を超えています。\033[0m")
            time.sleep(2)
            return False

        self.inserted_total += value
        self.inserted_count[value] += 1

        # 投入中のお金として一時保持する
        # この時点ではmoney_stockには入れない
        self.inserted_money[value] += 1

        return True

    def commit_inserted_money(self):
        # 購入成立時だけ、投入中のお金を自販機内部在庫へ反映する
        for coin, count in self.inserted_money.items():
            self.money_stock[coin] = self.money_stock.get(coin, 0) + count

    def can_return_change(self, change):
        # 購入成立後は投入金も自販機内に入るため、
        # 釣銭判定時だけ一時的に投入金を含める
        temp_stock = self.money_stock.copy()

        for coin, count in self.inserted_money.items():
            temp_stock[coin] = temp_stock.get(coin, 0) + count

        remaining = change

        for coin in [1000, 500, 100, 50, 10]:
            use = min(temp_stock.get(coin, 0), remaining // coin)
            remaining -= use * coin

        return remaining == 0

    def calculate_change_detail(self, change):
        remaining = change
        change_detail = {}

        for coin in [1000, 500, 100, 50, 10]:
            use = min(self.money_stock.get(coin, 0), remaining // coin)

            if use > 0:
                change_detail[coin] = use

            remaining -= use * coin

        if remaining != 0:
            return None

        return change_detail

    def return_change(self, change):
        change_detail = self.calculate_change_detail(change)

        if change_detail is None:
            return None

        for coin, count in change_detail.items():
            self.money_stock[coin] -= count

        return change_detail

    def display_money_stock(self):
        print("\n--- 釣銭用金銭残数確認 ---")

        for coin in [10, 50, 100, 500, 1000]:
            print(f"{coin}円: {self.money_stock.get(coin, 0)}枚")

    def reset(self):
        self.inserted_total = 0
        self.inserted_count.clear()
        self.inserted_money.clear()


# ---------- 商品管理 ----------

class ItemManager:
    ITEM_KEYS = {"A", "B", "C", "D", "E"}

    def __init__(self, money_manager):
        self.items = []
        self.money_manager = money_manager

    def load_items(self, filepath):
        self.items.clear()

        with open(filepath, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)

            for row in reader:
                self.items.append(
                    Item(
                        row["code"],
                        row["name"],
                        int(row["price"]),
                        int(row["stock"])
                    )
                )

    def save_items(self, filepath):
        with open(filepath, mode="w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)

            writer.writerow(["code", "name", "price", "stock"])

            for item in self.items:
                writer.writerow([
                    item.code,
                    item.name,
                    item.price,
                    item.stock
                ])

    def display_items(self):
        for item in self.items:
            if item.stock == 0:
                print(f"{item.code} {item.name}\033[31m 売切\033[0m")

            elif item.price <= self.money_manager.inserted_total:
                print(f"{item.code} {item.name}\033[34m {item.price}円\033[0m")

            else:
                print(f"{item.code} {item.name} {item.price}円")

    def display_stock_status(self):
        print("\n--- 商品残数確認 ---")

        for item in self.items:
            print(f"{item.code} {item.name}: {item.stock}本")

    def select_item(self, code):
        item = next((i for i in self.items if i.code == code), None)

        if item is None:
            return False

        if item.stock == 0:
            print("\033[31m 売切れ商品です。他の商品を選択してください。\033[0m")
            time.sleep(2)
            return False

        if self.money_manager.inserted_total < item.price:
            print("\033[31m 投入金額が不足しています。\033[0m")
            time.sleep(2)
            return False

        change = self.money_manager.inserted_total - item.price

        if not self.money_manager.can_return_change(change):
            print("\033[31m 硬貨の釣銭切れのため購入できません。\033[0m")
            time.sleep(2)
            return False

        # ---------- 購入成立 ----------

        # 商品在庫を減らす
        item.stock -= 1

        # 売上を加算する
        self.money_manager.sales_total += item.price

        # 投入中のお金を自販機内部在庫に反映する
        self.money_manager.commit_inserted_money()

        # 釣銭を返却する
        change_detail = self.money_manager.return_change(change)

        # ---------- CSV保存 ----------

        self.save_items(ITEMS_FILE)
        self.money_manager.save_money(MONEY_FILE)
        self.money_manager.save_sales(SALE_FILE)

        print(f"\033[34m \n{item.name} の購入ありがとうございました。\033[0m")

        if change > 0:
            print(f"\033[34mお釣り {change}円 をお受け取りください。\033[0m")
            print("\033[34m釣銭内訳:\033[0m")

            for coin, count in change_detail.items():
                print(f"\033[34m{coin}円: {count}枚\033[0m")

        time.sleep(10)

        self.money_manager.reset()

        return True


# ---------- メイン制御 ----------

class VendMachineController:
    def __init__(self):
        self.money = MoneyManager()
        self.items = ItemManager(self.money)

    def setup(self):
        self.items.load_items(ITEMS_FILE)
        self.money.load_money(MONEY_FILE)
        self.money.load_sales(SALE_FILE)

    def clear(self):
        os.system("cls" if os.name == "nt" else "clear")

    def display_admin_status(self):
        self.clear()

        # 管理画面表示前に固定パスのCSVを再読み込みする
        self.items.load_items(ITEMS_FILE)
        self.money.load_money(MONEY_FILE)
        self.money.load_sales(SALE_FILE)

        print("*** 管理情報確認画面 ***")

        self.items.display_stock_status()

        print("\n--- 売上金額確認 ---")
        print(f"現在の売上金額: {self.money.sales_total}円")

        self.money.display_money_stock()

        input("\nEnterキーで購入画面に戻ります")

    def refund_inserted_money(self):
        refund = self.money.inserted_total

        if refund <= 0:
            return

        print(f"返金 {refund}円")
        print("返金内訳:")

        for coin in [1000, 500, 100, 50, 10]:
            count = self.money.inserted_money.get(coin, 0)

            if count > 0:
                print(f"{coin}円: {count}枚")

        # 返金時は購入成立していないため、money_stockは変更しない
        self.money.reset()

    def run(self):
        self.setup()

        while True:
            self.clear()

            print("*** 自動販売機 シミュレーション ソフトウェア ***")

            self.items.display_items()

            print(f"\n投入金額: {self.money.inserted_total}円")

            print("お金を入れてください。")
            print("1=10円 2=50円 3=100円 4=500円 5=1000円 staff code=99")

            print("商品を選択してください。 A/B/C/D/E")

            print("終了する場合は 9 を入力してください。")

            key = input(">> ").strip().upper()

            if key == "99":
                self.display_admin_status()
                continue

            if key == "9":
                self.refund_inserted_money()
                time.sleep(10)
                break

            if key in MoneyManager.MONEY_KEYS:
                self.money.insert_money(key)

            elif key in ItemManager.ITEM_KEYS:
                self.items.select_item(key)


# ---------- 実行 ----------

if __name__ == "__main__":
    VendMachineController().run()
