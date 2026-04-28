import json
import os
from datetime import datetime, timedelta, timezone

KST = timezone(timedelta(hours=9))

from flask import Blueprint, abort, current_app, flash, jsonify, redirect, render_template, request, send_file, session, url_for

from ..db import get_db
from ..services.news_service import stock_news_items
from ..utils.decorators import login_required


main_bp = Blueprint("main", __name__)

HOME_HISTORY_LIMIT = 60
REWARD_BALANCE_THRESHOLD = 30_000_000_000
REWARD_EXCLUDED_USERNAME = "user162"
REWARD_FLAG = "FLAG-VT-300EOK-CLUB"
REWARD_IMAGE_NAME = "starbucks_americano_gifticon.png"


def transaction_label(tx_type):
    return {
        "buy": "매수",
        "sell": "매도",
        "transfer_in": "입금",
        "transfer_out": "출금",
    }.get(tx_type, tx_type)


def history_payload(history_rows, current_price, time_format="%H:%M:%S"):
    prices = [row["current_price"] for row in history_rows] or [current_price]
    kst_times = [row["recorded_at"].replace(tzinfo=timezone.utc).astimezone(KST) for row in history_rows]
    timestamps = [dt.strftime("%Y-%m-%d %H:%M:%S") for dt in kst_times]
    labels = [dt.strftime(time_format) for dt in kst_times] or ["지금"]
    return prices, timestamps, labels


def enrich_stock_cards(cursor, stocks):
    enriched = []
    for stock in stocks:
        cursor.execute(
            """
            SELECT current_price, recorded_at
            FROM stock_price_history
            WHERE stock_id=%s
            ORDER BY recorded_at DESC
            LIMIT %s
            """,
            (stock["id"], HOME_HISTORY_LIMIT),
        )
        history_rows = list(reversed(cursor.fetchall()))
        prices, timestamps, labels = history_payload(history_rows, stock["current_price"])
        previous_price = prices[-2] if len(prices) > 1 else prices[-1]
        change_amount = stock["current_price"] - previous_price
        change_rate = round((change_amount / previous_price) * 100, 2) if previous_price else 0

        stock["previous_price"] = previous_price
        stock["change_amount"] = change_amount
        stock["change_rate"] = change_rate
        stock["history_prices"] = prices
        stock["history_labels"] = labels
        stock["history_timestamps"] = timestamps
        stock["detail_url"] = url_for("stocks.stock_detail", stock_id=stock["id"])
        stock["latest_time_label"] = labels[-1] if labels else datetime.now().strftime("%H:%M:%S")
        stock["news_items"] = stock_news_items(stock)
        stock["preview_json"] = json.dumps(
            {
                "stock": stock["name"],
                "symbol": stock["symbol"],
                "current_price": stock["current_price"],
                "change_amount": change_amount,
                "change_rate": change_rate,
                "prices": prices,
                "labels": labels,
                "timestamps": timestamps,
                "detail_url": stock["detail_url"],
                "latest_time_label": stock["latest_time_label"],
                "news_items": stock["news_items"],
            },
            ensure_ascii=False,
        )
        enriched.append(stock)
    return enriched


def build_order_meta(tx):
    quantity = tx["quantity"] or 0
    unit_price = int(tx["amount"] / max(quantity, 1))
    return f"{tx['symbol'] or '-'} · {quantity}주 · {unit_price:,}원"


def build_transfer_meta(tx):
    direction = "출금" if tx["type"] == "transfer_out" else "입금"
    return f"{direction} · {tx['sender_name'] or '-'} → {tx['receiver_name'] or '-'}"


