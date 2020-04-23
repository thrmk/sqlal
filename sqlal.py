from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
import sqlite3
from dash.dependencies import Input, Output, State
import paho.mqtt.client as mqtt
import time
import pandas as pd
import sqlite3
import os
from datetime import datetime
FA ="https://use.fontawesome.com/releases/v5.8.1/css/all.css"

server = Flask(__name__)
server.config['DEBUG'] = True
server.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///test.db')

#server.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
server.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(server)


class User(db.Model):
    __tablename__ = 'datatable'

    id = db.Column(db.Integer, primary_key=True)
    stamp = db.Column(db.String(26))
    devId = db.Column(db.String(15))
    SPA = db.Column(db.String(10))
    TA = db.Column(db.String(10))

    def __repr__(self):
        return '<User %r %r  %r %r>' % (self.stamp, self.devId, self.SPA, self.TA)
db.create_all()
def on_connect(client, userdata, flags, rc):
    print("Connected!", rc)

def on_subscribe(client, userdata, mid, granted_qos):
    print("Subscribed:", str(mid), str(granted_qos))

def on_unsubscribe(client, userdata, mid):
    print("Unsubscribed:", str(mid))

def on_publish(client, userdata, mid):
    print("Publish:", client)

def on_log(client, userdata, level, buf):
    print("log:", buf)

def on_disconnect(client, userdata, rc):
    if rc != 0:
        print("Unexpected disconnection.")

def on_message(client, userdata, message):

    payload = str(message.payload.decode("utf-8"))
    print("payload=",payload)
    data = dict(x.split(": ") for x in payload.split(" , "))
    admin = User(stamp=str(datetime.now()),devId=data['devId'],SPA=data['SPA'],TA=data['TA'])
    db.session.add(admin)
    db.session.commit()
client = mqtt.Client()
print("client=",client)

client.on_subscribe = on_subscribe
client.on_unsubscribe = on_unsubscribe
client.on_connect = on_connect
client.on_message = on_message
time.sleep(1)

subtop="tracker/device/sub"
pubtop="tracker/device/pub"
#link=""
#if link!="":
#client.connect("ec2-35-162-194-10.us-west-2.compute.amazonaws.com",1883)
#client.connect("env-5116852.gpuoncloud.in",11002)
#client.connect("iot.smarttrak.info",1883)
client.username_pw_set("cbocdpsu", "3_UFu7oaad-8")
client.connect('soldier.cloudmqtt.com', 14035,60)
client.loop_start()
client.subscribe(subtop)
client.loop()

graph=html.Div([
    dcc.Dropdown(
        id='devices',
        options=[
            {'label': 'R1', 'value': 'R1 '},
            {'label': 'G2', 'value': 'G2 '},
            {'label': 'R2', 'value': 'R2 '}
        ],
        value='R1 ', style={"width":"auto"}),
html.Div(id='dd-output-container')
    ,


 #style={"backgroundColor":"grey","width":"auto"},
    dcc.Graph(id='graph-with-slider'),
    dcc.Interval(
            id='interval-component',
            interval=1*1000, # in milliseconds
            n_intervals=0
        )
        ])

data1= html.Div([
        #html.H4('Substation Data Live Feed'),
        html.Table(id="live-update-text"),],style={"overflowX":"scroll"})

app = dash.Dash(__name__,server=server,external_stylesheets=[dbc.themes.BOOTSTRAP, FA])

app.config['suppress_callback_exceptions']=True

def table(devices):
    #global reading
    print("table devices=",devices)
    #reading=reading+1
    table_header=[
        html.Thead(html.Tr([html.Th('stamp'),html.Th('devId'),html.Th('sun angle') ,html.Th('tracker angle')#, html.Th('motor status') ,
         ]))]
    table_body=[
        html.Tbody(html.Tr([html.Td(dev[1]),html.Td(dev[2]),html.Td(dev[3]),html.Td(dev[4])]))for dev in devices]
    table=dbc.Table(table_header+table_body,bordered=True,striped=True,hover=True,style={"backgroundColor":"white"})
    return table

app.layout = html.Div([data1,graph,dcc.Location(id="url",refresh=True)])

@app.callback(
    Output('graph-with-slider', 'figure'),
    [Input('devices', 'value')])#,Input('interval-component', 'n_intervals')])
def update_figure(selected_device):
    connection1 = sqlite3.connect('test.db')#,check_same_thread=False)
    df=pd.read_sql("select * from datatable",connection1)

    filtered_df = df[df.devId == selected_device]
    print("filtered df=",filtered_df)

    return {
                                'data': [
                                    {'x': filtered_df.stamp, 'y':filtered_df.SPA
                                    #.where(df.devname=='dev_01')
                                    , 'name': 'SPA'},
                                    {'x': filtered_df.stamp, 'y':filtered_df.TA
                                                                  , 'name': 'TA'},

                                  #  {'x': df['tStamp'], 'y': df['yphvol'], 'z':df['devname'],  'name': 'yphvol'},
                                #    {'x': df['tStamp'], 'y': df['bphvol'], 'z':df['devname'],  'name': 'bphvol'},
                                   # {'x': df['tStamp'], 'y': df['avgvol'], 'type': 'bar', 'name': 'avgvol'}#if df['devId']  =="1",
                                   ],
            'layout': {
                'title': 'SPA and TA'
                }}

@app.callback(Output("live-update-text", "children"),
              [Input("live-update-text", "className")])
def update_output_div(input_value):
    #cursor.execute("SELECT * FROM data")
    connection2 = sqlite3.connect('test.db')#,check_same_thread=False)
    #df=pd.read_sql("select * from datatable",connection2)
    cursor=connection2.cursor()
    cursor.execute("SELECT * FROM datatable")

    rows = cursor.fetchall()
    print("rows=",rows)

    for row in rows:
        print("row=",row)
    #devices = DeviceModel.query.all()
    return [html.Table(table(rows)
        )]

if __name__=="__main__":
#    print("main starts")
    app.run_server(debug=True,port=443)

