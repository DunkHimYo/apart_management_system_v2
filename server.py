import asyncio
import websockets
import json
import pymysql
import jwt
import datetime

SECRET_PRE = 'secret'

class connect_DB:
    select_type = {'주민': 'dweller', '경비원': 'security', '관리자': 'manager'}

    def __init__(self, host='127.0.0.1', user='root', pw='1234', db_name='amsDB'):
        self.conn = pymysql.connect(host=host, user=user, password=pw, db=db_name, charset='utf8')
        self.cur = self.conn.cursor()

    def _click_signUp(self, id, pw, type, name, phone_number, address):
        """회원가입 DB Setting"""
        try:
            self.cur.execute(f'INSERT INTO totalList VALUES("{id}","{type}")')
            self.cur.execute(f'INSERT INTO signUp VALUES("{id}",0)')
            print(f'INSERT INTO {self.select_type[type]} VALUES("{id}","{pw}","{name}","{phone_number}","{address}")')
            self.cur.execute(
                f'INSERT INTO {self.select_type[type]} VALUES("{id}","{pw}","{name}","{phone_number}","{address}")')

        except pymysql.err.IntegrityError:
            self.conn.rollback()
            return False
        else:
            self.conn.commit()
            return True

    def _find_id_pw(self, type, name, phone_number, address):
        """ID/PW Select DB Setting"""
        try:
            self.cur.execute(f'SELECT ID,pw FROM {self.select_type[type]} '
                             f'where name = "{name}" and phoneNumber = "{phone_number}" and address = "{address}";')
        except:
            self.conn.rollback()
            return False
        else:
            select_data = self.cur.fetchone()
            return select_data

    def _chking_id_pw(self, id, pw):
        """ID/PW Select DB Setting"""
        try:
            self.cur.execute(f'SELECT pw FROM amsdb.dweller where ID="{id}";')
        except:
            self.conn.rollback()
        else:
            select_data, = self.cur.fetchone()

            if select_data == pw:
                return True
            else:
                return False

    def _click_question(self, questionNumber, title, contents):
        """회원가입 DB Setting"""
        try:
            self.cur.execute(f'INSERT INTO question VALUES("{questionNumber}","{title}","{contents}")')
        except pymysql.err.IntegrityError:
            self.conn.rollback()
            return False
        else:
            self.conn.commit()
            return True

    def _click_inquire(self, id, boardNumber, title,contents):
        """회원가입 DB Setting"""
        print(f'INSERT INTO inquire VALUES({boardNumber},"{id}","{title}")')
        try:
            self.cur.execute(f'INSERT INTO inquire VALUES({boardNumber},"{id}","{title}")')
        except pymysql.err.IntegrityError:

            self.conn.rollback()
            return False
        else:

            self.conn.commit()
            return True


def create_token(id, pw):
    encoded = jwt.encode({'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=10)
                             , 'id': id, 'pw': pw}, SECRET_PRE, algorithm='HS256')
    return encoded


def validate_token(token):
    try:
        return jwt.decode(token, SECRET_PRE, algorithms='HS256')
    except jwt.ExpiredSignatureError:
        return 'signatureError'
    except jwt.InvalidTokenError:
        return 'invalidTokenError'


async def accept(websocket, path):
    db = connect_DB()
    while True:
        data_rcv = json.loads(await websocket.recv())

        if 'logIn' == data_rcv['method']:
            if db._chking_id_pw(data_rcv['params']['id'], data_rcv['params']['pw']):
                await websocket.send(json.dumps(
                    {f'jsonrpc': '2.0', 'method': data_rcv['method'],
                     'params': create_token(data_rcv['params']['id'], data_rcv['params']['pw']),
                     'id': str(data_rcv['id'])}))
            else:
                await websocket.send(json.dumps(
                    {f'jsonrpc': '2.0', 'method': data_rcv['method'],
                     'params': 'fail',
                     'id': str(data_rcv['id'])}))

        elif 'signUp' == data_rcv['method']:
            if db._click_signUp(data_rcv['params']['id'], data_rcv['params']['pw'], data_rcv['params']['type'],
                                data_rcv['params']['name'], data_rcv['params']['phone_number'],
                                data_rcv['params']['address']):

                await websocket.send(json.dumps(
                    {f'jsonrpc': '2.0', 'method': data_rcv['method'],
                     'params': 'clear', 'id': str(data_rcv['id'])}))
            else:
                await websocket.send(json.dumps(
                    {f'jsonrpc': '2.0', 'method': data_rcv['method'],
                     'params': 'fail', 'id': str(data_rcv['id'])}))

        elif 'findIdPw' == data_rcv['method']:
            rcv = db._find_id_pw(data_rcv['params']['type'], data_rcv['params']['name'],
                                 data_rcv['params']['phone_number'], data_rcv['params']['address'])
            if rcv:
                await websocket.send(json.dumps(
                    {f'jsonrpc': '2.0', 'method': data_rcv['method'],
                     'params': {'id': rcv[0], 'pw': rcv[1]}, 'id': str(data_rcv['id'])}))
            else:
                if rcv:
                    await websocket.send(json.dumps(
                        {f'jsonrpc': '2.0', 'method': data_rcv['method'],
                         'params': 'fail', 'id': str(data_rcv['id'])}))

        elif 'question' == data_rcv['method']:

            if db._click_question(data_rcv['params']['questionNumber'], data_rcv['params']['title'],
                                  data_rcv['params']['contents']):
                await websocket.send(json.dumps(
                    {f'jsonrpc': '2.0', 'method': data_rcv['method'],
                     'params': 'clear', 'id': str(data_rcv['id'])}))
            else:
                await websocket.send(json.dumps(
                    {f'jsonrpc': '2.0', 'method': data_rcv['method'],
                     'params': 'fail', 'id': str(data_rcv['id'])}))

        elif 'inquire' == data_rcv['method']:

            information = validate_token(data_rcv['params']['token'])

            if information:
                if db._click_inquire(information['id'], int(datetime.datetime.utcnow().timestamp()),
                                     data_rcv['params']['title'], data_rcv['params']['contents'],):
                    await websocket.send(json.dumps(
                        {f'jsonrpc': '2.0', 'method': data_rcv['method'],
                         'params': 'clear', 'id': str(data_rcv['id'])}))
                else:
                    await websocket.send(json.dumps(
                        {f'jsonrpc': '2.0', 'method': data_rcv['method'],
                         'params': 'fail', 'id': str(data_rcv['id'])}))

        elif data_rcv is not None:
            await websocket.send(json.dumps(
                {f'jsonrpc': '2.0', 'method': data_rcv['method'], 'params': 'clear', 'id': str(data_rcv['id'])}))

        else:
            await websocket.send(json.dumps(
                {f'jsonrpc': '2.0', 'method': data_rcv['method'], 'params': 'fail', 'id': str(data_rcv['id'])}))


if __name__ == '__main__':
    websoc_svr = websockets.serve(accept, 'localhost', 3000, ping_interval=None)

    asyncio.get_event_loop().run_until_complete(websoc_svr)
    asyncio.get_event_loop().run_forever()