def load_home_data():
    db = get_db()
    cash_balance = 0
    portfolio = []
    recent_orders = []
    recent_transfers = []

    with db.cursor() as cursor:
        cursor.execute(
            """
            SELECT s.*, h.quantity, h.avg_price
            FROM holdings h
            JOIN stocks s ON s.id = h.stock_id
            WHERE h.user_id=%s
            ORDER BY (s.current_price * h.quantity) DESC, s.name
            """,
            (session.get("user_id", 0),),
        )
        portfolio = cursor.fetchall()

        cursor.execute("SELECT id, name, symbol, current_price FROM stocks ORDER BY current_price DESC, id")
        stocks = enrich_stock_cards(cursor, cursor.fetchall())

        cursor.execute(
            """
            SELECT p.id, p.title, p.content, p.created_at, u.display_name
            FROM posts p
            JOIN users u ON u.id = p.user_id
            ORDER BY p.created_at DESC
            LIMIT 4
            """
        )
        recent_posts = cursor.fetchall()

        if session.get("user_id"):
            cursor.execute("SELECT balance FROM users WHERE id=%s", (session["user_id"],))
            user_row = cursor.fetchone()
            cash_balance = user_row["balance"] if user_row else 0

            cursor.execute(
                """
                SELECT t.*, s.symbol
                FROM transactions t
                LEFT JOIN stocks s ON s.id = t.stock_id
                WHERE t.user_id=%s
                  AND t.type IN ('buy', 'sell')
                ORDER BY t.created_at DESC
                LIMIT 6
                """,
                (session["user_id"],),
            )
            recent_orders = cursor.fetchall()

            cursor.execute(
                """
                SELECT t.*,
                       sender.display_name AS sender_name,
                       receiver.display_name AS receiver_name
                FROM transactions t
                LEFT JOIN users sender ON sender.id = CASE
                    WHEN t.type='transfer_out' THEN t.user_id
                    WHEN t.type='transfer_in' THEN t.target_user_id
                    ELSE NULL
                END
                LEFT JOIN users receiver ON receiver.id = CASE
                    WHEN t.type='transfer_out' THEN t.target_user_id
                    WHEN t.type='transfer_in' THEN t.user_id
                    ELSE NULL
                END
                WHERE t.user_id=%s
                  AND t.type IN ('transfer_in', 'transfer_out')
                ORDER BY t.created_at DESC
                LIMIT 6
                """,
                (session["user_id"],),
            )
            recent_transfers = cursor.fetchall()

    total_stock_value = sum(item["current_price"] * item["quantity"] for item in portfolio)
    total_assets = cash_balance + total_stock_value

    for item in portfolio:
        current_value = item["current_price"] * item["quantity"]
        invested_amount = item["avg_price"] * item["quantity"]
        profit = current_value - invested_amount
        profit_rate = round((profit / max(invested_amount, 1)) * 100, 2)
        item["current_value"] = current_value
        item["profit"] = profit
        item["profit_rate"] = profit_rate

    for tx in recent_orders:
        tx["display_type"] = transaction_label(tx["type"])
        tx["meta"] = build_order_meta(tx)

    for tx in recent_transfers:
        tx["display_type"] = transaction_label(tx["type"])
        tx["meta"] = build_transfer_meta(tx)

    return {
        "portfolio": portfolio,
        "account_stocks": portfolio[:6],
        "stocks": stocks,
        "recent_posts": recent_posts,
        "recent_orders": recent_orders,
        "recent_transfers": recent_transfers,
        "total_assets": total_assets,
        "cash_balance": cash_balance,
        "total_stock_value": total_stock_value,
        "preview_stock": stocks[0] if stocks else None,
    }


@main_bp.app_context_processor
def inject_user():
    user = None
    reward_flag = None
    if session.get("user_id"):
        db = get_db()
        with db.cursor() as cursor:
            cursor.execute(
                "SELECT id, username, display_name, balance, role FROM users WHERE id=%s",
                (session["user_id"],),
            )
            user = cursor.fetchone()
        if (
            user
            and user["role"] != "admin"
            and user["username"] != REWARD_EXCLUDED_USERNAME
            and user["balance"] >= REWARD_BALANCE_THRESHOLD
        ):
            reward_flag = REWARD_FLAG
    return {"current_user": user, "reward_flag": reward_flag}


@main_bp.route("/")
def index():
    return render_template("index.html", **load_home_data())


@main_bp.route("/vuln_flag", methods=["GET", "POST"])
def vuln_flag():
    if request.method == "POST":
        submitted_flag = request.form.get("flag", "").strip()
        if submitted_flag == REWARD_FLAG:
            return redirect(url_for("main.vuln_flag_image", token=REWARD_FLAG))
        flash("flag 값이 올바르지 않습니다.", "error")
    return render_template("vuln_flag.html")


