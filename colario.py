#!/usr/bin/env python3

from glob import glob
import os
import pathlib
import shutil
import subprocess
import sys

from slugify import slugify

programa = {
    'separar_pdf': 'pdfseparate',
    'transformar_pdf_em_txt': 'pdftotext',
    'transformar_pdf_em_svg': 'pdf2svg',
}

class FatiadorPDF:
    '''
    Fatiador de arquivo PDF
    '''
    
    def __init__(self, categoria: str):
        
        self.caminho_arquivo = pathlib.Path(f'{categoria}.pdf')
        self.categoria = categoria
        self.membros = {}
        
        self._dir_raiz = pathlib.Path(os.getcwd())
        self._dir_pdf = self._dir_raiz / 'pdf' / categoria
        self._dir_txt = self._dir_raiz / 'txt' / categoria
        self._dir_svg = self._dir_raiz / 'svg' / categoria
        self._dir_md = self._dir_raiz / 'md' / categoria
        self._dir_md_img = self._dir_raiz / 'md' / 'imagens' / categoria
        
        self._separar_paginas()
        self._gerar_txt()
        self._gerar_svg()
        self._gerar_md()
        
        os.chdir(self._dir_raiz)
        
    def _separar_paginas(self):
        self._dir_pdf.mkdir(parents=True, exist_ok=True)
        os.chdir(self._dir_pdf)
        cmd = f'{programa["separar_pdf"]} ../../{self.caminho_arquivo.name} {self.categoria}-%d.pdf'
        subprocess.run(cmd.split())

    def _gerar_txt(self):
        self._dir_txt.mkdir(parents=True, exist_ok=True)
        os.chdir(self._dir_pdf)
        pdfs = glob('*.pdf')
        os.chdir(self._dir_raiz)
        for f in pdfs:
            cmd = f'{programa["transformar_pdf_em_txt"]} pdf/{self.categoria}/{f} txt/{self.categoria}/{f[:-4]}.txt'
            subprocess.run(cmd.split())

    def _gerar_svg(self):
        self._dir_svg.mkdir(parents=True, exist_ok=True)
        os.chdir(self._dir_pdf)
        pdfs = glob('*.pdf')
        os.chdir(self._dir_raiz)
        for f in pdfs:
            cmd = f'{programa["transformar_pdf_em_svg"]} pdf/{self.categoria}/{f} svg/{self.categoria}/{f[:-4]}.svg'
            subprocess.run(cmd.split())

    def _gerar_md(self):
        self._dir_md.mkdir(parents=True, exist_ok=True)
        shutil.copytree(self._dir_svg, self._dir_md_img)

        os.chdir(self._dir_txt)
        txts = glob('*.txt')

        for txt in txts:
            with open(txt, mode='r', encoding='utf-8') as man_arq_txt:
                texto = man_arq_txt.read().splitlines()
                titulo = texto[0].replace('Professor ', '') if self.categoria == 'professor' else texto[0]
                slug = slugify(titulo)
                self.membros[slug] = titulo
                nome_arq = txt[:-4]
                svg_orig = self._dir_md_img / f'{nome_arq}.svg'
                svg_dest = self._dir_md_img / f'{slug}.svg'
                os.rename(svg_orig, svg_dest)

                md = self._dir_md / f'{slug}.md'

                with open(md, mode='w', encoding='utf-8') as man_arq_md:
                    man_arq_md.write(f'''\

({slug})=

# {titulo}

![Hor??rio de {titulo}](../imagens/{self.categoria}/{slug}.svg)

''')
        
def main():

    for formato in ['pdf', 'txt', 'svg', 'md']:
        if os.path.exists(formato): 
            shutil.rmtree(formato)

    categorias = ['professor', 'sala', 'turma']
    plural_categoria = {
        'professor': 'Professores',
        'sala': 'Salas',
        'turma': 'Turmas',
    }

    global catalogo
    catalogo = {}
               
    if len(sys.argv) == 2:
        caminho = pathlib.Path(sys.argv[1])
        
    for cat in categorias:
        catalogo[cat] = FatiadorPDF(cat)
        arq_indice = catalogo[cat]._dir_md / 'index.md'

        with arq_indice.open(mode='w', encoding='utf-8') as indice:
            plural = plural_categoria[cat]
            indice.write(f'''\
({cat})=

# {plural}

```{{toctree}}
:maxdepth: 1

''')
            for elemento in sorted(catalogo[cat].membros):
                indice.write(f'{elemento}\n')

            indice.write('\n```')

if __name__ == '__main__':
    main()
