#!/usr/bin/env python3

import argparse
import csv
from datetime import date, datetime
from dataclasses import dataclass
from glob import glob
import logging
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import venv


from slugify import slugify
import yaml

cmd_tmpl = {
    'pdf2pdfs': 'pdfseparate {arq_pdf} {pag_pdf_padrao}',
    'pdf2txt': 'pdftotext -layout {arq_pdf} {arq_alvo}.txt',
    'pdf2svg': 'pdf2svg {arq_pdf} {arq_alvo}.svg',
    'pdf2png': 'pdftoppm -png -singlefile {arq_pdf} {arq_alvo}',
}

plural_categoria = {
    'professor': 'professores',
    'sala': 'salas e laboratórios',  
    'turma': 'turmas'
}

@dataclass
class MembroCategoria:
    slug: str
    nome: str
    texto_horario: str
    termos_horario: str
    categoria: str


def atualizar_site(pdf_dir, www_dir):
    data_hoje = datetime.now().date()

    arq_conf = pathlib.Path(pdf_dir/'horario.yaml')
    arq_turma = pathlib.Path(pdf_dir/'turma.pdf')
    arq_index = pathlib.Path(www_dir/'index.html')

    if arq_conf.exists():
        with arq_conf.open(mode='r', encoding='utf-8') as man_arq_conf:
            confs_horario = yaml.safe_load(man_arq_conf)
            data_ini = confs_horario['validade']['ini']
            data_fim = confs_horario['validade']['fim']
            assert data_fim >= data_ini

            dif_datas = (data_hoje-data_ini).days
            
            return 0==dif_datas # TODO: Qual é a data do arquivo "index.html"?
    else:
        datahora_index = datetime.fromtimestamp(arq_index.stat().st_mtime)
        datahora_turma = datetime.fromtimestamp(arq_turma.stat().st_mtime)
        return datahora_index < datahora_turma

    # return False
    return True # Só para passar pelo teste

def carrega_abreviacoes(categoria: str) -> dict:
    cam_arq = pathlib.Path(os.getcwd()) / 'abrev' / f'{categoria}.csv'
    with cam_arq.open(mode='r', encoding='utf-8') as arq_abrev:
        leitor = csv.DictReader(arq_abrev)
        nome_abrev = {linha['Abreviacao']:linha['Nome'] for linha in leitor}
        return nome_abrev


def carrega_turmas_professores() -> dict:
    cam_arq = pathlib.Path(os.getcwd()) / 'abrev' / 'professor.csv'
    with cam_arq.open(mode='r', encoding='utf-8') as arq_prof:
        leitor = csv.DictReader(arq_prof)
        turmas_prof = {slugify(linha['Nome']):linha['Turmas'].split(', ') for linha in leitor}
        return turmas_prof