@main_bp.route("/vuln_flag/reward/<path:token>")
def vuln_flag_image(token):
    if token != REWARD_FLAG:
        abort(404)
    reward_path = os.path.join(current_app.root_path, "rewards", REWARD_IMAGE_NAME)
    if not os.path.exists(reward_path):
        abort(404)
    return send_file(reward_path, mimetype="image/png")


@main_bp.route("/market-snapshot")
def market_snapshot():
    payload = load_home_data()
    return jsonify(
        {
            "stocks": [
                {
                    "id": stock["id"],
                    "name": stock["name"],
                    "symbol": stock["symbol"],
                    "current_price": stock["current_price"],
                    "change_amount": stock["change_amount"],
                    "change_rate": stock["change_rate"],
                    "history_prices": stock["history_prices"],
                    "history_labels": stock["history_labels"],
                    "history_timestamps": stock["history_timestamps"],
                    "preview_json": stock["preview_json"],
                    "detail_url": stock["detail_url"],
                    "latest_time_label": stock["latest_time_label"],
                    "news_items": stock["news_items"],
                }
                for stock in payload["stocks"]
            ],
            "cash_balance": payload["cash_balance"],
            "total_stock_value": payload["total_stock_value"],
            "total_assets": payload["total_assets"],
            "account_stocks": [
                {
                    "id": item["id"],
                    "name": item["name"],
                    "quantity": item["quantity"],
                    "avg_price": item["avg_price"],
                    "current_value": item["current_value"],
                    "profit": item["profit"],
                    "profit_rate": item["profit_rate"],
                }
                for item in payload["account_stocks"]
            ],
            "recent_orders": [
                {
                    "display_type": tx["display_type"],
                    "meta": tx["meta"],
                }
                for tx in payload["recent_orders"]
            ],
            "recent_transfers": [
                {
                    "display_type": tx["display_type"],
                    "meta": tx["meta"],
                    "amount": tx["amount"],
                }
                for tx in payload["recent_transfers"]
            ],
        }
    )


