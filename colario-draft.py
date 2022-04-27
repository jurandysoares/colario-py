#!/usr/bin/env python3

from glob import glob
from logging import shutdown
import os
import pathlib
import shutil
import subprocess

from slugify import slugify

categorias = [
    'professor',
    'sala',
    'turma'
]

script_path = pathlib.Path(__file__)
dirname = script_path.parents[0]
horario_dir = dirname / 'horario'

# Separação dos PDFs
pdf_dir = horario_dir / 'pdf'

for cat in categorias:
    cat_dir = pdf_dir / cat
    cat_dir.mkdir(exist_ok=True)
    os.chdir(cat_dir)
    subprocess.run(['pdfseparate', f'../{cat}.pdf', f'{cat}-%d.pdf'])

# Geração de TXTs e SVGs a partir dos PDFs

txt_dir = horario_dir / 'txt'
svg_dir = horario_dir / 'svg'

for cat in categorias:
    cat_txt_dir = txt_dir / cat
    cat_svg_dir = svg_dir / cat
    cat_pdf_dir = pdf_dir / cat

    cat_txt_dir.mkdir(parents=True, exist_ok=True)
    cat_svg_dir.mkdir(parents=True, exist_ok=True)

    os.chdir(cat_pdf_dir)
    pdfs_cat = glob('*.pdf')

    for pdf in pdfs_cat:
        txt = cat_txt_dir / f'{pdf[:-4]}.txt'
        subprocess.run(['pdftotext', pdf, txt])

        svg = cat_svg_dir / f'{pdf[:-4]}.svg'
        subprocess.run(['pdf2svg', pdf, svg])


md_dir = horario_dir / 'md'
md_svg_dir = md_dir / 'imagens'
md_dir.mkdir(parents=True, exist_ok=True)
shutil.copytree(svg_dir, md_svg_dir)

mkdocs_dir = dirname / 'docs'

for cat in categorias:
    cat_md_dir = md_dir / cat
    cat_txt_dir = txt_dir / cat
    cat_md_dir.mkdir(parents=True, exist_ok=True)

    os.chdir(cat_txt_dir)
    txts_cat = glob('*.txt')

    for txt in txts_cat:

        with open(txt, mode='r', encoding='utf-8') as man_arq_txt:
            texto = man_arq_txt.read().splitlines()
            titulo = texto[0].replace('Professor ', '') if cat == 'professor' else texto[0]
            slug = slugify(titulo)

            svg_orig = md_svg_dir / cat / f'{txt[:-4]}.svg'
            svg_dest = md_svg_dir / cat / f'{slug}.svg'
            os.rename(svg_orig, svg_dest)

            md = cat_md_dir / f'{slug}.md'
        
            with open(md, mode='w', encoding='utf-8') as man_arq_md:
                man_arq_md.write(f'''\
# {titulo}

![Horário de {titulo}](../imagens/{cat}/{slug}.svg)

''')

#shutil.copytree(md_dir, mkdocs_dir)


