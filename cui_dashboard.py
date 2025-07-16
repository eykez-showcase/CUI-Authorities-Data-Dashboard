import pandas as pd
import dash
from dash import dcc, html, Input, Output, dash_table
import plotly.express as px

# Load your data
df = pd.read_excel("data/cui_authorities_full.xlsx", sheet_name="CUI Authorities")

# Optional: rename columns for prettier UI
df.rename(columns={
    "Safeguarding and/or Dissemination Authority": "Safeguarding",
    "Organizational Category": "Org Category",
    "Authority": "Legal Authority",
    "Basic/Specified": "Type",
    "Category": "CUI Category",
    "Sanctions": "Sanctions"
}, inplace=True)

# Init the app
app = dash.Dash(__name__)
app.title = "CUI Authorities Dashboard"

app.layout = html.Div([
    html.H1("🔐 CUI Authorities Data Dashboard", style={"textAlign": "center"}),

    html.Div([
        dcc.Dropdown(
            id="category-filter",
            options=[{"label": cat, "value": cat} for cat in sorted(df["CUI Category"].unique())],
            placeholder="Filter by CUI Category...",
            multi=True,
            style={"width": "40%", "display": "inline-block", "marginRight": "10px"},
        ),
        dcc.Dropdown(
            id="org-filter",
            options=[{"label": org, "value": org} for org in sorted(df["Org Category"].unique())],
            placeholder="Filter by Org Category...",
            multi=True,
            style={"width": "40%", "display": "inline-block"},
        ),
    ], style={"padding": "10px"}),

    dash_table.DataTable(
        id="cui-table",
        columns=[{"name": i, "id": i} for i in df.columns],
        data=df.to_dict("records"),
        page_size=15,
        style_table={"overflowX": "auto"},
        style_cell={"textAlign": "left", "minWidth": "100px"},
        filter_action="native",
        sort_action="native",
    ),

    html.Br(),

    html.Div([
        dcc.Graph(id="source-bar"),
        dcc.Graph(id="sanction-bar"),
    ])
])


@app.callback(
    Output("cui-table", "data"),
    Output("source-bar", "figure"),
    Output("sanction-bar", "figure"),
    Input("category-filter", "value"),
    Input("org-filter", "value")
)
def update_display(selected_categories, selected_orgs):
    filtered_df = df.copy()

    if selected_categories:
        filtered_df = filtered_df[filtered_df["CUI Category"].isin(selected_categories)]
    if selected_orgs:
        filtered_df = filtered_df[filtered_df["Org Category"].isin(selected_orgs)]

    fig1 = px.bar(
        filtered_df.groupby("CUI Category").size().reset_index(name="Source Count"),
        x="CUI Category", y="Source Count", title="📊 Sources per CUI Category"
    )

    fig2 = px.bar(
        filtered_df[filtered_df["Sanctions"] != ""].groupby("CUI Category").size().reset_index(name="Sanction Count"),
        x="CUI Category", y="Sanction Count", title="🚨 Sanctions per CUI Category"
    )

    return filtered_df.to_dict("records"), fig1, fig2


if __name__ == "__main__":
    app.run(debug=True)
