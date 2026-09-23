"""Generate a sample sales CSV for UAT (2000 rows).  Run:  py generate_sample.py"""
import csv, os, random

os.makedirs(os.path.join(os.path.dirname(__file__), "sample_data"), exist_ok=True)
random.seed(42)
path = os.path.join(os.path.dirname(__file__), "sample_data", "sample_sales.csv")
regions = ["North", "South", "East", "West"]
categories = ["Electronics", "Clothing", "Food", "Toys"]

with open(path, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["order_id", "date", "region", "category",
                "units", "unit_price", "revenue"])
    for i in range(1, 2001):
        region = random.choice(regions)
        cat = random.choice(categories)
        units = random.randint(1, 50)
        price = round(random.uniform(5, 500), 2)
        revenue = round(units * price, 2)
        month = random.randint(1, 12)
        day = random.randint(1, 28)
        w.writerow([i, f"2024-{month:02d}-{day:02d}", region, cat,
                    units, price, revenue])

print(f"Wrote {path} ({os.path.getsize(path)} bytes)")
