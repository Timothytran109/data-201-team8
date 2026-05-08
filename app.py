import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, Input, Output, dcc, html

from db import run_query
from queries import (
    BASKET_COMPLEXITY_QUERY,
    CATEGORY_OPTIONS_QUERY,
    CUSTOMER_STATE_OPTIONS_QUERY,
    DELIVERY_STATUS_REVIEW_QUERY,
    FREIGHT_BY_WEIGHT_BAND_QUERY,
    FULFILLMENT_DELAY_BREAKDOWN_QUERY,
    KPI_QUERY,
    PAYMENT_METHOD_DISTRIBUTION_QUERY,
    PAYMENT_TOP_DIFFERENCES_QUERY,
    PAYMENT_RECON_KPI_QUERY,
    PRODUCT_WEIGHT_REVIEW_QUERY,
    REVIEW_RESPONSE_TIME_QUERY,
    SELLER_OUTLIERS_QUERY,
)

app = Dash(__name__)
app.title = "DATA 201 Olist Dashboard"

PALETTE = {
    "blue": "#2563EB",
    "gray": "#64748B",
    "orange": "#F97316",
    "green": "#16A34A",
    "red": "#DC2626",
    "amber": "#F59E0B",
    "bg": "#F8FAFC",
    "text": "#0F172A",
}

SELLER_STATE_COLORS = [
    "#2563EB",
    "#64748B",
    "#F59E0B",
    "#F97316",
    "#16A34A",
    "#DC2626",
]


def apply_chart_theme(fig: go.Figure, height: int = 420) -> go.Figure:
    fig.update_layout(
        template="plotly_white",
        paper_bgcolor=PALETTE["bg"],
        plot_bgcolor="white",
        font={"family": "Segoe UI, Tahoma, sans-serif", "size": 14, "color": PALETTE["text"]},
        title={"font": {"size": 21, "color": PALETTE["text"]}},
        xaxis={"title_font": {"size": 14}, "tickfont": {"size": 12}},
        yaxis={"title_font": {"size": 14}, "tickfont": {"size": 12}},
        legend={"title_font": {"size": 12}, "font": {"size": 12}},
        height=height,
        margin={"l": 60, "r": 30, "t": 70, "b": 60},
    )
    return fig


def delivery_status_color(label: str) -> str:
    v = str(label).lower()
    if "late" in v:
        return PALETTE["red"]
    if "on time" in v or "early" in v or "delivered" in v:
        return PALETTE["green"]
    if "neutral" in v:
        return PALETTE["amber"]
    return PALETTE["gray"]


def load_options() -> tuple[list[dict], list[dict]]:
    category_df = run_query(CATEGORY_OPTIONS_QUERY)
    state_df = run_query(CUSTOMER_STATE_OPTIONS_QUERY)

    category_options = [{"label": "All", "value": "All"}] + [
        {"label": c, "value": c}
        for c in category_df["category"].dropna().astype(str).tolist()
    ]
    state_options = [{"label": "All", "value": "All"}] + [
        {"label": s, "value": s}
        for s in state_df["customer_state"].dropna().astype(str).tolist()
    ]
    return category_options, state_options


def pct_label(value: float | None, digits: int = 1) -> str:
    if value is None or pd.isna(value):
        return "N/A"
    return f"{value * 100:.{digits}f}%"


category_options, state_options = load_options()

