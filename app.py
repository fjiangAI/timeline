import dash
from dash import dcc, html, Input, Output, State
import plotly.graph_objects as go
import pandas as pd
from io import BytesIO
import base64
import os
from flask import send_file

# 默认事件数据加载
def load_default_events():
    if os.path.exists('events.xlsx'):
        return pd.read_excel('events.xlsx')
    else:
        return pd.DataFrame({
            '日期': pd.to_datetime(['2023-01-01', '2023-05-01', '2023-12-25']),
            '事件类型': ['重要事件', '日常任务', '节假日'],
            '事件描述': ['描述1', '描述2', '描述3']
        })

# 尝试加载默认事件数据
default_events_df = load_default_events()

# 动态生成事件类型（唯一的事件类型）
def generate_event_types(events_df):
    event_types = events_df['事件类型'].unique()
    color_map = {
        event_type: f"rgba({(i * 70) % 255}, {(i * 120) % 255}, {(i * 180) % 255}, 0.7)"
        for i, event_type in enumerate(event_types)
    }
    y_position_map = {event_type: i for i, event_type in enumerate(event_types)}
    return event_types, color_map, y_position_map

# 创建时间线图的函数
def create_timeline(events_df):
    event_types, color_map, y_position_map = generate_event_types(events_df)

    fig = go.Figure()

    for event_type in event_types:
        event_data = events_df[events_df['事件类型'] == event_type]

        # 按照事件出现顺序交替设置text位置
        text_position = []
        for i in range(len(event_data)):
            if i % 2 == 0:
                text_position.append("bottom center")
            else:
                text_position.append("top center")

        # 添加散点
        fig.add_trace(go.Scatter(
            x=event_data['日期'],
            y=[y_position_map[event_type]] * len(event_data),
            mode="markers+text",
            text=event_data['日期'].dt.strftime('%m-%d'),
            textposition=text_position,
            hovertext=event_data['事件描述'],
            hoverinfo="text+x",
            marker=dict(
                size=12,
                color=color_map[event_type],
                line=dict(width=2, color='black')
            ),
            name=event_type
        ))

    fig.update_layout(
        title="我的大事件线 (2023-2024)",
        title_x=0.5,
        xaxis_title="日期",
        yaxis=dict(
            tickvals=list(y_position_map.values()),
            ticktext=list(y_position_map.keys()),
            title="事件类型",
        ),
        plot_bgcolor="white",
        hovermode="closest",
        showlegend=True,
        template="plotly_white",
        height=500,
        autosize=True  # 自动调整大小
    )

    fig.update_xaxes(range=["2023-01-01", "2024-12-31"])

    return fig

# 创建 Excel 模板并将其保存到内存中
def create_excel_template():
    df = pd.DataFrame({
        '日期': pd.to_datetime(['2023-01-01', '2023-05-01', '2023-12-25']),
        '事件类型': ['重要事件', '日常任务', '节假日'],
        '事件描述': ['描述1', '描述2', '描述3']
    })

    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Sheet1')
    output.seek(0)

    return output

# 初始化 Dash 应用
app = dash.Dash(__name__,
                external_stylesheets=['https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css'])


