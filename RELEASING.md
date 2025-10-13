# Releasing the dataset

## Recreate the data extracted from the source

```shell
cldfbench download cldfbench_wurm1981pacific.py
```

## Recreate the CLDF dataset

```shell
cldfbench makecldf cldfbench_wurm1981pacific.py --glottolog-version v5.2
cldfbench cldfreadme cldfbench_wurm1981pacific.py
cldfbench zenodo --communities glottography cldfbench_wurm1981pacific.py
cldfbench readme cldfbench_wurm1981pacific.py
```


## Validation

```shell
cldf validate cldf
```

```shell
cldfbench geojson.validate cldf
```

```shell
cldfbench geojson.glottolog_distance cldf --glottolog-version v5.2 --format tsv | csvformat -t | csvgrep -c Distance -r"^0\.?" -i | csvsort -c Distance | csvcut -c ID,Distance | csvformat -E | termgraph
```
