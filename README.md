# Configuring an OpenStreetMap server (Ubuntu 16.04)

The process described here provides a means of creating a standalone tile server that is capable of creating
Raster and Vector tiles from OpenStreetMap data.

It is inspired and based upon the information contained at:

* [Manually building a tile server from switch2osm](https://switch2osm.org/serving-tiles/manually-building-a-tile-server-14-04/)
* [OSM 2 Vector tiles](http://osm2vectortiles.org/)
* [Imposm3 Differ](https://github.com/lyrk/imposm3-differ)

This process utilises [imposm3](https://github.com/omniscale/imposm3) to import data into a postgis database.
The import is significantly faster than using [osm2pgsql](https://github.com/openstreetmap/osm2pgsql).

## Installing prerequisites

```
sudo apt-get install libboost-all-dev subversion git-core tar unzip wget bzip2 build-essential autoconf libtool libxml2-dev libgeos-dev libgeos++-dev 
libpq-dev libbz2-dev libproj-dev munin-node munin libprotobuf-c0-dev protobuf-c-compiler libfreetype6-dev libpng12-dev libtiff5-dev libicu-dev 
libgdal-dev libcairo-dev libcairomm-1.0-dev apache2 apache2-dev libagg-dev liblua5.2-dev ttf-unifont lua5.1 liblua5.1-dev libgeotiff-epsg node-carto sqlite3
gdal-bin osmctools
```

## Install postgresql / postgis

Get the relevant packages from the Ubuntu package manager
```
sudo apt-get install postgresql postgresql-contrib postgis postgresql-9.5-postgis-2.2 pgadmin3
```
Create a database and create a user called osm
```
sudo -u postgres -i
createuser osm
createdb -E UTF8 -O osm osm
exit
```
Create a Ubuntu username called osm and set a password
```
sudo useradd -m osm
sudo passwd osm
```
Setup PostGIS and hstore on the PostgreSQL database and set the osm user password to osm.
```
sudo -u postgres psql
\c osm
CREATE EXTENSION postgis;
CREATE EXTENSION hstore;
ALTER TABLE geometry_columns OWNER TO osm;
ALTER TABLE spatial_ref_sys OWNER TO osm;
ALTER USER osm WITH PASSWORD 'osm';
\q
```

## Install Go and Imposm3
Install Go using
```
sudo apt-get install golang-go
```
Obtain the latest Imposm3 [binary](https://imposm.org/static/rel/).
```
mkdir ~/bin
```
Extract the archive to the `~/bin` and add it to your path. To persist this add the following to .bashrc and source it to apply the changes
```
export PATH=$PATH:$HOME/bin
```

## Install and configure a Samba share

To enable easy access to the Data folder for later processing setup samba by following [this](https://help.ubuntu.com/community/How%20to%20Create%20a%20Network%20Share%20Via%20Samba%20Via%20CLI%20(Command-line%20interface/Linux%20Terminal)%20-%20Uncomplicated,%20Simple%20and%20Brief%20Way!) guide.

Setup the share on the folder
```
~/src/OSMServer/Data
```

## Clone OSMServer repo
```
cd ~/src
git clone https://github.com/daveb1034/OSMServer.git
cd OSMServer
```

## Download OpenStreetMap data

This process has been designed to work on a whole planet load and applies the daily change files to the data on completion.

Download the latest [plant file](http://planet.openstreetmap.org/pbf/planet-latest.osm.pbf) from [planet.openstreetmap.org](http://planet.openstreetmap.org/).

```
cd ~/src/OSMServer/Data/
wget http://planet.openstreetmap.org/pbf/planet-latest.osm.pbf
```

## Import the data into PostgreSQL

The import process is managed using a number of configuration files and a python script.
You will need to set the execute flag on the python script to enable it to run.
```
cd ~/src/OSMServer/src/updater
./import_pbf.py -i -C
```
The -i switch calls imposm3 to import the data using the default configuration which will store the cache in ~/src/OSMServer/Data and utilise the mapping file in the smae directory as import_pbf.py.
The -C switch converts the planet-latest.osm.pnf to .o5m for later processing.

A full planet import (~33GB) took approximately 29hours on my hardware (48GB Ram Dual 8Core Intel Xeon Processors and 2 x 20TB RAID)

## Optional section

**This section is not needed if using the mapping.yml file provided with the project**

The imposm3 importer looks in the background for an id column. If one is found the importer skips the creation of a SERIAL PRIMARY KEY field. THis will prevnt the data being accessible in ArcGIS.

If you specify the option to use single id space and specify a cloumn named id the following code sql file will need to be run. 

```
cd ~/src/OSMServer/src/updater
sudo -u postgres psql
\c osm
\i table_id.sql
\q
```

To avoid having to run this ensure that your mapping file does not have a column named id specified.

## Apply diff updates

This process has been adapted from the [differ_cron.py](https://github.com/lyrk/imposm3-differ) script.
Before setting up the auto update script it is advisable to apply all the previous change files. This can be achieved using the auto update script by specifiying -d and the diff number.

By design Imposm3 tries to guess the last state number but this is based on the minutely replication. In order to change this open the last.state.text file in the imposm3 cache directory and change the number to relevant daily number eg 1517.
Failure to do this will cause imposm3 to report that each daily diff has already been imported.

You will need to set the execute flag on the python script to enable it to run.

```
cd ~/src/OSMServer/src/updater
./update.py -d <diffnumber>
```

At this time only one diff file at a time can be applied using the update script.

## Configure the cron

To ensure the database updates daily use the user crontab to run the task

```
crontab -e
```

To ensure that the task runs correctly the PATH= variable will need setting with cron. Add the script with the options specified.

This is not yet working and wll be resolved soon.

The daily update will also update the .o5m planet file and filter all highway related information for use in the ArcGIS OSM Editor tools.

## Additional tasks

To enable access to the database from a remote machine follow the Postgres instructions to expose the database on your network. To apply bounding boxes to 
highways file on a windows machine setup Samba on the server and share the Data folder. There are lenty of tutorials out there to do this.

## Extract a bounding box of the osm data within ArcGIS

To extract the data, add all the layers from the postgis database. Save the map document and then run Package Map with extent of the map as the AOI. If ths map document is symbolise it can be used to create a map cache as well.

## Future work

* Optimise Postgresql for the large imports.
* Create more suitable mapping file.
  * Each table results in a connection to the database when writing due to the underlying operation of imposm3 so max connections needs to reflect this
* Benchmark on current hardware in diff and normal mode
* Design optimised hardware config for the process
  * confirm planet import cache sizes normal and diff
  * confirm size of resulting database tables