# 创建应用布局
app.layout = html.Div([
    html.H1("我的大事件线 (2023-2024)", style={'width': '100%', 'textAlign': 'center'}),  # 调整标题宽度

    html.Div(id='motivational-text', className='motivational-text',
             style={'fontSize': '24px', 'textAlign': 'center', 'marginTop': '20px', 'fontWeight': 'bold'}),

    # 时间线图
    dcc.Graph(id='timeline-graph', config={'responsive': True}, style={'width': '100%'}),  # 调整图表宽度

    # 按钮和下载链接区域
    html.Div(
        className="container-fluid",  # 使用fluid容器，适应整个屏幕宽度
        children=[
            html.Div(
                className="row",
                children=[
                    html.Div(
                        className="col-12 col-md-6",  # 使用Bootstrap响应式列
                        children=[
                            dcc.Upload(
                                id='upload-data',
                                children=html.Button('上传自己的大事件（Excel文件）',
                                                     style={'width': '100%', 'fontSize': '16px', 'padding': '10px',
                                                            'backgroundColor': '#4CAF50', 'color': 'white',
                                                            'border': 'none',
                                                            'cursor': 'pointer'}),
                                multiple=False
                            ),
                        ]
                    ),
                    html.Div(
                        className="col-12 col-md-6",  # 使用Bootstrap响应式列
                        children=[
                            html.A(
                                id='download-link',
                                href='/download-template',
                                download='events_template.xlsx',
                                target='_blank',
                                children=html.Button(
                                    '下载 Excel 模板',
                                    style={'width': '100%', 'fontSize': '16px', 'padding': '10px',
                                           'backgroundColor': '#2196F3', 'color': 'white', 'border': 'none',
                                           'cursor': 'pointer'}
                                )
                            ),
                        ]
                    ),
                ]
            )
        ]
    ),

    # 存储上传的文件内容（缓存）
    dcc.Store(id='file-store'),

    # 添加间隔器，用于字幕动画
    dcc.Interval(id='interval', interval=500, n_intervals=0, max_intervals=0),  # 初始max_intervals设置为0

    # 添加背景音乐
    html.Audio(
        src='/assets/7260.mp3',  # 请确保音乐文件路径正确
        controls=False,
        autoPlay=True,
        preload="auto",  # 提前加载音频
        loop=True,
        style={'position': 'fixed', 'top': '0', 'left': '0', 'width': '0', 'height': '0'}
    ),
])


# 路由处理：下载模板
@app.server.route('/download-template')
def download_template():
    output = create_excel_template()
    return send_file(output, as_attachment=True, download_name="events_template.xlsx",
                     mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


# 回调函数处理文件上传
@app.callback(
    Output('file-store', 'data'),
    [Input('upload-data', 'contents')],
    [State('upload-data', 'filename')]
)
def store_file(contents, filename):
    if contents is not None:
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        try:
            events_df = pd.read_excel(BytesIO(decoded))
            return events_df.to_dict('records')  # 存储文件内容
        except Exception as e:
            print(e)
            return default_events_df.to_dict('records')  # 如果解析失败，返回默认数据
    return None


# 更新图表的回调函数
@app.callback(
    Output('timeline-graph', 'figure'),
    [Input('file-store', 'data')]
)
def update_graph(data):
    if data is None:
        events_df = default_events_df
    else:
        events_df = pd.DataFrame(data)

    fig = create_timeline(events_df)
    return fig


# 动画效果的回调函数（字幕动画）
@app.callback(
    Output('motivational-text', 'children'),
    [Input('interval', 'n_intervals')]
)
def update_motivational_text(n_intervals):
    text = [
        "2024年，岁月匆匆，回望过往，心中涌动着感激与希望。",
        "每一滴汗水，每一段努力，都在岁月的河流中留下痕迹。",
        "曾经的坚持与拼搏，化作了今天的坚韧与信心。",
        "感谢自己，感谢每一个奋斗的瞬间，感谢所有支持的人。",
        "未来的路充满未知，但我已准备好迎接一切挑战。",
        "每一步都在创造新的故事，属于我，属于我们的篇章。"
    ]

    all_words = []
    for i, sentence in enumerate(text):
        sentence_words = [
            html.Span(word, className='motivational-word', style={'--index': i * len(sentence) + j})
            for j, word in enumerate(sentence)
        ]
        all_words.append(
            html.Div(
                sentence_words,
                className='motivational-line',
                style={'animationDelay': f'{i * 2}s'}
            )
        )

    # 如果动画完成，则停止刷新
    if n_intervals >= len(text) * 2:
        return all_words

    return all_words


# 运行应用
if __name__ == '__main__':
    app.run_server(debug=True, port=6005, host='0.0.0.0')














