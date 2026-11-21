"""
test_app.py
===========
Automated test suite verifying the expense reader, analytics engine,
and Flask web application endpoints.
"""

import unittest
import json
from app import app, data_manager
from expense_analytics import ExpenseAnalytics


class TestExpenseApp(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.client = app.test_client()

    def test_metadata_endpoint(self):
        res = self.client.get('/api/metadata')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn('accounts', data)
        self.assertIn('categories', data)
        self.assertIn('labels', data)
        self.assertGreater(data['total_rows'], 0)
        self.assertGreater(len(data['accounts']), 0)
        self.assertGreater(len(data['categories']), 0)

    def test_filter_default_expense(self):
        payload = {
            "types": ["Expense"],
            "page": 1,
            "page_size": 15
        }
        res = self.client.post('/api/filter', json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data['status'], 'success')
        self.assertIn('kpis', data)
        self.assertIn('monthly', data)
        self.assertIn('category', data)
        self.assertIn('weekday', data)
        self.assertIn('weekly', data)
        self.assertIn('account', data)
        self.assertIn('label', data)
        self.assertIn('transactions', data)
        self.assertGreater(data['kpis']['total_expense'], 0)
        self.assertGreater(len(data['transactions']), 0)

    def test_filter_by_label(self):
        payload = {
            "labels": ["Amit"],
            "page": 1,
            "page_size": 10
        }
        res = self.client.post('/api/filter', json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data['status'], 'success')
        self.assertGreater(data['pagination']['total_rows'], 0)
        for tx in data['transactions']:
            self.assertIn('Amit', tx['label_list'])

    def test_filter_by_account(self):
        payload = {
            "accounts": ["AmitK CC"],
            "page": 1,
            "page_size": 10
        }
        res = self.client.post('/api/filter', json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data['status'], 'success')
        self.assertGreater(data['pagination']['total_rows'], 0)
        for tx in data['transactions']:
            self.assertEqual(tx['account'], 'AmitK CC')

    def test_filter_by_category(self):
        payload = {
            "categories": ["Grocery"],
            "page": 1,
            "page_size": 10
        }
        res = self.client.post('/api/filter', json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data['status'], 'success')
        self.assertGreater(data['pagination']['total_rows'], 0)
        for tx in data['transactions']:
            self.assertEqual(tx['category'], 'Grocery')

    def test_filter_by_nature_discretionary(self):
        payload = {
            "spending_nature": "discretionary",
            "page": 1,
            "page_size": 10
        }
        res = self.client.post('/api/filter', json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data['status'], 'success')
        for tx in data['transactions']:
            self.assertNotIn(tx['category'], ['Monthly', 'Donation', 'EMI'])

    def test_filter_weekend_only(self):
        payload = {
            "weekend_filter": "weekend",
            "page": 1,
            "page_size": 10
        }
        res = self.client.post('/api/filter', json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        for tx in data['transactions']:
            self.assertIn(tx['weekday'], ['Saturday', 'Sunday'])

    def test_export_csv(self):
        payload = {
            "categories": ["Grocery"]
        }
        res = self.client.post('/api/export/csv', json=payload)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.mimetype, 'text/csv')
        csv_text = res.data.decode('utf-8')
        self.assertIn('Date', csv_text)
        self.assertIn('Amount', csv_text)
        self.assertIn('Grocery', csv_text)

    def test_home_page(self):
        res = self.client.get('/')
        self.assertEqual(res.status_code, 200)
        html = res.data.decode('utf-8')
        self.assertIn('ExpensePulse', html)
        self.assertIn('monthlyChart', html)
        self.assertIn('tab-label-analysis', html)
        self.assertIn('view-label-analysis', html)

    def test_label_deep_dive_endpoint(self):
        payload = {
            "label": "Amit"
        }
        res = self.client.post('/api/label-analysis', json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data['status'], 'success')
        dive = data['data']
        self.assertEqual(dive['label'], 'Amit')
        self.assertGreater(dive['total_spend'], 0)
        self.assertGreater(len(dive['categories']), 0)
        self.assertGreater(len(dive['accounts']), 0)
        self.assertIn('category_chart', dive)
        self.assertIn('account_chart', dive)
        self.assertIn('monthly_trend', dive)
        # Check that categories and accounts have total and percentage
        for cat in dive['categories'][:3]:
            self.assertIn('category', cat)
            self.assertIn('total', cat)
            self.assertIn('percentage', cat)
        for acc in dive['accounts'][:3]:
            self.assertIn('account', acc)
            self.assertIn('total', acc)
            self.assertIn('percentage', acc)

    def test_filter_by_date_range_prev_month(self):
        payload = {
            "start_date": "2026-10-01",
            "end_date": "2026-10-31",
            "types": ["Expense"],
            "page": 1,
            "page_size": 20
        }
        res = self.client.post('/api/filter', json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data['status'], 'success')
        self.assertGreater(data['pagination']['total_rows'], 0)
        for tx in data['transactions']:
            self.assertTrue(tx['date'] >= '2026-10-01')
            self.assertTrue(tx['date'] <= '2026-10-31 23:59:59')

    def test_home_page_contains_prev_month_preset(self):
        res = self.client.get('/')
        self.assertEqual(res.status_code, 200)
        html = res.data.decode('utf-8')
        self.assertIn('Previous Month', html)
        self.assertIn("setDatePreset('prevMonth'", html)
        self.assertIn('prevMonthBadge', html)

    def test_validation_error_invalid_page(self):
        """Pydantic should reject page < 1 with 422 Unprocessable Entity."""
        payload = {"page": 0}
        res = self.client.post('/api/filter', json=payload)
        self.assertEqual(res.status_code, 422)
        data = res.get_json()
        self.assertEqual(data['status'], 'error')
        self.assertIn('errors', data)

    def test_validation_error_invalid_min_amount(self):
        """Pydantic should reject non-numeric amount with 422."""
        payload = {"min_amount": "invalid_number"}
        res = self.client.post('/api/filter', json=payload)
        self.assertEqual(res.status_code, 422)
        data = res.get_json()
        self.assertEqual(data['status'], 'error')

    def test_validation_empty_strings_and_nulls_accepted(self):
        """Pydantic should gracefully clean empty strings and accept nulls."""
        payload = {
            "min_amount": "",
            "max_amount": None,
            "search_query": "   ",
            "page": 1,
            "page_size": 10
        }
        res = self.client.post('/api/filter', json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data['status'], 'success')


if __name__ == '__main__':
    unittest.main()

