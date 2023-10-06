from flask import Flask, render_template, request, jsonify, send_file
import cv2
import os
import pandas as pd
from pyzbar import pyzbar
import re
import json
import sqlite3
from werkzeug.local import Local
import requests
import datetime


app = Flask(__name__)
# 创建线程本地存储对象
local = Local()

def get_db():
    # 如果当前线程没有数据库连接，创建一个并存储在 TLS 中
    if not hasattr(local, 'db'):
        local.db = sqlite3.connect('your_database.db')  # 替换为您的数据库连接信息
    return local.db

def read_qrcode(image_path):
    # 使用cv2读取图像
    image = cv2.imread(image_path)
    height, width, channels = image.shape
    image = image[:, width // 2:]
    #图像灰化处理
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    #检测二维码
    barcodes = pyzbar.decode(gray)
    barcode_data_list = []
    #for barcode in barcodes:
    #    (x, y, w, h) = barcode.rect
    #    cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)
    #    barcode_data = barcode.data.decode("utf-8")
    #    barcode_data_list.append(barcode_data)
    #return barcode_data_list
    detect_obj = cv2.wechat_qrcode_WeChatQRCode('detect.prototxt','detect.caffemodel','sr.prototxt','sr.caffemodel')
    res,points = detect_obj.detectAndDecode(gray)
    barcode_data_list = [item for item in res]
    return barcode_data_list


@app.route('/')
def html():
    return render_template('index.html')

@app.route('/decode_qrcode', methods=['POST'])
def decode_qrcode():
    # 从POST请求中获取图像文件
    file = request.files['image']
    # 保存图像到临时文件
    temp_image_path = 'temp_image.png'
    file.save(temp_image_path)
    # 识别QR码
    decoded_info = read_qrcode(temp_image_path)
    # 删除临时文件
    os.remove(temp_image_path)
    target_month_id  = '202310'
    new_decoded_info = []
    # 遍历原始数组
    for url in decoded_info:
    # 使用正则表达式提取monthId的值
        match = re.search(r'monthId=(\d+)', url)
        if match:
            month_id = match.group(1)
            # 如果monthId匹配目标值，则提取ticketCardId的值并添加到新数组
            if month_id == target_month_id:
                match = re.search(r'ticketCardId=(\d+)', url)
                if match:
                    ticket_card_id = match.group(1)
                    new_decoded_info.append(ticket_card_id)
    if not new_decoded_info:
        return jsonify({'decoded_info': []})
    else:
        return jsonify({'decoded_info': new_decoded_info})

@app.route('/upload', methods=['POST'])
def upload():
    conflict_data = []
    current_timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    monthId = '202310'
    try:
        data = request.get_json()
        if data is not None:
            for key, values in data.items():
                if isinstance(values, list):
                    db_connection = get_db()
                    cursor = db_connection.cursor()
                    existing_values = cursor.execute("SELECT DISTINCT value FROM lottery WHERE key = ?", (key,)).fetchall()
                    existing_values = [value[0] for value in existing_values]
                    # 去重并将不重复的值插入数据库
                    for value in values:
                        if value not in existing_values:
                            cursor.execute("SELECT key FROM lottery WHERE key != ? AND value = ?", (key, value))
                            result = cursor.fetchall()
                            if result:
                                for row in result:
                                    # 如果有冲突记录，可以将它们存储在一个列表中
                                    conflict_data.append({"conflict_key": row[0], "conflict_value": value})
                                    response = requests.get(f'https://h5.if.qidian.com/argus/api/v1/interaction/queryTicketCardById?monthId={monthId}&ticketCardId={value}')
                                    responsedata = json.loads(response.text)
                                    Nickname = responsedata.get('Data', {}).get('NickName')
                                    if key == Nickname:
                                        cursor.execute("UPDATE lottery SET key = ? WHERE key = ? AND value = ?", (key, row[0], value))
                                        existing_values.append(value)
                                    else:
                                        return jsonify("传自己的图")
                            else:
                                # 如果没有冲突记录，将值插入数据库
                                cursor.execute("INSERT INTO lottery (key, value,timestamp) VALUES (?, ?, ?)", (key, value,current_timestamp))
                                existing_values.append(value)
                    db_connection.commit()
                    cursor.close()


                    if conflict_data:
                        return jsonify({"conflict_data": conflict_data})
                    else:
                        return jsonify({"message": "数据插入成功"})
        else:
            return jsonify({'error': 'Invalid JSON format'})                
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/lottery')
def lottery():
    return render_template('lottery.html')

@app.route('/query',methods = ['POST'])
def query():
    try:
        data = request.data
        key = data.decode("utf-8")
        db_connection = get_db()
        cursor = db_connection.cursor()
        cursor.execute("SELECT COUNT(DISTINCT value) AS value_count FROM lottery WHERE key = ?", (key,))
        result = cursor.fetchone()
        value_count = result[0]
        cursor.close()
        return jsonify({"value_count": value_count})
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/querylottery',methods = ['POST'])
def querylottery():
    monthId = '202310'
    try:
        conn = sqlite3.connect('your_database.db')
        cursor = conn.cursor()
        data = request.data.decode('utf-8')
        cursor.execute(f"SELECT key FROM lottery WHERE value = ?", (data,))
        result = cursor.fetchone()
        response = requests.get(f'https://h5.if.qidian.com/argus/api/v1/interaction/queryTicketCardById?monthId={monthId}&ticketCardId={data}')
        responsedata = json.loads(response.text)
        Nickname = responsedata.get('Data', {}).get('NickName')
        BookName = responsedata.get('Data', {}).get('BookName')
        TicketId = responsedata.get('Data', {}).get('TicketId')
        cursor.close()
        if (BookName == '您完全不按套路通关是吗'):
            if (Nickname == result[0]):
                return jsonify({'Nickname': Nickname,'TicketId':TicketId})
            else:
                return jsonify({'error':'用户名不匹配','Nickname':Nickname,'Nowname':result[0]})
        else:
            return jsonify({'error':'非本书月票','BookName':BookName,'Nowname':result[0]})
    except Exception as e:
        return jsonify({'error': str(e)})


@app.route('/getexcel')
def getexcel():
    # 连接到数据库并获取数据
    conn = sqlite3.connect('your_database.db')
    query = "SELECT * FROM lottery;"
    df = pd.read_sql_query(query, conn)
    # 将数据写入Excel文件
    df.to_excel('output.xlsx', index=False)
    # 关闭数据库连接
    conn.close()
    return send_file('output.xlsx')

if __name__ == '__main__':
    app.run(host='0.0.0.0',debug=False)
