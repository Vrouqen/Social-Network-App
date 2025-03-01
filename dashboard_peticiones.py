import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objs as go
import pandas as pd
import time
import threading

# Variables globales
log_file = "./logs/custom_access.log"
instances = {"172.18.0.4:5000": 0, "172.18.0.5:5000": 0, "172.18.0.6:5000": 0}
timestamps = []
data = {"time": [], "172.18.0.4:5000": [], "172.18.0.5:5000": [], "172.18.0.6:5000": []}

# Función para leer el log en tiempo real
def read_log():
    global instances, timestamps, data
    with open(log_file, "r") as file:
        file.seek(0, 2)  # Ir al final del archivo
        while True:
            line = file.readline()
            if line:
                for instance in instances.keys():
                    if f"backend={instance}" in line:
                        instances[instance] += 1
                timestamps.append(time.strftime("%H:%M:%S"))
                data["time"].append(timestamps[-1])
                for instance in instances.keys():
                    data[instance].append(instances[instance])
            time.sleep(1)

# Iniciar el hilo de lectura del log
t = threading.Thread(target=read_log, daemon=True)
t.start()

# Inicializar la aplicación Dash
app = dash.Dash(__name__)
app.layout = html.Div([
    html.H1("Monitor de Peticiones en Tiempo Real"),
    dcc.Graph(id='live-graph'),
    dcc.Interval(
        id='interval-component',
        interval=2000,
        n_intervals=0
    )
])

@app.callback(
    Output('live-graph', 'figure'),
    Input('interval-component', 'n_intervals')
)
def update_graph(n):
    df = pd.DataFrame(data)
    traces = []
    for instance in instances.keys():
        traces.append(go.Scatter(x=df["time"], y=df[instance], mode='lines', name=instance))
    return {'data': traces, 'layout': go.Layout(title='Peticiones por Instancia', xaxis={'title': 'Tiempo'}, yaxis={'title': 'Número de Peticiones'})}

if __name__ == '__main__':
    app.run_server(debug=True)
