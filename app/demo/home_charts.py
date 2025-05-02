import pandas as pd # type: ignore
import plotly.express as px # type: ignore
import plotly.graph_objects as go # type: ignore

def generate_staff_donut_chart(df_staff: pd.DataFrame, session: str) -> str:
    """
    Generates a donut chart for staff positions in a given session and returns it as an HTML string.
    """
    df_session = df_staff[df_staff["session"] == session]
    position_counts = df_session.groupby("position")["count"].sum().reset_index()
    total_sum = df_session["count"].sum()

    fig = px.pie(
        position_counts,
        names="position",
        values="count",
        hole=0.7,
        color_discrete_sequence=px.colors.sequential.PuRd
    )
    fig.add_annotation(
        x=0.5,
        y=0.5,
        text=f'{total_sum}',
        showarrow=False,
        font=dict(size=25)
    )
    return fig.to_html(include_plotlyjs='False', full_html=False)

def generate_student_donut_chart(df_students: pd.DataFrame, session: str) -> str:
    """
    Generates a donut chart for student types in a given session and returns it as an HTML string.
    """
    df_session = df_students[df_students["session"] == session]
    type_counts = df_session.groupby("type")["count"].sum().reset_index()
    total_students = df_session["count"].sum()

    fig = px.pie(
        type_counts,
        names="type",
        values="count",
        hole=0.7,
        color_discrete_sequence=px.colors.sequential.Bluyl
    )
    fig.add_annotation(
        x=0.5,
        y=0.5,
        text=f"{total_students:,}",
        showarrow=False,
        font=dict(size=25)
    )
    return fig.to_html(include_plotlyjs='False', full_html=False)

def generate_staff_trend_chart(df_staff: pd.DataFrame) -> str:
    """
    Generates a dual-axis chart for staff trends over sessions and returns it as an HTML string.
    """
    total_staff_per_year = df_staff.groupby("session")["count"].sum().reset_index()
    positions_of_interest = [
        "Assistant lecturer",
        "Lecturer 2",
        "Lecturer 1",
        "Associate professor",
        "Professor"
    ]
    position_trends = (
        df_staff[df_staff["position"].isin(positions_of_interest)]
        .groupby(["session", "position"])["count"]
        .sum()
        .reset_index()
    )

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=total_staff_per_year["session"],
        y=total_staff_per_year["count"],
        name="Total Staff",
        marker_color="rgb(231, 225, 239)",
        yaxis="y1"
    ))

    colors = px.colors.sequential.Jet
    color_mapping = {position: colors[i] for i, position in enumerate(positions_of_interest)}

    for position in positions_of_interest:
        pos_data = position_trends[position_trends["position"] == position]
        fig.add_trace(go.Scatter(
            x=pos_data["session"],
            y=pos_data["count"],
            mode="lines+markers",
            name=position,
            yaxis="y2",
            line=dict(color=color_mapping[position], width=2),
            marker=dict(size=6, color=color_mapping[position])
        ))

    fig.update_layout(
        xaxis=dict(title="Academic Session"),
        yaxis=dict(title="Total Staff Count", side="left", showgrid=False),
        yaxis2=dict(title="Position Count", overlaying="y", side="right", showgrid=False),
        legend=dict(orientation="v", x=1.06, y=0, xanchor="left", title=""),
        barmode="overlay",
        template="plotly_white"
    )
    return fig.to_html(include_plotlyjs='False', full_html=False)

def generate_student_trend_chart(df_students: pd.DataFrame) -> str:
    """
    Generates a line chart for student trends over sessions and returns it as an HTML string.
    """
    aggregated_df = df_students.groupby(['session', 'type'])['count'].sum().reset_index()
    aggregated_df['session'] = pd.Categorical(
        aggregated_df['session'],
        categories=sorted(aggregated_df['session'].unique()),
        ordered=True
    )

    fig = px.line(
        aggregated_df,
        x='session',
        y='count',
        color='type',
        markers=True,
        labels={'session': '', 'count': 'Number of Students', 'type': 'Student Type'},
        color_discrete_sequence=px.colors.sequential.Bluyl
    )
    fig.update_layout(
        xaxis_tickangle=-45,
        xaxis=dict(showgrid=False),
        yaxis=dict(side="left", showgrid=False),
        plot_bgcolor='rgba(0,0,0,0)',
        legend=dict(orientation="v", x=.8, y=0, xanchor="left")
    )
    return fig.to_html(include_plotlyjs='False', full_html=False)