@main_bp.route("/mypage")
@login_required
def profile():
    target_user_id = request.args.get("user_id", session["user_id"])
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute(
            "SELECT id, username, display_name, balance, role, created_at FROM users WHERE id=%s",
            (target_user_id,),
        )
        profile_data = cursor.fetchone()

    if not profile_data:
        flash("사용자를 찾을 수 없습니다.", "error")
        return redirect(url_for("main.index"))

    with db.cursor() as cursor:
        cursor.execute(
            """
            SELECT h.*, s.name, s.symbol, s.current_price
            FROM holdings h
            JOIN stocks s ON s.id = h.stock_id
            WHERE h.user_id=%s
            ORDER BY (s.current_price * h.quantity) DESC
            """,
            (target_user_id,),
        )
        holdings = cursor.fetchall()

        cursor.execute(
            """
            SELECT t.*, s.name AS stock_name, s.symbol
            FROM transactions t
            LEFT JOIN stocks s ON s.id = t.stock_id
            WHERE t.user_id=%s AND t.type IN ('buy', 'sell')
            ORDER BY t.created_at DESC LIMIT 5
            """,
            (target_user_id,),
        )
        recent_trades = cursor.fetchall()

        cursor.execute(
            """
            SELECT t.*,
                   sender.display_name AS sender_name,
                   receiver.display_name AS receiver_name
            FROM transactions t
            LEFT JOIN users sender ON sender.id = CASE
                WHEN t.type='transfer_out' THEN t.user_id
                WHEN t.type='transfer_in' THEN t.target_user_id
                ELSE NULL END
            LEFT JOIN users receiver ON receiver.id = CASE
                WHEN t.type='transfer_out' THEN t.target_user_id
                WHEN t.type='transfer_in' THEN t.user_id
                ELSE NULL END
            WHERE t.user_id=%s AND t.type IN ('transfer_in', 'transfer_out')
            ORDER BY t.created_at DESC LIMIT 5
            """,
            (target_user_id,),
        )
        recent_transfers = cursor.fetchall()

        cursor.execute(
            """
            SELECT
                COUNT(*) AS total_trades,
                SUM(CASE WHEN type='buy' THEN 1 ELSE 0 END) AS buy_count,
                SUM(CASE WHEN type='sell' THEN 1 ELSE 0 END) AS sell_count
            FROM transactions WHERE user_id=%s AND type IN ('buy', 'sell')
            """,
            (target_user_id,),
        )
        trade_stats = cursor.fetchone()

        cursor.execute("SELECT COUNT(*) AS cnt FROM posts WHERE user_id=%s", (target_user_id,))
        post_count = cursor.fetchone()["cnt"]

        cursor.execute("SELECT COUNT(*) AS cnt FROM comments WHERE user_id=%s", (target_user_id,))
        comment_count = cursor.fetchone()["cnt"]

    total_stock_value = 0
    total_invested = 0
    for item in holdings:
        current_value = item["current_price"] * item["quantity"]
        invested = item["avg_price"] * item["quantity"]
        item["current_value"] = current_value
        item["profit"] = current_value - invested
        item["profit_rate"] = round((item["profit"] / max(invested, 1)) * 100, 2)
        total_stock_value += current_value
        total_invested += invested

    unrealized_profit = total_stock_value - total_invested
    total_assets = profile_data["balance"] + total_stock_value

    for tx in recent_trades:
        tx["type_label"] = "매수" if tx["type"] == "buy" else "매도"

    for tx in recent_transfers:
        tx["direction_label"] = "출금" if tx["type"] == "transfer_out" else "입금"

    return render_template(
        "mypage/profile.html",
        profile=profile_data,
        is_own=(int(target_user_id) == int(session["user_id"])),
        holdings=holdings,
        total_assets=total_assets,
        total_stock_value=total_stock_value,
        total_invested=total_invested,
        unrealized_profit=unrealized_profit,
        recent_trades=recent_trades,
        recent_transfers=recent_transfers,
        trade_stats=trade_stats,
        post_count=post_count,
        comment_count=comment_count,
    )


@main_bp.route("/mypage/settings")
@login_required
def settings():
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute(
            "SELECT id, username, display_name FROM users WHERE id=%s",
            (session["user_id"],),
        )
        profile_data = cursor.fetchone()
    if not profile_data:
        return redirect(url_for("main.profile"))
    return render_template("mypage/settings.html", profile=profile_data)


@main_bp.route("/mypage/update-profile", methods=["POST"])
@login_required
def update_profile():
    display_name = request.form.get("display_name", "").strip()
    if not display_name:
        flash("닉네임을 입력해 주세요.", "error")
        return redirect(url_for("main.settings"))
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute("UPDATE users SET display_name=%s WHERE id=%s", (display_name, session["user_id"]))
    db.commit()
    flash("닉네임이 변경되었습니다.", "success")
    return redirect(url_for("main.settings"))


@main_bp.route("/mypage/change-password", methods=["POST"])
@login_required
def change_password():
    from ..utils.auth import hash_password, verify_password
    current_pw = request.form.get("current_password", "")
    new_pw = request.form.get("new_password", "")
    confirm_pw = request.form.get("confirm_password", "")
    if not current_pw or not new_pw or not confirm_pw:
        flash("모든 필드를 입력해 주세요.", "error")
        return redirect(url_for("main.profile"))
    if new_pw != confirm_pw:
        flash("새 비밀번호가 일치하지 않습니다.", "error")
        return redirect(url_for("main.profile"))
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute("SELECT password FROM users WHERE id=%s", (session["user_id"],))
        user = cursor.fetchone()
    if not user or not verify_password(current_pw, user["password"]):
        flash("현재 비밀번호가 올바르지 않습니다.", "error")
        return redirect(url_for("main.settings"))
    with db.cursor() as cursor:
        cursor.execute("UPDATE users SET password=%s WHERE id=%s", (hash_password(new_pw), session["user_id"]))
    db.commit()
    flash("비밀번호가 변경되었습니다.", "success")
    return redirect(url_for("main.settings"))


