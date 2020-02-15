"""接続時のLambdaプログラムです
"""

import os

import boto3

def lambda_handler(event, context):
    """Lambdaハンドラのメインプログラムです
    """
    # リージョン名を取得します
    region_name = boto3.session.Session().region_name
    # 環境変数からテーブル名を取得します
    # TABLE_NAMEという名前はformation.ymlにある名前です
    table_name = os.environ['TABLE_NAME']
    # DynamoDBのリソース要素を取得します
    dynamo = boto3.resource('dynamodb', region_name=region_name)
    # DynamoDBのテーブルリソースを取得します
    # 後ろのコメントはPyLintに対してエラーを抑止するためです
    table = dynamo.Table(table_name)  # pylint: disable=no-member

    # コネクションIDを取得します
    conn_id = event['requestContext']['connectionId']
    # テーブルに接続のレコードを記録します
    table.put_item(Item={
        'Id': conn_id,
        'Field': 'CMng',
        'Content': {
            'Name': None
        }
    })
    # 最後にreturnして正常に接続できたことを返します
    return {
        'statusCode': 200
    }
