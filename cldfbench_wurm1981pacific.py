"""
fixes:


- L018:
  - add island name to label for SONSOROLESE
  - a couple atolls are missing in particular for MARSHALLESE.
- L019b:
  - add Tuamotuan dialects!

from ecai:

3076 -> vani1248, YANIMO -> VANIMO
"""
import pathlib
import itertools
import collections

from shapely.geometry import Point, shape
from clldutils.jsonlib import dump, load
from csvw.dsv import UnicodeWriter, reader
import pyglottography

OBSOLETE_FEATURES = {
    # L002_fix
    '1844': None,
    # L002, Yapen Island.
    '1850': None,
    '1852': None,
    '1078': [(-1.7, 135.9)],
    # L003:
    '3085': None,
    # L004: Kai Islands and Aru Islands (L004) all (wrongly) mapped to Bazaar Malay / BIAK?
    '1079': None,
    '1983': None,  # CENTRAL ASMAT, replaced by
    # L006:
    '3076': None, '3077': None, '3555': None, '2308': None, '2152': None,
    # L007:
    '2071': None, '2400': None, '2443': None, '2468': None, '3792': None, '3797': None, '3799': None,
    # L008:
    '2235': None, '2485': None, '2486': None, '2495': None, '2600': None, '2710': None, '2598': None,
    # L011:
    "2247": None, "2297": None, "3229": None, "3239": None, "3241": None,
    # L012: Miriam on Darnsley Island missing!
    # L013:
    '3655': None, '4391': None, '4396': None, '4398': None,
    # L014, Manus Island and Kaniet, Hermit, Seimat, Wuvulu-Aua
    # FIXME: remove completely. The remainder will be digitized as L010_new
    '2067': None,
    # L015: Santa Cruz:
    '4284': None, '4285': None, '2047': None, '4286': None, '4287': None,
    # L019b: Fijian dialects
    '2052': None,  # Eastern Fijian. There's a bit Vanua Levu stretching across the Antimeridian ...
    '4290': None,
    # L032: Batan Islands: Some polygons have not been digitized
    '233': None,
    # L037: Andaman Islands/Nicobar Islands: not digitized at all!
    # L038: Madagascar
    '2063': [
        (-19, 47),  # part of mainland Madagascar
        (-18.874, -159.777), (-19.214, -159.049), (-19.714, -158.426), (-20.025, -158.332),
        (-19.575, -157.656), (-20.14, -157.411), (-21.192, -159.753),  # Cook Islands,
    ],
    '893': None, '895': None, '897': None,
    # L040b: Roti dialects
    '1068': None,
    # L043: Talaud Islands, Sangihe Islands
    '1693': None,  # Includes some polygons in Northern Borneo, but these may be wrong as well.
    # L044: Flores Sea
    '1121': None, '1120': None, '1063': None,
    # L045a: Sula Islands and Buru
    '713': [(-1.8, 125), (-1.858, 125.88), (-2.07, 125.93), (-3.4, 126.6)],
    '1968': None, '3602': None, '1909': None,
    # L045b: Banda Island

    # L019
    '4465': None,  # Easter Island
    '4335': None,  # Mangareva
    '3753': [(-8.86, -140.206), (-9.72, -139.06)],  # PA'UMOTU
    '4332': None,  # Austral, replace by dialect-specific polys.
    # L038
    '891': None,  # That's uninhabited area.
    '803': [(4.702, 97.188), (4.381, 97.681), (4.063, 96.43), (3.933, 96.748)],
    # Uninhabited or "Java languages" on Sumatra.
}


class Dataset(pyglottography.Dataset):
    dir = pathlib.Path(__file__).parent
    id = "wurm1981pacific"

    def from_ecai_props(self, d):
        props = {k: v for k, v in d['properties'].items()}
        props['id'] = d['id']
        props['name'] = props.pop('LANGUAGE')
        props['glottocode'] = props.pop('cldf:languageReference', [])
        props['glottocode'] = None if not props['glottocode'] else props['glottocode'][0]
        return props['id'], props

    def cmd_download(self, args):
        """
        Create source data from legacy CLDF dataset:
        - raw/dataset.geojson from cldf/ecai.geojson
          -> removing/pruning according to OBSOLETE_FEATURES, rewriting props
        - etc/features.csv from cldf/contributions.csv
          -> removing rows according to OBSOLETE_FEATURES

        adding in:
        - etc/dataset_insets.geojson
        - etc/features_insets.csv
        """
        for p in self.raw_dir.glob('*_ecai.csv'):
            for row in reader(p, dicts=True):
                OBSOLETE_FEATURES[row['id']] = None
        features, fmd = [], []
        for f in load(self.raw_dir / 'cldf-datasets-languageatlasofthepacificarea-f85e505' / 'cldf' / 'ecai.geojson')['features']:
            fid, props = self.from_ecai_props(f)
            f['properties'] = props
            if fid in OBSOLETE_FEATURES:
                if OBSOLETE_FEATURES[fid] is None:
                    continue
                else:
                    assert f['geometry']['type'] == 'MultiPolygon'
                    points = [Point(y, x) for x, y in OBSOLETE_FEATURES[fid]]
                    oc = len(f['geometry']['coordinates'])
                    f['geometry']['coordinates'] = [
                        coords for coords in f['geometry']['coordinates']
                        if not any(
                            shape(dict(type='Polygon', coordinates=coords)).contains(p)
                            for p in points)]
                    features.append(f)
            else:
                features.append(f)
            fmd.append(dict(
                id=fid,
                name=props['name'],
                glottocode=props['glottocode'],
                year='traditional',
                map_name_full='ecai'))

        def get_name(f):
            return f['properties'].get('name', f['properties'].get('LANGUAGE'))

        l, i = set(), 0
        for p in sorted(self.raw_dir.glob('L0*'), key=lambda p_: p_.name):
            print(p)

            names = set()
            pp = p / '{}.geojson'.format(p.name)
            assert pp.exists(), str(pp)
            fs = load(pp)['features']
            #assert all(f['geometry']['type'] == 'Polygon' for f in fs), p
            lgs = p / 'languages.csv'
            known = {r[0]: r[1] for r in reader(lgs)} if lgs.exists() else {}

            assert all(get_name(f) for f in fs), p

            for name, shapes in itertools.groupby(sorted(fs, key=get_name), get_name):
                names.add(name)
                i += 1
                props = collections.OrderedDict([
                    ('id', '{}_{}'.format(p.name, i)),
                    ('name', name),
                    ('glottocode', known.get(name, '')),
                    ('year', 'traditional'),
                    ('map_name_full', p.name),
                ])
                fmd.append(props)
                coords = []
                for f in shapes:
                    if f['geometry']['type'] == 'Polygon':
                        coords.append(f['geometry']['coordinates'])
                    elif f['geometry']['type'] == 'MultiPolygon':
                        coords.extend(f['geometry']['coordinates'])
                    else:
                        raise ValueError(f['geometry']['type'])
                features.append(dict(
                    type='Feature',
                    properties=props,
                    geometry=dict(type='MultiPolygon', coordinates=coords)))
            with UnicodeWriter(lgs) as w:
                for name in sorted(names):
                    w.writerow([name, known.get(name, '')])

        dump(dict(type='FeatureCollection', features=features), self.raw_dir / 'dataset.geojson')
        with UnicodeWriter(self.etc_dir / 'features.csv') as w:
            cols = ['id', 'name', 'glottocode', 'year', 'map_name_full']
            w.writerow(cols)
            for md in fmd:
                w.writerow([md[col] for col in cols])
        return

    #
    # FIXME: handle geo-referenced scans!
    #
