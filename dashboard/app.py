import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

CVD_SAFE = px.colors.qualitative.Safe
CVD_SEQUENTIAL = "Viridis"

@st.cache_data(show_spinner=False)
def load_data(path="data/players_22.csv"):
    df = pd.read_csv(path, low_memory=False)

    df = df.rename(columns={
        "player_positions": "player_position",
        "nationality_name": "nationality",
        "club_name": "club",
        "league_name": "league",
        "release_clause_eur": "release_clause",
    })

    drop_cols = [
        "player_url",
        "player_face_url",
        "club_logo_url",
        "club_flag_url",
        "nation_logo_url",
        "nation_flag_url",
        "club_loaned_from",
        "player_tags",
        "player_traits",
    ]
    df = df.drop(columns=[c for c in drop_cols if c in df.columns])

    df["player_position"] = df["player_position"].fillna("Unknown").astype(str)
    df["primary_position"] = (
        df["player_position"].str.split(",").str[0].str.strip().replace("", "Unknown")
    )

    df["club"] = df["club"].fillna("Unknown")
    df["nationality"] = df["nationality"].fillna("Unknown")
    df["work_rate"] = df["work_rate"].fillna("Unknown")
    df["preferred_foot"] = df["preferred_foot"].fillna("Unknown")
    df["body_type"] = df["body_type"].fillna("Unknown")

    convert_numeric = [
        "overall",
        "potential",
        "value_eur",
        "wage_eur",
        "age",
        "height_cm",
        "weight_kg",
        "release_clause",
        "pace",
        "shooting",
        "passing",
        "dribbling",
        "defending",
        "physic",
        "movement_acceleration",
        "movement_sprint_speed",
        "movement_agility",
        "movement_reactions",
        "movement_balance",
        "power_shot_power",
        "power_jumping",
        "power_stamina",
        "power_strength",
        "power_long_shots",
        "mentality_aggression",
        "mentality_interceptions",
        "mentality_positioning",
        "mentality_vision",
        "mentality_penalties",
        "mentality_composure",
        "defending_marking_awareness",
        "defending_standing_tackle",
        "defending_sliding_tackle",
        "goalkeeping_diving",
        "goalkeeping_handling",
        "goalkeeping_kicking",
        "goalkeeping_positioning",
        "goalkeeping_reflexes",
        "goalkeeping_speed",
        "league_level",
    ]

    for col in convert_numeric:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df["league_level"] = df["league_level"].fillna(0).astype(int)
    df["league_level_label"] = df["league_level"].replace({0: "Unknown"}).astype(str)
    df["league_level_label"] = df["league_level_label"].replace({"0": "Unknown"})
    df["league_level_label"] = np.where(
        df["league_level_label"] == "Unknown",
        "Unknown",
        "Level " + df["league_level_label"],
    )

    df = df.fillna({"value_eur": 0, "wage_eur": 0, "release_clause": 0})
    medians = df[convert_numeric].median()
    df[convert_numeric] = df[convert_numeric].fillna(medians)

    df["value_m"] = (df["value_eur"] / 1_000_000).round(2)
    df["wage_k"] = (df["wage_eur"] / 1_000).round(1)
    df["combined_score"] = df["pace"] + df["shooting"] + df["passing"]
    df["defensive_strength"] = df["defending"] + df["physic"]
    df["attack_strength"] = df["pace"] + df["shooting"] + df["dribbling"]
    df["playmaking"] = df["passing"] + df["vision"] if "vision" in df.columns else df["passing"]

    return df


