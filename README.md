# Zonal-Stats-Merge-Toolbox
This ArcGIS Python Toolbox to batch compute zonal statistics (maximum) from multiple TIFF rasters, merge outputs by zone ID, and export the results as both a shapefile and CSV.
--

## Tool Overview

**Tool Name:** `Batch Zonal Stats (MAX) and Merge`  
**Toolbox Label:** `Zonal Stats Merge Toolbox`

This tool is designed for batch processing using the ArcGIS Toolbox functionality "Zonal Statistics as Table".

---

## Parameters

| Parameter | Type | Description |
|----------|------|-------------|
| `Input Zone Feature Layer` | Feature Layer | Polygon features to define zones (e.g., parcels, watersheds). |
| `Zone Field` | Field | The unique ID field within the zone layer (e.g., `Asset_Uniq`). |
| `Folders Containing TIFF Rasters` | Folder(s) | One or more folders with `.tif` raster files to process. |
| `Output Folder (CSV and Shapefile)` | Folder | Destination where the merged shapefile and CSV table will be saved. |

---

## What It Does

For each `.tif` raster in the specified folders:
1. Computes zonal statistics (`MAXIMUM`) using `ZonalStatisticsAsTable_sa`.
2. Extracts the `MAX` value and associates it with the zone ID.
3. Renames the `MAX` column based on the raster name, ensuring uniqueness.
4. Merges results across all rasters into a single table.
5. Outputs:
   - `zonal_stats_joined.shp` — the original polygon zones with joined attributes
   - `zonal_stats_joined.csv` — the final attribute table in tabular format

---

## Output Structure

Example outputs in the specified output folder:

/output_folder/

├── zonal_stats_joined.shp -> Shapefile with merged attributes

├── zonal_stats_joined.csv -> Matching CSV attribute table

Each new column in the output corresponds to a raster, named using the raster filename (shortened to 10 characters for shapefile compatibility).

---

## Requirements

- ArcGIS Pro with ArcPy
- Python 3.11.11 (ArcGIS Python environment)
- Pandas (`pip install pandas` if running outside the ArcGIS environment)

---

## Notes

- Only rasters with `.tif` extensions will be processed.
- Designed to work recursively over multiple folders.
- Automatically handles column name conflicts to ensure merging works correctly.
- The output folder will be created if it does not exist.
- Shapefiles have a 10-character limit on field names; longer names will be truncated.

---

## Example Use Case

You have:
- A set of building footprints (`buildings.shp`) with a unique field `Asset_Uniq`
- Multiple flood depth rasters (`depth_01.tif`, `depth_02.tif`, etc.)

This tool will:
- Compute the maximum flood depth per building per raster
- Merge all values into a final shapefile and export as CSV

---
