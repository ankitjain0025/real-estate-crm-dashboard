import pandas as pd


def ask_gemini(question, dataframe):

    question = question.lower()

    numeric_df = dataframe.select_dtypes(include='number')

    total_value = numeric_df.sum().sum()

    if "total collection" in question:

        return f"Total collection related value is ₹ {round(total_value,2):,.0f}"

    elif "top defaulters" in question:

        temp_df = dataframe.copy()

        temp_df["Total Outstanding"] = (
            numeric_df.sum(axis=1)
        )

        top_df = temp_df.sort_values(
            by="Total Outstanding",
            ascending=False
        ).head(10)

        return top_df.to_markdown(index=False)

    elif "records" in question:

        return f"Total records available are {len(dataframe)}"

    elif "overdue" in question:

        return "Please check overdue analysis chart in dashboard."

    else:

        return (
            "AI assistant is active. "
            "Advanced Gemini integration can be added later."
        )