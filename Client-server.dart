import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';

class LocationPage extends StatefulWidget {
  @override
  _LocationPageState createState() => _LocationPageState();
}

class _LocationPageState extends State<LocationPage> {
  // Declare variables to store the location data
  double latitude;
  double longitude;

  // Function to send the location data to the server
  sendLocationData() async {
    // Set up the API endpoint and the payload (i.e., the location data)
    var apiEndpoint = "http://yourserver.com/api/location";
    var payload = {
      "latitude": latitude,
      "longitude": longitude,
    };

    // Send the POST request to the server with the payload in the body
    var response = await http.post(apiEndpoint, body: payload);

    // If the request was successful, parse the JSON response
    if (response.statusCode == 200) {
      var data = json.decode(response.body);
      // Do something with the data (e.g., update a state variable)
      setState(() {
        // Update the latitude and longitude with the data from the server
        latitude = data['latitude'];
        longitude = data['longitude'];
      });
    } else {
      // If the request was unsuccessful, display an error message
      print("Failed to send location data: ${response.statusCode}");
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: <Widget>[
            // Display the latitude and longitude
            Text("Latitude: $latitude"),
            Text("Longitude: $longitude"),
            // Button to send the location data to the server
            RaisedButton(
              onPressed: sendLocationData,
              child: Text("Send Location Data"),
            ),
          ],
        ),
      ),
    );
  }
}


//In this example, the sendLocationData function sends a POST request to the server with the location data (latitude and longitude) in the request body. The server should compute the data and send back updated data in the response body, which is then parsed and used to update the state variables in the Flutter app.


//date and time
import 'package:flutter/material.dart';
import 'dart:core';

class ClockPage extends StatefulWidget {
  @override
  _ClockPageState createState() => _ClockPageState();
}

class _ClockPageState extends State<ClockPage> {
  // Declare a variable to store the current time
  DateTime currentTime;

  @override
  void initState() {
    // Call the getCurrentTime function when the app starts
    getCurrentTime();
    super.initState();
  }

  // Function to get the current time
  getCurrentTime() {
    // Get the current time
    currentTime = DateTime.now();
    // Set the state to update the clock
    setState(() {});
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Center(
        // Display the current time using the Text widget
        child: Text(currentTime.toString()),
      ),
    );
  }
}

//This example displays the current time as a string using the Text widget. The time is retrieved using the DateTime.now() method and stored in the currentTime variable. The clock is updated by calling the setState method whenever the getCurrentTime function is called.

//To update the clock continuously, you can use a timer to call the getCurrentTime function at regular intervals. Here's an example of how you can set up a timer in Flutter:

import 'package:flutter/material.dart';
import 'dart:async';

class ClockPage extends StatefulWidget {
  @override
  _ClockPageState createState() => _ClockPageState();
}

class _ClockPageState extends State<ClockPage> {
  // Declare a variable to store the current time
  DateTime currentTime;
  // Declare a timer
  Timer timer;

  @override
  void initState() {
    // Call the getCurrentTime function when the app starts
    getCurrentTime();
    super.initState();
  }

  // Function to get the current time
  getCurrentTime() {
    // Get the current time
    currentTime = DateTime.now();
    // Set the state to update the clock
    setState(() {});
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Center(
        // Display the current time using the Text widget
        child: Text(currentTime.toString()),
      ),
    );
  }

  @override
  void dispose() {
    // Cancel the timer when the app is closed
    timer.cancel();
    super.dispose();
  }
}

//In this example, the timer is created in the initState method and starts running immediately. The timer calls the getCurrentTime function every second (1000 milliseconds), which updates the clock.
