#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

import argparse
import asyncio
import glob
import os
import pathlib
import subprocess
import tempfile

# Singular da categoria
sing_categ = {
    'professores': 'professor',
    'salas': 'sala',
    'turmas': 'turma'
}

cmd_pdf2 = {
    'txt': 'pdftotext -layout {nome_arq_pdf} ../{ext}/{nome_arq_pdf[:-4]}.txt',
    'svg': 'pdf2svg {nome_arq_pdf} ../{ext}/{nome_arq_pdf[:-4]}.svg',
    'png': 'pdftoppm -png -singlefile {nome_arq_pdf} ../{ext}/{nome_arq_pdf[:-4]}'
}


async def converter_pdf(arquivo_pdf, ext: str):
    comando = cmd_pdf2[ext].format(arquivo_pdf, ext)
    print(comando)
    subprocess.run(comando.split())

async def separar_pdf(nome_categoria: str, dir_dest_pdf: pathlib.Path):
    dir_pdf_categoria = dir_dest_pdf/f'{nome_categoria}'
    dir_pdf_categoria.mkdir(parents=True, exist_ok=True)
    padrao_caminho = dir_pdf_categoria/f'{nome_categoria}-%02d.pdf'

    comando = f'pdfseparate {nome_categoria}.pdf {padrao_caminho}'
    print(comando)
    subprocess.run(comando.split())
    print(f'Separação de "{nome_categoria}.pdf" concluída.')

    arqs_pdf = glob.glob('*.pdf')
    arqs = [arq_pdf[:-4] for arq_pdf in arqs_pdf]
    for ext in 'txt svg png'.split():
        dir_dest_ext = dir_dest_pdf.parent/f'ext'
        dir_dest_ext.mkdir(parents=True, exist_ok=True)
        async with asyncio.TaskGroup() as tg:
            conversores_ext = [
                asyncio.create_task(converter_pdf(arq_pdf, ext))
                for arq_pdf in arqs_pdf
            ]


async def main():
    ana_args = argparse.ArgumentParser()
    ana_args.add_argument('diretorio_pdf', 
                          help='Diretório com arquivos PDF')
    args = ana_args.parse_args()

    global pdf_dir
    pdf_dir = pathlib.Path(args.diretorio_pdf)
    if pdf_dir.exists and pdf_dir.is_dir():
        os.chdir(pdf_dir)
        print(os.getcwd())
        categorias = 'professor sala turma'.split()
        dir_pdf = pathlib.Path(tempfile.mkdtemp('-concolario'))/'pdf'
        dir_pdf.mkdir(parents=True, exist_ok=True)
        async with asyncio.TaskGroup() as tg:
            sepadores_pdf = [
                asyncio.create_task(separar_pdf(categoria, dir_pdf))
                for categoria in categorias
            ]

asyncio.run(main())