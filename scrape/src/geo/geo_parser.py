import re

import pycountry

_COUNTRY_LIST = {x.name.lower(): x for x in pycountry.countries}
_COUNTRY_ALIASES = {"USA": "United States"}
_COUNTRY_COORDS = {
    "AD": {"lat": 42.546245, "lon": 1.601554, "name": "Andorra"},
    "AE": {"lat": 23.424076, "lon": 53.847818, "name": "United Arab Emirates"},
    "AF": {"lat": 33.93911, "lon": 67.709953, "name": "Afghanistan"},
    "AG": {"lat": 17.060816, "lon": -61.796428, "name": "Antigua and Barbuda"},
    "AI": {"lat": 18.220554, "lon": -63.068615, "name": "Anguilla"},
    "AL": {"lat": 41.153332, "lon": 20.168331, "name": "Albania"},
    "AM": {"lat": 40.069099, "lon": 45.038189, "name": "Armenia"},
    "AN": {"lat": 12.226079, "lon": -69.060087, "name": "Netherlands Antilles"},
    "AO": {"lat": -11.202692, "lon": 17.873887, "name": "Angola"},
    "AQ": {"lat": -75.250973, "lon": -0.071389, "name": "Antarctica"},
    "AR": {"lat": -38.416097, "lon": -63.616672, "name": "Argentina"},
    "AS": {"lat": -14.270972, "lon": -170.132217, "name": "American Samoa"},
    "AT": {"lat": 47.516231, "lon": 14.550072, "name": "Austria"},
    "AU": {"lat": -25.274398, "lon": 133.775136, "name": "Australia"},
    "AW": {"lat": 12.52111, "lon": -69.968338, "name": "Aruba"},
    "AZ": {"lat": 40.143105, "lon": 47.576927, "name": "Azerbaijan"},
    "BA": {"lat": 43.915886, "lon": 17.679076, "name": "Bosnia and Herzegovina"},
    "BB": {"lat": 13.193887, "lon": -59.543198, "name": "Barbados"},
    "BD": {"lat": 23.684994, "lon": 90.356331, "name": "Bangladesh"},
    "BE": {"lat": 50.503887, "lon": 4.469936, "name": "Belgium"},
    "BF": {"lat": 12.238333, "lon": -1.561593, "name": "Burkina Faso"},
    "BG": {"lat": 42.733883, "lon": 25.48583, "name": "Bulgaria"},
    "BH": {"lat": 25.930414, "lon": 50.637772, "name": "Bahrain"},
    "BI": {"lat": -3.373056, "lon": 29.918886, "name": "Burundi"},
    "BJ": {"lat": 9.30769, "lon": 2.315834, "name": "Benin"},
    "BM": {"lat": 32.321384, "lon": -64.75737, "name": "Bermuda"},
    "BN": {"lat": 4.535277, "lon": 114.727669, "name": "Brunei"},
    "BO": {"lat": -16.290154, "lon": -63.588653, "name": "Bolivia"},
    "BR": {"lat": -14.235004, "lon": -51.92528, "name": "Brazil"},
    "BS": {"lat": 25.03428, "lon": -77.39628, "name": "Bahamas"},
    "BT": {"lat": 27.514162, "lon": 90.433601, "name": "Bhutan"},
    "BV": {"lat": -54.423199, "lon": 3.413194, "name": "Bouvet Island"},
    "BW": {"lat": -22.328474, "lon": 24.684866, "name": "Botswana"},
    "BY": {"lat": 53.709807, "lon": 27.953389, "name": "Belarus"},
    "BZ": {"lat": 17.189877, "lon": -88.49765, "name": "Belize"},
    "CA": {"lat": 56.130366, "lon": -106.346771, "name": "Canada"},
    "CC": {"lat": -12.164165, "lon": 96.870956, "name": "Cocos [Keeling] Islands"},
    "CD": {"lat": -4.038333, "lon": 21.758664, "name": "Congo [DRC]"},
    "CF": {"lat": 6.611111, "lon": 20.939444, "name": "Central African Republic"},
    "CG": {"lat": -0.228021, "lon": 15.827659, "name": "Congo [Republic]"},
    "CH": {"lat": 46.818188, "lon": 8.227512, "name": "Switzerland"},
    "CI": {"lat": 7.539989, "lon": -5.54708, "name": "Côte d'Ivoire"},
    "CK": {"lat": -21.236736, "lon": -159.777671, "name": "Cook Islands"},
    "CL": {"lat": -35.675147, "lon": -71.542969, "name": "Chile"},
    "CM": {"lat": 7.369722, "lon": 12.354722, "name": "Cameroon"},
    "CN": {"lat": 35.86166, "lon": 104.195397, "name": "China"},
    "CO": {"lat": 4.570868, "lon": -74.297333, "name": "Colombia"},
    "CR": {"lat": 9.748917, "lon": -83.753428, "name": "Costa Rica"},
    "CU": {"lat": 21.521757, "lon": -77.781167, "name": "Cuba"},
    "CV": {"lat": 16.002082, "lon": -24.013197, "name": "Cape Verde"},
    "CX": {"lat": -10.447525, "lon": 105.690449, "name": "Christmas Island"},
    "CY": {"lat": 35.126413, "lon": 33.429859, "name": "Cyprus"},
    "CZ": {"lat": 49.817492, "lon": 15.472962, "name": "Czech Republic"},
    "DE": {"lat": 51.165691, "lon": 10.451526, "name": "Germany"},
    "DJ": {"lat": 11.825138, "lon": 42.590275, "name": "Djibouti"},
    "DK": {"lat": 56.26392, "lon": 9.501785, "name": "Denmark"},
    "DM": {"lat": 15.414999, "lon": -61.370976, "name": "Dominica"},
    "DO": {"lat": 18.735693, "lon": -70.162651, "name": "Dominican Republic"},
    "DZ": {"lat": 28.033886, "lon": 1.659626, "name": "Algeria"},
    "EC": {"lat": -1.831239, "lon": -78.183406, "name": "Ecuador"},
    "EE": {"lat": 58.595272, "lon": 25.013607, "name": "Estonia"},
    "EG": {"lat": 26.820553, "lon": 30.802498, "name": "Egypt"},
    "EH": {"lat": 24.215527, "lon": -12.885834, "name": "Western Sahara"},
    "ER": {"lat": 15.179384, "lon": 39.782334, "name": "Eritrea"},
    "ES": {"lat": 40.463667, "lon": -3.74922, "name": "Spain"},
    "ET": {"lat": 9.145, "lon": 40.489673, "name": "Ethiopia"},
    "FI": {"lat": 61.92411, "lon": 25.748151, "name": "Finland"},
    "FJ": {"lat": -16.578193, "lon": 179.414413, "name": "Fiji"},
    "FK": {"lat": -51.796253, "lon": -59.523613, "name": "Falkland Islands [Islas Malvinas]"},
    "FM": {"lat": 7.425554, "lon": 150.550812, "name": "Micronesia"},
    "FO": {"lat": 61.892635, "lon": -6.911806, "name": "Faroe Islands"},
    "FR": {"lat": 46.227638, "lon": 2.213749, "name": "France"},
    "GA": {"lat": -0.803689, "lon": 11.609444, "name": "Gabon"},
    "GB": {"lat": 55.378051, "lon": -3.435973, "name": "United Kingdom"},
    "GD": {"lat": 12.262776, "lon": -61.604171, "name": "Grenada"},
    "GE": {"lat": 42.315407, "lon": 43.356892, "name": "Georgia"},
    "GF": {"lat": 3.933889, "lon": -53.125782, "name": "French Guiana"},
    "GG": {"lat": 49.465691, "lon": -2.585278, "name": "Guernsey"},
    "GH": {"lat": 7.946527, "lon": -1.023194, "name": "Ghana"},
    "GI": {"lat": 36.137741, "lon": -5.345374, "name": "Gibraltar"},
    "GL": {"lat": 71.706936, "lon": -42.604303, "name": "Greenland"},
    "GM": {"lat": 13.443182, "lon": -15.310139, "name": "Gambia"},
    "GN": {"lat": 9.945587, "lon": -9.696645, "name": "Guinea"},
    "GP": {"lat": 16.995971, "lon": -62.067641, "name": "Guadeloupe"},
    "GQ": {"lat": 1.650801, "lon": 10.267895, "name": "Equatorial Guinea"},
    "GR": {"lat": 39.074208, "lon": 21.824312, "name": "Greece"},
    "GS": {"lat": -54.429579, "lon": -36.587909, "name": "South Georgia and the South Sandwich Islands"},
    "GT": {"lat": 15.783471, "lon": -90.230759, "name": "Guatemala"},
    "GU": {"lat": 13.444304, "lon": 144.793731, "name": "Guam"},
    "GW": {"lat": 11.803749, "lon": -15.180413, "name": "Guinea-Bissau"},
    "GY": {"lat": 4.860416, "lon": -58.93018, "name": "Guyana"},
    "GZ": {"lat": 31.354676, "lon": 34.308825, "name": "Gaza Strip"},
    "HK": {"lat": 22.396428, "lon": 114.109497, "name": "Hong Kong"},
    "HM": {"lat": -53.08181, "lon": 73.504158, "name": "Heard Island and McDonald Islands"},
    "HN": {"lat": 15.199999, "lon": -86.241905, "name": "Honduras"},
    "HR": {"lat": 45.1, "lon": 15.2, "name": "Croatia"},
    "HT": {"lat": 18.971187, "lon": -72.285215, "name": "Haiti"},
    "HU": {"lat": 47.162494, "lon": 19.503304, "name": "Hungary"},
    "ID": {"lat": -0.789275, "lon": 113.921327, "name": "Indonesia"},
    "IE": {"lat": 53.41291, "lon": -8.24389, "name": "Ireland"},
    "IL": {"lat": 31.046051, "lon": 34.851612, "name": "Israel"},
    "IM": {"lat": 54.236107, "lon": -4.548056, "name": "Isle of Man"},
    "IN": {"lat": 20.593684, "lon": 78.96288, "name": "India"},
    "IO": {"lat": -6.343194, "lon": 71.876519, "name": "British Indian Ocean Territory"},
    "IQ": {"lat": 33.223191, "lon": 43.679291, "name": "Iraq"},
    "IR": {"lat": 32.427908, "lon": 53.688046, "name": "Iran"},
    "IS": {"lat": 64.963051, "lon": -19.020835, "name": "Iceland"},
    "IT": {"lat": 41.87194, "lon": 12.56738, "name": "Italy"},
    "JE": {"lat": 49.214439, "lon": -2.13125, "name": "Jersey"},
    "JM": {"lat": 18.109581, "lon": -77.297508, "name": "Jamaica"},
    "JO": {"lat": 30.585164, "lon": 36.238414, "name": "Jordan"},
    "JP": {"lat": 36.204824, "lon": 138.252924, "name": "Japan"},
    "KE": {"lat": -0.023559, "lon": 37.906193, "name": "Kenya"},
    "KG": {"lat": 41.20438, "lon": 74.766098, "name": "Kyrgyzstan"},
    "KH": {"lat": 12.565679, "lon": 104.990963, "name": "Cambodia"},
    "KI": {"lat": -3.370417, "lon": -168.734039, "name": "Kiribati"},
    "KM": {"lat": -11.875001, "lon": 43.872219, "name": "Comoros"},
    "KN": {"lat": 17.357822, "lon": -62.782998, "name": "Saint Kitts and Nevis"},
    "KP": {"lat": 40.339852, "lon": 127.510093, "name": "North Korea"},
    "KR": {"lat": 35.907757, "lon": 127.766922, "name": "South Korea"},
    "KW": {"lat": 29.31166, "lon": 47.481766, "name": "Kuwait"},
    "KY": {"lat": 19.513469, "lon": -80.566956, "name": "Cayman Islands"},
    "KZ": {"lat": 48.019573, "lon": 66.923684, "name": "Kazakhstan"},
    "LA": {"lat": 19.85627, "lon": 102.495496, "name": "Laos"},
    "LB": {"lat": 33.854721, "lon": 35.862285, "name": "Lebanon"},
    "LC": {"lat": 13.909444, "lon": -60.978893, "name": "Saint Lucia"},
    "LI": {"lat": 47.166, "lon": 9.555373, "name": "Liechtenstein"},
    "LK": {"lat": 7.873054, "lon": 80.771797, "name": "Sri Lanka"},
    "LR": {"lat": 6.428055, "lon": -9.429499, "name": "Liberia"},
    "LS": {"lat": -29.609988, "lon": 28.233608, "name": "Lesotho"},
    "LT": {"lat": 55.169438, "lon": 23.881275, "name": "Lithuania"},
    "LU": {"lat": 49.815273, "lon": 6.129583, "name": "Luxembourg"},
    "LV": {"lat": 56.879635, "lon": 24.603189, "name": "Latvia"},
    "LY": {"lat": 26.3351, "lon": 17.228331, "name": "Libya"},
    "MA": {"lat": 31.791702, "lon": -7.09262, "name": "Morocco"},
    "MC": {"lat": 43.750298, "lon": 7.412841, "name": "Monaco"},
    "MD": {"lat": 47.411631, "lon": 28.369885, "name": "Moldova"},
    "ME": {"lat": 42.708678, "lon": 19.37439, "name": "Montenegro"},
    "MG": {"lat": -18.766947, "lon": 46.869107, "name": "Madagascar"},
    "MH": {"lat": 7.131474, "lon": 171.184478, "name": "Marshall Islands"},
    "MK": {"lat": 41.608635, "lon": 21.745275, "name": "Macedonia [FYROM]"},
    "ML": {"lat": 17.570692, "lon": -3.996166, "name": "Mali"},
    "MM": {"lat": 21.913965, "lon": 95.956223, "name": "Myanmar [Burma]"},
    "MN": {"lat": 46.862496, "lon": 103.846656, "name": "Mongolia"},
    "MO": {"lat": 22.198745, "lon": 113.543873, "name": "Macau"},
    "MP": {"lat": 17.33083, "lon": 145.38469, "name": "Northern Mariana Islands"},
    "MQ": {"lat": 14.641528, "lon": -61.024174, "name": "Martinique"},
    "MR": {"lat": 21.00789, "lon": -10.940835, "name": "Mauritania"},
    "MS": {"lat": 16.742498, "lon": -62.187366, "name": "Montserrat"},
    "MT": {"lat": 35.937496, "lon": 14.375416, "name": "Malta"},
    "MU": {"lat": -20.348404, "lon": 57.552152, "name": "Mauritius"},
    "MV": {"lat": 3.202778, "lon": 73.22068, "name": "Maldives"},
    "MW": {"lat": -13.254308, "lon": 34.301525, "name": "Malawi"},
    "MX": {"lat": 23.634501, "lon": -102.552784, "name": "Mexico"},
    "MY": {"lat": 4.210484, "lon": 101.975766, "name": "Malaysia"},
    "MZ": {"lat": -18.665695, "lon": 35.529562, "name": "Mozambique"},
    "NA": {"lat": -22.95764, "lon": 18.49041, "name": "Namibia"},
    "NC": {"lat": -20.904305, "lon": 165.618042, "name": "New Caledonia"},
    "NE": {"lat": 17.607789, "lon": 8.081666, "name": "Niger"},
    "NF": {"lat": -29.040835, "lon": 167.954712, "name": "Norfolk Island"},
    "NG": {"lat": 9.081999, "lon": 8.675277, "name": "Nigeria"},
    "NI": {"lat": 12.865416, "lon": -85.207229, "name": "Nicaragua"},
    "NL": {"lat": 52.132633, "lon": 5.291266, "name": "Netherlands"},
    "NO": {"lat": 60.472024, "lon": 8.468946, "name": "Norway"},
    "NP": {"lat": 28.394857, "lon": 84.124008, "name": "Nepal"},
    "NR": {"lat": -0.522778, "lon": 166.931503, "name": "Nauru"},
    "NU": {"lat": -19.054445, "lon": -169.867233, "name": "Niue"},
    "NZ": {"lat": -40.900557, "lon": 174.885971, "name": "New Zealand"},
    "OM": {"lat": 21.512583, "lon": 55.923255, "name": "Oman"},
    "PA": {"lat": 8.537981, "lon": -80.782127, "name": "Panama"},
    "PE": {"lat": -9.189967, "lon": -75.015152, "name": "Peru"},
    "PF": {"lat": -17.679742, "lon": -149.406843, "name": "French Polynesia"},
    "PG": {"lat": -6.314993, "lon": 143.95555, "name": "Papua New Guinea"},
    "PH": {"lat": 12.879721, "lon": 121.774017, "name": "Philippines"},
    "PK": {"lat": 30.375321, "lon": 69.345116, "name": "Pakistan"},
    "PL": {"lat": 51.919438, "lon": 19.145136, "name": "Poland"},
    "PM": {"lat": 46.941936, "lon": -56.27111, "name": "Saint Pierre and Miquelon"},
    "PN": {"lat": -24.703615, "lon": -127.439308, "name": "Pitcairn Islands"},
    "PR": {"lat": 18.220833, "lon": -66.590149, "name": "Puerto Rico"},
    "PS": {"lat": 31.952162, "lon": 35.233154, "name": "Palestinian Territories"},
    "PT": {"lat": 39.399872, "lon": -8.224454, "name": "Portugal"},
    "PW": {"lat": 7.51498, "lon": 134.58252, "name": "Palau"},
    "PY": {"lat": -23.442503, "lon": -58.443832, "name": "Paraguay"},
    "QA": {"lat": 25.354826, "lon": 51.183884, "name": "Qatar"},
    "RE": {"lat": -21.115141, "lon": 55.536384, "name": "Réunion"},
    "RO": {"lat": 45.943161, "lon": 24.96676, "name": "Romania"},
    "RS": {"lat": 44.016521, "lon": 21.005859, "name": "Serbia"},
    "RU": {"lat": 61.52401, "lon": 105.318756, "name": "Russia"},
    "RW": {"lat": -1.940278, "lon": 29.873888, "name": "Rwanda"},
    "SA": {"lat": 23.885942, "lon": 45.079162, "name": "Saudi Arabia"},
    "SB": {"lat": -9.64571, "lon": 160.156194, "name": "Solomon Islands"},
    "SC": {"lat": -4.679574, "lon": 55.491977, "name": "Seychelles"},
    "SD": {"lat": 12.862807, "lon": 30.217636, "name": "Sudan"},
    "SE": {"lat": 60.128161, "lon": 18.643501, "name": "Sweden"},
    "SG": {"lat": 1.352083, "lon": 103.819836, "name": "Singapore"},
    "SH": {"lat": -24.143474, "lon": -10.030696, "name": "Saint Helena"},
    "SI": {"lat": 46.151241, "lon": 14.995463, "name": "Slovenia"},
    "SJ": {"lat": 77.553604, "lon": 23.670272, "name": "Svalbard and Jan Mayen"},
    "SK": {"lat": 48.669026, "lon": 19.699024, "name": "Slovakia"},
    "SL": {"lat": 8.460555, "lon": -11.779889, "name": "Sierra Leone"},
    "SM": {"lat": 43.94236, "lon": 12.457777, "name": "San Marino"},
    "SN": {"lat": 14.497401, "lon": -14.452362, "name": "Senegal"},
    "SO": {"lat": 5.152149, "lon": 46.199616, "name": "Somalia"},
    "SR": {"lat": 3.919305, "lon": -56.027783, "name": "Suriname"},
    "ST": {"lat": 0.18636, "lon": 6.613081, "name": "São Tomé and Príncipe"},
    "SV": {"lat": 13.794185, "lon": -88.89653, "name": "El Salvador"},
    "SY": {"lat": 34.802075, "lon": 38.996815, "name": "Syria"},
    "SZ": {"lat": -26.522503, "lon": 31.465866, "name": "Swaziland"},
    "TC": {"lat": 21.694025, "lon": -71.797928, "name": "Turks and Caicos Islands"},
    "TD": {"lat": 15.454166, "lon": 18.732207, "name": "Chad"},
    "TF": {"lat": -49.280366, "lon": 69.348557, "name": "French Southern Territories"},
    "TG": {"lat": 8.619543, "lon": 0.824782, "name": "Togo"},
    "TH": {"lat": 15.870032, "lon": 100.992541, "name": "Thailand"},
    "TJ": {"lat": 38.861034, "lon": 71.276093, "name": "Tajikistan"},
    "TK": {"lat": -8.967363, "lon": -171.855881, "name": "Tokelau"},
    "TL": {"lat": -8.874217, "lon": 125.727539, "name": "Timor-Leste"},
    "TM": {"lat": 38.969719, "lon": 59.556278, "name": "Turkmenistan"},
    "TN": {"lat": 33.886917, "lon": 9.537499, "name": "Tunisia"},
    "TO": {"lat": -21.178986, "lon": -175.198242, "name": "Tonga"},
    "TR": {"lat": 38.963745, "lon": 35.243322, "name": "Turkey"},
    "TT": {"lat": 10.691803, "lon": -61.222503, "name": "Trinidad and Tobago"},
    "TV": {"lat": -7.109535, "lon": 177.64933, "name": "Tuvalu"},
    "TW": {"lat": 23.69781, "lon": 120.960515, "name": "Taiwan"},
    "TZ": {"lat": -6.369028, "lon": 34.888822, "name": "Tanzania"},
    "UA": {"lat": 48.379433, "lon": 31.16558, "name": "Ukraine"},
    "UG": {"lat": 1.373333, "lon": 32.290275, "name": "Uganda"},
    "US": {"lat": 37.09024, "lon": -95.712891, "name": "United States"},
    "UY": {"lat": -32.522779, "lon": -55.765835, "name": "Uruguay"},
    "UZ": {"lat": 41.377491, "lon": 64.585262, "name": "Uzbekistan"},
    "VA": {"lat": 41.902916, "lon": 12.453389, "name": "Vatican City"},
    "VC": {"lat": 12.984305, "lon": -61.287228, "name": "Saint Vincent and the Grenadines"},
    "VE": {"lat": 6.42375, "lon": -66.58973, "name": "Venezuela"},
    "VG": {"lat": 18.420695, "lon": -64.639968, "name": "British Virgin Islands"},
    "VI": {"lat": 18.335765, "lon": -64.896335, "name": "U.S. Virgin Islands"},
    "VN": {"lat": 14.058324, "lon": 108.277199, "name": "Vietnam"},
    "VU": {"lat": -15.376706, "lon": 166.959158, "name": "Vanuatu"},
    "WF": {"lat": -13.768752, "lon": -177.156097, "name": "Wallis and Futuna"},
    "WS": {"lat": -13.759029, "lon": -172.104629, "name": "Samoa"},
    "XK": {"lat": 42.602636, "lon": 20.902977, "name": "Kosovo"},
    "YE": {"lat": 15.552727, "lon": 48.516388, "name": "Yemen"},
    "YT": {"lat": -12.8275, "lon": 45.166244, "name": "Mayotte"},
    "ZA": {"lat": -30.559482, "lon": 22.937506, "name": "South Africa"},
    "ZM": {"lat": -13.133897, "lon": 27.849332, "name": "Zambia"},
    "ZW": {"lat": -19.015438, "lon": 29.154857, "name": "Zimbabwe"}
}

