
import db.model as m

class CountryRatioLookupTable(object):
	def _populate_retio_map(iso2='AU'):
		c = m.Country.query.filter(m.Country.iso2==iso2).one()
		if not (c and c.hourlyRate != None and c.hourlyRate > 0):
			raise RuntimeError('error loading reference hourly rate: {}'.format(iso2))
		reference_rate = float(c.hourlyRate)
		ratio_map = {}
		countries = m.Country.query.all()
		for c in countries:
			ratio_map[c.countryId] = c.hourlyRate / reference_rate
		return reference_rate, ratio_map
	reference_rate, _ratio_map = _populate_retio_map()
	@classmethod
	def get_ratio(cls, countryId):
		return cls._ratio_map.get(countryId)

