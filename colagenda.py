import pathlib

import yaml

class Estrutura:
    def __init__(self, **entradas) -> None:
        self.__dict__.update(entradas)

arq_conf = pathlib.Path('horario.yaml')
if arq_conf.exists():
    with arq_conf.open(mode='r', encoding='utf-8') as man_arq_conf:
        confs_horario = yaml.safe_load(man_arq_conf)

        estruturas = Estrutura(**confs_horario)
