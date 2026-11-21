"""
expense_analytics.py
====================
Provides analytical aggregations, pattern recognition, and report generation
for the expense management system.
"""

from typing import Dict, List, Any, Optional
import pandas as pd
import numpy as np


class ExpenseAnalytics:
    """
    Computes KPIs, expense pattern reports, time-series aggregations,
    and categorical distributions on filtered expense DataFrames.
    """

    WEEKDAY_ORDER = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

    @staticmethod
    def compute_kpis(df: pd.DataFrame) -> Dict[str, Any]:
        """Calculates headline key performance indicators."""
        if df.empty:
            return {
                "total_expense": 0.0,
                "total_income": 0.0,
                "net_savings": 0.0,
                "savings_rate": 0.0,
                "tx_count": 0,
                "expense_tx_count": 0,
                "income_tx_count": 0,
                "avg_expense_per_tx": 0.0,
                "avg_daily_expense": 0.0,
                "top_category": "N/A",
                "top_category_amount": 0.0,
                "top_account": "N/A",
                "top_account_amount": 0.0,
                "recurring_spend": 0.0,
                "emi_spend": 0.0,
                "discretionary_spend": 0.0,
                "active_days": 0
            }

        df_exp = df[df['Type'] == 'Expense']
        df_inc = df[df['Type'] == 'Income']

        total_exp = float(df_exp['amount'].sum())
        total_inc = float(df_inc['amount'].sum())
        net_savings = total_inc - total_exp
        savings_rate = (net_savings / total_inc * 100.0) if total_inc > 0 else 0.0

        num_tx = len(df)
        exp_count = len(df_exp)
        inc_count = len(df_inc)
        avg_exp_tx = (total_exp / exp_count) if exp_count > 0 else 0.0

        active_days = df['DateOnly'].nunique()
        avg_daily = (total_exp / active_days) if active_days > 0 else 0.0

        # Top category
        top_cat = "N/A"
        top_cat_amt = 0.0
        if not df_exp.empty:
            cat_sums = df_exp.groupby('Category')['amount'].sum().sort_values(ascending=False)
            if not cat_sums.empty:
                top_cat = str(cat_sums.index[0])
                top_cat_amt = float(cat_sums.iloc[0])

        # Top account
        top_acc = "N/A"
        top_acc_amt = 0.0
        if not df_exp.empty:
            acc_sums = df_exp.groupby('Account')['amount'].sum().sort_values(ascending=False)
            if not acc_sums.empty:
                top_acc = str(acc_sums.index[0])
                top_acc_amt = float(acc_sums.iloc[0])

        # Nature breakdown
        recurring_spend = float(df_exp[df_exp['is_recurring']]['amount'].sum())
        emi_spend = float(df_exp[df_exp['is_excluded']]['amount'].sum())
        discretionary_spend = float(df_exp[df_exp['is_discretionary']]['amount'].sum())

        return {
            "total_expense": round(total_exp, 2),
            "total_income": round(total_inc, 2),
            "net_savings": round(net_savings, 2),
            "savings_rate": round(savings_rate, 1),
            "tx_count": num_tx,
            "expense_tx_count": exp_count,
            "income_tx_count": inc_count,
            "avg_expense_per_tx": round(avg_exp_tx, 2),
            "avg_daily_expense": round(avg_daily, 2),
            "top_category": top_cat,
            "top_category_amount": round(top_cat_amt, 2),
            "top_account": top_acc,
            "top_account_amount": round(top_acc_amt, 2),
            "recurring_spend": round(recurring_spend, 2),
            "emi_spend": round(emi_spend, 2),
            "discretionary_spend": round(discretionary_spend, 2),
            "active_days": active_days
        }

    @classmethod
    def compute_monthly_report(cls, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Computes monthly Income vs Expense, Savings, and Month-over-Month deltas.
        Similar to `amountsSummaryByMonth` & `amtByMonth`.
        """
        if df.empty:
            return {"months": [], "table": [], "chart": {}, "mean_expense": 0.0, "total_expense": 0.0}

        # Pivot by YearMonth and Type
        months = sorted(df['YearMonth'].unique())
        
        records = []
        chart_labels = []
        chart_expenses = []
        chart_income = []
        chart_savings = []

        all_exp_values = []

        for m in months:
            df_m = df[df['YearMonth'] == m]
            exp_val = float(df_m[df_m['Type'] == 'Expense']['amount'].sum())
            inc_val = float(df_m[df_m['Type'] == 'Income']['amount'].sum())
            sav_val = inc_val - exp_val
            sav_rate = (sav_val / inc_val * 100.0) if inc_val > 0 else 0.0
            
            all_exp_values.append(exp_val)

            records.append({
                "month": m,
                "expense": round(exp_val, 2),
                "income": round(inc_val, 2),
                "savings": round(sav_val, 2),
                "savings_rate": round(sav_rate, 1),
                "tx_count": len(df_m)
            })

            chart_labels.append(m)
            chart_expenses.append(round(exp_val, 2))
            chart_income.append(round(inc_val, 2))
            chart_savings.append(round(sav_val, 2))

        # Mean expense and deltas
        mean_exp = float(np.mean(all_exp_values)) if all_exp_values else 0.0
        total_exp = float(np.sum(all_exp_values)) if all_exp_values else 0.0

        for i, rec in enumerate(records):
            rec["delta_from_mean"] = round(rec["expense"] - mean_exp, 2)
            if i > 0:
                prev_exp = records[i - 1]["expense"]
                rec["mom_delta"] = round(rec["expense"] - prev_exp, 2)
                rec["mom_pct"] = round(((rec["expense"] - prev_exp) / prev_exp * 100.0), 1) if prev_exp > 0 else 0.0
            else:
                rec["mom_delta"] = 0.0
                rec["mom_pct"] = 0.0

        return {
            "months": months,
            "table": records,
            "chart": {
                "labels": chart_labels,
                "expenses": chart_expenses,
                "income": chart_income,
                "savings": chart_savings
            },
            "mean_expense": round(mean_exp, 2),
            "total_expense": round(total_exp, 2)
        }

    @classmethod
    def compute_category_report(cls, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Category & Category Group pattern breakdown and monthly matrix.
        """
        df_exp = df[df['Type'] == 'Expense']
        if df_exp.empty:
            return {
                "by_group": [],
                "by_category": [],
                "group_chart": {"labels": [], "data": []},
                "category_chart": {"labels": [], "data": []},
                "matrix": {"categories": [], "months": [], "rows": []}
            }

        total_exp = float(df_exp['amount'].sum())

        # 1. By Category Group
        grp_agg = df_exp.groupby('Category Group').agg(
            total=('amount', 'sum'),
            count=('amount', 'count')
        ).sort_values(by='total', ascending=False)

        by_group = []
        for name, row in grp_agg.iterrows():
            amt = float(row['total'])
            pct = (amt / total_exp * 100.0) if total_exp > 0 else 0.0
            by_group.append({
                "group": name,
                "total": round(amt, 2),
                "count": int(row['count']),
                "percentage": round(pct, 1)
            })

        # 2. By Category
        cat_agg = df_exp.groupby(['Category', 'Category Group']).agg(
            total=('amount', 'sum'),
            count=('amount', 'count')
        ).reset_index().sort_values(by='total', ascending=False)

        by_cat = []
        for _, row in cat_agg.iterrows():
            amt = float(row['total'])
            pct = (amt / total_exp * 100.0) if total_exp > 0 else 0.0
            by_cat.append({
                "category": row['Category'],
                "group": row['Category Group'],
                "total": round(amt, 2),
                "count": int(row['count']),
                "percentage": round(pct, 1)
            })

        # 3. Monthly Pivot Matrix (Category x YearMonth)
        pivot = df_exp.pivot_table(
            index='Category',
            columns='YearMonth',
            values='amount',
            aggfunc='sum',
            fill_value=0.0
        )
        # Add total column for sorting
        pivot['Total'] = pivot.sum(axis=1)
        pivot = pivot.sort_values(by='Total', ascending=False)
        
        months = [c for c in pivot.columns if c != 'Total']
        matrix_rows = []
        for cat_name, row in pivot.iterrows():
            matrix_rows.append({
                "category": cat_name,
                "values": {m: round(float(row[m]), 2) for m in months},
                "total": round(float(row['Total']), 2)
            })

        # Charts data
        top_groups = by_group[:8]
        top_cats = by_cat[:12]

        return {
            "by_group": by_group,
            "by_category": by_cat,
            "group_chart": {
                "labels": [g["group"] for g in top_groups],
                "data": [g["total"] for g in top_groups]
            },
            "category_chart": {
                "labels": [c["category"] for c in top_cats],
                "data": [c["total"] for c in top_cats]
            },
            "matrix": {
                "categories": list(pivot.index),
                "months": months,
                "rows": matrix_rows
            }
        }

    @classmethod
    def compute_weekday_pattern(cls, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Weekday pattern analysis (Monday through Sunday) and Weekend vs Weekday analysis.
        Matches and extends `expByWeekday` in `mth_exp.py`.
        """
        df_exp = df[df['Type'] == 'Expense']
        if df_exp.empty:
            return {
                "weekday_table": [],
                "weekend_vs_weekday": {},
                "mean_weekday": 0.0,
                "chart": {"labels": [], "totals": [], "averages": []}
            }

        total_exp = float(df_exp['amount'].sum())

        # Group by weekday
        days_data = []
        labels = []
        totals = []
        averages = []

        day_sums = df_exp.groupby('Weekday')['amount'].sum().to_dict()
        day_counts = df_exp.groupby('Weekday')['amount'].count().to_dict()
        
        # Calculate distinct dates per weekday in the dataset
        day_date_counts = df_exp.groupby('Weekday')['DateOnly'].nunique().to_dict()

        for day in cls.WEEKDAY_ORDER:
            tot = float(day_sums.get(day, 0.0))
            cnt = int(day_counts.get(day, 0))
            date_cnt = int(day_date_counts.get(day, 1))
            avg_per_day = (tot / date_cnt) if date_cnt > 0 else 0.0
            pct = (tot / total_exp * 100.0) if total_exp > 0 else 0.0

            days_data.append({
                "weekday": day,
                "total": round(tot, 2),
                "tx_count": cnt,
                "days_observed": date_cnt,
                "avg_per_day": round(avg_per_day, 2),
                "percentage": round(pct, 1)
            })

            labels.append(day)
            totals.append(round(tot, 2))
            averages.append(round(avg_per_day, 2))

        # Overall weekday mean
        weekday_mean = float(np.mean(totals)) if totals else 0.0
        for d in days_data:
            d["delta_from_mean"] = round(d["total"] - weekday_mean, 2)

        # Weekend vs Weekday
        weekend_df = df_exp[df_exp['Weekend'] == 'WeekEnd']
        weekday_df = df_exp[df_exp['Weekend'] == 'WeekDay']

        weekend_tot = float(weekend_df['amount'].sum())
        weekday_tot = float(weekday_df['amount'].sum())
        weekend_dates = weekend_df['DateOnly'].nunique()
        weekday_dates = weekday_df['DateOnly'].nunique()

        weekend_daily_avg = (weekend_tot / weekend_dates) if weekend_dates > 0 else 0.0
        weekday_daily_avg = (weekday_tot / weekday_dates) if weekday_dates > 0 else 0.0

        return {
            "weekday_table": days_data,
            "mean_weekday": round(weekday_mean, 2),
            "weekend_vs_weekday": {
                "weekend_total": round(weekend_tot, 2),
                "weekday_total": round(weekday_tot, 2),
                "weekend_pct": round((weekend_tot / total_exp * 100.0), 1) if total_exp > 0 else 0.0,
                "weekday_pct": round((weekday_tot / total_exp * 100.0), 1) if total_exp > 0 else 0.0,
                "weekend_daily_avg": round(weekend_daily_avg, 2),
                "weekday_daily_avg": round(weekday_daily_avg, 2),
                "weekend_days": weekend_dates,
                "weekday_days": weekday_dates
            },
            "chart": {
                "labels": labels,
                "totals": totals,
                "averages": averages
            }
        }

    @classmethod
    def compute_weekly_pattern(cls, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Weekly pattern analysis by ISO Week number.
        Matches and extends `expByWeek` in `mth_exp.py`.
        """
        df_exp = df[df['Type'] == 'Expense']
        if df_exp.empty:
            return {"weeks": [], "mean_weekly": 0.0, "projected_monthly": 0.0, "chart": {}}

        week_agg = df_exp.groupby('YearWeek').agg(
            total=('amount', 'sum'),
            count=('amount', 'count'),
            week_num=('WeekNum', 'first')
        ).sort_index()

        weeks = []
        labels = []
        totals = []

        all_totals = []
        for yw, row in week_agg.iterrows():
            tot = float(row['total'])
            all_totals.append(tot)
            weeks.append({
                "year_week": yw,
                "week_num": row['week_num'],
                "total": round(tot, 2),
                "tx_count": int(row['count'])
            })
            labels.append(yw)
            totals.append(round(tot, 2))

        mean_weekly = float(np.mean(all_totals)) if all_totals else 0.0
        # Projected monthly run rate as in mth_exp: mean * 4.33
        projected_monthly = mean_weekly * 4.33

        for i, w in enumerate(weeks):
            w["delta_from_mean"] = round(w["total"] - mean_weekly, 2)
            if i > 0:
                w["delta_prev_week"] = round(w["total"] - weeks[i - 1]["total"], 2)
            else:
                w["delta_prev_week"] = 0.0

        return {
            "weeks": weeks,
            "mean_weekly": round(mean_weekly, 2),
            "projected_monthly": round(projected_monthly, 2),
            "chart": {
                "labels": labels,
                "totals": totals,
                "mean_line": round(mean_weekly, 2)
            }
        }

    @classmethod
    def compute_account_report(cls, df: pd.DataFrame) -> Dict[str, Any]:
        """Account-wise expenditure and distribution."""
        df_exp = df[df['Type'] == 'Expense']
        if df_exp.empty:
            return {"accounts": [], "chart": {"labels": [], "data": []}}

        total_exp = float(df_exp['amount'].sum())
        acc_agg = df_exp.groupby('Account').agg(
            total=('amount', 'sum'),
            count=('amount', 'count')
        ).sort_values(by='total', ascending=False)

        accounts = []
        labels = []
        data = []

        for acc, row in acc_agg.iterrows():
            amt = float(row['total'])
            pct = (amt / total_exp * 100.0) if total_exp > 0 else 0.0
            accounts.append({
                "account": acc,
                "total": round(amt, 2),
                "tx_count": int(row['count']),
                "percentage": round(pct, 1)
            })
            labels.append(acc)
            data.append(round(amt, 2))

        return {
            "accounts": accounts,
            "chart": {
                "labels": labels,
                "data": data
            }
        }

    @classmethod
    def compute_label_report(cls, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Label / Person / Tag spending pattern.
        Computes spending breakdown for individual tags (Amit, Dipti, Family, Adi, etc.).
        """
        df_exp = df[df['Type'] == 'Expense']
        if df_exp.empty:
            return {"labels": [], "chart": {"labels": [], "data": []}}

        total_exp = float(df_exp['amount'].sum())

        # Explode label_list to aggregate by individual tag
        exploded = df_exp.explode('label_list')
        exploded = exploded[exploded['label_list'].notna() & (exploded['label_list'] != "")]

        if exploded.empty:
            return {"labels": [], "chart": {"labels": [], "data": []}}

        tag_agg = exploded.groupby('label_list').agg(
            total=('amount', 'sum'),
            count=('amount', 'count')
        ).sort_values(by='total', ascending=False)

        label_records = []
        chart_labels = []
        chart_data = []

        for tag, row in tag_agg.iterrows():
            amt = float(row['total'])
            pct = (amt / total_exp * 100.0) if total_exp > 0 else 0.0
            label_records.append({
                "label": tag,
                "total": round(amt, 2),
                "tx_count": int(row['count']),
                "percentage": round(pct, 1)
            })

        # Top 12 tags for chart
        for item in label_records[:12]:
            chart_labels.append(item["label"])
            chart_data.append(item["total"])

        return {
            "labels": label_records,
            "chart": {
                "labels": chart_labels,
                "data": chart_data
            }
        }

    @classmethod
    def compute_top_transactions(cls, df: pd.DataFrame, limit: int = 20) -> List[Dict[str, Any]]:
        """Returns top highest expense transactions."""
        df_exp = df[df['Type'] == 'Expense'].copy()
        if df_exp.empty:
            return []

        top_df = df_exp.sort_values(by='amount', ascending=False).head(limit)
        results = []
        for _, row in top_df.iterrows():
            results.append({
                "date": row['DateOnly'],
                "title": row['Title'],
                "amount": round(float(row['amount']), 2),
                "category": row['Category'],
                "category_group": row['Category Group'],
                "account": row['Account'],
                "labels": row['Labels_Clean']
            })
        return results

    @classmethod
    def compute_xls_data(cls, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Structures recurring, large/EMI, and weekend data formatted
        for direct spreadsheet export/copy, matching `processForXls`.
        """
        df_exp = df[df['Type'] == 'Expense'].copy()
        if df_exp.empty:
            return {"recurring": [], "large_emi": [], "weekend_summary": []}

        # 1. Recurring expenses (Monthly, Donation)
        df_recurring = df_exp[df_exp['is_recurring']].sort_values(by=['YearMonth', 'Title'])
        recurring_by_month = []
        for ym, group in df_recurring.groupby('YearMonth', sort=False):
            items = []
            for _, r in group.iterrows():
                items.append({
                    "date": r['DateOnly'],
                    "title": r['Title'],
                    "category": r['Category'],
                    "amount": round(float(r['amount']), 2),
                    "account": r['Account']
                })
            recurring_by_month.append({
                "month": ym,
                "total": round(float(group['amount'].sum()), 2),
                "items": items
            })

        # 2. Large/EMI expenses
        df_emi = df_exp[df_exp['is_excluded']].sort_values(by=['YearMonth', 'Title'])
        emi_by_month = []
        for ym, group in df_emi.groupby('YearMonth', sort=False):
            items = []
            for _, r in group.iterrows():
                items.append({
                    "date": r['DateOnly'],
                    "title": r['Title'],
                    "category": r['Category'],
                    "amount": round(float(r['amount']), 2),
                    "account": r['Account']
                })
            emi_by_month.append({
                "month": ym,
                "total": round(float(group['amount'].sum()), 2),
                "items": items
            })

        # 3. Weekend Discretionary Spending by Week
        df_weekend = df_exp[(df_exp['Weekend'] == 'WeekEnd') & (df_exp['is_discretionary'])]
        weekend_by_month = []
        for ym, group in df_weekend.groupby('YearMonth', sort=False):
            week_sums = group.groupby('WeekNum')['amount'].sum().to_dict()
            weekend_by_month.append({
                "month": ym,
                "weeks": {f"Week {w}": round(float(v), 2) for w, v in sorted(week_sums.items())},
                "total": round(float(group['amount'].sum()), 2)
            })

        return {
            "recurring": recurring_by_month,
            "large_emi": emi_by_month,
            "weekend_summary": weekend_by_month
        }

    @classmethod
    def compute_label_deep_dive(cls, df: pd.DataFrame, selected_label: str) -> Dict[str, Any]:
        """
        Deep-dive analysis for a single selected label:
        - Category & Category Group breakdown
        - Account level breakdown
        - Monthly trend
        - Top transactions
        - Summary KPIs
        """
        empty_res = {
            "label": selected_label or "",
            "total_spend": 0.0,
            "overall_total": 0.0,
            "percentage_of_total": 0.0,
            "tx_count": 0,
            "avg_per_tx": 0.0,
            "active_months": 0,
            "monthly_avg": 0.0,
            "top_category": "N/A",
            "top_category_amt": 0.0,
            "top_account": "N/A",
            "top_account_amt": 0.0,
            "categories": [],
            "category_groups": [],
            "accounts": [],
            "monthly_trend": {"labels": [], "data": []},
            "category_chart": {"labels": [], "data": []},
            "group_chart": {"labels": [], "data": []},
            "account_chart": {"labels": [], "data": []},
            "category_matrix": {"categories": [], "months": [], "rows": []},
            "transactions": []
        }

        if not selected_label or df.empty:
            return empty_res

        df_exp = df[df['Type'] == 'Expense']
        overall_total = float(df_exp['amount'].sum())

        # Filter to rows containing selected_label in label_list
        lbl_mask = df_exp['label_list'].apply(lambda lst: selected_label in lst if isinstance(lst, list) else False)
        df_lbl = df_exp[lbl_mask].copy()

        if df_lbl.empty:
            empty_res["overall_total"] = round(overall_total, 2)
            return empty_res

        total_lbl_spend = float(df_lbl['amount'].sum())
        lbl_tx_count = len(df_lbl)
        pct_of_total = (total_lbl_spend / overall_total * 100.0) if overall_total > 0 else 0.0
        avg_per_tx = total_lbl_spend / lbl_tx_count if lbl_tx_count > 0 else 0.0

        active_months = df_lbl['YearMonth'].nunique()
        monthly_avg = total_lbl_spend / active_months if active_months > 0 else 0.0

        # 1. Category Breakdown
        cat_agg = df_lbl.groupby(['Category', 'Category Group']).agg(
            total=('amount', 'sum'),
            count=('amount', 'count')
        ).reset_index().sort_values(by='total', ascending=False)

        cat_list = []
        for _, r in cat_agg.iterrows():
            amt = float(r['total'])
            pct = (amt / total_lbl_spend * 100.0) if total_lbl_spend > 0 else 0.0
            cat_list.append({
                "category": r['Category'],
                "group": r['Category Group'],
                "total": round(amt, 2),
                "count": int(r['count']),
                "percentage": round(pct, 1)
            })

        # Category Group breakdown
        grp_agg = df_lbl.groupby('Category Group').agg(
            total=('amount', 'sum'),
            count=('amount', 'count')
        ).sort_values(by='total', ascending=False)

        grp_list = []
        for name, r in grp_agg.iterrows():
            amt = float(r['total'])
            pct = (amt / total_lbl_spend * 100.0) if total_lbl_spend > 0 else 0.0
            grp_list.append({
                "group": name,
                "total": round(amt, 2),
                "count": int(r['count']),
                "percentage": round(pct, 1)
            })

        top_cat = cat_list[0]["category"] if cat_list else "N/A"
        top_cat_amt = cat_list[0]["total"] if cat_list else 0.0

        # 2. Account Breakdown
        acc_agg = df_lbl.groupby('Account').agg(
            total=('amount', 'sum'),
            count=('amount', 'count')
        ).sort_values(by='total', ascending=False)

        acc_list = []
        for name, r in acc_agg.iterrows():
            amt = float(r['total'])
            pct = (amt / total_lbl_spend * 100.0) if total_lbl_spend > 0 else 0.0
            acc_list.append({
                "account": name,
                "total": round(amt, 2),
                "count": int(r['count']),
                "percentage": round(pct, 1)
            })

        top_acc = acc_list[0]["account"] if acc_list else "N/A"
        top_acc_amt = acc_list[0]["total"] if acc_list else 0.0

        # 3. Monthly Trend for this label
        m_agg = df_lbl.groupby('YearMonth')['amount'].sum().sort_index()
        m_labels = list(m_agg.index)
        m_data = [round(float(v), 2) for v in m_agg.values]

        # 4. Category Matrix for this label (Category x Month)
        pivot = df_lbl.pivot_table(
            index='Category',
            columns='YearMonth',
            values='amount',
            aggfunc='sum',
            fill_value=0.0
        )
        pivot['Total'] = pivot.sum(axis=1)
        pivot = pivot.sort_values(by='Total', ascending=False)
        matrix_months = [c for c in pivot.columns if c != 'Total']
        matrix_rows = []
        for cat_name, row in pivot.iterrows():
            matrix_rows.append({
                "category": cat_name,
                "values": {m: round(float(row[m]), 2) for m in matrix_months},
                "total": round(float(row['Total']), 2)
            })

        # 5. Top transactions for this label
        top_tx_df = df_lbl.sort_values(by='amount', ascending=False).head(30)
        top_tx_list = []
        for _, r in top_tx_df.iterrows():
            top_tx_list.append({
                "date": r['DateOnly'],
                "title": r['Title'],
                "amount": round(float(r['amount']), 2),
                "category": r['Category'],
                "category_group": r['Category Group'],
                "account": r['Account'],
                "notes": r['Notes']
            })

        return {
            "label": selected_label,
            "total_spend": round(total_lbl_spend, 2),
            "overall_total": round(overall_total, 2),
            "percentage_of_total": round(pct_of_total, 1),
            "tx_count": lbl_tx_count,
            "avg_per_tx": round(avg_per_tx, 2),
            "active_months": active_months,
            "monthly_avg": round(monthly_avg, 2),
            "top_category": top_cat,
            "top_category_amt": round(top_cat_amt, 2),
            "top_account": top_acc,
            "top_account_amt": round(top_acc_amt, 2),
            "categories": cat_list,
            "category_groups": grp_list,
            "accounts": acc_list,
            "monthly_trend": {"labels": m_labels, "data": m_data},
            "category_chart": {
                "labels": [c["category"] for c in cat_list[:10]],
                "data": [c["total"] for c in cat_list[:10]]
            },
            "group_chart": {
                "labels": [g["group"] for g in grp_list[:6]],
                "data": [g["total"] for g in grp_list[:6]]
            },
            "account_chart": {
                "labels": [a["account"] for a in acc_list],
                "data": [a["total"] for a in acc_list]
            },
            "category_matrix": {
                "categories": list(pivot.index),
                "months": matrix_months,
                "rows": matrix_rows
            },
            "transactions": top_tx_list
        }
