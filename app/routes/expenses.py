"""Expense routes."""

from datetime import date

from flask import Blueprint, jsonify, redirect, render_template, request, url_for

from app import db
from app.models import Expense

bp = Blueprint("expenses", __name__, url_prefix="/expenses")

CATEGORIES = ["Yedek Parça", "Kira", "Personel", "Fatura/Elektrik", "Yakıt", "Diğer"]


@bp.route("/")
def list_expenses():
    expenses = db.session.execute(
        db.select(Expense).order_by(Expense.date.desc())
    ).scalars().all()
    return render_template("expenses/list.html", expenses=expenses)


@bp.route("/new", methods=["GET", "POST"])
def create_expense():
    if request.method == "POST":
        data = request.form
        expense = Expense(
            category=data["category"],
            description=data["description"],
            amount=float(data["amount"]),
            date=date.fromisoformat(data["date"]),
        )
        db.session.add(expense)
        db.session.commit()
        return redirect(url_for("expenses.list_expenses"))
    return render_template("expenses/form.html", expense=None, categories=CATEGORIES)


@bp.route("/<int:expense_id>/edit", methods=["GET", "POST"])
def edit_expense(expense_id):
    expense = db.get_or_404(Expense, expense_id)
    if request.method == "POST":
        data = request.form
        expense.category = data["category"]
        expense.description = data["description"]
        expense.amount = float(data["amount"])
        expense.date = date.fromisoformat(data["date"])
        db.session.commit()
        return redirect(url_for("expenses.list_expenses"))
    return render_template("expenses/form.html", expense=expense, categories=CATEGORIES)


@bp.route("/<int:expense_id>/delete", methods=["POST"])
def delete_expense(expense_id):
    expense = db.get_or_404(Expense, expense_id)
    db.session.delete(expense)
    db.session.commit()
    return redirect(url_for("expenses.list_expenses"))


# --- JSON API ---

@bp.route("/api/expenses", methods=["GET"])
def api_list():
    expenses = db.session.execute(
        db.select(Expense).order_by(Expense.date.desc())
    ).scalars().all()
    return jsonify([e.to_dict() for e in expenses])


@bp.route("/api/expenses", methods=["POST"])
def api_create():
    data = request.get_json(force=True)
    required = ["category", "description", "amount", "date"]
    if not data or any(not str(data.get(f, "")).strip() for f in required):
        return jsonify({"error": "category, description, amount ve date alanları zorunludur"}), 400
    expense = Expense(
        category=data["category"],
        description=data["description"],
        amount=float(data["amount"]),
        date=date.fromisoformat(data["date"]),
    )
    db.session.add(expense)
    db.session.commit()
    return jsonify(expense.to_dict()), 201


@bp.route("/api/expenses/<int:expense_id>", methods=["GET"])
def api_get(expense_id):
    expense = db.get_or_404(Expense, expense_id)
    return jsonify(expense.to_dict())


@bp.route("/api/expenses/<int:expense_id>", methods=["PUT"])
def api_update(expense_id):
    expense = db.get_or_404(Expense, expense_id)
    data = request.get_json(force=True)
    if not data:
        return jsonify({"error": "JSON gövdesi gereklidir"}), 400
    expense.category = data.get("category", expense.category)
    expense.description = data.get("description", expense.description)
    expense.amount = float(data.get("amount", expense.amount))
    if "date" in data:
        expense.date = date.fromisoformat(data["date"])
    db.session.commit()
    return jsonify(expense.to_dict())


@bp.route("/api/expenses/<int:expense_id>", methods=["DELETE"])
def api_delete(expense_id):
    expense = db.get_or_404(Expense, expense_id)
    db.session.delete(expense)
    db.session.commit()
    return jsonify({"message": "Gider silindi"}), 200
