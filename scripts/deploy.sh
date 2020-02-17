#!/bin/bash

set -eu

date_prfx=`date '+%Y%m%d%H%M%S'`

mkdir api/dst
mkdir api/dst/code
cd api
cd code
for dname in *; do
  set +e
  if [ -d $dname ]; then
    set -e
    cd $dname
    zip -r ../../dst/code/${date_prfx}_${dname}.zip .
    cd ..
  fi
done
cd ..
sed -e "s/Key: code\//Key: code\/${date_prfx}_/g" formation.yml >\
dst/formation_${date_prfx}.yml
cd dst
aws s3 sync . s3://${SRC_BUCKET_NAME}
set +e
aws cloudformation wait stack-exists --stack-name $STACK_NAME
BUCKET_URL=https://$SRC_BUCKET_NAME.s3-$AWS_DEFAULT_REGION.amazonaws.com
if [ $? = 0 ]; then
  set -e
  aws cloudformation update-stack --stack-name $STACK_NAME \
  --template-url ${BUCKET_URL}/formation_${date_prfx}.yml \
  --capabilities CAPABILITY_IAM CAPABILITY_AUTO_EXPAND \
  --parameters ParameterKey=codeBucketName,ParameterValue=$SRC_BUCKET_NAME
  aws cloudformation wait stack-update-complete --stack-name \
  $STACK_NAME
else
  set -e
  aws cloudformation create-stack --stack-name $STACK_NAME \
  --template-url ${BUCKET_URL}/formation_${date_prfx}.yml \
  --capabilities CAPABILITY_IAM CAPABILITY_AUTO_EXPAND \
  --parameters ParameterKey=codeBucketName,ParameterValue=$SRC_BUCKET_NAME
  aws cloudformation wait stack-create-complete --stack-name \
  $STACK_NAME
fi
