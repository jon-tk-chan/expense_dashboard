import streamlit as st
import pandas as pd
import datetime
import plotly.express as px
st.set_page_config(page_title="Variable Expenses Dashboard",
                    page_icon=":speech_bubble:",
                    layout="wide")
st.markdown("## Spending Dashboard - by Category, date range")
st.markdown("""
    Test run using random sample of expense data (Notes column anonymized). 
    This dashboard displays generated visuals from the input file listed in the side bar.
    The purpose is to show: rolling average over the selected time duration,
     distribution of spending by category
     Heatmap of daily spending by month, day of month
     EXTRA: show categorical spending on a given weekday (stacked bar chart).
""")
####### FUNCTIONS
def preprocess_raw(in_df):
    """Return the cleaned data (record wise) 

    
    lowercase column names
    filter: any positive amounts, days with negative daily budget (only leave expenses)
    Make categories into lowercase and remove spaces
    Add datetime columns for visualization -datetime components
    """
    out_df = in_df.copy()
    out_df.columns = ['date', 'note', 'category', 'amount']
    out_df = out_df[out_df['note'] != "Daily Budget"]

    out_df['date'] = pd.to_datetime(out_df['date'])
    out_df['category'] = out_df['category'].str.lower()
    out_df['category'] = out_df['category'].replace(" ", "_", regex=True).replace("-", "", regex=True).replace("__", "_", regex=True)
    #Get expenses - make 'Amount' into Float, get negative rows only (expenses), then get absolute value
    out_df['amount'] = out_df['amount'].replace(",", "", regex=True).astype(float)
    out_df = out_df[out_df["amount"]  < 0]
    out_df['amount'] = out_df['amount'].abs()

    #add datetime components - year/month/day num, week of year, day of week, name of month, name of weekday
    out_df['year_num'] = out_df['date'].apply(lambda x: x.strftime("%Y"))
    out_df['month_num'] = out_df['date'].apply(lambda x: x.strftime("%m"))
    out_df['day_num'] = out_df['date'].apply(lambda x: x.strftime("%d"))

    out_df['yearweek_num'] = out_df['date'].apply(lambda x: x.strftime("%U"))
    out_df['weekday_num'] = out_df['date'].apply(lambda x: x.strftime("%w"))

    out_df['month_name'] = out_df['date'].apply(lambda x: x.strftime("%B"))
    out_df['weekday_name'] = out_df['date'].apply(lambda x: x.strftime("%A"))
    
    print(out_df['category'].unique())
    # out_df['month_name'] = out_df['date'].apply(lambda x: x.month_name())

    return out_df
def line_chart(in_df, all_cats=['groceries', 'for_others_food', 'restaurant'], rolling_avg_days = 21,
               start_str = "2021-01-01", end_str = "2021-12-31"):
    
    """Returns a line chart showing rolling_avg_days day average expenses in in_df with any 'category' entry included in all_cats
    filtered by start_str and end_str: YYYY-MM-DD
    """
    start_date = pd.to_datetime(start_str)
    end_date = pd.to_datetime(end_str)
    curr_df = in_df.loc[(in_df['date'] >= start_date) & (in_df['date'] <= end_date)]


    all_dfs = []
    for cat in all_cats:
        # print(cat)
        curr_merged = pd.DataFrame()
        left_df = pd.DataFrame(pd.date_range(start_str, end_str,freq='D'))
        left_df.columns = ['date']
        left_df['category'] = cat
        cat_df = curr_df[curr_df['category']==cat]
        right_df = cat_df[['date', 'amount']]
        curr_merged = left_df.merge(right_df, how='left', left_on='date', right_on='date')
        curr_merged = curr_merged.fillna(0.0)
        curr_merged['rolling_avg'] = curr_merged['amount'].rolling(window=rolling_avg_days).mean()
        curr_merged['rolling_avg'] =curr_merged['rolling_avg'].round(3)
        curr_merged = curr_merged.fillna(0.0)
        all_dfs.append(curr_merged)
        # print(curr_merged.head(10))
        # print("----")
    line_df = pd.concat(all_dfs)
    title_str = f"Rolling {rolling_avg_days}-Day Average spending by Category ({start_str} - {end_str})"
    fig = px.line(line_df, x="date", y="rolling_avg", color='category', title=title_str)
    fig.update_yaxes(title="Rolling Average($)",showgrid=False)
    fig.update_xaxes(showgrid=False)

    return fig
def box_plot(in_df, cats_kept=['groceries', 'for_others_food', 'restaurant'],
               start_str = "2021-01-01", end_str = "2021-12-31"):
    """Returns a box plot for spending in each category in all_cats"""
    start_date = pd.to_datetime(start_str)
    end_date = pd.to_datetime(end_str)
    curr_df = in_df.loc[(in_df['date'] >= start_date) & (in_df['date'] <= end_date)]
    curr_df = curr_df.query("category == @cats_kept")
    box_df = curr_df[['note', 'category', 'amount', 'weekday_name']]

    title_str = f"Transactions by Category ({start_str} - {end_str})"
    fig = px.box(box_df, x="category", y="amount", color='category', points='all',
                hover_data = ['amount', 'note'],
                title=title_str)
    
    fig.update_yaxes(title="Amount ($)")
    return fig

##### INPUT DATA
in_file = "data/daily_budget_ex.csv"
df_raw = pd.read_csv(in_file)
df = preprocess_raw(df_raw)

##### SIDEBAR HEADER AND INPUTS
st.sidebar.header("Selection tools: ")
st.sidebar.subheader(f"INPUT FILE: {in_file}")
start_date = st.sidebar.date_input(
    "Start date:",
    datetime.date(2021, 1, 1))

end_date = st.sidebar.date_input(
    "End Date:",
    datetime.date(2021, 6, 1))
categories = st.sidebar.multiselect(
    'Select Categories to display',
    df['category'].unique().tolist(),
    ['groceries', 'for_others_food'])
rolling_avg_number = st.sidebar.slider(
    "Select number of days to average spending (default: 14 days)",
    0, 60, 14, 1 )
### CREATE VARIABLES, WRITE TO DASHBOARD
start_str = str(start_date)
end_str= str(end_date)
l_chart = line_chart(df, categories, rolling_avg_number, start_str, end_str)
b_chart = box_plot(df, categories, start_str, end_str)

st.plotly_chart(l_chart, use_container_width=True)
left_column, right_column = st.columns(2)
with left_column:
    st.plotly_chart(b_chart, use_container_width=True)

# ---- HIDE STREAMLIT STYLE ----
hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)



#### TO DO
# bind color pallette to specific 