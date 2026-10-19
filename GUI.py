import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import norm
import streamlit as st

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
    "Analysedato"
]

kl_cols = [
    "Pl.prvt.kl", "Prvt.kl", "Modtag.kl",
    "Ana.kl.", "Godk.kl."
]



for col in dato_cols:
    df[col] = pd.to_datetime(df[col], errors="coerce")

for col in kl_cols:
    df[col] = pd.to_timedelta(df[col].astype(str), errors="coerce")

df["UgedagPrvt"] = df["Prvt.dato"].dt.day_name()

df["Pl.prvt_datetime"] = df["Pl.prvt.dato"].dt.normalize() + df["Pl.prvt.kl"]
df["Prvt_datetime"] = df["Prvt.dato"].dt.normalize() + df["Prvt.kl"]
df["Modtag_datetime"] = df["Modtag.dato"].dt.normalize() + df["Modtag.kl"]
df["Analyse_datetime"] = df["Analysedato"].dt.normalize() + df["Ana.kl."]
df["Godk_datetime"] = df["Godk.dato"].dt.normalize() + df["Godk.kl."]


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




# Filtrering
valgPRVT_STED = st.selectbox(
    "Vælg Prvt.stedgeo",
    options=["Begge", "Tages nu", "Tages på runde"]
)

if valgPRVT_STED == "Begge":
    df_filtered = df[
        df["Prvt.stedgeo"].isin(["Tages nu", "Tages på runde"])
    ]
elif valgPRVT_STED == "Tages nu":
    df_filtered = df[df["Prvt.stedgeo"] == "Tages nu"]
else:
    df_filtered = df[df["Prvt.stedgeo"] == "Tages på runde"]



valgKVNT_NAVN = st.selectbox(
    "Vælg Kvnt.navn",
    options=["Alle", "Kreatinin;P", "C-reaktivt protein [CRP];P", "Leukocytter;B"]
)

if valgKVNT_NAVN == "Alle":
    df_filtered = df[
        df["Kvnt.navn"].isin(["Kreatinin;P", "C-reaktivt protein [CRP];P", "Leukocytter;B"])
    ]
elif valgKVNT_NAVN == "Kreatinin;P":
    df_filtered = df[df["Kvnt.navn"] == "Kreatinin;P"]
elif valgKVNT_NAVN == "C-reaktivt protein [CRP];P":
    df_filtered = df[df["Kvnt.navn"] == "C-reaktivt protein [CRP];P"]
elif valgKVNT_NAVN == "Leukocytter;B":
    df_filtered = df[df["Kvnt.navn"] == "Leukocytter;B"]



df_filtered = df_filtered.dropna(
    subset=[
        "Pl.prvt_datetime", "Prvt_datetime", "Modtag_datetime",
        "Analyse_datetime", "Godk_datetime"
    ]
)




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