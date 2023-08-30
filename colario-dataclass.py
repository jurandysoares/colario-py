#!/usr/bin/env python3

from dataclasses import dataclass
from datetime import datetime
from glob import glob
import os
import pathlib
import shutil
import subprocess
import sys

from slugify import slugify
import yaml

programa = {
    'separar_pdf': 'pdfseparate',
    'transformar_pdf_em_txt': 'pdftotext',
    'transformar_pdf_em_svg': 'pdf2svg',
}

def atualizar_hoje():
    data_hoje = datetime.now().date()

    arq_conf = pathlib.Path('horario.yaml')
    if arq_conf.exists():
        with arq_conf.open(mode='r', encoding='utf-8') as man_arq_conf:
            confs_horario = yaml.safe_load(man_arq_conf)
            data_ini = confs_horario['validade']['ini']
            data_fim = confs_horario['validade']['fim']
            assert data_fim >= data_ini

            dif_datas = (data_hoje-data_ini).days
            
            return 0==dif_datas

    return False    

@dataclass
class MembroCategoria:
    slug: str
    nome: str
    txt_horario: str

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

![Horário de {titulo}](../imagens/{self.categoria}/{slug}.svg)

''')
        
def main():

    # if not atualizar_hoje():
    #     sys.exit(1)

    for formato in ['pdf', 'txt', 'svg', 'md']:
        if os.path.exists(formato): 
            shutil.rmtree(formato)

    categorias = ['professor', 'sala', 'turma']
    plural_categoria = {
        'professor': 'Professores',
        'sala': 'Salas e laboratórios',
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

    sys.exit(0)

if __name__ == '__main__':
    main()


# TESTE

desc_turma = {
    'INT_INFO_1M': 'Informática 1º ano matutino (Integrado)',
    'INT_INFO_1V': 'Informática 1º ano vespertino (Integrado)',
    'INT_INFO_2M': 'Informática 2º ano matutino (Integrado)',
    'INT_INFO_2V': 'Informática 2º ano vespertino (Integrado)',
    'INT_INFO_3M': 'Informática 3º ano matutino (Integrado)',
    'INT_INFO_3V': 'Informática 3º ano vespertino (Integrado)',
    'INT_INFO_4M': 'Informática 4º ano matutino (Integrado)',
    'INT_INFO_4V': 'Informática 4º ano vespertino (Integrado)',
    'INT_MECA_1M': 'Mecatrônica 1º ano matutino (Integrado)',
    'INT_MECA_1V': 'Mecatrônica 1º ano vespertino (Integrado)',
    'INT_MECA_2M': 'Mecatrônica 2º ano matutino (Integrado)',
    'INT_MECA_2V': 'Mecatrônica 2º ano vespertino (Integrado)',
    'INT_MECA_3M': 'Mecatrônica 3º ano matutino (Integrado)',
    'INT_MECA_3V': 'Mecatrônica 3º ano vespertino (Integrado)',
    'INT_MECA_4M': 'Mecatrônica 4º ano matutino (Integrado)',
    'INT_MECA_4V': 'Mecatrônica 4º ano vespertino (Integrado)',
    'SUB_REDES_1N': 'Redes de computadores 1º per. noturno (Subsequente)',
    'SUB_REDES_2N': 'Redes de computadores 2º per. noturno (Subsequente)',
    'SUB_REDES_3N': 'Redes de computadores 3º per. noturno (Subsequente)',
    'SUB_REDES_4N': 'Redes de computadores 4º per. noturno (Subsequente)',
    'SUB_MECA_1N': 'Mecatrônica 1º per. noturno (Subsequente)',
    'SUB_MECA_2N': 'Mecatrônica 2º per. noturno (Subsequente)',
    'SUB_MECA_3N': 'Mecatrônica 3º per. noturno (Subsequente)',
    'SUB_MECA_4N': 'Mecatrônica 4º per. noturno (Subsequente)',
    'TEC_SIST_1V': 'Sistemas para Internet 1º per. vespertino (Tecnólogo)',
    'TEC_SIST_2V': 'Sistemas para Internet 2º per. vespertino (Tecnólogo)',
    'TEC_SIST_3M': 'Sistemas para Internet 3º per. matutino (Tecnólogo)',
    'TEC_SIST_4M': 'Sistemas para Internet 4º per. matutino (Tecnólogo)',
    'TEC_SIST_5V': 'Sistemas para Internet 5º per. vespertino (Tecnólogo)',
    'TEC_SIST_6V': 'Sistemas para Internet 6º per. vespertino (Tecnólogo)',
    'LIC_FORM_PED': 'Formação Pedagógica vespertino (Licenciatura)',
}