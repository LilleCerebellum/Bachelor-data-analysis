import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import norm
import streamlit as st

st.set_page_config(layout="centered")

filename2026 = "Akutafd-010126-310826 (version 2).xlsx"
filename2025 = "Akutafd datasæt 2025.xlsx"


df1 = pd.read_excel(
    filename2026,
    sheet_name="Data Akutafd-010126-310826"
)
df2 = pd.read_excel(
    filename2025,
    sheet_name="Akutafd-010125-311225"
)

df = pd.DataFrame()

valgAAR = st.selectbox(
    "2025 eller 2026",
    options=["Begge", "2025", "2026"]
)

if valgAAR == "Begge":
    df = pd.concat([df1, df2], ignore_index=True)
elif valgAAR == "2025":
    df = df2
elif valgAAR == "2026":
    df = df1




# Konverter datoer og klokkeslæt
dato_cols = [
    "Pl.prvt.dato", "Prvt.dato", "Modtag.dato",
    "Analysedato", "Godk.dato"
]

kl_cols = [
    "Pl.prvt.kl", "Prvt.kl", "Modtag.kl",
    "Ana.kl.", "Godk.kl."
]



for col in dato_cols:
    df[col] = pd.to_datetime(df[col], format="%d/%m/%Y", errors="coerce")

for col in kl_cols:
    df[col] = pd.to_timedelta(df[col].astype(str), errors="coerce")

df["UgedagPrvt"] = df["Prvt.dato"].dt.day_name()

df["Pl.prvt_datetime"] = df["Pl.prvt.dato"] + df["Pl.prvt.kl"]
df["Prvt_datetime"] = df["Prvt.dato"] + df["Prvt.kl"]
df["Modtag_datetime"] = df["Modtag.dato"] + df["Modtag.kl"]
df["Analyse_datetime"] = df["Analysedato"] + df["Ana.kl."]
df["Godk_datetime"] = df["Godk.dato"] + df["Godk.kl."]





df["Planlagt til prøvetagning"] = (
    df["Prvt_datetime"] - df["Pl.prvt_datetime"]
).dt.total_seconds() / 60

df["Prøvetagning til modtagelse"] = (
    df["Modtag_datetime"] - df["Prvt_datetime"]
).dt.total_seconds() / 60

df["Modtagelse til analyse"] = (
    df["Analyse_datetime"] - df["Modtag_datetime"]
).dt.total_seconds() / 60

df["Analyse til godkendelse"] = (
    df["Godk_datetime"] - df["Analyse_datetime"]
).dt.total_seconds() / 60

df["Flowtid_min"] = (
    df["Godk_datetime"] - df["Prvt_datetime"]
).dt.total_seconds() / 60

df["Flowtid_timer"] = df["Flowtid_min"] / 60



df_filtered = df.copy()


df_filtered = df_filtered[
    (df_filtered["Prøvetagning til modtagelse"] >= 1) &
    (df_filtered["Modtagelse til analyse"] >= 1)
]


# Filtrering
valgPRVT_STED = st.selectbox(
    "Vælg Prvt.stedgeo",
    options=["Begge", "Tages nu", "Tages på runde"]
)

if valgPRVT_STED == "Begge":
    df_filtered = df_filtered[
        df_filtered["Prvt.stedgeo"].isin(["Tages nu", "Tages på runde"])
    ]
elif valgPRVT_STED == "Tages nu":
    df_filtered = df_filtered[df_filtered]
else:
    df_filtered = df_filtered[df_filtered["Prvt.stedgeo"] == "Tages på runde"]



valgKVNT_NAVN = st.selectbox(
    "Vælg Kvnt.navn",
    options=["Alle", "Kreatinin;P", "C-reaktivt protein [CRP];P", "Leukocytter;B"]
)

if valgKVNT_NAVN == "Alle":
    df_filtered = df_filtered[
        df_filtered["Kvnt.navn"].isin(["Kreatinin;P", "C-reaktivt protein [CRP];P", "Leukocytter;B"])
    ]
elif valgKVNT_NAVN == "Kreatinin;P":
    df_filtered = df_filtered[df_filtered["Kvnt.navn"] == "Kreatinin;P"]
elif valgKVNT_NAVN == "C-reaktivt protein [CRP];P":
    df_filtered = df_filtered[df_filtered["Kvnt.navn"] == "C-reaktivt protein [CRP];P"]
elif valgKVNT_NAVN == "Leukocytter;B":
    df_filtered = df_filtered[df_filtered["Kvnt.navn"] == "Leukocytter;B"]



