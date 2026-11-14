"""One-off script used to export data/prices.csv from the original Excel workbook.

Usage: python scripts/extract_from_excel.py workbook.xlsx data/prices.csv [sheet_name]
Requires openpyxl (not needed for the main analysis).
"""

import csv
import datetime
import sys

import openpyxl

# Column positions (0-based) of each closing-price column in the data sheet.
COLUMNS = {"AMZN": 1, "SPX": 8, "STX": 12, "F": 21, "NVDA": 26, "MSFT": 31}
DATE_COL = 2


def main(src: str, dst: str, sheet: str | None = None) -> None:
    wb = openpyxl.load_workbook(src, read_only=True)
    ws = wb[sheet] if sheet else wb.worksheets[-1]
    with open(dst, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["date", *COLUMNS])
        for row in ws.iter_rows(min_row=2, values_only=True):
            if not row[DATE_COL]:
                continue
            d = datetime.datetime.strptime(row[DATE_COL], "%b %d %Y").date().isoformat()
            w.writerow([d, *(row[i] for i in COLUMNS.values())])


if __name__ == "__main__":
    main(*sys.argv[1:])
