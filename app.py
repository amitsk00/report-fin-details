"""
app.py
======
Flask backend and Web UI application for expense reporting and pattern analysis.
Maintains transactions in a pandas DataFrame and serves an interactive frontend
with rich filtering, pattern reports, and spreadsheet-ready views.
"""

import os
import io
import csv
from datetime import datetime
from typing import Dict, Any
from flask import Flask, render_template, request, jsonify, Response, send_file
import pandas as pd
from pydantic import ValidationError

from expense_reader import ExpenseDataManager
from expense_analytics import ExpenseAnalytics
from schemas import (
    FilterRequestSchema,
    ExportCsvSchema,
    LabelAnalysisSchema,
    ReloadRequestSchema
)

app = Flask(__name__)

# Global Pydantic validation error handler
@app.errorhandler(ValidationError)
def handle_validation_error(err: ValidationError):
    """Returns structured 422 Unprocessable Entity on validation failure."""
    formatted_errors = [
        {
            "field": " -> ".join(str(loc) for loc in e.get("loc", [])),
            "message": e.get("msg"),
            "type": e.get("type")
        }
        for e in err.errors()
    ]
    return jsonify({
        "status": "error",
        "message": "Validation failed for request parameters.",
        "errors": formatted_errors
    }), 422

# Initialize data manager with configuration
data_manager = ExpenseDataManager(config_file="config.ini")


@app.route("/")
def index():
    """Renders the main single-page web application."""
    metadata = data_manager.get_metadata()
    return render_template("index.html", metadata=metadata)


@app.route("/api/metadata", methods=["GET"])
def get_metadata():
    """Returns available filter options and dataset boundaries."""
    return jsonify(data_manager.get_metadata())


@app.route("/api/reload", methods=["POST"])
def reload_data():
    """Reloads transaction files from disk."""
    raw_payload = request.get_json(silent=True) or {}
    params = ReloadRequestSchema.model_validate(raw_payload)
    df = data_manager.reload(custom_path=params.custom_path)
    metadata = data_manager.get_metadata()
    return jsonify({
        "status": "success",
        "message": f"Successfully loaded {metadata['total_rows']} transactions from {len(metadata['loaded_files'])} files.",
        "metadata": metadata
    })


@app.route("/api/filter", methods=["POST"])
def filter_and_analyze():
    """
    Applies user filters to the backend DataFrame and returns KPIs,
    pattern analytics, and paginated transaction records.
    """
    raw_payload = request.get_json(silent=True) or {}
    filters = FilterRequestSchema.model_validate(raw_payload)

    # Filter dataframe using validated attributes
    filtered_df = data_manager.filter_data(
        start_date=filters.start_date,
        end_date=filters.end_date,
        year_months=filters.year_months,
        accounts=filters.accounts,
        categories=filters.categories,
        category_groups=filters.category_groups,
        labels=filters.labels,
        types=filters.types,
        spending_nature=filters.spending_nature,
        weekend_filter=filters.weekend_filter,
        min_amount=filters.min_amount,
        max_amount=filters.max_amount,
        search_query=filters.search_query,
        include_transfers=filters.include_transfers
    )

    total_filtered = len(filtered_df)

    # Compute Analytics
    kpis = ExpenseAnalytics.compute_kpis(filtered_df)
    monthly = ExpenseAnalytics.compute_monthly_report(filtered_df)
    category_rep = ExpenseAnalytics.compute_category_report(filtered_df)
    weekday_rep = ExpenseAnalytics.compute_weekday_pattern(filtered_df)
    weekly_rep = ExpenseAnalytics.compute_weekly_pattern(filtered_df)
    account_rep = ExpenseAnalytics.compute_account_report(filtered_df)
    label_rep = ExpenseAnalytics.compute_label_report(filtered_df)
    top_tx = ExpenseAnalytics.compute_top_transactions(filtered_df, limit=15)
    xls_data = ExpenseAnalytics.compute_xls_data(filtered_df)

    # Label Deep Dive (Selected label or default to highest spend label)
    selected_label = filters.selected_label
    if not selected_label:
        if filters.labels and len(filters.labels) == 1:
            selected_label = filters.labels[0]
        elif label_rep["labels"]:
            selected_label = label_rep["labels"][0]["label"]
        else:
            selected_label = "Family"

    label_deep_dive = ExpenseAnalytics.compute_label_deep_dive(filtered_df, selected_label)

    # Sorting
    if not filtered_df.empty:
        valid_sort_cols = {
            'Date': 'Date',
            'amount': 'amount',
            'Title': 'Title',
            'Category': 'Category',
            'Category Group': 'Category Group',
            'Account': 'Account',
            'Type': 'Type'
        }
        col = valid_sort_cols.get(filters.sort_by, 'Date')
        ascending = (filters.sort_dir == 'asc')
        filtered_df = filtered_df.sort_values(by=col, ascending=ascending)

    # Paginate using validated integer bounds
    page = filters.page
    page_size = filters.page_size
    total_pages = max(1, (total_filtered + page_size - 1) // page_size) if total_filtered > 0 else 1
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    page_df = filtered_df.iloc[start_idx:end_idx] if not filtered_df.empty else pd.DataFrame()
    end_idx = start_idx + page_size
    page_df = filtered_df.iloc[start_idx:end_idx] if not filtered_df.empty else pd.DataFrame()

    # Prepare transaction rows for JSON
    tx_list = []
    if not page_df.empty:
        for _, row in page_df.iterrows():
            tx_list.append({
                "date": row['DateOnly'],
                "title": row['Title'],
                "amount": round(float(row['amount']), 2),
                "signed_amount": round(float(row['signed_amount']), 2),
                "type": row['Type'],
                "category": row['Category'],
                "category_group": row['Category Group'],
                "account": row['Account'],
                "labels": row['Labels_Clean'],
                "label_list": row['label_list'],
                "weekday": row['Weekday'],
                "weekend": row['Weekend'],
                "is_recurring": bool(row['is_recurring']),
                "is_excluded": bool(row['is_excluded']),
                "notes": row['Notes']
            })

    return jsonify({
        "status": "success",
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total_rows": total_filtered,
            "total_pages": total_pages
        },
        "kpis": kpis,
        "monthly": monthly,
        "category": category_rep,
        "weekday": weekday_rep,
        "weekly": weekly_rep,
        "account": account_rep,
        "label": label_rep,
        "label_deep_dive": label_deep_dive,
        "top_transactions": top_tx,
        "xls_data": xls_data,
        "transactions": tx_list
    })