df_filtered = df_filtered.dropna(
    subset=[
        "Pl.prvt_datetime", "Prvt_datetime", "Modtag_datetime",
        "Analyse_datetime", "Godk_datetime"
    ]
)

#filter extremer vaek for flowtid
n = 20

lower = df_filtered["Flowtid_timer"].quantile(0.15)
upper = df_filtered["Flowtid_timer"].quantile(0.85)

df_filtered = df_filtered[
    (df_filtered["Flowtid_timer"] >= lower) &
    (df_filtered["Flowtid_timer"] <= upper)
]




alder_min, alder_max= st.slider("Vælg alder", min_value=0, max_value=120, value=(1, 120), step=1)

df_filtered = df_filtered[
    df_filtered["Alder"].between(alder_min, alder_max)
]


st.dataframe(df_filtered)

# Antal analyser per ugedag
st.write("Antal analyser per ugedag")

ugedags_raekkefoelge = [
    "Monday", "Tuesday", "Wednesday", "Thursday",
    "Friday", "Saturday", "Sunday"
]

sorteret_counts = (
    df_filtered["UgedagPrvt"]
    .value_counts()
    .reindex(ugedags_raekkefoelge, fill_value=0)
)

st.bar_chart(sorteret_counts, use_container_width=True, sort=False)


# Normalfordeling: prøvetagning -> modtagelse
st.write("Normalfordelingsplot af Tids difference fra prøvetagning til modtagelse")

mu1 = df_filtered["Prøvetagning til modtagelse"].mean()
std1 = df_filtered["Prøvetagning til modtagelse"].std()

fig, ax = plt.subplots()

x = np.linspace(mu1 - 4 * std1, mu1 + 4 * std1, 300)
p = norm.pdf(x, loc=mu1, scale=std1)

ax.plot(
    x,
    p,
    color="crimson",
    linewidth=2,
    label=f"Normalfordeling\n(μ = {mu1:.2f}, σ = {std1:.2f})",
)

ax.set_title("PRVT kl -> modtag kl", fontsize=14)
ax.set_xlabel("Tidsforskel (minutter)", fontsize=12)
ax.set_ylabel("Tæthed (Density)", fontsize=12)
ax.legend()
ax.grid(axis="y", linestyle="--", alpha=0.7)

st.pyplot(fig)


# Normalfordeling: modtagelse af prøve -> analyse påbegyndt
st.write("Normalfordelingsplot af Tids difference fra Modtagelse til Analyse")

mu2 = df_filtered["Modtagelse til analyse"].mean()
std2 = df_filtered["Modtagelse til analyse"].std()

fig2, ax2 = plt.subplots()

x2 = np.linspace(mu2 - 4 * std2, mu2 + 4 * std2, 300)
p2 = norm.pdf(x2, loc=mu2, scale=std2)

ax2.plot(
    x2,
    p2,
    color="crimson",
    linewidth=2,
    label=f"Normalfordeling\n(μ = {mu2:.2f}, σ = {std2:.2f})",
)

ax2.set_title("modtag kl -> analyse kl", fontsize=14)
ax2.set_xlabel("Tidsforskel (minutter)", fontsize=12)
ax2.set_ylabel("Tæthed (Density)", fontsize=12)
ax2.legend()
ax2.grid(axis="y", linestyle="--", alpha=0.7)

st.pyplot(fig2)





# Gennemsnitlig tid pr. deltrin
st.subheader("Gennemsnitlig tid pr. deltrin")

trin_cols = [
    "Planlagt til prøvetagning",
    "Prøvetagning til modtagelse",
    "Modtagelse til analyse",
    "Analyse til godkendelse"
]

gennemsnit = df_filtered[trin_cols].mean() / 60

fig_steps, ax_steps = plt.subplots()

ax_steps.barh(
    gennemsnit.index,
    gennemsnit.values,
    color="seagreen"
)

ax_steps.set_xlabel("Gennemsnitlig tid (timer)")
ax_steps.set_title("Hvor lang tid bruges i hvert trin?")
ax_steps.grid(axis="x", linestyle="--", alpha=0.5)

st.pyplot(fig_steps)



# Fuld forløb
st.subheader("Fuld forløb. tid Prøvetagning til godkendelse")

flowtid = df_filtered["Flowtid_timer"].dropna()


fig3, ax3 = plt.subplots()

ax3.hist(
    flowtid,
    bins=20,
    color="steelblue",
    edgecolor="white"
)

ax3.set_xlabel("Tid fra prøvetagning til godkendelse (timer)")
ax3.set_ylabel("Antal prøver")
ax3.set_title("Fordeling af Flowtid")
ax3.grid(axis="y", linestyle="--", alpha=0.5)

st.pyplot(fig3)



