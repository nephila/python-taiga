#!/usr/bin/env bash
export LC_ALL="C"

pip install -e . --upgrade

cd docs ; make clean html

mv build/html/_static build/html/static
mv build/html/_sources build/html/sources

sed -i -e's/_static/static/g' build/html/index.html
sed -i -e's/_sources/sources/g' build/html/index.html
sed -i -e's/_static/static/g' build/html/genindex.html
sed -i -e's/_static/static/g' build/html/py-modindex.html
sed -i -e's/_static/static/g' build/html/search.html
