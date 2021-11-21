import datetime as dt
from skyfield.api import N, W, wgs84, load, Star
from skyfield.data import hipparcos
from skyfield.almanac import find_discrete, risings_and_settings
from skyfield.searchlib import find_maxima
from pytz import timezone
from types import SimpleNamespace

def degToCompass(num):
    val = int((num/22.5)+.5)
    arr = ["N","NNE","NE","ENE","E","ESE", "SE", "SSE","S","SSW","SW","WSW","W","WNW","NW","NNW"]
    return arr[(val % 16)]

def searchElongation(time, sun, earth, planet):
	c_earth = earth.at(time)
	c_sun = c_earth.observe(sun).apparent()
	c_planet = c_earth.observe(planet).apparent()
	actual_elong = c_sun.separation_from(c_planet).degrees
	return int(actual_elong)

tz = timezone('US/Central')
location = wgs84.latlon(41.5868 * N, 93.6250 * W)

now = tz.localize(dt.datetime.now())
start_time = now
end_time = start_time + dt.timedelta(days=1)

ts = load.timescale()
t0 = ts.from_datetime(start_time)
t1 = ts.from_datetime(end_time)

eph = load('de440s.bsp')
sun = eph['sun']
earth = eph['earth']
sun_apparent = (earth + location).at(t0).observe(sun).apparent()

with load.open(hipparcos.URL) as f:
	df = hipparcos.load_dataframe(f)

star_list = [SimpleNamespace(name = 'Sirius', number = 32349)]

for star_info in star_list:
	star = Star.from_dataframe(df.loc[star_info.number])
	
	f = risings_and_settings(eph, star, location)
	
	star_apparent = (earth + location).at(t0).observe(star).apparent()
	alt, az, d = star_apparent.altaz()
	elong = sun_apparent.separation_from(star_apparent)
	above_horizon = alt.degrees > 0
	
	future_elongs = list(map(lambda x: searchElongation(ts.from_datetime(start_time + dt.timedelta(days = 30 * x)), sun, (earth + location), star), range(1,13)))
	
	degAtTime = lambda x: (earth + location).at(x).observe(star).apparent().altaz()[0].degrees
	degAtTime.step_days = 0.04
	
	searchTimes, searchDegrees = find_maxima(t0, t1, degAtTime)
	
	print(star_info.name , '(above horizon)' if above_horizon else '(below horizon)')
	
	print('Max altitude tonight:', int(searchDegrees[0]), 'degrees at', searchTimes[0].astimezone(tz).strftime('%a %d %H:%M'), 'CST')
	
	if(above_horizon):
		print('Azimuth:', az, '(' + degToCompass(az.degrees) + ')')
		print('Altitude:', alt)
	
	print('Elongation:', elong)
		
	print('Future Elongation by Month:', future_elongs)

	for t, updown in zip(*find_discrete(t0, t1, f)):
		event_az = (earth + location).at(t).observe(star).apparent().altaz()[1]
		print(t.astimezone(tz).strftime('%a %d %H:%M'), 'CST',
			  '- rise at' if updown else '- set at', event_az, '(' + degToCompass(event_az.degrees) + ')')
	
	print('')