class GeoParser:
    def __init__(self, log=print):
        from mordecai import Geoparser
        self.geo = Geoparser()
        self.log = log

    @staticmethod
    def _search_country(location):
        try:
            word = _COUNTRY_ALIASES[location["word"]]
        except KeyError:
            word = location["word"]

        try:
            return _COUNTRY_LIST[word.lower()].alpha_2
        except KeyError:
            if "geo" in location and location["geo"]["feature_code"] == "PCLI":
                # Feature code for "independent political entity"
                return location["geo"]["country_code2"]
            return None

    @staticmethod
    def get_country_data(alpha_2):
        return _COUNTRY_COORDS[alpha_2]

    def parse(self, query):
        geo_matches = self.geo.geoparse(query)

        for location in geo_matches:
            location["certain"] = False

        certain_geo_matches = [x for x in geo_matches if "geo" in x and x["country_predicted"] != "NA"]

        for x in [x for x in geo_matches if x not in certain_geo_matches]:
            self.log(f"Ignore [{x['word']}], {query}")

        for location in certain_geo_matches:
            location["geo"]["country_code2"] = pycountry.countries.get(alpha_3=location["geo"]["country_code3"]).alpha_2
            location["is_country"] = self._search_country(location)
            location["certain"] = True

        ignore_locations = []
        location_suffix_pattern = r"(( Province| City)?, ?)(.*)$"
        for location in certain_geo_matches:
            span = location["spans"][0]

            match = re.match(location_suffix_pattern, query[span["end"]:])
            if match:
                idx = span["end"] + len(match.group(1))
                # Group 1 is character before the beginning of the actually wanted group 2

                try:
                    succeeding_location = [
                        x for x in certain_geo_matches if any([span["start"] == idx for span in x["spans"]])
                    ][0]
                except IndexError:
                    continue

                if (
                        succeeding_location["is_country"] and
                        succeeding_location["is_country"] == location["geo"]["country_code2"] and
                        len(succeeding_location["spans"]) == 1
                ):
                    span_end = succeeding_location["spans"][0]["end"]
                    location["word"] = query[span["start"]:succeeding_location["spans"][0]["end"]]
                    location["spans"][0]["end"] = span_end

                    ignore_locations.append(succeeding_location)

        return [x for x in geo_matches if x not in ignore_locations]

