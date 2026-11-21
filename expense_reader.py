"""
expense_reader.py
=================
Module to read expense CSV files, clean and enrich data, and maintain 
an in-memory pandas DataFrame for personal finance analysis and filtering.
"""

import os
import glob
import re
import fnmatch
import configparser
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional, Set
import pandas as pd
import numpy as np


class ExpenseDataManager:
    """
    Manages loading, parsing, cleaning, deriving features, and filtering
    for expense transaction data.
    """

    DEFAULT_LIST_MONTHLY = ['Monthly', 'Donation']
    DEFAULT_LIST_EXCLUDE = ['EMI']
    WEEKDAY_ORDER = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    WEEKDAY_MAPPING = {'Monday': 1, 'Tuesday': 2, 'Wednesday': 3, 'Thursday': 4, 'Friday': 5, 'Saturday': 6, 'Sunday': 7}

    def __init__(self, config_file: str = "config.ini"):
        self.config_file = config_file
        self.config = configparser.ConfigParser()
        self.file_path = ""
        self.file_name = "*ransactions_*202*.csv"
        self.days_in_past: Optional[int] = None
        self.raw_df: pd.DataFrame = pd.DataFrame()
        self.df: pd.DataFrame = pd.DataFrame()
        self.loaded_files: List[str] = []
        self.load_config()
        self.load_data()

    def load_config(self) -> None:
        """Loads configuration from config.ini if available."""
        if os.path.exists(self.config_file):
            try:
                self.config.read(self.config_file)
                if "EXP" in self.config:
                    exp = self.config["EXP"]
                    rel_path = exp.get("filePath", "Downloads/")
                    home_dir = os.path.expanduser("~")
                    if os.path.isabs(rel_path):
                        self.file_path = rel_path
                    else:
                        self.file_path = os.path.join(home_dir, rel_path)
                    
                    self.file_name = exp.get("fileName", "*ransactions_*202*.csv")
                    days_raw = exp.get("daysInPast", "")
                    if days_raw and days_raw.strip().isdigit():
                        self.days_in_past = int(days_raw.strip())
            except Exception as e:
                print(f"Warning: Failed reading {self.config_file}: {e}")

        # Fallback if file_path is empty or non-existent
        if not self.file_path or not os.path.isdir(self.file_path):
            home_downloads = os.path.join(os.path.expanduser("~"), "Downloads")
            if os.path.isdir(home_downloads):
                self.file_path = home_downloads
            else:
                self.file_path = os.getcwd()

    def discover_files(self) -> List[str]:
        """Finds all CSV files matching the configured file_name pattern."""
        matched = []
        if not os.path.isdir(self.file_path):
            return matched

        for root, _, filenames in os.walk(self.file_path):
            for filename in fnmatch.filter(filenames, self.file_name):
                matched.append(os.path.join(root, filename))
        return sorted(matched)

    @staticmethod
    def extract_labels(raw_label: Any) -> List[str]:
        """
        Extracts individual cleaned label tags from the raw label string.
        Examples:
          '0 Amit 0 Dipti' -> ['Amit', 'Dipti']
          '0 Family Health ' -> ['Family', 'Health']
          '0 Adi' -> ['Adi']
          'Donation' -> ['Donation']
          'CreditCardSettlement' -> ['CreditCardSettlement']
        """
        if pd.isna(raw_label) or not str(raw_label).strip():
            return []
        
        s = str(raw_label).strip()
        # Replace leading '0 ' or standalone '0 ' with delimiter
        s = re.sub(r'(^|\s+)0\s*', '|', s)
        # Handle comma delimiters as well
        s = s.replace(',', '|')
        # Also handle multiple spaces between capitalized words if not separated
        parts = [p.strip() for p in s.split('|') if p.strip()]
        
        # Further refine: split if multiple known tags concatenated with space (e.g. 'Family Health')
        refined_tags = []
        for p in parts:
            # Clean unwanted quotes or punctuation
            p_clean = p.strip(" '\",")
            if p_clean:
                refined_tags.append(p_clean)
        return refined_tags

    def process_dataframe(self, raw_df: pd.DataFrame) -> pd.DataFrame:
        """
        Cleans, standardizes, and adds rich derived features to the transactions DataFrame.
        """
        if raw_df.empty:
            return pd.DataFrame()

        df = raw_df.copy()

        # 1. Standardize column names & handle variations (Name -> Title, Category Group Name -> Category Group, Amount -> Expenses)
        if 'Name' in df.columns:
            if 'Title' in df.columns:
                df['Title'] = df['Title'].fillna(df['Name'])
            else:
                df['Title'] = df['Name']

        if 'Category Group Name' in df.columns:
            if 'Category Group' in df.columns:
                df['Category Group'] = df['Category Group'].fillna(df['Category Group Name'])
            else:
                df['Category Group'] = df['Category Group Name']

        if 'Amount' in df.columns:
            if 'Expenses' in df.columns:
                df['Expenses'] = df['Expenses'].fillna(df['Amount'])
            else:
                df['Expenses'] = df['Amount']

        # Ensure required columns exist with defaults if missing
        required_cols = ['Date', 'Type', 'Expenses', 'Title', 'Category', 'Category Group', 'Account', 'Labels', 'Notes']
        for col in required_cols:
            if col not in df.columns:
                df[col] = "" if col in ['Title', 'Category', 'Category Group', 'Account', 'Labels', 'Notes'] else 0.0

        # Clean and fill string values
        df['Title'] = df['Title'].fillna("Untitled").astype(str).str.strip()
        df.loc[df['Title'].isin(['', 'nan', 'NaN', 'None']), 'Title'] = "Untitled"
        df['Category'] = df['Category'].fillna("Uncategorized").astype(str).str.strip()
        df['Category Group'] = df['Category Group'].fillna("General").astype(str).str.strip()
        df.loc[df['Category Group'].isin(['', 'nan', 'NaN', 'None']), 'Category Group'] = "General"
        df['Account'] = df['Account'].fillna("Default").astype(str).str.strip()
        df['Notes'] = df['Notes'].fillna("").astype(str).str.strip()
        df['Type'] = df['Type'].fillna("Expense").astype(str).str.strip()

        # 2. Date parsing
        # Date strings in CSV often have timestamps: '2026-08-31 20:50:48.726'
        df['Date_Raw'] = df['Date'].astype(str)
        df['Date_Str'] = df['Date_Raw'].str[:19]
        df['Date'] = pd.to_datetime(df['Date_Str'], errors='coerce')
        # Drop rows where Date could not be parsed
        df = df.dropna(subset=['Date']).copy()

        # 3. Amount parsing
        # Raw Amount is usually negative for Expense, positive for Income
        df['Expenses'] = pd.to_numeric(df['Expenses'], errors='coerce').fillna(0.0).round(2)
        
        # 'raw_amount': as exported
        df['raw_amount'] = df['Expenses']
        
        # 'amount': positive value for expenditures and positive for incomes
        df['amount'] = df['raw_amount'].abs()
        
        # 'signed_amount': positive for Income, negative for Expense
        df['signed_amount'] = np.where(df['Type'] == 'Income', df['amount'], -df['amount'])

        # 4. Clean Labels and extract list of tags
        df['Labels_Raw'] = df['Labels'].fillna("").astype(str)
        # Stripped display label string
        df['Labels_Clean'] = df['Labels_Raw'].str.replace(r'(,|^|\s)0\s*', r'\1', regex=True).str.strip()
        df['label_list'] = df['Labels_Raw'].apply(self.extract_labels)

        # 5. Derived Time Features
        df['Year'] = df['Date'].dt.year
        df['Month'] = df['Date'].dt.month
        df['YearMonth'] = df['Date'].dt.strftime('%Y-%m')
        df['MonthName'] = df['Date'].dt.strftime('%b')
        df['Weekday'] = df['Date'].dt.day_name()
        df['DayOfWeekNum'] = df['Weekday'].map(self.WEEKDAY_MAPPING).fillna(1).astype(int)
        df['Weekend'] = np.where(df['Weekday'].isin(['Saturday', 'Sunday']), 'WeekEnd', 'WeekDay')
        df['WeekNum'] = df['Date'].dt.isocalendar().week.astype(str)
        df['YearWeek'] = df['Year'].astype(str) + "-W" + df['WeekNum'].str.zfill(2)
        df['DayOfMonth'] = df['Date'].dt.day
        df['DateOnly'] = df['Date'].dt.strftime('%Y-%m-%d')

        # 6. Classification tags
        df['is_recurring'] = df['Category'].isin(self.DEFAULT_LIST_MONTHLY)
        df['is_excluded'] = df['Category'].isin(self.DEFAULT_LIST_EXCLUDE)
        df['is_discretionary'] = (~df['is_recurring']) & (~df['is_excluded']) & (df['Type'] == 'Expense')

        # Sort chronologically descending
        df.sort_values(by='Date', ascending=False, inplace=True)
        df.reset_index(drop=True, inplace=True)
        return df

    def load_data(self) -> pd.DataFrame:
        """Loads and processes all matched CSV files."""
        matched_files = self.discover_files()
        self.loaded_files = matched_files

        if not matched_files:
            print(f"No CSV files found in {self.file_path} matching {self.file_name}")
            self.raw_df = pd.DataFrame()
            self.df = pd.DataFrame()
            return self.df

        dfs = []
        for file_path in matched_files:
            try:
                temp_df = pd.read_csv(file_path)
                temp_df['source_file'] = os.path.basename(file_path)

                # Standardize column variations per-file before appending
                file_rename = {}
                if 'Name' in temp_df.columns and 'Title' not in temp_df.columns:
                    file_rename['Name'] = 'Title'
                if 'Category Group Name' in temp_df.columns and 'Category Group' not in temp_df.columns:
                    file_rename['Category Group Name'] = 'Category Group'
                if 'Amount' in temp_df.columns and 'Expenses' not in temp_df.columns:
                    file_rename['Amount'] = 'Expenses'
                if file_rename:
                    temp_df.rename(columns=file_rename, inplace=True)

                dfs.append(temp_df)
            except Exception as e:
                print(f"Error reading {file_path}: {e}")

        if not dfs:
            self.raw_df = pd.DataFrame()
            self.df = pd.DataFrame()
            return self.df

        combined_raw = pd.concat(dfs, ignore_index=True)
        # Deduplicate identical transaction rows if any
        core_cols = [c for c in ['Date', 'Type', 'Expenses', 'Amount', 'Title', 'Account'] if c in combined_raw.columns]
        if core_cols:
            combined_raw.drop_duplicates(subset=core_cols, inplace=True)

        self.raw_df = combined_raw
        self.df = self.process_dataframe(combined_raw)
        return self.df

    def reload(self, custom_path: Optional[str] = None) -> pd.DataFrame:
        """Reloads the data from disk, optionally using a new directory."""
        if custom_path and os.path.isdir(custom_path):
            self.file_path = custom_path
        else:
            self.load_config()
        return self.load_data()

    def get_metadata(self) -> Dict[str, Any]:
        """
        Returns all unique options for UI filtering and data boundaries.
        """
        if self.df.empty:
            return {
                "accounts": [],
                "categories": [],
                "category_groups": [],
                "labels": [],
                "types": [],
                "year_months": [],
                "min_date": None,
                "max_date": None,
                "total_rows": 0,
                "loaded_files": [os.path.basename(f) for f in self.loaded_files],
                "file_path": self.file_path
            }

        # Collect unique individual label tags
        all_tags: Set[str] = set()
        for tags in self.df['label_list']:
            for t in tags:
                if t:
                    all_tags.add(t)

        return {
            "accounts": sorted(self.df['Account'].dropna().unique().tolist()),
            "categories": sorted(self.df['Category'].dropna().unique().tolist()),
            "category_groups": sorted(self.df['Category Group'].dropna().unique().tolist()),
            "labels": sorted(list(all_tags)),
            "types": sorted(self.df['Type'].dropna().unique().tolist()),
            "year_months": sorted(self.df['YearMonth'].dropna().unique().tolist(), reverse=True),
            "min_date": self.df['DateOnly'].min(),
            "max_date": self.df['DateOnly'].max(),
            "total_rows": int(len(self.df)),
            "loaded_files": [os.path.basename(f) for f in self.loaded_files],
            "file_path": self.file_path
        }

    def filter_data(self, 
                    start_date: Optional[str] = None,
                    end_date: Optional[str] = None,
                    year_months: Optional[List[str]] = None,
                    accounts: Optional[List[str]] = None,
                    categories: Optional[List[str]] = None,
                    category_groups: Optional[List[str]] = None,
                    labels: Optional[List[str]] = None,
                    types: Optional[List[str]] = None,
                    spending_nature: Optional[str] = None, # 'all', 'discretionary', 'recurring', 'emi'
                    weekend_filter: Optional[str] = None,  # 'all', 'weekend', 'weekday'
                    min_amount: Optional[float] = None,
                    max_amount: Optional[float] = None,
                    search_query: Optional[str] = None,
                    include_transfers: bool = False
                    ) -> pd.DataFrame:
        """
        Applies multidimensional filtering across the loaded DataFrame.
        """
        if self.df.empty:
            return pd.DataFrame()

        filtered = self.df.copy()

        # 1. Filter out Transfer unless explicitly requested
        if not include_transfers and (not types or 'Transfer' not in types):
            filtered = filtered[filtered['Type'] != 'Transfer']

        # 2. Date range
        if start_date:
            filtered = filtered[filtered['DateOnly'] >= start_date]
        if end_date:
            filtered = filtered[filtered['DateOnly'] <= end_date]

        # 3. YearMonth list
        if year_months and len(year_months) > 0:
            filtered = filtered[filtered['YearMonth'].isin(year_months)]

        # 4. Accounts
        if accounts and len(accounts) > 0:
            filtered = filtered[filtered['Account'].isin(accounts)]

        # 5. Categories
        if categories and len(categories) > 0:
            filtered = filtered[filtered['Category'].isin(categories)]

        # 6. Category Groups
        if category_groups and len(category_groups) > 0:
            filtered = filtered[filtered['Category Group'].isin(category_groups)]

        # 7. Types (Expense, Income, Transfer)
        if types and len(types) > 0:
            filtered = filtered[filtered['Type'].isin(types)]

        # 8. Labels / Tags (Match if row has ANY of the selected labels)
        if labels and len(labels) > 0:
            selected_set = set(labels)
            filtered = filtered[filtered['label_list'].apply(lambda lst: bool(selected_set.intersection(lst)))]

        # 9. Spending Nature
        if spending_nature == 'discretionary':
            filtered = filtered[filtered['is_discretionary']]
        elif spending_nature == 'recurring':
            filtered = filtered[filtered['is_recurring']]
        elif spending_nature == 'emi':
            filtered = filtered[filtered['is_excluded']]

        # 10. Weekend / Weekday
        if weekend_filter == 'weekend':
            filtered = filtered[filtered['Weekend'] == 'WeekEnd']
        elif weekend_filter == 'weekday':
            filtered = filtered[filtered['Weekend'] == 'WeekDay']

        # 11. Amount boundaries
        if min_amount is not None:
            filtered = filtered[filtered['amount'] >= float(min_amount)]
        if max_amount is not None:
            filtered = filtered[filtered['amount'] <= float(max_amount)]

        # 12. Search query (Title, Notes, Category, Account)
        if search_query and search_query.strip():
            query = search_query.strip().lower()
            mask = (
                filtered['Title'].str.lower().str.contains(query, na=False) |
                filtered['Notes'].str.lower().str.contains(query, na=False) |
                filtered['Category'].str.lower().str.contains(query, na=False) |
                filtered['Account'].str.lower().str.contains(query, na=False) |
                filtered['Labels_Clean'].str.lower().str.contains(query, na=False)
            )
            filtered = filtered[mask]

        return filtered
