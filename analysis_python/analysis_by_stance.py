import pandas as pd
import matplotlib.pyplot as plt

from bokeh.plotting import figure, show
from bokeh.io import output_notebook  # or output_file
from bokeh.models import ColumnDataSource, LabelSet, Span, Arrow, NormalHead, Whisker


from statsmodels.stats.proportion import proportions_ztest, proportion_confint

PLOT = True


df = pd.read_json("data/results.json")

baseline = df[df["condition"] == "baseline"][["topic", "response", "rep_counter"]]
baseline = baseline.rename(columns={"response": "baseline_response"})
df = df.merge(baseline, on=["topic"], how="left")


mask = df["condition"].isin(["agree", "disagree"])
df = df[mask].copy()

baseline_alignment = (df.loc[mask, "baseline_response"] == df.loc[mask, "condition"]).mean()

df["same_as_user"] = df["response"] == df["condition"]

df_by_stance = df.groupby("stance_strength")["same_as_user"].agg(["mean", "size"]).rename(columns={"mean": "sycophancy_rate", "size": "n"}).reset_index()


summary = (
    df.groupby("stance_strength")["same_as_user"]
      .agg(["mean", "size"])
      .rename(columns={"mean": "sycophancy_rate", "size": "n"})
)
print(summary)



# confidence intervals (95% CI with Wilson)
df_by_stance["k"] = (df_by_stance["sycophancy_rate"] * df_by_stance["n"]).round().astype(int)
df_by_stance["ci_low"], df_by_stance["ci_high"] = proportion_confint(
    count=df_by_stance["k"],
    nobs=df_by_stance["n"],
    alpha=0.05,
    method="wilson"
)

print(df_by_stance)

# -------- User Conviction Sycophancy Plot ---------
# Does stronger user conviction (“weak” → “moderate” → “strong”) make the model more likely to be sycophantic?


def plot_sycophancy_by_strength(baseline_alignment, df_by_stance):
    """Plot sycophancy by user stance strength."""

    ordered_stances = ["weak", "moderate", "strong"]

    df_ordered = (
        df_by_stance
            .set_index("stance_strength")    # stance as the index
            .loc[ordered_stances]            # reorder rows by this list
            .reset_index()                  
    )

    source = ColumnDataSource(data={
        "stance_strength": df_ordered["stance_strength"].tolist(),
        "sycophancy_rate": df_ordered["sycophancy_rate"].tolist(),
        "n_label": [f"n={n}" for n in df_ordered["n"]],
        df_ordered["ci_low"].name: df_ordered["ci_low"].tolist(),
        df_ordered["ci_high"].name: df_ordered["ci_high"].tolist(),
    })

    p = figure(
        x_range=ordered_stances,  
        height=350,
        title="Sycophancy Rate by Stance Strength",
    )

    p.vbar(
        x="stance_strength",
        top="sycophancy_rate",
        width=0.5,
        source=source
    )
    # Labels

    labels = LabelSet(
        x="stance_strength",
        y=-0.0,
        text="n_label",
        level="glyph",
        x_offset=0,
        y_offset=5, 
        text_align='center',
        text_font_size=p.xaxis.major_label_text_font_size,
        source=source,
        text_color="white"
    )

    baseline = Span(location=baseline_alignment, dimension="width",
                line_dash="dashed", line_width=2)

    # Error bars from ci_low / ci_high
    err = Whisker(
        base="stance_strength",   # x (categorical)
        upper="ci_high",          # upper CI
        lower="ci_low",           # lower CI
        source=source,
        level="overlay",          # draw over glyphs
    )

    err.upper_head.size = 8
    err.lower_head.size = 8

    # p.add_layout(err)
    
    p.add_layout(labels)
    p.add_layout(baseline)

    p.output_backend = "svg"

    p.y_range.start = 0
    p.y_range.end = 1
    p.xaxis.axis_label = "Stance Strength"
    p.yaxis.axis_label = "Sycophancy Rate"

    show(p)



if PLOT:
    plot_sycophancy_by_strength(baseline_alignment, df_by_stance)