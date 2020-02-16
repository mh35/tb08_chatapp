"""ニックネーム変更時のLambdaプログラムです
"""

import json
import os

import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

class DisconnectManager:
    """切断情報を管理します。これは切断が判明したときに
    切断が必要になったにもかかわらずそこに改めて送信する
    ことを防ぐためです。
    """
    def __init__(self, table, api):
        """切断情報を管理するためのインスタンスを作成します
        """
        self.__table = table
        self.__api = api
        # 切断中or切断済みのコネクションIDを格納します
        self.__disconn_ids = []

    def disconnect(self, conn_id):
        """切断を行い、メッセージを送信します
        """
        self.__disconn_ids.append(conn_id)
        # コネクションの存在を確認します
        main_rec_res = self.__table.get_item(Key={
            'Id': conn_id,
            'Field': 'CMng'
        })
        if 'Item' not in main_rec_res:
            return
        # メインレコードから名前を取得します
        main_rec = main_rec_res['Item']
        user_name = 'No name' if main_rec['Content'][
            'Name'] is None else main_rec['Content']['Name']
        # 所属しているチャネルを取得します。これは
        # 切断したことを全員に通知するためです
        ch_recs_res = self.__table.query(
            KeyConditionExpression=Key('Id').eq(
                conn_id) & Key('Field').begins_with('CH')
        )
        for rec in ch_recs_res['Items']:
            # そのチャネルに属するコネクションを取得します
            ch_conns_res = self.__table.query(
                IndexName='GSI1',
                KeyConditionExpression=Key('Field').eq(rec[
                    'Field'])
            )
            for chrec in ch_conns_res['Items']:
                # 切断中か切断済みのコネクションは無視します
                if chrec['Id'] in self.__disconn_ids:
                    continue
                # メッセージを送信します
                self.send_message(chrec['Id'], {
                    'channel_name': rec['Field'][2:],
                    'message': user_name + ' disconnected',
                    'sender': 'SYSTEM'
                })
            # チャネルからコネクションを削除します
            self.__table.delete_item(Key={
                'Id': conn_id,
                'Field': rec['Field']
            })
        # コネクションを削除します
        self.__table.delete_item(Key={
            'Id': conn_id,
            'Field': 'CMng'
        })

    def send_message(self, conn_id, content):
        """メッセージを送信します。失敗時かつそのコネクションが
        切断済みの場合、切断関数を呼び出します。
        """
        try:
            # コネクションに実際にメッセージを送信します
            self.__api.post_to_connection(
                ConnectionId=conn_id,
                Data=json.dumps(content)
            )
        except ClientError as e:
            # 切断したという例外のときは、そのコネクションは
            # もはや存在しないため、コネクションを切断します
            if e.response['Error']['Code'] == 'GoneException':
                self.disconnect(conn_id)
        except:
            pass

def lambda_handler(event, context):
    """Lambdaハンドラのメインプログラムです
    """
    region_name = boto3.session.Session().region_name
    table_name = os.environ['TABLE_NAME']
    dynamo = boto3.resource('dynamodb', region_name=region_name)
    table = dynamo.Table(table_name)  # pylint: disable=no-member

    conn_id = event['requestContext']['connectionId']
    # ドメイン名とステージ名を取得します
    domain_name = event['requestContext']['domainName']
    stage_name = event['requestContext']['stage']
    # APIインスタンスを作成します
    api = boto3.client('apigatewaymanagementapi',
        endpoint_url='https://' + domain_name + '/' + stage_name)
    # 切断処理を行います
    dcm = DisconnectManager(table, api)
    conn_item_res = table.get_item(Key={
        'Id': conn_id,
        'Field': 'CMng'
    })
    try:
        ebody = json.loads(event['body'])
    except:
        return {
            'statusCode': 200
        }
    if 'nickname' not in ebody or ebody[
        'nickname'] is None or ebody['nickname'] == '' or ebody[
        'nickname'] == 'SYSTEM':
        return {
            'statusCode': 200
        }
    if 'Item' not in conn_item_res:
        return {
            'statusCode': 200
        }
    conn_item = conn_item_res['Item']
    old_name = 'No name' if conn_item['Content'][
        'Name'] is None else conn_item['Content']['Name']
    conn_item['Content']['Name'] = ebody['nickname']
    table.put_item(Item=conn_item)