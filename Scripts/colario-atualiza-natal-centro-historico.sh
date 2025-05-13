#!/bin/bash -xv

CAMPUS="natal-centro-historico"
TIME_STAMP="$(ls /var/www/html/sis/${CAMPUS}/envios/*.pdf | tail -3 | cut -d_ -f1 | sort -u)"
DEST_DIR="/var/lib/colario/${CAMPUS}/horario"
ANO_PERIODO="2025.1"
cd "${DEST_DIR}"

for categoria in professor sala turma; do
  cp -v ${TIME_STAMP}_${categoria}.pdf ${categoria}.pdf
done

#cat << EOF > /dev/null
source /home/jurandy/proj/colario-py/.venv/bin/activate
#rm -rf md
#mkdir md
/home/jurandy/proj/colario-py/colario.py natal-centro-historico . "/var/www/html/horario/${CAMPUS}/${ANO_PERIODO}"

# Atualiza a versão web (HTML)

cp -r modelo/* md && cd md && make html && \
	cd /var/www/html/horario/${CAMPUS} && \
	rm -rf "${ANO_PERIODO}" && mv ${OLDPWD}/_build/html "${ANO_PERIODO}" && \
    cd -

cd ../

# Atualiza os arquivos no formato PDF, SVG e TXT
pwd

for fmt in pdf svg txt; do
   FMT_DEST="/var/www/html/horario/${fmt}/${CAMPUS}"
   rm -rf "${FMT_DEST}"
   mkdir -pv "${FMT_DEST}"
   mv -v "${fmt}"/* "${FMT_DEST}"
done

# EOF

