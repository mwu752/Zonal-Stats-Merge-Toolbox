# -*- coding: utf-8 -*-

import arcpy
import os
import pandas as pd
from functools import reduce

class Toolbox:
    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of the
        .pyt file)."""
        self.label = "Zonal Stats Merge Toolbox"
        self.alias = "zonalstatsmerge"

        # List of tool classes associated with this toolbox
        self.tools = [ZonalStatsMerge]


class ZonalStatsMerge(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Batch Zonal Stats (MAX) and Merge"
        self.description = "Loop through TIFF rasters in multiple folders, run Zonal Statistics (Maximum), " \
                           "and merge results by Asset_Uniq, and export as CSV and shapefile."
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define the tool parameters."""
        params = [
            arcpy.Parameter(
                displayName="Input Zone Feature Layer",
                name="in_zone_data",
                datatype="GPFeatureLayer",
                parameterType="Required",
                direction="Input"
            ),
            arcpy.Parameter(
                displayName="Zone Field (e.g., Asset_Uniq)",
                name="zone_field",
                datatype="Field",
                parameterType="Required",
                direction="Input"
            ),
            arcpy.Parameter(
                displayName="Folders Containing TIFF Rasters",
                name="raster_folders",
                datatype="DEFolder",
                parameterType="Required",
                direction="Input",
                multiValue=True
            ),
            arcpy.Parameter(
                displayName="Output Folder (CSV and Shapefile)",
                name="output_folder",
                datatype="DEFolder",
                parameterType="Required",
                direction="Output"
            )
        ]
        params[1].value = "Asset_Uniq"
        return params

        
    def isLicensed(self):
        """Set whether the tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter. This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        in_zone_data = parameters[0].valueAsText
        zone_field = parameters[1].valueAsText
        raster_folders = parameters[2].valueAsText.split(";")
        output_folder = parameters[3].valueAsText

        # Create output folder if it doesn't exist
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
            arcpy.AddMessage(f"📁 Created output folder: {output_folder}")

        result_dfs = []

        for folder in raster_folders:
            folder = folder.strip().strip('"').strip("'")  # Clean up the folder path

            if not os.path.exists(folder):
                arcpy.AddWarning(f"⚠️ Folder does not exist: {folder}")
                continue

            tif_files = [os.path.join(folder, f) for f in os.listdir(folder) if f.lower().endswith('.tif')]

            if not tif_files:
                arcpy.AddWarning(f"⚠️ No .tif files found in: {folder}")
                continue


            for raster_path in tif_files:
                try:
                    raster_name = os.path.splitext(os.path.basename(raster_path))[0]
                    table_name = f"in_memory\\zonal_{raster_name}"

                    # Run Zonal Statistics
                    arcpy.gp.ZonalStatisticsAsTable_sa(
                        in_zone_data,
                        zone_field,
                        raster_path,
                        table_name,
                        "DATA",
                        "MAXIMUM"
                    )

                    fields = [f.name for f in arcpy.ListFields(table_name) if f.type != 'OID']
                    data = [row for row in arcpy.da.SearchCursor(table_name, fields)]
                    df = pd.DataFrame(data, columns=fields)

                    if "MAX" in df.columns:
                        # Ensure unique column name from raster
                        short_col = arcpy.ValidateFieldName(raster_name[:10])
                        original_col = short_col
                        suffix = 1
                        existing_cols = [col for df_ in result_dfs for col in df_.columns if col != zone_field]

                        while short_col in existing_cols:
                            short_col = f"{original_col[:8]}{suffix}"
                            suffix += 1

                        df = df[[zone_field, "MAX"]].rename(columns={"MAX": short_col})
                        result_dfs.append(df)
                        arcpy.AddMessage(f"✅ Processed: {raster_name}")
                    else:
                        arcpy.AddWarning(f"⚠️ 'MAX' field missing in: {raster_name}")

                except Exception as e:
                    arcpy.AddError(f"❌ Failed: {raster_path} | {str(e)}")


        if not result_dfs:
            arcpy.AddWarning("⚠️ No valid results to merge.")
            return

        merged_df = reduce(lambda left, right: pd.merge(left, right, on=zone_field, how='outer'), result_dfs)

        output_shapefile = os.path.join(output_folder, "zonal_stats_joined.shp")
        temp_csv = os.path.join(output_folder, "_temp_table.csv")
        merged_df.to_csv(temp_csv, index=False)
        arcpy.TableToTable_conversion(temp_csv, "in_memory", "temp_table")

        arcpy.management.CopyFeatures(in_zone_data, output_shapefile)
        arcpy.management.JoinField(
            in_data=output_shapefile,
            in_field=zone_field,
            join_table="in_memory\\temp_table",
            join_field=zone_field
        )

        arcpy.AddMessage(f"🗺️ Shapefile saved: {output_shapefile}")

        # Export the final attribute table of the shapefile as CSV
        output_csv = os.path.join(output_folder, "zonal_stats_joined.csv")
        fields = [f.name for f in arcpy.ListFields(output_shapefile) if f.type != 'OID']
        data = [row for row in arcpy.da.SearchCursor(output_shapefile, fields)]
        final_df = pd.DataFrame(data, columns=fields)
        final_df.to_csv(output_csv, index=False)
        arcpy.AddMessage(f"📄 Final attribute table saved as CSV: {output_csv}")

        if os.path.exists(temp_csv):
            os.remove(temp_csv)


    def postExecute(self, parameters):
        """This method takes place after outputs are processed and
        added to the display."""
        return