app.layout = html.Div(
    className="container",
    children=[
        html.H1("Olist Marketplace Satisfaction Dashboard"),
        html.P(
            "SQL-driven Dash app for DATA 201 final project: delivery performance, logistics, basket complexity, seller freight efficiency, and payment consistency vs customer satisfaction.",
            className="subtitle",
        ),
        html.Div(
            className="controls",
            children=[
                html.Div(
                    children=[
                        html.Label("Product Category"),
                        dcc.Dropdown(
                            id="category-dropdown",
                            options=category_options,
                            value="All",
                            clearable=False,
                        ),
                    ]
                ),
                html.Div(
                    children=[
                        html.Label("Customer State (Brazil UF Code)"),
                        html.P(
                            "State values use Brazilian two-letter UF abbreviations such as SP, RJ, MG.",
                            className="helper-text",
                        ),
                        dcc.Dropdown(
                            id="state-dropdown",
                            options=state_options,
                            value="All",
                            clearable=False,
                        ),
                    ]
                ),
                html.Div(
                    children=[
                        html.Label("Minimum Item Count (Seller Outliers)"),
                        dcc.Slider(
                            id="min-item-slider",
                            min=1,
                            max=200,
                            step=1,
                            value=20,
                            marks={1: "1", 20: "20", 50: "50", 100: "100", 200: "200"},
                        ),
                    ]
                ),
            ],
        ),
        html.H2("Overview"),
        html.Div(
            className="kpi-grid",
            children=[
                html.Div([html.H4("Total Orders"), html.P(id="kpi-total-orders")], className="kpi-card"),
                html.Div([html.H4("Average Review Score"), html.P(id="kpi-avg-review")], className="kpi-card"),
                html.Div([html.H4("Avg Days Early/Late"), html.P(id="kpi-avg-delay")], className="kpi-card"),
                html.Div([html.H4("Average Freight Burden (%)"), html.P(id="kpi-avg-freight")], className="kpi-card"),
            ],
        ),
        html.P(
            "Negative values mean orders arrived earlier than the estimated delivery date; positive values mean orders arrived late.",
            className="helper-text",
        ),
        html.H2("Operations & Reviews"),
        dcc.Graph(id="delivery-status-review-chart"),
        html.P("Caption: Delivery status patterns help explain review score differences.", className="caption"),
        dcc.Graph(id="fulfillment-delay-breakdown-chart"),
        html.P(
            "Caption: This chart compares average fulfillment-stage delays to show which stage contributes most to total timing.",
            className="caption",
        ),
        dcc.Graph(id="review-response-time-chart"),
        html.P("Caption: Review response speed is compared across sentiment groups.", className="caption"),
        html.H2("Product Logistics"),
        dcc.Graph(id="freight-weight-band-chart"),
        html.P("Caption: Freight burden rises in certain weight bands and may affect satisfaction.", className="caption"),
        dcc.Graph(id="basket-complexity-chart"),
        html.P("Caption: Low-review rate by basket size can be easier to interpret than average score alone.", className="caption"),
        dcc.Graph(id="seller-outliers-chart"),
        html.P("Caption: Top freight-burden sellers are filtered by minimum sold item count.", className="caption"),
        html.Div(
            className="payment-section",
            children=[
                html.H2("Payment Consistency"),
                html.H3("Payment Difference Flags"),
                html.P(
                    "These are reconciliation flags, not confirmed data errors. Olist orders may have multiple payments, vouchers, and payment behaviors that require order-level review.",
                    className="caption",
                ),
                html.Div(
                    className="kpi-grid",
                    children=[
                        html.Div([html.H4("Matched Orders"), html.P(id="kpi-matched-orders")], className="kpi-card"),
                        html.Div([html.H4("Flagged Orders"), html.P(id="kpi-flagged-orders")], className="kpi-card"),
                        html.Div([html.H4("Average Absolute Difference"), html.P(id="kpi-avg-abs-diff")], className="kpi-card"),
                    ],
                ),
                dcc.Graph(id="payment-top-diff-chart"),
                html.P(
                    "This chart highlights the largest order-level payment difference flags. These are review flags, not confirmed data errors.",
                    className="caption",
                ),
                dcc.Graph(id="payment-method-distribution-chart"),
                html.P(
                    "This chart shows the distribution of payment methods in the dataset and provides context for interpreting payment reconciliation behavior.",
                    className="caption",
                ),
            ],
        ),
    ],
)


