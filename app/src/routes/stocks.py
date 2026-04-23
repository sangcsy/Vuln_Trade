from flask import Blueprint, flash, jsonify, redirect, render_template, request, session, url_for

from ..db import get_db
from ..services.stock_service import buy_stock, sell_stock
from ..utils.decorators import login_required


stocks_bp = Blueprint("stocks", __name__)

LIST_HISTORY_LIMIT = 60
DETAIL_HISTORY_LIMIT = 420


def build_history_bundle(history_rows, current_price, time_format="%H:%M:%S"):
    prices = [row["current_price"] for row in history_rows] or [current_price]
    timestamps = [row["recorded_at"].strftime("%Y-%m-%d %H:%M:%S") for row in history_rows]
    labels = [row["recorded_at"].strftime(time_format) for row in history_rows] or ["\uc9c0\uae08"]
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


def stock_news_items(stock, limit=3):
    name = stock["name"]
    symbol = stock["symbol"]
    return [
        {
            "title": f"{name}, \uc0dd\uc0b0 \ub77c\uc778 \uc815\ube44 \uc77c\uc815 \uc55e\ub450\uace0 \uacf5\uae09\ub9dd \uc810\uac80",
            "summary": f"{symbol} \ud611\ub825\uc0ac\ub4e4\uc740 \ubd80\ud488 \uc7ac\uace0\uc640 \ub0a9\uae30 \uc77c\uc815\uc744 \ub2e4\uc2dc \ud655\uc778\ud558\uba70 \ub2e4\uc74c \ubd84\uae30 \uc6b4\uc601 \uacc4\ud68d\uc744 \uc870\uc728\ud558\uace0 \uc788\uc2b5\ub2c8\ub2e4.",
            "source": "Industry Desk",
        },
        {
            "title": f"{name}, \uc9c0\uc5ed \ucc44\uc6a9 \ubc0f \ud604\uc7a5 \uc2e4\uc2b5 \ud504\ub85c\uadf8\ub7a8 \ud655\ub300",
            "summary": "\ud68c\uc0ac\ub294 \uc9c0\uc5ed \ub300\ud559\uacfc\uc758 \ud611\uc5c5\uc744 \ub298\ub9ac\uace0 \uccad\ub144 \uc778\ud134\uc2ed \uaddc\ubaa8\ub97c \ud655\ub300\ud558\ub294 \ubc29\uc548\uc744 \ubc1c\ud45c\ud588\uc2b5\ub2c8\ub2e4.",
            "source": "Local Business",
        },
        {
            "title": f"{symbol}, \ub0b4\ubd80 \ubcf4\uc548 \uaddc\uc815 \uac15\ud654\uc640 \uad8c\ud55c \uac80\uc218 \ucc29\uc218",
            "summary": "\ucd5c\uadfc \uc0ac\uc774\ubc84 \uc704\ud611 \uc99d\uac00\uc5d0 \ub300\uc751\ud574 \uc784\uc9c1\uc6d0 \uacc4\uc815 \uad8c\ud55c\uacfc \ubb38\uc11c \ubc18\ucd9c \uc808\ucc28\ub97c \ub2e4\uc2dc \uc815\ube44\ud558\uace0 \uc788\uc2b5\ub2c8\ub2e4.",
            "source": "Tech Compliance",
        },
    ][:limit]


def attach_news(stocks):
    for stock in stocks:
        stock["news_items"] = stock_news_items(stock)
    return stocks


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
                f"ORDER BY current_price DESC, id"
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

        quantity = int(request.form.get("quantity", "0") or 0)
        total_price = int(float(request.form.get("total_price", "0") or 0))
        action = request.form.get("action")

        if quantity <= 0:
            flash("\uc218\ub7c9\uc744 \ud655\uc778\ud574 \uc8fc\uc138\uc694.", "error")
            return redirect(url_for("stocks.stock_detail", stock_id=stock_id))

        if action == "buy":
            ok, message = buy_stock(db, session["user_id"], stock, quantity, total_price)
        else:
            ok, message = sell_stock(db, session["user_id"], stock, quantity, total_price)

        flash(message, "success" if ok else "error")
        return redirect(url_for("stocks.stock_detail", stock_id=stock_id))

    return render_template("stocks/detail.html", stock=stock, holding=holding)


@stocks_bp.route("/<int:stock_id>/chart-data")
def chart_data(stock_id):
    db = get_db()
    holding = None
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
            (stock_id, DETAIL_HISTORY_LIMIT),
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