def style_figure(fig):
    fig.update_layout(
        template="plotly_white",
        font=dict(family="Arial", size=12, color="#111111"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        margin=dict(l=50, r=30, t=70, b=40),
        plot_bgcolor="white",
        paper_bgcolor="white",
    )
    fig.update_xaxes(showgrid=True, gridcolor="#E5E5E5", zeroline=False)
    fig.update_yaxes(showgrid=True, gridcolor="#E5E5E5", zeroline=False)
    return fig


def build_top_position_line(df):
    top_positions = df["primary_position"].value_counts().nlargest(6).index.tolist()
    trend = (
        df[df["primary_position"].isin(top_positions)]
        .groupby(["age", "primary_position"]) ["overall"]
        .mean()
        .reset_index()
    )
    fig = px.line(
        trend,
        x="age",
        y="overall",
        color="primary_position",
        markers=True,
        color_discrete_sequence=CVD_SAFE,
        labels={"overall": "Average Overall", "age": "Age", "primary_position": "Position"},
        title="Average Overall Rating by Age for Leading Positions",
    )
    return style_figure(fig)


def build_value_wage_scatter(df):
    fig = px.scatter(
        df,
        x="value_m",
        y="wage_k",
        color="preferred_foot",
        size="overall",
        hover_data=["short_name", "club", "nationality", "primary_position", "overall", "potential"],
        color_discrete_sequence=CVD_SAFE,
        labels={"value_m": "Market Value (€M)", "wage_k": "Wage (€K)", "preferred_foot": "Preferred Foot"},
        title="Market Value vs Wage for Players by Quality",
    )
    fig.update_traces(marker=dict(opacity=0.85, line=dict(width=0.5, color="#444444")))
    return style_figure(fig)


def build_league_skill_profile(df):
    league = df.groupby("league_level_label")[ ["attack_strength", "playmaking", "defensive_strength"] ].mean().reset_index()
    league_melt = league.melt(id_vars="league_level_label", value_vars=["attack_strength", "playmaking", "defensive_strength"], var_name="Skill Group", value_name="Average Score")
    fig = px.bar(
        league_melt,
        x="league_level_label",
        y="Average Score",
        color="Skill Group",
        barmode="group",
        color_discrete_sequence=CVD_SAFE,
        labels={"league_level_label": "League Level", "Average Score": "Mean Score"},
        title="Comparing Attacking, Playmaking, and Defensive Strength Across League Levels",
    )
    return style_figure(fig)


def build_club_midfield_scatter(df):
    midfield = df[df["primary_position"].isin(["CM", "CDM", "CAM", "LM", "RM"])]
    club_stats = (
        midfield.groupby("club")
        .agg(average_passing=("passing", "mean"), average_dribbling=("dribbling", "mean"), overall=("overall", "mean"), player_count=("sofifa_id", "count"))
        .reset_index()
        .sort_values(by="overall", ascending=False)
        .head(12)
    )
    fig = px.scatter(
        club_stats,
        x="average_passing",
        y="average_dribbling",
        size="player_count",
        color="overall",
        color_continuous_scale=CVD_SEQUENTIAL,
        hover_data=["club", "overall", "player_count"],
        labels={"average_passing": "Average Passing", "average_dribbling": "Average Dribbling", "overall": "Average Overall"},
        title="Top Clubs by Midfield Passing and Dribbling Profiles",
    )
    return style_figure(fig)


def build_work_rate_box(df):
    work_df = df[ df["work_rate"] != "Unknown" ].copy()
    fig = go.Figure()
    for metric, label, color in [ ("pace", "Pace", CVD_SAFE[0]), ("power_stamina", "Stamina", CVD_SAFE[1]) ]:
        fig.add_trace(
            go.Box(
                x=work_df["work_rate"],
                y=work_df[metric],
                name=label,
                marker_color=color,
                boxmean=True,
                hovertemplate="%{x}<br>%{y:.1f}",
            )
        )
    fig.update_layout(
        title="Pace and Stamina Distributions by Work Rate Category",
        xaxis_title="Work Rate",
        yaxis_title="Attribute Value",
    )
    return style_figure(fig)


def build_nation_skill_radar(df):
    top_nations = df["nationality"].value_counts().nlargest(5).index.tolist()
    radar_df = df[df["nationality"].isin(top_nations)]
    skill_dims = ["overall", "potential", "pace", "passing", "defending"]
    radar = (
        radar_df.groupby("nationality")[skill_dims].mean().reset_index()
    )
    fig = go.Figure()
    for idx, row in radar.iterrows():
        fig.add_trace(
            go.Scatterpolar(
                r=row[skill_dims].tolist() + [row[skill_dims].iloc[0]],
                theta=skill_dims + [skill_dims[0]],
                fill="toself",
                name=row["nationality"],
                marker=dict(color=CVD_SAFE[idx]),
            )
        )
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100], gridcolor="#E5E5E5")),
        title="Elite Nation Profiles: Average Skill Attributes for Top Countries",
    )
    return style_figure(fig)


def build_goalkeeper_profile(df):
    keepers = df[df["primary_position"] == "GK"].copy()
    if keepers.empty:
        return go.Figure()

    keeper_agg = (
        keepers.groupby("league_level_label")[ ["goalkeeping_diving", "goalkeeping_handling", "goalkeeping_kicking", "goalkeeping_positioning", "goalkeeping_reflexes"] ].mean().reset_index()
    )
    keeper_melt = keeper_agg.melt(id_vars="league_level_label", var_name="GK Skill", value_name="Average Value")
    fig = px.bar(
        keeper_melt,
        x="league_level_label",
        y="Average Value",
        color="GK Skill",
        barmode="group",
        color_discrete_sequence=CVD_SAFE,
        labels={"league_level_label": "League Level", "Average Value": "Average Skill"},
        title="Goalkeeper Skill Profiles by League Level",
    )
    return style_figure(fig)


def build_combined_score_scatter(df):
    top_players = df.sort_values(by="combined_score", ascending=False).head(18)
    fig = px.scatter(
        top_players,
        x="value_m",
        y="combined_score",
        color="primary_position",
        size="overall",
        hover_data=["short_name", "club", "overall", "potential"],
        color_discrete_sequence=CVD_SAFE,
        labels={"value_m": "Market Value (€M)", "combined_score": "Attack + Passing + Pace"},
        title="Players with Highest Combined Scoring, Passing, and Pace Profiles",
    )
    fig.update_traces(marker=dict(line=dict(width=1, color="#222222")))
    return style_figure(fig)


