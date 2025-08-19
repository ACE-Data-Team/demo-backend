import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

def generate_total_count(df_students: pd.DataFrame, session: str = 2022/2023, student_type: str = "Undergraduate") -> str:
    # Check for required columns
    required_columns = {"session", "type"}
    if not required_columns.issubset(df_students.columns):
        print("Error: Data missing required columns")
        return f"Error: Data missing required columns {required_columns - set(df_students.columns)}"

    # Filter for session and type
    df_session = df_students[df_students["session"] == session]
    if df_session.empty:
        return f"<p>No data available for session '{session}'.</p>"

    students = df_session[df_session["type"] == student_type]
    if students.empty:
        return f"<p>No {student_type} student data available for session '{session}'.</p>"

    total_count = students["count"].sum()

    fig = go.Figure(data=[
        go.Bar(
            x=[f"Total {student_type} Students"],
            y=[total_count],
            marker_color='indianred'
        )
    ])

    fig.update_layout(
        title=f"Total {student_type} Students in {session}",
        yaxis_title="Count",
        xaxis_title="",
        template="plotly_white"
    )

    return fig.to_html(include_plotlyjs=False, full_html=False)


def generate_donut_chart(df_enrollment: pd.DataFrame, session: str) -> str:
    """
    Generates a minimal donut chart showing the total enrollment count for a given session.
    """
    df_session = df_enrollment[df_enrollment["session"] == session]

    # Compute total count for the session
    if "count" in df_session.columns:
        total_students = int(df_session["count"].sum())
    else:
        # If there is no 'count' column, assume one row per unit and count rows
        total_students = int(df_session.shape[0])

    # Placeholder data for a single-segment donut
    fig = px.pie(
        names=["Total"],  # single segment label
        values=[total_students],
        hole=0.7,
        color_discrete_sequence=px.colors.sequential.Blues
    )

    fig.add_annotation(
        x=0.5,
        y=0.5,
        text=f"{total_students:,}",
        showarrow=False,
        font=dict(size=25)
    )

    return fig.to_html(include_plotlyjs=False, full_html=False)

def student_distribution_by_type(df_enrollment: pd.DataFrame, type: str) -> str:
    required_columns = [type]
    if not required_columns.issubset(df_enrollment.columns):
        print('Errro: Data missing required columns')
        return f"Error: Data Missing required Columns {required_columns - set(df_enrollment.columns)}"
    
def student_gender_barchart():
    pass