import altair as alt


DATA = [
    {
        "Interessent": "Cheflæge for AKA",
        "Rolle i projektet": (
            "Beslutningstager, giver adgang til afdelingen "
            "og vurderer løsningsforslag"
        ),
        "Indflydelse": 5,
        "Interesse": 5,
        "Prioritet": "Meget høj",
        "Håndtering": (
            "Tæt dialog, løbende status, inddrages i valg "
            "og validering af løsning"
        ),
    },
    {
        "Interessent": "Overbioanalytiker",
        "Rolle i projektet": (
            "Ekspert i laboratoriets arbejdsgange, svartider og flaskehalse"
        ),
        "Indflydelse": 5,
        "Interesse": 5,
        "Prioritet": "Meget høj",
        "Håndtering": (
            "Nøgleinformant, inddrages aktivt i kortlægning og design"
        ),
    },
    {
        "Interessent": "Sygeplejersker på AKA",
        "Rolle i projektet": (
            "Udfører prøvetagning og patientkoordinering; kender daglig praksis"
        ),
        "Indflydelse": 4,
        "Interesse": 5,
        "Prioritet": "Høj",
        "Håndtering": (
            "Interviews og observationer; deres arbejdsbyrde "
            "og praktiske muligheder skal respekteres"
        ),
    },
    {
        "Interessent": "Bioanalytikere",
        "Rolle i projektet": (
            "Udfører analyse, validering og frigivelse af svar"
        ),
        "Indflydelse": 4,
        "Interesse": 4,
        "Prioritet": "Høj",
        "Håndtering": (
            "Interview og proceskortlægning; inddrages "
            "ved ændringer i laboratorieflow"
        ),
    },
    {
        "Interessent": "Læger på AKA",
        "Rolle i projektet": (
            "Bruger blodprøvesvar til klinisk beslutningstagning"
        ),
        "Indflydelse": 4,
        "Interesse": 4,
        "Prioritet": "Høj",
        "Håndtering": (
            "Kort interview eller spørgeskema; sikrer at løsningen "
            "understøtter klinisk praksis"
        ),
    },
    {
        "Interessent": "Patienter",
        "Rolle i projektet": (
            "Direkte påvirket af ventetid, opholdstid og behandlingsforløb"
        ),
        "Indflydelse": 2,
        "Interesse": 5,
        "Prioritet": "Mellem",
        "Håndtering": (
            "Representeres gennem anonymiserede tidsdata og observationer; "
            "ingen direkte belastende inddragelse"
        ),
    },
    {
        "Interessent": "Afdelingsledelse / sygehusledelse",
        "Rolle i projektet": (
            "Godkender ressourcebrug og eventuel implementering"
        ),
        "Indflydelse": 5,
        "Interesse": 3,
        "Prioritet": "Høj",
        "Håndtering": (
            "Informeres via kontaktperson og slutrapport; "
            "løsning skal være ressourceneutral"
        ),
    },
    {
        "Interessent": "Laboratorieledelse",
        "Rolle i projektet": (
            "Ansvarlig for kapacitet, bemanding og kvalitet i analyseenheden"
        ),
        "Indflydelse": 4,
        "Interesse": 4,
        "Prioritet": "Høj",
        "Håndtering": (
            "Samarbejde gennem overbioanalytiker; informeres om anbefalinger"
        ),
    },
    {
        "Interessent": "IT / laboratorieinformationssystem",
        "Rolle i projektet": (
            "Leverer eller begrænser adgang til tidsstempler og data"
        ),
        "Indflydelse": 3,
        "Interesse": 2,
        "Prioritet": "Mellem",
        "Håndtering": (
            "Kun kontakt ved dataproblemer eller behov for ny dataudtrækning"
        ),
    },
]

st.title("Interessentanalyse – AKA")


st.subheader("Interessenttabel")

edited = st.data_editor(
    pd.DataFrame(DATA),
    key="interessent_editor",
    hide_index=True,
    use_container_width=True,
    height=460,
    column_config={
        "Interessent": st.column_config.TextColumn(
            "Interessent", width="medium", required=True
        ),
        "Rolle i projektet": st.column_config.TextColumn(
            "Rolle i projektet", width="large"
        ),
        "Indflydelse": st.column_config.NumberColumn(
            "Indflydelse (1–5)",
            min_value=1,
            max_value=5,
            step=1,
            required=True,
        ),
        "Interesse": st.column_config.NumberColumn(
            "Interesse (1–5)",
            min_value=1,
            max_value=5,
            step=1,
            required=True,
        ),
        "Prioritet": st.column_config.SelectboxColumn(
            "Prioritet",
            options=["Lav", "Mellem", "Høj", "Meget høj"],
            required=True,
        ),
        "Håndtering": st.column_config.TextColumn(
            "Håndtering", width="large"
        ),
    },
)


