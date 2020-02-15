"""接続時のLambdaプログラムです
"""

import os

import boto3

def lambda_handler(event, context):
    """Lambdaハンドラのメインプログラムです
    """
    # リージョン名を取得します
    region_name = boto3.session.Session().region_name
    # 環境変数から
    table_name = os.environ['TABLE_NAME']
    dynamo = boto3.resource('dynamodb', region_name=region_name)
    table = dynamo.Table(table_name)  # pylint: disable=no-member

    conn_id = event['requestContext']['connectionId']
    table.put_item(Item={
        'Id': conn_id,
        'Field': 'CMng',
        'Content': {
            'Name': None
        }
    })
    return {
        'statusCode': 200
    }
