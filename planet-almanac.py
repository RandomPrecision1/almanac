import datetime as dt
from skyfield.api import N, W, wgs84, load
from skyfield.almanac import find_discrete, risings_and_settings, moon_phase
from skyfield.data import mpc
from skyfield.constants import GM_SUN_Pitjeva_2005_km3_s2 as GM_SUN
from pytz import timezone

def degToCompass(num):
    val = int((num/22.5)+.5)
    arr = ["N","NNE","NE","ENE","E","ESE", "SE", "SSE","S","SSW","SW","WSW","W","WNW","NW","NNW"]
    return arr[(val % 16)]
	
def degToPhase(num):
    val = int((num/45)+.5)
    arr = ['New', 'Waxing Crescent', 'First Quarter', 'Waxing Gibbous', 'Full', 'Waning Gibbous', 'Last Quarter', 'Waxing Crescent']
    return arr[(val % 8)]

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

with load.open('mpcorb.excerpt.dat') as f:
	mp_eph = mpc.load_mpcorb_dataframe(f)

mp_eph = mp_eph.set_index('designation', drop=False)

sun = eph['sun']
earth = eph['earth']
sun_apparent = (earth + location).at(t0).observe(sun).apparent()

planet_list = ['Sun', 'Moon', 'Mercury barycenter', 'Venus barycenter', 'Mars barycenter', 'Jupiter barycenter', 'Saturn barycenter', 'Uranus barycenter', 'Neptune barycenter'] # '(1) Ceres', 'Pluto barycenter'

for planet_name in planet_list:
	if planet_name.startswith('('):
		planet = mp_eph.loc[planet_name]
		planet = sun + mpc.mpcorb_orbit(planet, ts, GM_SUN)
	else:
		planet = eph[planet_name.lower()]
		
	planet_name_t = planet_name.replace(' barycenter', '')
	planet_name_t = planet_name_t.replace('(1) ', '')
	
	
	planet_apparent = (earth + location).at(t0).observe(planet).apparent()
	alt, az, d = planet_apparent.altaz()
	elong = sun_apparent.separation_from(planet_apparent)
	above_horizon = alt.degrees > 0
	
	f = risings_and_settings(eph, planet, location)
	
	future_elongs = list(map(lambda x: searchElongation(ts.from_datetime(start_time + dt.timedelta(days = 7 * x)), sun, (earth + location), planet), range(1,13)))
	
	print(planet_name_t , '(above horizon)' if above_horizon else '(below horizon)')
	if(above_horizon):
		print('Azimuth:', az, '(' + degToCompass(az.degrees) + ')')
		print('Altitude:', alt)
	
	if(planet_name_t != 'Sun'):
		print('Elongation:', elong)
		
	if(planet_name_t != 'Sun' and planet_name_t != 'Moon'):
		print('Future Elongation by Week:', future_elongs)
		
	if(planet_name_t == 'Moon'):
		moon_degrees = moon_phase(eph, t0).degrees
		print('Phase: {:.1f}'.format(moon_degrees), '(' + degToPhase(moon_degrees) + ')')

	for t, updown in zip(*find_discrete(t0, t1, f)):
		event_az = (earth + location).at(t).observe(planet).apparent().altaz()[1]
		print(t.astimezone(tz).strftime('%a %d %H:%M'), 'CST',
			  '- rise at' if updown else '- set at', event_az, '(' + degToCompass(event_az.degrees) + ')')
	
	print('')