
import xarray as xr
import pygrib
import numpy as np
import matplotlib.pyplot as plt
import os
from ambiance import Atmosphere

%matplotlib inline


#assumes ftp server is mounted (ftp://ftp.ncep.noaa.gov/pub/data/nccf/com/hrrr/prod)
#format hrrr.<date>/conus/hrrr.t<hh_run>z.wrfnatf<hh_pred>.grib2
date = '20241023'
model_run_time = '15' #TODO: automatically find most recent model run
prediction_time = '05' #TODO: convert based on model run time (15 + 5 = 20 UTC = 1pm mst)
fname = '/Volumes/prod/hrrr.' + date + '/conus/hrrr.t' + model_run_time + 'z.wrfnatf' + prediction_time + '.grib2'
LAT = 40.056273
LON = -105.299860
lat_lon_idx = 1072882   # If you change LAT/LON, recompute this with find_idx_for_location(), 
                        # or set this to None and the code will compute it each time
grbs = pygrib.open(fname)
DAL = 9.760 #K/KM
surface_temp_variability = 0 # assume local patch of ground is heated up ~3 deg C more than average temp at ground level
#https://www.mdpi.com/2072-4292/13/1/113
# Select temperature at different levels (altitudes)
# Typically, temperatures are available at isobaric levels (pressure levels)
pressure_data = grbs.select(name='Pressure')
temp_data = grbs.select(name='Temperature')


data = []
#levels = []
#temps = []

def find_idx_for_location(dat, target_lat, target_lon):
    grb = dat[0]
    lat, lon = grb.latlons()
    lat_diff = (lat - target_lat) ** 2
    lon_diff = (lon - target_lon) ** 2
    dist = lat_diff + lon_diff

    idx = dist.argmin()
    real_lat = lat.ravel()[idx]
    real_lon = lon.ravel()[idx]
    print('Closest grid point to (%.6f, %.6f): (%.6f, %.6f)' % (target_lat, target_lon, real_lat, real_lon))

    return idx

if lat_lon_idx is None:
    lat_lon_idx = find_idx_for_location(temp_data, LAT, LON)
    print('Index for (%.3f, %.3f): %d' % (LAT, LON, lat_lon_idx))


#TODO: add directly to pandas dataframe instead of list then sorting, then wrap in a function so can get 
#each hour data easily

pressure_levels = {}
for grb in pressure_data:
    p_vals = grb.values
    p = p_vals.ravel()[lat_lon_idx]
   # print(grb.level, p)
    pressure_levels[grb.level] = p

for grb in temp_data:
    temp_vals = grb.values
    temp_at_location = temp_vals.ravel()[lat_lon_idx]

    #pressure = 90
    if grb.level in pressure_levels and grb.level != 0:
        pressure = pressure_levels[grb.level]
    #print(temp_at_location, grb.level, pressure)
        data.append((pressure, temp_at_location)) #pressure in units of pascals
    #levels.append(grb.level)
    #temps.append(temp_at_location)

data = sorted(data, key=lambda x: x[0])
levels =[x[0] for x in data]
temps = [x[1] for x in data]

#would be nice to convert temperature to deg C

atmos = Atmosphere.from_pressure(levels)
#get altitude in meters from international standard atmosphere model
altitudes = atmos.h.round(2)

#TODO: show surface temp variability as envelope around plotted adiabatic lapse rate
#calculate the expected temperature of a partical of air rising from the surface
temps_lapse = [temps[-1] + surface_temp_variability - DAL*(altitudes[i] - altitudes[-1] )/1000 for i in range(len(altitudes))]

plt.figure(figsize=(8, 6))
plt.plot(temps, altitudes, marker='o', label = "atmospheric lapse rate")
plt.plot(temps_lapse, altitudes, '--k', label = "surface-temp-aligned dry adiabatic lapse rate")
#plt.gca().invert_yaxis()  # Invert axis since pressure decreases with height
plt.ylim([1737, 6096])
plt.xlim([260, 300])
plt.xlabel('Temperature (K)')
plt.ylabel('Altitude (m)')
plt.title('Temperature Profile at (Lat: {}, Lon: {})'.format(LAT, LON))
plt.grid(True)
plt.legend()
plt.show()



# %%
