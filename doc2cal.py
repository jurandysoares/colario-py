#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from slugify import slugify

meses = 'Janeiro Fevereiro Março Abril Maio Junho Julho Agosto Setembro Outubro Novembro Dezembro'.split()

for i,m in enumerate(meses, start=1):
    slug_m = slugify(m)
    
    with open(f'{slug_m}.md', encoding='utf-8', mode='w') as arq_mes:
        arq_mes.write(f'''\
({slug_m})=

# {m}

![Mês de {m}](../imagens/calendario/2022/calendario-2022-{i:02}.svg)
''')