def build_age_potential_bubble(df):
    sample = df.sort_values(by="potential", ascending=False).head(600)
    fig = px.scatter(
        sample,
        x="age",
        y="overall",
        size="potential",
        color="league_level_label",
        color_discrete_sequence=CVD_SAFE,
        hover_data=["short_name", "club", "nationality", "potential"],
        labels={"age": "Age", "overall": "Overall Rating", "league_level_label": "League Level"},
        title="Age, Overall Rating, and Potential: Bubble View of Development Opportunity",
    )
    return style_figure(fig)


def build_top_players_bar(df):
    top_players = df.sort_values(by="overall", ascending=False).head(15)
    fig = px.bar(
        top_players,
        x="overall",
        y="short_name",
        orientation="h",
        color="primary_position",
        color_discrete_sequence=CVD_SAFE,
        hover_data=["club", "nationality", "potential"],
        labels={"overall": "Overall Rating", "short_name": "Player"},
        title="Top 15 Players by Overall Rating",
    )
    fig.update_layout(yaxis={'categoryorder':'total ascending'})
    return style_figure(fig)


def main():
    st.set_page_config(
        page_title="Football Analytics Dashboard",
        page_icon="⚽",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.title("Football Analytics Dashboard")
    st.markdown(
        "Explore 10 multi-dimensional questions about FIFA 22 player performance, market value, and development potential with interactive Plotly visuals."
    )

    df = load_data()

    with st.sidebar:
        st.header("Filters")
        position_options = ["All"] + sorted(df["primary_position"].unique())
        selected_position = st.selectbox("Primary Position", position_options, index=0)

        club_options = ["All"] + df["club"].value_counts().head(60).index.tolist()
        selected_club = st.selectbox("Club", club_options, index=0)

        nation_options = ["All"] + df["nationality"].value_counts().head(60).index.tolist()
        selected_nation = st.selectbox("Nationality", nation_options, index=0)

        age_min = int(df["age"].min())
        age_max = int(df["age"].max())
        selected_age = st.slider("Age Range", age_min, age_max, (age_min, age_max), step=1)

        selected_league = st.multiselect(
            "League Level",
            sorted(df["league_level_label"].unique()),
            default=[label for label in sorted(df["league_level_label"].unique()) if label != "Unknown"],
        )

        sample_size = st.slider("Records to sample", 200, 2000, 1000, step=100)
        st.write("Data rows after filtering will display below.")

    filtered = df[
        (df["age"] >= selected_age[0])
        & (df["age"] <= selected_age[1])
        & (df["league_level_label"].isin(selected_league))
    ]
    if selected_position != "All":
        filtered = filtered[filtered["primary_position"] == selected_position]
    if selected_club != "All":
        filtered = filtered[filtered["club"] == selected_club]
    if selected_nation != "All":
        filtered = filtered[filtered["nationality"] == selected_nation]

    filtered = filtered.head(sample_size)

    st.subheader("Filtered Dataset Preview")
    st.dataframe(
        filtered[
            ["short_name", "primary_position", "overall", "potential", "age", "club", "nationality", "value_m", "wage_k", "work_rate"]
        ].reset_index(drop=True),
        height=260,
    )

    st.markdown("---")
    st.header("1. How does rating evolve with age across position groups?")
    st.plotly_chart(build_top_position_line(filtered), use_container_width=True)

    st.markdown("---")
    st.header("2. What is the market value / wage relationship for high-quality players?")
    st.plotly_chart(build_value_wage_scatter(filtered), use_container_width=True)

    st.markdown("---")
    st.header("3. How do offensive, playmaking, and defensive skill groups differ by league level?")
    st.plotly_chart(build_league_skill_profile(filtered), use_container_width=True)

    st.markdown("---")
    st.header("4. Which clubs lead in midfield passing and dribbling for top performers?")
    st.plotly_chart(build_club_midfield_scatter(filtered), use_container_width=True)

    st.markdown("---")
    st.header("5. How does work rate impact pace and stamina distributions?")
    st.plotly_chart(build_work_rate_box(filtered), use_container_width=True)

    st.markdown("---")
    st.header("6. What do the top nations’ skill profiles look like?")
    st.plotly_chart(build_nation_skill_radar(filtered), use_container_width=True)

    st.markdown("---")
    st.header("7. How are goalkeeper skill profiles distributed by league level?")
    st.plotly_chart(build_goalkeeper_profile(filtered), use_container_width=True)

    st.markdown("---")
    st.header("8. Which players have the strongest combined pace-shooting-passing profile?")
    st.plotly_chart(build_combined_score_scatter(filtered), use_container_width=True)

    st.markdown("---")
    st.header("9. Where are the highest-potential players located by age and overall rating?")
    st.plotly_chart(build_age_potential_bubble(filtered), use_container_width=True)

    st.markdown("---")
    st.header("10. Who are the top-rated players in the current filter selection?")
    st.plotly_chart(build_top_players_bar(filtered), use_container_width=True)

    st.markdown("---")
    st.caption(
        "This Streamlit dashboard is built with Plotly for publication-ready, colorblind-safe analytics and supports interactive filtering across age, league, club, position, and nationality."
    )

if __name__ == "__main__":
    main()
