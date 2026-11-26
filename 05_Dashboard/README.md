# Power BI dashboard

The report is built in Power BI Desktop on top of `03_Data/suez_services_clean.csv`.

![Power BI dashboard](https://github.com/Mayur96k/Suez_Services_Power_BI_Dashboard/assets/114133429/6293f2f4-9cb0-4369-8f94-36445cc54d16)

## Report contents
- **Map visual**: every site plotted by latitude/longitude, coloured by service type
- **Slicers**: service type and country
- **KPI cards**: total sites and number of service types
- **Bar chart**: sites per service type, cross-filtered with the map

## Rebuild it
1. Open Power BI Desktop → **Get data → Text/CSV** → `03_Data/suez_services_clean.csv`.
2. Set the `latitude` / `longitude` data category to **Latitude** / **Longitude** and summarisation to **Don't summarise**.
3. Add a **Map** (or Azure Map) visual: Latitude, Longitude, Legend = `service_type`, Tooltips = `service_name`.
4. Add slicers for `service_type` and `country`, a card with *Count of service_name*, and a bar chart of sites by type.

> The `.pbix` file will be added to this folder (`Suez_Services_Dashboard.pbix`).
