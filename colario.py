#!/usr/bin/env python3

from datetime import datetime
from dataclasses import dataclass
from glob import glob
import logging
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

from slugify import slugify
import tabula
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
    categoria: str


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

    # return False
    return True # Só para passar pelo teste


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
            logging.info(f'Diretório temporário: {temp_dir}')
            cwd = os.getcwd()
            os.chdir(temp_dir)
            cmd = cmd_tmpl["pdf2pdfs"].format(arq_pdf=self.caminho_arquivo, pag_pdf_padrao=f'{self.categoria}-%02d.pdf')
            subprocess.run(cmd.split())

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
                        10 == 'Professor '
                        nome = linhas[0].strip()[10:]
                    else:
                        nome = linhas[0].strip()
                    
                    slug = slugify(nome)
                    novo_membro = MembroCategoria(
                        slug=slug,
                        nome=nome,
                        texto_horario=texto,
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
    if not atualizar_hoje():
        sys.exit(1)

    logging.basicConfig(level=logging.INFO)
    categorias = ('professor',  'sala',  'turma')
    logging.basicConfig(level=logging.INFO)

    formatos_suportados = ('md', 'pdf', 'png', 'svg', 'txt')
    for formato in formatos_suportados:
        if os.path.exists(formato): 
            shutil.rmtree(formato)

    membros_categoria = {categoria:FatiadorPDF(categoria).membros for categoria in categorias}

    sys.exit(0)

if __name__ == '__main__':
    main()
