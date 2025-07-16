import pandas as pd
import dash
from dash import html, dcc, dash_table, Input, Output
import plotly.express as px

# Load data
df = pd.read_excel("CUI_Authorities.xlsx", sheet_name="CUI Authorities")

app = dash.Dash(__name__)
app.title = "CUI Authorities Dashboard"

app.layout = html.Div([
    html.H1("🛡️ CUI Authorities Data Dashboard"),

    dcc.Dropdown(
        id='category-filter',
        options=[{"label": c, "value": c} for c in sorted(df["Category"].unique())],
        placeholder="Select a CUI Category",
        multi=True
    ),

    dash_table.DataTable(
        id='data-table',
        columns=[{"name": i, "id": i} for i in df.columns],
        page_size=15,
        style_table={'overflowX': 'auto'},
        style_cell={'textAlign': 'left', 'minWidth': '150px'},
    ),

    html.Br(),

    dcc.Graph(id='source-count-bar'),
    dcc.Graph(id='sanction-count-bar'),
])

@app.callback(
    Output('data-table', 'data'),
    Output('source-count-bar', 'figure'),
    Output('sanction-count-bar', 'figure'),
    Input('category-filter', 'value')
)
def update_dashboard(selected_categories):
    filtered_df = df[df["Category"].isin(selected_categories)] if selected_categories else df

    source_fig = px.bar(
        filtered_df.groupby("Category").size().reset_index(name="Sources"),
        x="Category", y="Sources", title="Sources per Category"
    )

    sanction_fig = px.bar(
        filtered_df[filtered_df["Sanctions"] != ""].groupby("Category").size().reset_index(name="Sanctions"),
        x="Category", y="Sanctions", title="Sanctions per Category"
    )

    return filtered_df.to_dict("records"), source_fig, sanction_fig

if __name__ == "__main__":
    app.run_server(debug=True)
