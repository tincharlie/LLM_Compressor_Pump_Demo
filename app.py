import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

# --- Dummy Data Generator ---
def generate_dummy_data(n=100):
    timestamps = [datetime.now() - timedelta(minutes=i * 10) for i in range(n)]
    inlet_pressure = np.random.normal(2.5, 0.1, n)
    outlet_pressure = np.random.normal(6.0, 0.2, n)
    inlet_temp = np.random.normal(25, 1, n)
    outlet_temp = np.random.normal(80, 2, n)
    flow_rate = np.random.normal(10, 0.5, n)
    power_consumed = np.random.normal(50, 5, n)
    efficiency = (flow_rate * (outlet_pressure - inlet_pressure)) / power_consumed

    df = pd.DataFrame({
        "Timestamp": timestamps,
        "Inlet Pressure (bar)": inlet_pressure,
        "Outlet Pressure (bar)": outlet_pressure,
        "Inlet Temp (C)": inlet_temp,
        "Outlet Temp (C)": outlet_temp,
        "Flow Rate (m3/h)": flow_rate,
        "Power (kW)": power_consumed,
        "Efficiency": efficiency
    })

    # Critical conditions
    df["Critical Flag"] = np.where(
        (df["Efficiency"] < 0.3) | (df["Inlet Pressure (bar)"] < 2.2) | (df["Power (kW)"] > 60),
        "CRITICAL", "OK"
    )
    return df

# --- LLM-style Explanation ---
def explain_efficiency(row):
    if row['Efficiency'] < 0.3:
        return "CRITICAL: Very low efficiency. Immediate investigation required."
    elif row['Efficiency'] < 0.5:
        return "Low efficiency. Possible issues with pressure delta or power."
    elif row['Efficiency'] > 2.0:
        return "High efficiency. System optimal."
    else:
        return "Moderate efficiency. Acceptable range."

# --- Prompt Engine ---
def compressor_efficiency_prompt(question, row, df):
    q = question.lower()
    if "efficiency" in q and "what" in q:
        return f"The current efficiency is {row['Efficiency']:.2f}."
    elif "why" in q or "cause" in q:
        if row["Efficiency"] < 0.5:
            return f"Efficiency is low likely due to small pressure difference ({row['Outlet Pressure (bar)']:.2f}-{row['Inlet Pressure (bar)']:.2f}) or high power usage ({row['Power (kW)']:.2f} kW)."
        else:
            return "Efficiency is within normal range. No cause for concern."
    elif "first" in  q:
        first10row = df[['Critical Flag', "Timestamp"]].head(50)
        first10 = "CRITICAL" in list(first10row['Critical Flag'])
        print(first10)
        if first10 == True:  
            timestamp = list(first10row[first10row["Critical Flag"] == 'CRITICAL']["Timestamp"].reset_index(drop=True))
            print(timestamp)
            timestamp = str(timestamp)
            return f"The pump/compressor status was critical at {timestamp} from top 50 row."
        else:
            return f"Not found any critical in the data for pump/compressor."
    elif "last" in  q:
        last10row = df[['Critical Flag', "Timestamp"]].tail(50)
        last10 = "CRITICAL" in list(last10row['Critical Flag'])
        print(last10)
        if last10 == True:  
            timestamp = list(last10row[last10row["Critical Flag"] == 'CRITICAL']["Timestamp"].reset_index(drop=True))
            print(timestamp)
            timestamp = str(timestamp)
            return f"The pump/compressor status was critical at {timestamp} from last 50 row."
        else:
            return f"Not found any critical in the data for pump/compressor."
    elif "pressure" in q:
        return f"Inlet Pressure: {row['Inlet Pressure (bar)']:.2f} bar, Outlet Pressure: {row['Outlet Pressure (bar)']:.2f} bar."
    elif "flow" in q:
        return f"Flow rate is {row['Flow Rate (m3/h)']:.2f} m3/h."
    elif "power" in q:
        return f"Power consumption is {row['Power (kW)']:.2f} kW."
    elif "time" in q:
        return f"The record timestamp is {row['Timestamp']}."
    elif "critical" in q or "alert" in q:
        return f"System status: {row['Critical Flag']}."
    elif "pump" in q or "compressor" in q:
        return f"This system operates as a {('pump' if row['Efficiency'] < 1.0 else 'compressor')}."
    elif "improve" in q:
        return "Reduce power usage or increase pressure delta to improve efficiency."
    
    else:
        return "Please ask about efficiency, pressure, flow, power, or status."

# --- Streamlit UI ---
st.set_page_config(page_title="Pump/Compressor Dashboard", layout="wide")
st.title("Compressor / Pump Efficiency Dashboard with LLM Intelligence")

st.markdown("This dashboard visualizes sensor data and responds to natural language queries about system efficiency.")

# Data
data = generate_dummy_data()
data['LLM Explanation'] = data.apply(explain_efficiency, axis=1)

# View records
selected = st.slider("Select number of recent records to view:", 1, 100, 10, key="slider_recent_records")
st.dataframe(data.head(selected))

# Plot
st.markdown("### Efficiency Over Time")
fig, ax = plt.subplots(figsize=(10, 4))
ax.plot(data["Timestamp"], data["Efficiency"], label="Efficiency", color="blue")
ax.set_ylabel("Efficiency")
ax.set_xlabel("Time")
ax.grid(True)
plt.xticks(rotation=45)
st.pyplot(fig)

# Summary
st.markdown("### Summary Insights")
low_eff_count = (data['Efficiency'] < 0.5).sum()
high_eff_count = (data['Efficiency'] > 2.0).sum()
critical_count = (data['Critical Flag'] == "CRITICAL").sum()
st.write(f"Low Efficiency: {low_eff_count}")
st.write(f"High Efficiency: {high_eff_count}")
st.write(f"Critical Alerts: {critical_count}")

# Manual input
st.markdown("### Test with Manual Input")
inlet_p = st.number_input("Inlet Pressure (bar)", value=2.5, key="inlet_pressure")
outlet_p = st.number_input("Outlet Pressure (bar)", value=6.0, key="outlet_pressure")
flow = st.number_input("Flow Rate (m3/h)", value=10.0, key="flow_rate")
power = st.number_input("Power (kW)", value=50.0, key="power")

if st.button("Calculate Efficiency"):
    efficiency = (flow * (outlet_p - inlet_p)) / power if power else 0
    flag = "CRITICAL" if efficiency < 0.3 else "OK"
    st.write(f"Calculated Efficiency: {efficiency:.2f} ({flag})")
    st.write(explain_efficiency({'Efficiency': efficiency}))

# Prompt-based Q&A
st.markdown("### Ask the Assistant (LLM-style Explanation)")
user_question = st.text_input("Type your question about pump/compressor status:", key="qa_input")
if user_question:
    st.markdown("**Answer:**")
    st.write(compressor_efficiency_prompt(user_question, data.iloc[0], data))

# Export
csv = data.to_csv(index=False).encode("utf-8")
st.download_button("Download Data as CSV", csv, "efficiency_data.csv", "text/csv")

# Sample Prompts
st.markdown("### Example Prompts You Can Try:")
prompts = [
    "What is the efficiency of the compressor?",
    "Why is the efficiency low?",
    "What are the inlet and outlet pressures?",
    "What is the power consumption?",
    "What is the flow rate?",
    "What time was this data recorded?",
    "Is the system in a critical state?",
    "How to improve pump performance?",
    "What is the status of the pump?",
    "Why is there a critical flag?",
    "Tell me first 60 row where status is critical?"
]
for p in prompts:
    st.code(p)
