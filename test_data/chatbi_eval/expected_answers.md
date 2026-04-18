# Expected Answers

Use these as the ground truth when testing ChatBI.

## 1. `sales_basic.csv`

### Questions and expected answers

1. `What is total revenue?`
Expected: `1700`

2. `Which product generated the highest total revenue?`
Expected: `Hammer` with `720`

3. `What is total revenue in the East region?`
Expected: `680`

4. `What is total revenue on 2026-03-04?`
Expected: `340`

5. `Which region generated the highest revenue?`
Expected: `East` with `680`

6. `How many units of Nails were sold in total?`
Expected: `250`

7. `What were total sales by channel?`
Expected:
- `Store = 920`
- `Online = 780`

8. `What was the top-selling product by units?`
Expected: `Nails` with `250` units

9. `What is the average unit price for Drill?`
Expected: `80`

10. `Show revenue by date.`
Expected:
- `2026-03-01 = 300`
- `2026-03-02 = 400`
- `2026-03-03 = 260`
- `2026-03-04 = 340`
- `2026-03-05 = 200`
- `2026-03-06 = 200`

11. `Which date had the highest revenue?`
Expected: `2026-03-02` with `400`

12. `What was West region revenue for Hammer only?`
Expected: `280`

## 2. `inventory_status.csv`

### Questions and expected answers

1. `Which products are out of stock?`
Expected:
- `Nails` in `WH-B`
- `Saw` in `WH-A`

2. `Which rows are below reorder point?`
Expected:
- `Hammer, WH-B`
- `Drill, WH-A`
- `Saw, WH-A`
- `Saw, WH-B`
- `Nails, WH-B`

3. `How many low-stock or out-of-stock rows are there?`
Expected: `5`

4. `What is total on-hand inventory for Hammer across warehouses?`
Expected: `33`

5. `Which product has the lowest total on-hand stock?`
Expected: `Saw` with `2`

## 3. `receivables_aging.csv`

### Questions and expected answers

1. `What is total overdue amount?`
Expected: `5400`

2. `Which customer has the highest overdue amount?`
Expected: `Central Supply` with `2300`

3. `How many overdue invoices are there?`
Expected: `4`

4. `Which overdue invoices are more than 20 days overdue?`
Expected:
- `INV-1003` (`34`)
- `INV-1005` (`29`)

5. `What is the average overdue amount for overdue invoices?`
Expected: `1350`

## Failure signals

Treat these as failures:
- The answer uses numbers not derivable from the CSV.
- The answer ignores a filter like `West region` or `Hammer only`.
- The answer mixes `units` and `revenue`.
- The answer gives the right product but wrong total.
- The answer invents a cause, prediction, or business recommendation not present in the data.