st.subheader("Filtrér visningen")

selected_priorities = st.multiselect(
    "Vis prioriteter",
    options=["Lav", "Mellem", "Høj", "Meget høj"],
    default=["Lav", "Mellem", "Høj", "Meget høj"],
)

filtered = edited[
    edited["Prioritet"].isin(selected_priorities)
].copy()

col1, col2, col3 = st.columns(3)
col1.metric("Interessenter i visningen", len(filtered))
col2.metric(
    "Meget høj prioritet",
    int(filtered["Prioritet"].eq("Meget høj").sum()),
)
col3.metric(
    "Høj prioritet",
    int(filtered["Prioritet"].eq("Høj").sum()),
)

st.subheader("Indflydelse–interesse-matrix")

st.caption(
    "I denne visning regnes 4–5 som høj og 1–3 som lavere. "
    "Opdelingen er et visuelt hjælpemiddel, ikke en beregning af prioritet. "
    "Interessenter med samme koordinater samles i ét punkt."
)

if filtered.empty:
    st.info("Ingen interessenter matcher det valgte filter.")
else:
      # Give each stakeholder a separate label at their shared coordinates.
    plot_data = filtered.copy()

    plot_data["GroupSize"] = (
        plot_data.groupby(["Interesse", "Indflydelse"])["Interessent"]
        .transform("size")
    )

    plot_data["LabelIndex"] = (
        plot_data.groupby(["Interesse", "Indflydelse"]).cumcount()
    )

    # Centre the stack of labels around the actual score.
    plot_data["LabelY"] = (
        plot_data["Indflydelse"]
        + (
            (plot_data["GroupSize"] - 1) / 2
            - plot_data["LabelIndex"]
        ) * 0.22
    )

    quadrants = pd.DataFrame([
        {
            "x1": 0.5, "x2": 3.5, "y1": 3.5, "y2": 5.5,
            "Farve": "#fff0ce",
        },
        {
            "x1": 3.5, "x2": 5.5, "y1": 3.5, "y2": 5.5,
            "Farve": "#dcefe1",
        },
        {
            "x1": 0.5, "x2": 3.5, "y1": 0.5, "y2": 3.5,
            "Farve": "#eeeeee",
        },
        {
            "x1": 3.5, "x2": 5.5, "y1": 0.5, "y2": 3.5,
            "Farve": "#deebf7",
        },
    ])

    background = alt.Chart(quadrants).mark_rect(opacity=0.65).encode(
        x=alt.X(
            "x1:Q",
            title="Interesse",
            scale=alt.Scale(domain=[0.5, 5.5]),
            axis=alt.Axis(values=[1, 2, 3, 4, 5]),
        ),
        x2="x2:Q",
        y=alt.Y(
            "y1:Q",
            title="Indflydelse",
            scale=alt.Scale(domain=[0.5, 5.5]),
            axis=alt.Axis(values=[1, 2, 3, 4, 5]),
        ),
        y2="y2:Q",
        color=alt.Color("Farve:N", scale=None, legend=None),
    )

    labels = alt.Chart(plot_data).mark_text(
        align="center",
        baseline="middle",
        fontSize=12,
        fontWeight="bold",
        color="#17324d",
    ).encode(
        x=alt.X("Interesse:Q", title="Interesse"),
        y=alt.Y("LabelY:Q", title="Indflydelse"),
        text="Interessent:N",
        tooltip=[
            alt.Tooltip("Interessent:N", title="Interessent"),
            alt.Tooltip("Interesse:Q", title="Interesse"),
            alt.Tooltip("Indflydelse:Q", title="Indflydelse"),
            alt.Tooltip("Prioritet:N", title="Prioritet"),
            alt.Tooltip("Håndtering:N", title="Håndtering"),
        ],
    )

    chart = (background + labels).properties(height=550)

    st.altair_chart(chart, use_container_width=True)
    
    st.caption(
        "Tallet i hvert punkt viser antal interessenter. "
        "Hold musen over punktet for at se navnene."
    )

    with st.expander("Se roller og håndtering uden afkortet tabeltekst"):
        for _, row in filtered.iterrows():
            st.subheader(row["Interessent"])
            st.write("Rolle:", row["Rolle i projektet"])
            st.write(
                f"Indflydelse: {row['Indflydelse']} · "
                f"Interesse: {row['Interesse']} · "
                f"Prioritet: {row['Prioritet']}"
            )
            st.write("Håndtering:", row["Håndtering"])
