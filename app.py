# Import the dependencies.

import datetime as dt
import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func

from flask import Flask, jsonify
import numpy as np

#################################################
# Database Setup
#################################################
engine = create_engine("sqlite:///Resources/hawaii.sqlite")

# reflect an existing database into a new model
Base = automap_base()
# reflect the tables
Base.prepare(autoload_with=engine)

# Save references to each table
Measurement = Base.classes.measurement
Station = Base.classes.station


# Create our session (link) from Python to the DB
session = Session(engine)

#################################################
# Flask Setup
#################################################
app = Flask(__name__)



#################################################
# Flask Routes
#################################################
@app.route("/")
def home():
    """List all available routes."""
    return (
        f"Available Routes:<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/>"
        f"/api/v1.0/&lt;start&gt;<br/>"
        f"/api/v1.0/&lt;start&gt;/&lt;end&gt;"
    )

@app.route("/api/v1.0/precipitation")
def precipitation():
    session = Session(engine)
    """Convert the query results from precipitation analysis to a dictionary and return as JSON."""
    # Calculate the date 1 year ago from the last data point in the database
    last_date = session.query(Measurement.date).order_by(Measurement.date.desc()).first()
    last_date = dt.datetime.strptime(last_date[0], "%Y-%m-%d")
    one_year_ago = last_date - dt.timedelta(days=365)
    
    # Query precipitation data for the last 12 months
    precipitation_data = session.query(Measurement.date, Measurement.prcp).\
        filter(Measurement.date >= one_year_ago).all()
    
    # Convert the query results to a dictionary
    precipitation_dict = {}
    for date, prcp in precipitation_data:
        precipitation_dict[date] = prcp
    
    return jsonify(precipitation_dict)

@app.route("/api/v1.0/stations")
def stations():
    session = Session(engine)
    """Return a JSON list of stations."""
    station_data = session.query(Station.station, Station.name).all()
    stations_list = [{"station": station, "name": name} for station, name in station_data]
    
    return jsonify(stations_list)

@app.route("/api/v1.0/tobs")
def tobs():
    session = Session(engine)
    """Query temperature observations for the most-active station for the previous year and return as JSON."""
    # Find the most active station (you can define this based on your criteria)
    most_active_station = session.query(Measurement.station, func.count(Measurement.station)).\
        group_by(Measurement.station).\
        order_by(func.count(Measurement.station).desc()).first()
    
    most_active_station = most_active_station[0]
    
    # Calculate the date 1 year ago from the last data point for the most active station
    last_date = session.query(Measurement.date).\
        filter(Measurement.station == most_active_station).\
        order_by(Measurement.date.desc()).first()
    
    last_date = dt.datetime.strptime(last_date[0], "%Y-%m-%d")
    one_year_ago = last_date - dt.timedelta(days=365)
    
    # Query temperature observations for the last 12 months for the most active station
    temperature_data = session.query(Measurement.date, Measurement.tobs).\
        filter(Measurement.station == most_active_station).\
        filter(Measurement.date >= one_year_ago).all()
    
    temperature_list = [{"date": date, "tobs": tobs} for date, tobs in temperature_data]
    
    return jsonify(temperature_list)

@app.route("/api/v1.0/<start>")
@app.route("/api/v1.0/<start>/<end>")
def temp_stats(start, end=None):
    session = Session(engine)
    """Return JSON list of temperature statistics for a specified start or start-end range."""
    # Convert input dates to datetime objects
    start_date = dt.datetime.strptime(start, "%Y-%m-%d")
    
    if end:
        end_date = dt.datetime.strptime(end, "%Y-%m-%d")
    else:
        end_date = session.query(func.max(Measurement.date)).scalar()
        end_date = dt.datetime.strptime(end_date, "%Y-%m-%d")
    
    # Query temperature statistics
    temperature_stats = session.query(func.min(Measurement.tobs), func.avg(Measurement.tobs), func.max(Measurement.tobs)).\
        filter(Measurement.date >= start_date).filter(Measurement.date <= end_date).all()
    
    # Create a dictionary with the results
    temperature_dict = {
        "start_date": start_date.strftime("%Y-%m-%d"),
        "end_date": end_date.strftime("%Y-%m-%d"),
        "min_temperature": temperature_stats[0][0],
        "avg_temperature": temperature_stats[0][1],
        "max_temperature": temperature_stats[0][2]
    }
    
    return jsonify(temperature_dict)

if __name__ == "__main__":
    # Create a session link to the database
    session = Session(engine)
    app.run(debug=True)
