#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

import argparse
import asyncio
import glob
import logging
import os
import pathlib
import tempfile

# Singular da categoria
sing_categ = {
    'professores': 'professor',
    'salas': 'sala',
    'turmas': 'turma'
}

cmd_pdf2 = {
    'txt': 'pdftotext {cam_pdf} {cam_ext}',
    'svg': 'pdf2svg {cam_pdf} {cam_ext}',
    'png': 'pdftoppm -png -singlefile {cam_pdf} {cam_ext}'
}

async def disparar(comando: str):
    processo = await asyncio.subprocess.create_subprocess_shell(comando)
    stdout,stdin = await processo.communicate()
    await processo.wait()


async def separar_pdf(nome_categoria: str, dir_dest_pdf: pathlib.Path):
    dir_pdf_categoria = dir_dest_pdf/f'{nome_categoria}'
    dir_pdf_categoria.mkdir(parents=True, exist_ok=True)
    padrao_caminho = dir_pdf_categoria/f'{nome_categoria}-%02d.pdf'

    comando = f'/usr/bin/pdfseparate {nome_categoria}.pdf {padrao_caminho}'
    await disparar(comando)

async def converter_pdf(ext: str, dir_dest_pdf: pathlib.Path):
    dir_ext = dir_dest_pdf.parent/ext
    dir_ext.mkdir(exist_ok=True, parents=True)
    for categoria in 'professor sala turma'.split():
        dir_ext_categ = dir_ext/categoria
        dir_ext_categ.mkdir(parents=True, exist_ok=True)

    pdfs = dir_dest_pdf.glob('**/*.pdf')
    caminhos = [str(r) for r in pdfs]
    comandos = []
    mod_comando = cmd_pdf2[ext]
    for cam in caminhos:
         comandos.append(mod_comando.format(cam_pdf=cam, cam_ext=cam.replace("pdf", ext)))
    
    if ext=='png':
        tarefas = [disparar(cmd[:-4]) for cmd in comandos]
    else:
        tarefas = [disparar(cmd) for cmd in comandos]

    await asyncio.gather(*tarefas)

async def main():
    ana_args = argparse.ArgumentParser()
    ana_args.add_argument('diretorio_pdf', 
                          help='Diretório com arquivos PDF')
    args = ana_args.parse_args()

    pdf_dir = pathlib.Path(args.diretorio_pdf)

    if pdf_dir.exists and pdf_dir.is_dir():
        os.chdir(pdf_dir)
        categorias = 'professor sala turma'.split()
        with tempfile.TemporaryDirectory(prefix='concolario-') as dir_temp:
            print(f'Diretório temporário: {dir_temp}')
            dir_pdf = pathlib.Path(dir_temp)/'pdf'
            dir_pdf.mkdir(parents=True, exist_ok=True)

            tarefas = sepadores_pdf = [
                asyncio.create_task(separar_pdf(categoria, dir_pdf))
                for categoria in categorias
            ]
            await asyncio.gather(*tarefas)
            await converter_pdf(ext='txt', dir_dest_pdf=dir_pdf)
            await converter_pdf(ext='svg', dir_dest_pdf=dir_pdf)
            await converter_pdf(ext='png', dir_dest_pdf=dir_pdf)
            
            print('Separação terminada.')
            input('Pressione ENTER')

if __name__ == '__main__':
    asyncio.run(main())