# OpenStreetMap to File GeoDatabase (Ubuntu 18.04)

This process will utilise imposm3, the Esri FileGDB API and GDAL/OGR to import the OpenStreetMap planet file and convert to an Esri File Geodatabase.

The intent is to automate this process so that it runs weekly via Cron.

## Key Steps

1. Install Prerequisites - including libraries and Postgresql/Postgis.
2. Install File Geodatabase API.
3. Build GDAL with required 3rd Party Drivers.
4. Build Imposm3 from source.
5. Run the import.
6. Update database tables.
7. Export to File Geodatabase.