#!/bin/bash

which zip

date_prfx=`date '+%Y%m%d%H%M%S'`

cd api
￼mkdir dst
mkdir dst/code
cd code
for dname in *; do
  if [ -d $dname ]; then
    cd $dname
    zip -r ../../dst/code/${date_prfx}_${dname}.zip .
    cd ..
  fi
done
cd ..
sed -e "s/Key: code\//Key: code\/${date_prfx}_/g" formation.yml >\
dst/formation.yml
