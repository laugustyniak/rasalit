# to run this please make sure you've got the dependencies
# pip install streamlit altair pandas

import json
import pathlib

import streamlit as st
import altair as alt
import pandas as pd

def read_intent_report(path):
    blob = json.loads(path.read_text())
    jsonl = [{**v, 'config': path.parts[1]} for k,v in blob.items() if 'weighted avg' in k]
    return pd.DataFrame(jsonl).drop(columns=['support'])

def read_entity_report(path):
    blob = json.loads(path.read_text())
    jsonl = [{**v, 'config': path.parts[1]} for k,v in blob.items() if 'weighted avg' in k]
    return pd.DataFrame(jsonl).drop(columns=['support'])

def add_zeros(dataf, all_configs):
    for cfg in all_configs:
        if cfg not in list(dataf['config']):
            dataf = pd.concat([dataf, pd.DataFrame({'precision': [0], 
                                                    'recall': [0], 
                                                    'f1-score': [0],
                                                    'config': cfg})])
    return dataf

st.cache()
def read_pandas(results_folder):
    paths = list(pathlib.Path(results_folder).glob("*/*_report.json"))
    configurations = set([p.parts[1] for p in paths])
    intent_df = pd.concat([read_intent_report(p) for p in paths if 'intent_report' in str(p)])
    paths = list(pathlib.Path(results_folder).glob("*/CRFEntityExtractor_report.json")) 
    paths += list(pathlib.Path(results_folder).glob("*/DIETClassifier_report.json"))
    entity_df = pd.concat([read_entity_report(p) for p in paths]).pipe(add_zeros, all_configs=configurations)
    return intent_df, entity_df


st.markdown("# Rasa GridResults Summary")
st.markdown("Quick Overview of Crossvalidated Runs")

st.sidebar.markdown("### Configure Overview")

results_folder = st.sidebar.text_input("What is your results folder?", value='gridresults')

if pathlib.Path(results_folder).exists():
    intent_df, entity_df = read_pandas(results_folder=results_folder)
    possible_configs = list(intent_df['config'])
else: 
    st.write(f"Are you sure this results folder `{results_folder}` exists?")

st.sidebar.markdown("Select what you care about.")
selected_config = st.sidebar.multiselect("Select Result Folders", 
                                          possible_configs, 
                                          default=possible_configs)
show_raw_data = st.sidebar.checkbox("Show Raw Data")
if show_raw_data:
    show_markdown = st.sidebar.checkbox("Show Raw as Markdown")

subset_df = intent_df.loc[lambda d: d['config'].isin(selected_config)].melt('config')


st.markdown("## Intent Summary Overview")

c = alt.Chart(subset_df).mark_bar().encode(
    y='config:N',
    x='value:Q',
    color='config:N',
    row='variable:N'
)
st.altair_chart(c)

if show_raw_data:
    raw_data = intent_df.loc[lambda d: d['config'].isin(selected_config)]
    if show_markdown:
        st.code(raw_data.to_markdown())
    else:
        st.write(raw_data)


subset_df = entity_df.loc[lambda d: d['config'].isin(selected_config)].melt('config')

st.markdown("## Entity Summary Overview")
c = alt.Chart(subset_df).mark_bar().encode(
    y='config:N',
    x='value:Q',
    color='config:N',
    row='variable:N'
)

st.altair_chart(c)

if show_raw_data:
    raw_data = entity_df.loc[lambda d: d['config'].isin(selected_config)]
    if show_markdown:
        st.code(raw_data.to_markdown())
    else:
        st.write(raw_data)
