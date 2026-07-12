# Restaurant Historical Dataset

Synthetic hourly restaurant operations data for training the Self-Learning Forecaster (Phase 3).

## Output

| Property | Value |
|----------|-------|
| **File** | `restaurant_data.csv` |
| **Records** | ≥ 10,000 hourly rows |
| **Period** | ~417 days from 2024-01-01 (hourly snapshots) |
| **Format** | CSV (UTF-8) |

## Columns

### Temporal & calendar
`date`, `hour`, `day_of_week`, `month`, `is_weekend`, `is_holiday`, `season`, `created_at`

### External factors
`temperature`, `rainfall`, `weather`, `promotion`, `local_event`

### Customer demand
`previous_hour_customers`, `previous_day_customers`, `predicted_customers`, `actual_customers`, `walk_in_customers`, `online_reservations`, `takeaway_orders`, `delivery_orders`

### Operations & sales
`average_order_value`, `total_sales`, `kitchen_load`, `table_utilization`, `chef_count`, `waiter_count`, `cashier_count`, `cleaner_count`

### Inventory & quality
`ingredient_chicken_kg`, `ingredient_rice_kg`, `ingredient_oil_l`, `ingredient_onion_kg`, `ingredient_tomato_kg`, `ingredient_cheese_kg`, `ingredient_milk_l`, `inventory_cost`, `supplier_delay_days`, `food_wastage_kg`, `customer_satisfaction`

### Engineered features
`hour_sin`, `hour_cos`, `day_sin`, `day_cos`, `rolling_average_customers`, `moving_average_sales`, `customer_growth_rate`, `inventory_utilization`, `staff_efficiency`, `sales_per_customer`

## Realistic patterns

- **Weekends** → higher customer volume (~+35%)
- **Rain** → fewer walk-ins, higher prediction error
- **Promotions** → increased demand (~+28%)
- **Holidays / festivals** → demand spikes (~+45%)
- **Lunch (11–14) & dinner (18–21)** → demand peaks
- **Late night (22–02)** → low traffic
- **Summer / winter** → seasonal temperature and volume effects
- **Food wastage** → correlates with over-prediction
- **Inventory usage** → scales with actual customer count

## Pipeline

```
dataset_generator.py  →  raw hourly records
feature_engineering.py →  cyclical & rolling features
data_loader.py        →  validate, dedupe, save CSV
```

## API

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/dataset/info` | Row count, columns, missing values, date range, file size |
| POST | `/dataset/regenerate` | Rebuild and overwrite `restaurant_data.csv` |

## Regenerate from CLI

```bash
cd Backend
.\venv\Scripts\Activate.ps1
python -c "from app.dataset.data_loader import DatasetLoader; DatasetLoader().build_and_save()"
```

## Validation

The loader automatically:
1. Removes duplicate `(date, hour)` rows
2. Reports missing values (`local_event` may be null when no event)
3. Asserts ≥ 10,000 records after generation

## Next phase

This dataset will feed **Phase 4+** machine learning models for customer forecasting, staff planning, and inventory optimization.