@app.route("/api/export/csv", methods=["POST"])
def export_filtered_csv():
    """Generates and streams a CSV of filtered transactions."""
    raw_payload = request.get_json(silent=True) or {}
    params = ExportCsvSchema.model_validate(raw_payload)

    filtered_df = data_manager.filter_data(
        start_date=params.start_date,
        end_date=params.end_date,
        year_months=params.year_months,
        accounts=params.accounts,
        categories=params.categories,
        category_groups=params.category_groups,
        labels=params.labels,
        types=params.types,
        spending_nature=params.spending_nature,
        weekend_filter=params.weekend_filter,
        min_amount=params.min_amount,
        max_amount=params.max_amount,
        search_query=params.search_query,
        include_transfers=params.include_transfers
    )

    export_cols = ['DateOnly', 'Title', 'Type', 'amount', 'Category', 'Category Group', 'Account', 'Labels_Clean', 'Weekday', 'Weekend', 'Notes']
    available_cols = [c for c in export_cols if c in filtered_df.columns]
    
    out_df = filtered_df[available_cols].copy()
    rename_cols = {
        'DateOnly': 'Date',
        'amount': 'Amount',
        'Labels_Clean': 'Labels'
    }
    out_df.rename(columns=rename_cols, inplace=True)

    csv_buffer = io.StringIO()
    out_df.to_csv(csv_buffer, index=False)
    csv_bytes = csv_buffer.getvalue().encode('utf-8')

    filename = f"filtered_expenses_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    return Response(
        csv_bytes,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename={filename}"}
    )


@app.route("/api/label-analysis", methods=["POST"])
def get_label_analysis():
    """Returns deep-dive category and account analytics for a specific label."""
    raw_payload = request.get_json(silent=True) or {}
    params = LabelAnalysisSchema.model_validate(raw_payload)

    filtered_df = data_manager.filter_data(
        start_date=params.start_date,
        end_date=params.end_date,
        year_months=params.year_months,
        accounts=params.accounts,
        categories=params.categories,
        category_groups=params.category_groups,
        types=params.types,
        spending_nature=params.spending_nature,
        weekend_filter=params.weekend_filter,
        min_amount=params.min_amount,
        max_amount=params.max_amount,
        search_query=params.search_query,
        include_transfers=params.include_transfers
    )

    deep_dive = ExpenseAnalytics.compute_label_deep_dive(filtered_df, params.label)
    return jsonify({
        "status": "success",
        "data": deep_dive
    })


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