@app.callback(
    Output("kpi-total-orders", "children"),
    Output("kpi-avg-review", "children"),
    Output("kpi-avg-delay", "children"),
    Output("kpi-avg-freight", "children"),
    Output("delivery-status-review-chart", "figure"),
    Output("fulfillment-delay-breakdown-chart", "figure"),
    Output("review-response-time-chart", "figure"),
    Output("freight-weight-band-chart", "figure"),
    Output("basket-complexity-chart", "figure"),
    Output("seller-outliers-chart", "figure"),
    Output("kpi-matched-orders", "children"),
    Output("kpi-flagged-orders", "children"),
    Output("kpi-avg-abs-diff", "children"),
    Output("payment-top-diff-chart", "figure"),
    Output("payment-method-distribution-chart", "figure"),
    Input("category-dropdown", "value"),
    Input("state-dropdown", "value"),
    Input("min-item-slider", "value"),
)
def refresh_dashboard(category: str, customer_state: str, min_item_count: int):
    params = {
        "category": category,
        "customer_state": customer_state,
        "min_item_count": min_item_count,
    }

    kpi_df = run_query(KPI_QUERY, params)
    delivery_df = run_query(DELIVERY_STATUS_REVIEW_QUERY, params)
    delay_df = run_query(FULFILLMENT_DELAY_BREAKDOWN_QUERY, params)
    review_time_df = run_query(REVIEW_RESPONSE_TIME_QUERY, params)
    weight_df = run_query(FREIGHT_BY_WEIGHT_BAND_QUERY, params)
    basket_df = run_query(BASKET_COMPLEXITY_QUERY, params)
    seller_df = run_query(SELLER_OUTLIERS_QUERY, params)
    recon_kpi_df = run_query(PAYMENT_RECON_KPI_QUERY)
    recon_detail_df = run_query(PAYMENT_TOP_DIFFERENCES_QUERY)
    payment_method_df = run_query(PAYMENT_METHOD_DISTRIBUTION_QUERY)

    kpi_row = kpi_df.iloc[0] if not kpi_df.empty else pd.Series(dtype=float)
    recon_kpi_row = recon_kpi_df.iloc[0] if not recon_kpi_df.empty else pd.Series(dtype=float)

    total_orders = f"{int(kpi_row.get('total_orders', 0)):,}"
    avg_review = f"{kpi_row.get('avg_review_score', 0):.2f}"
    avg_delay_value = float(kpi_row.get("avg_delivery_offset_days", 0) or 0)
    if avg_delay_value < 0:
        avg_delay = f"{abs(avg_delay_value):.2f} days early"
    elif avg_delay_value > 0:
        avg_delay = f"{avg_delay_value:.2f} days late"
    else:
        avg_delay = "On estimate"
    avg_freight = pct_label(kpi_row.get("avg_freight_burden", None), digits=1)

    delivery_fig = px.bar(
        delivery_df,
        x="delivery_status",
        y="avg_review_score",
        text="avg_review_score",
        color_discrete_sequence=[PALETTE["blue"]],
        labels={
            "delivery_status": "Delivery Status",
            "avg_review_score": "Average Review Score",
            "orders_count": "Number of Orders",
        },
        title="Delivery Status vs Average Review Score",
        hover_data={"orders_count": True, "avg_review_score": ":.2f", "delivery_status": True},
    )
    delivery_fig.update_traces(texttemplate="%{text:.2f}", textposition="outside")
    delivery_fig.update_layout(showlegend=False)
    delivery_fig = apply_chart_theme(delivery_fig)

    delay_plot_df = delay_df.copy().melt(
        value_vars=["avg_approval_delay", "avg_carrier_delay", "avg_delivery_delay"],
        var_name="delay_stage",
        value_name="avg_days",
    )
    delay_plot_df["delay_stage"] = delay_plot_df["delay_stage"].map(
        {
            "avg_approval_delay": "Approval Delay",
            "avg_carrier_delay": "Carrier Handoff Delay",
            "avg_delivery_delay": "Delivery Delay",
        }
    )
    delay_fig = px.bar(
        delay_plot_df,
        x="delay_stage",
        y="avg_days",
        color="delay_stage",
        color_discrete_map={
            "Approval Delay": PALETTE["gray"],
            "Carrier Handoff Delay": PALETTE["amber"],
            "Delivery Delay": PALETTE["blue"],
        },
        labels={
            "delay_stage": "Fulfillment Stage",
            "avg_days": "Average Days",
            "delay_stage": "Delay Type",
        },
        title="Average Fulfillment Stage Delay",
        hover_data={"avg_days": ":.2f", "delay_stage": True},
    )
    delay_fig.update_xaxes(title_text="Fulfillment Stage")
    delay_fig.update_yaxes(title_text="Average Days")
    delay_fig.update_layout(showlegend=False)
    delay_fig = apply_chart_theme(delay_fig)

    review_time_fig = px.bar(
        review_time_df,
        x="sentiment_group",
        y="avg_review_response_days",
        color="sentiment_group",
        color_discrete_map={
            "Positive (4-5)": PALETTE["green"],
            "Neutral (3)": PALETTE["amber"],
            "Negative (1-2)": PALETTE["red"],
        },
        labels={
            "sentiment_group": "Sentiment Group",
            "avg_review_response_days": "Average Days",
            "review_count": "Number of Reviews",
        },
        title="Review Response Time by Sentiment Group",
        hover_data={"review_count": True, "avg_review_response_days": ":.2f", "sentiment_group": True},
    )
    review_time_fig.update_layout(showlegend=False)
    review_time_fig = apply_chart_theme(review_time_fig)

    weight_plot_df = weight_df.copy()
    if not weight_plot_df.empty:
        weight_plot_df["avg_freight_burden_pct"] = weight_plot_df["avg_freight_burden"] * 100
    weight_fig = px.bar(
        weight_plot_df,
        x="weight_band",
        y="avg_freight_burden_pct",
        color_discrete_sequence=[PALETTE["blue"]],
        labels={
            "weight_band": "Product Weight Band",
            "avg_freight_burden_pct": "Average Freight Burden (%)",
        },
        title="Freight Burden by Product Weight Band",
        hover_data={"item_count": True, "avg_freight_burden_pct": ":.1f"},
    )
    weight_fig.update_yaxes(title_text="Average Freight Burden (%)")
    weight_fig.update_yaxes(ticksuffix="%")
    weight_fig.update_layout(showlegend=False)
    weight_fig = apply_chart_theme(weight_fig)

    basket_plot_df = basket_df.copy().melt(
        id_vars=["basket_size_group"],
        value_vars=["avg_review_score", "low_review_rate_pct"],
        var_name="metric",
        value_name="value",
    )
    basket_plot_df["metric"] = basket_plot_df["metric"].map(
        {
            "avg_review_score": "Avg Review Score",
            "low_review_rate_pct": "Low Review Rate (%)",
        }
    )
    basket_fig = px.bar(
        basket_plot_df,
        x="basket_size_group",
        y="value",
        color="metric",
        color_discrete_map={
            "Avg Review Score": PALETTE["blue"],
            "Low Review Rate (%)": PALETTE["red"],
        },
        barmode="group",
        labels={
            "basket_size_group": "Basket Size Group",
            "value": "Value",
            "metric": "Legend",
        },
        title="Basket Size Group: Review Score and Low-Review Rate",
    )
    basket_fig.update_layout(legend_title_text="Metric")
    basket_fig.update_yaxes(title_text="Value")
    basket_fig = apply_chart_theme(basket_fig)

    seller_df = seller_df.copy()
    seller_df["avg_freight_to_price_ratio_pct"] = seller_df["avg_freight_to_price_ratio"] * 100
    seller_df["seller_id_short"] = seller_df["seller_id"].astype(str).str.slice(0, 8) + "..."
    seller_fig = px.bar(
        seller_df.sort_values("avg_freight_to_price_ratio_pct", ascending=True),
        x="avg_freight_to_price_ratio_pct",
        y="seller_id_short",
        color_discrete_sequence=[PALETTE["blue"]],
        orientation="h",
        hover_data={
            "seller_id": True,
            "seller_state": True,
            "items_sold": True,
            "avg_item_price": ":.2f",
            "avg_item_freight": ":.2f",
            "avg_freight_to_price_ratio_pct": ":.1f",
            "seller_id_short": False,
        },
        labels={
            "avg_freight_to_price_ratio_pct": "Average Freight Burden (%)",
            "seller_id_short": "Seller",
            "seller_state": "Seller State",
            "items_sold": "Items Sold",
            "avg_item_price": "Average Item Price",
            "avg_item_freight": "Average Item Freight",
        },
        title="Top Sellers by Average Freight Burden",
    )
    seller_fig.update_yaxes(
        categoryorder="array",
        categoryarray=seller_df.sort_values("avg_freight_to_price_ratio_pct", ascending=True)["seller_id_short"].tolist(),
    )
    seller_fig.update_xaxes(ticksuffix="%")
    seller_fig.update_layout(showlegend=False)
    seller_fig = apply_chart_theme(seller_fig, height=700)

    matched_orders = f"{int(recon_kpi_row.get('matched_orders', 0)):,}"
    flagged_orders = f"{int(recon_kpi_row.get('flagged_orders', 0)):,}"
    avg_abs_diff = f"{recon_kpi_row.get('avg_abs_difference', 0):.2f}"

    payment_bar_df = recon_detail_df.copy()
    if not payment_bar_df.empty:
        payment_bar_df = payment_bar_df.sort_values("abs_difference", ascending=False).head(10)
        payment_bar_df["order_id_short"] = payment_bar_df["order_id"].astype(str).str.slice(0, 8) + "..."

    payment_top_diff_fig = px.bar(
        payment_bar_df.sort_values("abs_difference", ascending=True) if not payment_bar_df.empty else payment_bar_df,
        x="abs_difference",
        y="order_id_short",
        orientation="h",
        color_discrete_sequence=[PALETTE["red"]],
        labels={
            "abs_difference": "Absolute Payment Difference",
            "order_id_short": "Order ID",
        },
        hover_data={
            "order_id": True,
            "item_freight_total": ":.2f",
            "payment_total": ":.2f",
            "difference": ":.2f",
            "abs_difference": ":.2f",
            "order_id_short": False,
        },
        title="Top Payment Difference Amounts",
    )
    payment_top_diff_fig.update_layout(showlegend=False)
    payment_top_diff_fig = apply_chart_theme(payment_top_diff_fig)

    payment_method_fig = px.pie(
        payment_method_df,
        names="payment_type",
        values="payment_count",
        hole=0.45,
        color_discrete_sequence=[PALETTE["blue"], PALETTE["gray"], PALETTE["amber"], PALETTE["green"], PALETTE["orange"]],
        labels={
            "payment_type": "Payment Method",
            "payment_count": "Number of Payments",
        },
        title="Payment Method Distribution",
        hover_data={"payment_count": True, "payment_pct": True},
    )
    payment_method_fig.update_traces(textinfo="percent+label", hovertemplate="%{label}<br>Count: %{value}<br>Share: %{customdata[0]}%<extra></extra>")
    payment_method_fig = apply_chart_theme(payment_method_fig)

    return (
        total_orders,
        avg_review,
        avg_delay,
        avg_freight,
        delivery_fig,
        delay_fig,
        review_time_fig,
        weight_fig,
        basket_fig,
        seller_fig,
        matched_orders,
        flagged_orders,
        avg_abs_diff,
        payment_top_diff_fig,
        payment_method_fig,
    )


if __name__ == "__main__":
    app.run(debug=True)
