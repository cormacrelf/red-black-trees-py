#!/bin/sh
python3 "$1" | csplit -s -f tmpforestfile - /digraph/ "{*}" \
  && fd tmpforestfile . \
  | xargs -I{} sh -c 'dot -Tpdf {} > {}.pdf' -- {} \
  && gs -dNOPAUSE -sDEVICE=pdfwrite -sOUTPUTFILE=combine.pdf -dBATCH tmpforestfile*.pdf

rm tmpforestfile*
