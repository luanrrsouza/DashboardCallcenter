from dash import Dash, html, dcc, Input, Output
import plotly.graph_objects as go
import pandas as pd
import mysql.connector
import dash_bootstrap_components as dbc
import datetime
import numpy as np


def get_data():
    try:
        conexao = mysql.connector.connect(
            host="localhost",
            user="Luan",
            password="14253020",
            database="bancoteste"
        )
    except mysql.connector.Error as err:
        print("Erro ao conectar ao banco de dados:", err)
        raise

    cursor = conexao.cursor()

    query = 'SELECT * FROM teste'
    cursor.execute(query)
    resultado = cursor.fetchall()
    colunas = [desc[0] for desc in cursor.description]
    cursor.close()
    conexao.close()

    df = pd.DataFrame(resultado, columns=colunas)

    df['DATAHORA_INICIO'] = pd.to_datetime(df['DATAHORA_INICIO'])
    df['DATAHORA_FIM'] = pd.to_datetime(df['DATAHORA_FIM'])

    df.loc[df['DATAHORA_FIM'].isnull(), 'DATAHORA_FIM'] = datetime.datetime.now()

    df['DURACAO'] = (df['DATAHORA_FIM'] - df['DATAHORA_INICIO']).dt.total_seconds()

    df['DURACAO'] = df['DURACAO'].fillna(0)

    def formatar_duracao(segundos):
        horas = int(segundos // 3600)
        minutos = int((segundos % 3600) // 60)
        segundos = int(segundos % 60)
        return f"{horas}h{minutos}min{segundos}s"

    df['DURACAO_FORMATADA'] = df['DURACAO'].apply(formatar_duracao)

    return df

app = Dash(__name__, external_stylesheets=[dbc.themes.LUX])

# Estilo CSS para aplicar a fonte personalizada Munito Sans
app.css.append_css({
    'external_url': '/assets/MunitoSans-Regular.ttf'
})

app.layout = dbc.Container([
    dbc.Card([
        dbc.CardBody([
            html.H1('Operadores', className='card-title',
                    style={'textAlign': 'center', 'color': 'black', 'font-family': 'Munito Sans, sans-serif', 'font-size': '30px'}),
            html.Div([
                html.Div([
                    html.Label('Filtrar por status:', style={'color': 'black'}),
                    dcc.Dropdown(
                        id='filtro_status',
                        options=[{'label': 'Off-line', 'value': 'Off-line'},
                                 {'label': 'On-line', 'value': 'On-line'},
                                 {'label': 'Selecione o status', 'value': 'Selecione o status'}],
                        value='Selecione o status',
                        clearable=False,
                        style={'borderWidth': '1px'}
                    ),
                ], style={'display': 'inline-block', 'width': '48%'}),
                html.Div([
                    html.Label('Filtrar por tipo:', style={'color': 'black'}),
                    dcc.Dropdown(
                        id='filtro_tipo',
                        options=[{'label': 'CPC', 'value': 'CPC'},
                                 {'label': 'NetSales', 'value': 'NetSales'},
                                 {'label': 'Selecione o tipo', 'value': 'Selecione o tipo'}],
                        value='Selecione o tipo',
                        clearable=False,
                        style={'borderWidth': '1px'}
                    ),
                ], style={'display': 'inline-block', 'width': '48%'}),
            ], style={'textAlign': 'center'}),
            dcc.Graph(
                id='grafico_ids',
                style={'overflowX': 'scroll'}
            ),
            dcc.Interval(
                id='interval-component',
                interval=1000,  # Alterar a consulta do banco de dados
                n_intervals=0
            )
        ])
    ], style={'backgroundColor': '#f8f9fa', 'padding': '20px', 'border-radius': '10px'})
], fluid=True, style={'backgroundColor': '#f8f9fa', 'padding': '20px'})

def formatar_duracao(segundos):
    horas = int(segundos // 3600)
    minutos = int((segundos % 3600) // 60)
    segundos = int(segundos % 60)
    return f"{horas:02d}:{minutos:02d}:{segundos:02d}"

def create_figure(df, filtro_status='Selecione o status', filtro_tipo='Selecione o tipo'):
    df_filtrado = df.copy()

    if filtro_status != 'Selecione o status':
        if filtro_status == 'Off-line':
            filtro_status = 0
        elif filtro_status == 'On-line':
            filtro_status = 1
        df_filtrado = df_filtrado[df_filtrado['STATUS'] == int(filtro_status)]

    if filtro_tipo != 'Selecione o tipo':
        df_filtrado = df_filtrado[df_filtrado['TIPO'] == filtro_tipo]

    fig = go.Figure()

    now = datetime.datetime.now()

    for idx, row in df_filtrado.iterrows():
        cor = 'green' if row['STATUS'] == 1 else 'red'

        width = 0.8
        height = 1
        rx = 0.2
        ry = 0.2
        x0 = idx
        x1 = idx + width
        y0 = 0.5
        y1 = y0 + height
        path = f'M {x0 + rx},{y0} ' \
               f'L {x1 - rx},{y0} Q {x1},{y0} {x1},{y0 + ry} ' \
               f'L {x1},{y1 - ry} Q {x1},{y1} {x1 - rx},{y1} ' \
               f'L {x0 + rx},{y1} Q {x0},{y1} {x0},{y1 - ry} ' \
               f'L {x0},{y0 + ry} Q {x0},{y0} {x0 + rx},{y0} Z'

        fig.add_shape(
            type="path",
            path=path,
            line=dict(color=cor, width=2),
            fillcolor=cor,
            opacity=0.6,
            xref="x",
            yref="y"
        )

        fig.add_annotation(
            x=idx + width / 2,
            y=1,
            text=f"{row['ID_ROBO']}",
            font=dict(color='white', size=24),
            showarrow=False,
            yshift=0
        )

        if row['STATUS'] == 1:
            online_time = (now - row['DATAHORA_INICIO']).total_seconds()
            online_time_formatted = formatar_duracao(online_time)
            fig.add_annotation(
                x=idx + width / 2,
                y=0.8,
                text=f"Online: {online_time_formatted}",
                font=dict(color='white', size=20),
                showarrow=False,
                yshift=0
            )

        elif row['STATUS'] == 0:
            encerrado_time = row['DATAHORA_FIM'].strftime('%H:%M:%S')
            fig.add_annotation(
                x=idx + width / 2,
                y=0.8,
                text=f"Encerrado: {encerrado_time}",
                font=dict(color='white', size=16),
                showarrow=False,
                yshift=0
            )

    fig.update_layout(
        xaxis=dict(
            showticklabels=False,
            zeroline=False,
            showgrid=False,
        ),
        yaxis=dict(
            showticklabels=False,
            zeroline=False,
            showgrid=False,
            range=[0, 2]
        ),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        height=400,
        margin=dict(l=0, r=0, t=0, b=0),
        autosize=True
    )

    fig.update_layout(xaxis=dict(autorange=True), yaxis=dict(autorange=True))

    return fig

@app.callback(
    Output('grafico_ids', 'figure'),
    [Input('filtro_status', 'value'),
     Input('filtro_tipo', 'value'),
     Input('interval-component', 'n_intervals')],
    prevent_initial_call=True
)
def update_output(filtro_status, filtro_tipo, n_intervals):
    df = get_data()
    return create_figure(df, filtro_status, filtro_tipo)




if __name__ == '__main__':
    app.run_server(debug=True)