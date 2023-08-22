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

    return False    


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
            'csv': self._dir_raiz / 'csv' / categoria,
            'md': self._dir_raiz / 'md' / categoria,
            'pdf': self._dir_raiz / 'pdf' / categoria,
            'png': self._dir_raiz / 'png' / categoria,
            'svg': self._dir_raiz / 'svg' / categoria,
            'txt': self._dir_raiz / 'txt' / categoria,
        }

        self._separar_paginas()
                
    def _separar_paginas(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            logging.info(f'Diretório temporário: {temp_dir}')
            cwd = os.getcwd()
            os.chdir(temp_dir)
            cmd = cmd_tmpl["pdf2pdfs"].format(arq_pdf=self.caminho_arquivo, pag_pdf_padrao=f'{self.categoria}-%02d.pdf')
            subprocess.run(cmd.split())

            arqs_pdf = glob('*.pdf')
            for ext in ('pdf', 'txt', 'png', 'svg'):
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

                
#                 md = self._dir_md / f'{slug}.md'

#                 with open(md, mode='w', encoding='utf-8') as man_arq_md:
#                     conteudo_md = f'''\
# ({self.categoria}:{slug})=

# # {titulo}

# ```{{figure}} ../_static/img/{self.categoria}/{slug}.svg
# ---
# width: 100%
# align: center
# alt: Horário de {self.categoria.capitalize()} {titulo}
# name: fig:{self.categoria}:{slug}
# ---
# ```

# '''
#                     print(conteudo_md)
#                     man_arq_md.write(conteudo_md)
#         shutil.rmtree(path=tmp_dir)

# def main():

#     # if not atualizar_hoje():
#     #     sys.exit(1)

#     logging.basicConfig(level=logging.INFO)

#     for formato in ['pdf', 'txt', 'svg', 'md', 'png', 'csv']:
#         if os.path.exists(formato): 
#             shutil.rmtree(formato)

#     categorias = ['professor', 'sala', 'turma']
#     plural_categoria = {
#         'professor': 'Professores',
#         'sala': 'Salas e laboratórios',
#         'turma': 'Turmas',
#     }

#     global catalogo
#     catalogo = {}
               
#     if len(sys.argv) == 2:
#         caminho = pathlib.Path(sys.argv[1])
        
#     for cat in categorias:
#         catalogo[cat] = FatiadorPDF(cat)
#         arq_indice = catalogo[cat]._dir_md / 'index.md'

#         with arq_indice.open(mode='w', encoding='utf-8') as indice:
#             plural = plural_categoria[cat]
#             indice.write(f'''\
# ({cat})=

# # {plural}

# ```{{toctree}}
# :maxdepth: 1

# ''')
#             for elemento in sorted(catalogo[cat].membros):
#                 indice.write(f'{elemento}\n')

#             indice.write('\n```')

#     sys.exit(0)

# if __name__ == '__main__':
#     main()

logging.basicConfig(level=logging.INFO)

for formato in ['pdf', 'txt', 'svg', 'md', 'png', 'csv']:
    if os.path.exists(formato): 
        shutil.rmtree(formato)

membros_categoria = {categoria:FatiadorPDF(categoria).membros for categoria in ('professor', 'sala', 'turma')}
