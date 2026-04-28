from datetime import timedelta, timezone
from flask import Blueprint, flash, jsonify, redirect, render_template, request, session, url_for

KST = timezone(timedelta(hours=9))

from ..db import get_db
from ..services.news_service import stock_news_items
from ..services.stock_service import buy_stock, sell_stock
from ..utils.decorators import login_required


stocks_bp = Blueprint("stocks", __name__)

LIST_HISTORY_LIMIT = 60
DETAIL_HISTORY_LIMIT = 420


def parse_positive_int(value):
    try:
        parsed = int(str(value).strip())
    except (TypeError, ValueError):
        return 0
    return parsed if parsed > 0 else 0


def build_history_bundle(history_rows, current_price, time_format="%H:%M:%S"):
    prices = [row["current_price"] for row in history_rows] or [current_price]
    kst_times = [row["recorded_at"].replace(tzinfo=timezone.utc).astimezone(KST) for row in history_rows]
    timestamps = [dt.strftime("%Y-%m-%d %H:%M:%S") for dt in kst_times]
    labels = [dt.strftime(time_format) for dt in kst_times] or ["\uc9c0\uae08"]
    return prices, labels, timestamps


def attach_market_data(cursor, stocks, history_limit=LIST_HISTORY_LIMIT):
    result = []
    for stock in stocks:
        ref_stock_id = stock.get("stock_id", stock["id"])
        cursor.execute(
            """
            SELECT current_price, recorded_at
            FROM stock_price_history
            WHERE stock_id=%s
            ORDER BY recorded_at DESC
            LIMIT %s
            """,
            (ref_stock_id, history_limit),
        )
        history_rows = list(reversed(cursor.fetchall()))
        prices, labels, timestamps = build_history_bundle(history_rows, stock["current_price"])
        previous_price = prices[-2] if len(prices) > 1 else prices[-1]
        change_amount = stock["current_price"] - previous_price
        change_rate = round((change_amount / previous_price) * 100, 2) if previous_price else 0

        stock["history_prices"] = prices
        stock["history_labels"] = labels
        stock["history_timestamps"] = timestamps
        stock["previous_price"] = previous_price
        stock["change_amount"] = change_amount
        stock["change_rate"] = change_rate
        stock["latest_time_label"] = labels[-1] if labels else "\uc9c0\uae08"
        result.append(stock)
    return result


def attach_news(stocks):
    for stock in stocks:
        stock["news_items"] = stock_news_items(stock)
    return stocks


def build_detail_metrics(stock):
    prices = stock.get("history_prices") or [stock["current_price"]]
    open_price = prices[0]
    close_price = stock["current_price"]
    base_shares = 42_000_000 + (stock["id"] * 3_700_000)
    recent_prices = prices[-30:] or prices
    trading_value = int(sum(recent_prices) * (900 + stock["id"] * 37))
    market_cap = int(close_price * base_shares)
    target_price = int(close_price * (1.08 if stock.get("change_rate", 0) >= 0 else 1.04))
    opinion = "\ub9e4\uc218" if target_price > close_price * 1.05 else "\uc911\ub9bd"

    return {
        "open_price": open_price,
        "close_price": close_price,
        "trading_value": trading_value,
        "market_cap": market_cap,
        "opinion": opinion,
        "target_price": target_price,
    }


@stocks_bp.route("/")
def list_stocks():
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute("SELECT * FROM stocks ORDER BY current_price DESC")
        stocks = attach_news(attach_market_data(cursor, cursor.fetchall()))
    return render_template("stocks/list.html", stocks=stocks, search_query="")


@stocks_bp.route("/search")
def search_stocks():
    q = request.args.get("q", "").strip()
    db = get_db()
    with db.cursor() as cursor:
        if q:
            query = (
                f"SELECT id, name, symbol, current_price, updated_at "
                f"FROM stocks "
                f"WHERE name LIKE '%{q}%' "
                f"OR symbol LIKE '%{q}%' "
                f"ORDER BY name ASC, id"
            )
            cursor.execute(query)
        else:
            cursor.execute("SELECT id, name, symbol, current_price, updated_at FROM stocks ORDER BY current_price DESC, id")
        stocks = attach_news(attach_market_data(cursor, cursor.fetchall()))
    return render_template("stocks/list.html", stocks=stocks, search_query=q)


@stocks_bp.route("/<int:stock_id>", methods=["GET", "POST"])
def stock_detail(stock_id):
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute("SELECT * FROM stocks WHERE id=%s", (stock_id,))
        stock = cursor.fetchone()
        holding = None
        if stock:
            stock = attach_market_data(cursor, [stock], history_limit=DETAIL_HISTORY_LIMIT)[0]
            stock["news_items"] = stock_news_items(stock)
            stock["detail_metrics"] = build_detail_metrics(stock)
        if session.get("user_id"):
            cursor.execute(
                "SELECT * FROM holdings WHERE user_id=%s AND stock_id=%s",
                (session["user_id"], stock_id),
            )
            holding = cursor.fetchone()

    if not stock:
        flash("\uc885\ubaa9\uc744 \ucc3e\uc744 \uc218 \uc5c6\uc2b5\ub2c8\ub2e4.", "error")
        return redirect(url_for("stocks.list_stocks"))

    if request.method == "POST":
        if not session.get("user_id"):
            flash("\ub85c\uadf8\uc778\uc774 \ud544\uc694\ud569\ub2c8\ub2e4.", "error")
            return redirect(url_for("auth.login"))

        quantity = parse_positive_int(request.form.get("quantity"))
        action = request.form.get("action")

        if quantity <= 0:
            flash("\uc218\ub7c9\uc744 \ud655\uc778\ud574 \uc8fc\uc138\uc694.", "error")
            return redirect(url_for("stocks.stock_detail", stock_id=stock_id))

        if action == "buy":
            ok, message = buy_stock(db, session["user_id"], stock, quantity)
        elif action == "sell":
            ok, message = sell_stock(db, session["user_id"], stock, quantity)
        else:
            ok, message = False, "\uc694\uccad\uc744 \ud655\uc778\ud574 \uc8fc\uc138\uc694."

        flash(message, "success" if ok else "error")
        return redirect(url_for("stocks.stock_detail", stock_id=stock_id))

    return render_template("stocks/detail.html", stock=stock, holding=holding)