class FatiadorPDF:
    '''
    Fatiador de arquivo PDF
    '''
    
    def __init__(self, categoria: str):

        self._dir_raiz = pathlib.Path(os.getcwd())
        self.categoria = categoria
        self.membros = {}        
        self.caminho_arquivo = self._dir_raiz/f'{categoria}.pdf'

        self._dir_ext = {
            'md': self._dir_raiz / 'md' / categoria,
            'pdf': self._dir_raiz / 'pdf' / categoria,
            'png': self._dir_raiz / 'png' / categoria,
            'svg': self._dir_raiz / 'svg' / categoria,
            'txt': self._dir_raiz / 'txt' / categoria
        }

        self._separar_paginas()
        self._gerar_md(ext_img='png')
                
    def _separar_paginas(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            logging.info(f'Diretório temporário {temp_dir} criado para horários de {plural_categoria[self.categoria]}.')
            cwd = os.getcwd()
            os.chdir(temp_dir)
            cmd = cmd_tmpl["pdf2pdfs"].format(arq_pdf=self.caminho_arquivo, pag_pdf_padrao=f'{self.categoria}-%02d.pdf')
            subprocess.run(cmd.split())

            logging.debug(f'Arquivos PDF de {plural_categoria[self.categoria]} separados.')

            arqs_pdf = glob('*.pdf')
            for ext in ('pdf', 'png', 'md', 'svg', 'txt'):
                self._dir_ext[ext].mkdir(parents=True, exist_ok=True)

            for nome_arq_pdf in arqs_pdf:
                nome_arq = nome_arq_pdf[:-4]
                nome_arq_txt = f'{nome_arq_pdf[:-4]}.txt'

                for ext in ('txt', 'png', 'svg'):
                    cmd = cmd_tmpl[f'pdf2{ext}'].format(arq_pdf=nome_arq_pdf, arq_alvo=nome_arq)
                    subprocess.run(cmd.split())
        
                with open(file=nome_arq_txt, mode='r', encoding='utf-8') as arq_txt:
                    texto = arq_txt.read()
                    linhas = texto.splitlines()
                    if self.categoria == 'professor':
                        nome = linhas[0].strip()[10:]
                    else:
                        nome = linhas[0].strip()

                        # Thanks professor Henrique Coelho for reporting this bug
                        if nome.startswith('Centro Federal'):
                            nome = linhas[1].strip()

                    slug = slugify(nome)
                    logging.debug(f'Arquivo: {nome_arq_txt}, Nome: {nome}, Slug: {slug}')

                    novo_membro = MembroCategoria(
                        slug=slug,
                        nome=nome,
                        texto_horario=texto,
                        termos_horario=texto.split(),
                        categoria=self.categoria
                    )
                    self.membros[slug] = novo_membro

                    for ext in ('txt', 'pdf', 'png', 'svg'):
                        shutil.copy(f'{nome_arq}.{ext}', self._dir_ext[ext]/f'{slug}.{ext}')

            os.chdir(cwd)

    def _gerar_md(self, ext_img='svg'):

        # Gera a página Markdown índice
        cam_arq_indice = self._dir_ext['md'] / 'index.md'
        plural = plural_categoria[self.categoria]

        # Cria diretório para salvar imagens
        cam_orig_imgs = self._dir_ext[ext_img]
        cam_dest_imgs = self._dir_ext['md'].parent / '_static' / 'img' / f'{self.categoria}'
        cam_dest_imgs.mkdir(parents=True, exist_ok=True)
        with cam_arq_indice.open(mode='w', encoding='utf-8') as arq_indice:
            arq_indice.write(f'''\
({self.categoria})=                             

# {plural.capitalize()}

```{{toctree}}
:maxdepth: 1

''')
            
            for slug in sorted(self.membros.keys()):
                arq_indice.write(f'{slug}\n')
                shutil.copy(cam_orig_imgs/f'{slug}.{ext_img}', cam_dest_imgs)

            arq_indice.write("```\n")


        # Gera uma página Markdown por membro da categoria

        for slug,membro in self.membros.items():
            md = self._dir_ext['md'] / f'{slug}.md'

            with open(md, mode='w', encoding='utf-8') as man_arq_md:
                conteudo_md = f'''\
({self.categoria}:{slug})=

# {membro.nome}

```{{figure}} ../_static/img/{self.categoria}/{slug}.{ext_img}
---
width: 100%
align: center
alt: Horário de {self.categoria.capitalize()} {membro.nome}
name: fig:{self.categoria}:{slug}
---
```

'''

                man_arq_md.write(conteudo_md)


def main():
    ana_args = argparse.ArgumentParser()
    ana_args.add_argument('dir_pdf', help='Diretório onde se encontram os arquivos PDF com horários')
    ana_args.add_argument('dir_www', help='Diretório para publicação dos horários na Web')
    args = ana_args.parse_args()

    dir_horarios = pathlib.Path(args.dir_pdf)
    ls_pdf = dir_horarios.glob('*.pdf')

    dir_www = pathlib.Path(args.dir_www)

    # assert dir_horarios.is_dir() and dir_www.is_dir()
    # assert all([arq_pdf in ls_pdf for arq_pdf in ('professor.pdf', 'sala.pdf', 'turma.pdf')])
    # assert 'index.html' in dir_www.glob('index.html')
  
    os.chdir(dir_horarios)
    # if not atualizar_site(dir_horarios, dir_www):
    #     sys.exit(1)

    now = datetime.now()   
    pid = os.getpid()

    fname = f"/tmp/colario_{now.strftime('%F_%T')}_{pid}.log"
    print(f'Arquivo de log: {fname}')

    logging.basicConfig(
        filename=fname,
        filemode='w',
        format='%(asctime)s - %(levelname)s - %(message)s',
        level=logging.DEBUG
    )
    categorias = ('professor',  'sala',  'turma')

    formatos_suportados = ('md', 'pdf', 'png', 'svg', 'txt')
    for formato in formatos_suportados:
        if os.path.exists(formato): 
            shutil.rmtree(formato)

    global membros_categoria

    membros_categoria = {categoria:FatiadorPDF(categoria).membros for categoria in categorias}

    sys.exit(0)

if __name__ == '__main__':
    main()
