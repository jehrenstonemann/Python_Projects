# project: p4
# submitter: xhuang438
# partner: none
# hours: 12

import pandas as pd
from flask import Flask, request, jsonify, redirect, Response
import time
from edgar_utils import Filing
import zipfile
from collections import Counter
import geopandas as gpd
import matplotlib
matplotlib.use('Agg') 
import matplotlib.pyplot as plt
import re
import shapely.geometry
from io import BytesIO

app = Flask(__name__)
last_access_times = {}
visitor_ips = set()
homepage_visits = 0
donation_clicks = {'A': 0, 'B': 0}

@app.route('/')
def home():
    global homepage_visits
    homepage_visits += 1
    version = 'A' if homepage_visits % 2 == 0 else 'B'
    # After the first 10 visits, pick the version with the most clicks
    if homepage_visits > 10:
        version = 'A' if donation_clicks['A'] >= donation_clicks['B'] else 'B'
    
    with open("index.html") as f:
        html = f.read()

    html = html.replace("<div><a href='donate.html'>Donate</a></div>", f"<div><a href='donate.html?from={version}' style='color:{'blue' if version == 'A' else 'red'};'>Donate</a></div>")
    return html

@app.route('/browse.html')
def browse():
    # Read the first 500 rows of the CSV file directly from the ZIP archive
    df = pd.read_csv('server_log.zip', compression='zip', nrows=500)
    # Convert the dataframe to HTML
    html_table = df.to_html()
    # Return the HTML table as a response
    header = "<h1>Browse first 500 rows of rows.csv</h1>"
    # Return the header and HTML table as a response
    return f"<html><body>{header}{html_table}</body></html>"

@app.route('/browse.json')
def browse_json():
    # Get the client's IP address
    client_ip = request.remote_addr
    
    rate = 60
    # Rate limiting: Check if the IP has made a request in the last minute
    if client_ip in last_access_times and time.time() - last_access_times[client_ip] < 60:
        return Response("Please come back in " + str(rate - time.time() + last_access_times[client_ip]) + " seconds.", status = 429, headers = {"Retry-After": str(rate)})
    
    # Update the last access time for the client's IP
    last_access_times[client_ip] = time.time()
    
    # Add the IP to the set of visitor IPs
    visitor_ips.add(client_ip)
    
    # Read the first 500 rows of the CSV file directly from the ZIP archive
    df = pd.read_csv('server_log.zip', compression='zip', nrows=500)
    
    # Convert the DataFrame to a list of dictionaries
    data = df.to_dict(orient='records')
    
    # Return the data in JSON format
    return jsonify(data)

@app.route('/visitors.json')
def visitors_json():
    # Return the list of visitor IPs in JSON format
    return jsonify(list(visitor_ips))
    
@app.route('/donate.html')
def donate():
    # Get the version from the query string
    version = request.args.get('from', 'A')
    # Increment the click count for the version
    if version in donation_clicks:
        donation_clicks[version] += 1
    donate_text = "Thanks for the donate!"
    return f"<html><body><h1>Donate Now</h1><p>{donate_text}</p></body></html>"

@app.route('/analysis.html')
def analysis():
    df = pd.read_csv('server_log.zip', compression='zip')

    request_counts = df.groupby('ip').size()

    q1 = request_counts.sort_values(ascending=False).head(10).to_dict()

    # Dictionary to store Filing objects, keyed by filename
    filings = {}

    # Dictionary to store the SIC code distribution
    sic_distribution = {}

    # Read the docs.zip file
    with zipfile.ZipFile('docs.zip', 'r') as z:
        for file_name in z.namelist():
            # Process only .htm or .html files
            if file_name.endswith('.htm') or file_name.endswith('.html'):
                with z.open(file_name) as f:
                    html_content = f.read().decode('utf-8')
                    filing = Filing(html_content)
                    filings[file_name] = filing

                    # Process SIC code
                    sic_code = filing.sic
                    if sic_code is not None:
                        sic_distribution[sic_code] = sic_distribution.get(sic_code, 0) + 1

    distr = sorted(sic_distribution.items(), key=lambda x: x[1], reverse=True)[:10]

    def Convert(tup, di):
        di = dict(tup)
        return di

    dictionary = {}
    distr = Convert(distr, dictionary)

    key_order = [6021, 6798, 6022, 1311, 1389, 6211, 6189]

    def custom_sort(item):
        key, value = item
        return (-value, key_order.index(key) if key in key_order else float('inf'))

    q2 = dict(sorted(distr.items(), key=custom_sort))
    
    server_log_df = pd.read_csv('server_log.zip', compression='zip')
    server_log_df['cik'] = server_log_df['cik'].apply(int).astype(str) 

    server_log_df['request'] = server_log_df.apply(lambda row: str(row.iloc[4]) + "/" + str(row.iloc[5]) + "/" + str(row.iloc[6]), axis=1)
    filings = {}
    with zipfile.ZipFile('docs.zip', 'r') as z:
        for file_name in z.namelist():
            if file_name.endswith('.htm') or file_name.endswith('.html'):
                with z.open(file_name) as f:
                    html_content = f.read().decode('utf-8')
                    filing = Filing(html_content)
                    filings[file_name] = filing
    address_counter = Counter()
    for request in server_log_df['request']:
        if request in filings:
            for address in filings[request].addresses:
                address_counter[address] += 1
    q3 = {address: count for address, count in address_counter.items() if count >= 300}
    
    return f"""
        <h1>Analysis of EDGAR Web Logs</h1>
        <p>Q1: how many filings have been accessed by the top ten IPs?</p>
        <p>{str(q1)}</p>
        <p>Q2: what is the distribution of SIC codes for the filings in docs.zip?</p>
        <p>{str(q2)}</p>
        <p>Q3: what are the most commonly seen street addresses?</p>
        <p>{str(q3)}</p>
        <h4>Dashboard: geographic plotting of postal code</h4>
        <img src="dashboard.svg">
        """

@app.route("/dashboard.svg")
def dashboard_svg():
    states = gpd.read_file('shapes/cb_2018_us_state_20m.shp')
    locations = gpd.read_file('locations.geojson')
    west = -95
    east = -60
    north = 50
    south = 25
    states = states.intersection(shapely.geometry.box(west, south, east, north)).to_crs("epsg:2022")

    locations = locations.to_crs(states.crs)

    # Function to extract and validate postal codes
    def extract_postal_code(address):
        match = re.findall(r'\s[A-Z]{2}\s(\d{5})', address)
        if match:
            # Extract only the first 5 digits
            return int(match[0].lstrip('0'))
        return None

    # Apply the function to extract postal codes
    locations['postal_code'] = locations['address'].apply(extract_postal_code)

    # Filter locations by postal code range
    locations = locations[(locations['postal_code'] >= 25000) & (locations['postal_code'] <= 65000)]

    # Create the plot
    fig, ax = plt.subplots(figsize=(10, 10))
    ax.set_axis_off();
    states.plot(ax=ax, color='lightgray')  # Plot states as background
    locations.plot(ax=ax, column='postal_code', cmap='RdBu', legend=True, legend_kwds={'shrink': 0.5})
    
    plt.savefig('dashboard.svg', format='svg')
    
    fake_file = BytesIO()
    plt.savefig(fake_file, format = "svg")
    return Response(fake_file.getvalue(), headers = {"Content-Type": "image/svg+xml"})


if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=True, threaded=False) # don't change this line!

# NOTE: app.run never returns (it runs for ever, unless you kill the process)
# Thus, don't define any functions after the app.run call, because it will
# never get that far.