INTERVAL_LIMITS = {10: 420, 30: 1260, 60: 2520, 600: 10000, 3600: 10000}

@stocks_bp.route("/<int:stock_id>/chart-data")
def chart_data(stock_id):
    db = get_db()
    holding = None
    interval = int(request.args.get("interval", 10))
    limit = INTERVAL_LIMITS.get(interval, min(max(int(request.args.get("limit", DETAIL_HISTORY_LIMIT)), 1), 10000))
    with db.cursor() as cursor:
        cursor.execute("SELECT id, name, symbol, current_price FROM stocks WHERE id=%s", (stock_id,))
        stock = cursor.fetchone()
        if not stock:
            return jsonify({"error": "not_found"}), 404

        cursor.execute(
            """
            SELECT current_price, recorded_at
            FROM stock_price_history
            WHERE stock_id=%s
            ORDER BY recorded_at DESC
            LIMIT %s
            """,
            (stock_id, limit),
        )
        rows = list(reversed(cursor.fetchall()))

        if session.get("user_id"):
            cursor.execute(
                "SELECT avg_price FROM holdings WHERE user_id=%s AND stock_id=%s",
                (session["user_id"], stock_id),
            )
            holding = cursor.fetchone()

    prices, labels, timestamps = build_history_bundle(rows, stock["current_price"])
    previous_price = prices[-2] if len(prices) > 1 else prices[-1]
    change_amount = stock["current_price"] - previous_price
    change_rate = round((change_amount / previous_price) * 100, 2) if previous_price else 0

    return jsonify(
        {
            "stock": stock["name"],
            "symbol": stock["symbol"],
            "current_price": stock["current_price"],
            "change_amount": change_amount,
            "change_rate": change_rate,
            "labels": labels,
            "timestamps": timestamps,
            "prices": prices,
            "avg_price": holding["avg_price"] if holding else None,
            "latest_time_label": labels[-1] if labels else "\uc9c0\uae08",
        }
    )


@stocks_bp.route("/portfolio")
@login_required
def portfolio():
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute(
            """
            SELECT h.*, s.name, s.symbol, s.current_price
            FROM holdings h
            JOIN stocks s ON s.id = h.stock_id
            WHERE h.user_id=%s
            ORDER BY s.name
            """,
            (session["user_id"],),
        )
        holdings = attach_market_data(cursor, cursor.fetchall())
    for item in holdings:
        invested_amount = item["avg_price"] * item["quantity"]
        item["current_value"] = item["current_price"] * item["quantity"]
        item["profit"] = item["current_value"] - invested_amount
        item["profit_rate"] = round((item["profit"] / max(invested_amount, 1)) * 100, 2)
    return render_template("stocks/portfolio.html", holdings=holdings)


@stocks_bp.route("/portfolio-snapshot")
@login_required
def portfolio_snapshot():
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute(
            """
            SELECT h.*, s.name, s.symbol, s.current_price
            FROM holdings h
            JOIN stocks s ON s.id = h.stock_id
            WHERE h.user_id=%s
            ORDER BY s.name
            """,
            (session["user_id"],),
        )
        holdings = attach_market_data(cursor, cursor.fetchall())

    payload = []
    for item in holdings:
        current_value = item["current_price"] * item["quantity"]
        invested_amount = item["avg_price"] * item["quantity"]
        profit = current_value - invested_amount
        payload.append(
            {
                "id": item["id"],
                "stock_id": item["stock_id"],
                "name": item["name"],
                "symbol": item["symbol"],
                "quantity": item["quantity"],
                "avg_price": item["avg_price"],
                "current_price": item["current_price"],
                "current_value": current_value,
                "profit": profit,
                "profit_rate": round((profit / max(invested_amount, 1)) * 100, 2),
                "history_prices": item["history_prices"],
                "history_labels": item["history_labels"],
                "history_timestamps": item["history_timestamps"],
                "detail_url": url_for("stocks.stock_detail", stock_id=item["stock_id"]),
            }
        )
    return jsonify({"holdings": payload})


@stocks_bp.route("/history")
@login_required
def trade_history():
    user_id = request.args.get("user_id", session["user_id"])
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute(
            """
            SELECT t.*, s.name AS stock_name, s.symbol
            FROM transactions t
            LEFT JOIN stocks s ON s.id = t.stock_id
            WHERE t.user_id=%s
              AND t.type IN ('buy', 'sell')
            ORDER BY t.created_at DESC
            """,
            (user_id,),
        )
        transactions = cursor.fetchall()
    return render_template("stocks/trade_history.html", transactions=transactions)
