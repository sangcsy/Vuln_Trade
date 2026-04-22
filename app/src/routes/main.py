import json

from flask import Blueprint, flash, jsonify, redirect, render_template, request, session, url_for

from ..db import get_db
from ..utils.decorators import login_required


main_bp = Blueprint("main", __name__)


def transaction_label(tx_type):
    return {
        "buy": "매수",
        "sell": "매도",
        "transfer_in": "송금 입금",
        "transfer_out": "송금",
    }.get(tx_type, tx_type)


def enrich_stock_cards(cursor, stocks):
    enriched = []
    for stock in stocks:
        cursor.execute(
            """
            SELECT current_price, recorded_at
            FROM stock_price_history
            WHERE stock_id=%s
            ORDER BY recorded_at DESC
            LIMIT 30
            """,
            (stock["id"],),
        )
        history_rows = list(reversed(cursor.fetchall()))
        prices = [row["current_price"] for row in history_rows] or [stock["current_price"]]
        previous_price = prices[-2] if len(prices) > 1 else prices[-1]
        change_amount = stock["current_price"] - previous_price
        change_rate = round((change_amount / previous_price) * 100, 2) if previous_price else 0

        stock["previous_price"] = previous_price
        stock["change_amount"] = change_amount
        stock["change_rate"] = change_rate
        stock["history_prices"] = prices
        stock["detail_url"] = url_for("stocks.stock_detail", stock_id=stock["id"])
        stock["preview_json"] = json.dumps(
            {
                "stock": stock["name"],
                "symbol": stock["symbol"],
                "current_price": stock["current_price"],
                "change_amount": change_amount,
                "change_rate": change_rate,
                "prices": prices,
                "labels": [str(index + 1) for index in range(len(prices))],
                "detail_url": stock["detail_url"],
            },
            ensure_ascii=False,
        )
        enriched.append(stock)
    return enriched


def load_home_data():
    db = get_db()
    cash_balance = 0
    portfolio = []
    recent_transactions = []

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

        cursor.execute("SELECT id, name, symbol, current_price FROM stocks ORDER BY current_price DESC, id LIMIT 17")
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
                ORDER BY t.created_at DESC
                LIMIT 6
                """,
                (session["user_id"],),
            )
            recent_transactions = cursor.fetchall()

    total_stock_value = sum(item["current_price"] * item["quantity"] for item in portfolio)
    total_assets = cash_balance + total_stock_value

    for item in portfolio:
        current_value = item["current_price"] * item["quantity"]
        profit = current_value - (item["avg_price"] * item["quantity"])
        profit_rate = round((profit / max(item["avg_price"] * item["quantity"], 1)) * 100, 2)
        item["current_value"] = current_value
        item["profit"] = profit
        item["profit_rate"] = profit_rate

    for tx in recent_transactions:
        tx["display_type"] = transaction_label(tx["type"])

    return {
        "portfolio": portfolio,
        "account_stocks": portfolio[:6],
        "stocks": stocks,
        "recent_posts": recent_posts,
        "recent_transactions": recent_transactions,
        "total_assets": total_assets,
        "cash_balance": cash_balance,
        "total_stock_value": total_stock_value,
        "preview_stock": stocks[0] if stocks else None,
    }


@main_bp.app_context_processor
def inject_user():
    user = None
    if session.get("user_id"):
        db = get_db()
        with db.cursor() as cursor:
            cursor.execute(
                "SELECT id, username, display_name, balance, role FROM users WHERE id=%s",
                (session["user_id"],),
            )
            user = cursor.fetchone()
    return {"current_user": user}


@main_bp.route("/")
def index():
    return render_template("index.html", **load_home_data())


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
                    "preview_json": stock["preview_json"],
                    "detail_url": stock["detail_url"],
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
                    "current_value": item["current_value"],
                    "profit": item["profit"],
                }
                for item in payload["account_stocks"]
            ],
            "recent_transactions": [
                {
                    "display_type": tx["display_type"],
                    "meta": tx["symbol"] or tx["note"] or "-",
                }
                for tx in payload["recent_transactions"]
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
        profile = cursor.fetchone()

    if not profile:
        flash("User not found.", "error")
        return redirect(url_for("main.index"))

    return render_template("mypage/profile.html", profile=profile)
