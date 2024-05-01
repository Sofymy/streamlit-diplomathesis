import streamlit as st
from google.cloud import firestore
import pandas as pd
import numpy as np
import altair as alt

st.header('Insights into user preferences')


class FirestoreDataRetriever:
    def __init__(self, user_id, firestore_client):
        self.user_id = user_id
        self.firestore_client = firestore_client

    def get_device_data(self, collection_name):
        data = self.firestore_client.collection(collection_name).document(self.user_id).get().to_dict()
        return data


    def get_applications_data(self, collection_name):
        collections = self.firestore_client.collection(collection_name).document(self.user_id).collections()
        data = []
        elements_collected = 0
        for collection in collections:
            for document in collection.stream():
                runningapps = document.get("runningApplications")
                for app in runningapps:
                   entry = app
                   if not any(d['closeTimestamp'] == entry['closeTimestamp'] for d in data):
                      data.append(entry)
                   if elements_collected == 12:
                     break
                   elements_collected += 1
                if elements_collected == 12:
                    break
            if elements_collected == 12:
                break
        print(f"Retrieved {len(data)} elements for collection {collection_name}")
        return data


    def get_networks_data(self, collection_name):
        collections = self.firestore_client.collection(collection_name).document(self.user_id).collections()
        data = []
        elements_collected = 0
        for collection in collections:
            for document in collection.stream():
                entry = document.to_dict()
                data.append(entry)
                elements_collected += 1
                if elements_collected == 1:
                    break
            if elements_collected == 1:
                break
        print(f"Retrieved {len(data)} elements for collection {collection_name}")
        return data

    def retrieve_data(self, collection_name):
        collections = self.firestore_client.collection(collection_name).document(self.user_id).collections()
        data = []
        elements_collected = 0
        for collection in collections:
            for document in collection.stream():
                entry = document.to_dict()
                entry["time"] = collection.id[-8:]
                data.append(entry)
                elements_collected += 1
                if elements_collected == 12:
                    break
            if elements_collected == 12:
                break
        print(f"Retrieved {len(data)} elements for collection {collection_name}")
        return data

    def get_chart_data(self, collection_name):
        data = self.retrieve_data(collection_name)
        chart_data = pd.DataFrame(data)
        return chart_data

    def get_chart(self, chart_data, title, x_name, color):
        table = pd.melt(chart_data, id_vars=['time'], value_vars=chart_data.columns.drop('time'))
        chart = alt.Chart(table, title=title).mark_bar(opacity=1).encode(
          column=alt.Column('time:O', spacing=5, header=alt.Header(labelOrient="bottom")),
          x=alt.X('variable', sort=chart_data.columns.drop('time').tolist(), axis=None),
          y=alt.Y('value:Q', title=x_name),  
          color=color
        ).configure_view(stroke='transparent')
        return chart

    def get_chart_simple(self, chart_data, title):
        chart = alt.Chart(chart_data, title=title).mark_bar().encode(
        x='time:O',
        y=alt.Y('batteryPct', scale=alt.Scale(domain=[0, 100], clamp=True), title = 'Battery percentage (%)'),
        color='charging:N'
        ).configure_view(stroke='transparent')
        return chart


# Authenticate to Firestore with the JSON account key.
# db = firestore.Client.from_service_account_json("firebase-key.json")
import json
key_dict = json.loads(st.secrets["textkey"])
creds = service_account.Credentials.from_service_account_info(key_dict)
db = firestore.Client(credentials=creds, project="streamlit-reddit")

# Create an instance of FirestoreDataRetriever
option = st.selectbox(
       'Device id',
      ('zEwunnkGzchjpUcnul8wB2NBlRp2', '1RkL4MsegrSgEUhJEjy7Hp0ciks2'))

st.write('You selected:', option)
data_retriever = FirestoreDataRetriever(option, db)

# Get chart data 
device_data = data_retriever.get_device_data('devices')
networks_data = data_retriever.get_networks_data('networks')

memoryusages_chart_data = data_retriever.get_chart_data('memoryusages')
storageusages_chart_data = data_retriever.get_chart_data('storageusages')
runningapplications_data = data_retriever.get_applications_data('runningapplications')
powerconnections_chart_data = data_retriever.get_chart_data('powerconnections')
mobiletrafficbytes_chart_data = data_retriever.get_chart_data('mobiletrafficbytes')
cells_data = data_retriever.get_chart_data('cells')
callstate_data = data_retriever.get_chart_data('callstate')
keygoardlocked_data = data_retriever.get_chart_data('keyguardlocked')


# Get charts
memoryusages_chart = data_retriever.get_chart(memoryusages_chart_data, 'Memory usage', 'Bytes', alt.Color('variable'))
storageusages_chart = data_retriever.get_chart(storageusages_chart_data, 'Storage usage', 'Bytes', alt.Color('variable'))
powerconnections_chart = data_retriever.get_chart_simple(powerconnections_chart_data, 'Power connections')
mobiletrafficbytes_chart = data_retriever.get_chart(mobiletrafficbytes_chart_data, 'Mobile traffic', 'Bytes', alt.Color('variable'))



# Display
st.write('Device info')
st.table(device_data)
st.write('Network info')
st.table(networks_data)
st.altair_chart(memoryusages_chart)
st.write('Currently used applications')
st.table(runningapplications_data)
st.altair_chart(storageusages_chart)
st.write('Keyguard locked')
st.table(keygoardlocked_data)
st.altair_chart(powerconnections_chart)
st.write('Call states')
st.table(callstate_data)
st.altair_chart(mobiletrafficbytes_chart)
st.write('Cell ids')
st.table(cells_data)