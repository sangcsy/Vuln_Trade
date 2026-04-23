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
    labels = [row["recorded_at"].strftime(time_format) for row in history_rows] or ["지금"]
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
        stock["latest_time_label"] = labels[-1] if labels else "지금"
        result.append(stock)
    return result


@stocks_bp.route("/")
def list_stocks():
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute("SELECT * FROM stocks ORDER BY current_price DESC")
        stocks = attach_market_data(cursor, cursor.fetchall())
    return render_template("stocks/list.html", stocks=stocks, search_query="")


@stocks_bp.route("/search")
def search_stocks():
    q = request.args.get("q", "").strip()
    db = get_db()
    with db.cursor() as cursor:
        if q:
            query = f"""
            SELECT id, name, symbol, current_price, updated_at
            FROM stocks
            WHERE name LIKE '%{q}%'
               OR symbol LIKE '%{q}%'
            ORDER BY current_price DESC, id
            """
            cursor.execute(query)
        else:
            cursor.execute("SELECT id, name, symbol, current_price, updated_at FROM stocks ORDER BY current_price DESC, id")
        stocks = attach_market_data(cursor, cursor.fetchall())
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
        if session.get("user_id"):
            cursor.execute(
                "SELECT * FROM holdings WHERE user_id=%s AND stock_id=%s",
                (session["user_id"], stock_id),
            )
            holding = cursor.fetchone()

    if not stock:
        flash("종목을 찾을 수 없습니다.", "error")
        return redirect(url_for("stocks.list_stocks"))

    if request.method == "POST":
        if not session.get("user_id"):
            flash("로그인이 필요합니다.", "error")
            return redirect(url_for("auth.login"))

        quantity = int(request.form.get("quantity", "0") or 0)
        total_price = int(float(request.form.get("total_price", "0") or 0))
        action = request.form.get("action")

        if quantity <= 0:
            flash("수량을 확인해 주세요.", "error")
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
            "latest_time_label": labels[-1] if labels else "지금",
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
        item["current_value"] = item["current_price"] * item["quantity"]
        item["profit"] = item["current_value"] - (item["avg_price"] * item["quantity"])
        item["profit_rate"] = round((item["profit"] / max(item["avg_price"] * item["quantity"], 1)) * 100, 2)
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
        profit = current_value - (item["avg_price"] * item["quantity"])
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
                "profit_rate": round((profit / max(item["avg_price"] * item["quantity"], 1)) * 100, 2),
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
            ORDER BY t.created_at DESC
            """,
            (user_id,),
        )
        transactions = cursor.fetchall()
    return render_template("stocks/trade_history.html", transactions=transactions)
