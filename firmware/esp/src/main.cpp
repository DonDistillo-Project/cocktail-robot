#include <Arduino.h>

#include <WiFi.h>
#include <WebServer.h>

// CONSTS
const int LED_PIN1 = 5;
const int LED_PIN2 = 7;

const int BUTTON_PIN = 8;
const int TEMP_PIN = A18;

const int POTI_PIN = A4;
const int RGB_POWER = 12;
const int R_PIN = 27;
const int G_PIN = 14;
const int B_PIN = 33;


// GLOBALS
int offset = 0;

int rgb_enabled = 1;
int rgb_speed_override = 0;
double rgb_phase = 0.0;
hw_timer_t *rgb_timer;

// config Wifi:
String wifi_ssid = "OnePlus 9 Pro";
String wifi_password = "y2jmf5yg";

WebServer server(80);

const char html[] PROGMEM = R"rawliteral(
<!DOCTYPE html>
<html>
<head>
  <title>ESP32 Web Server</title>
  <style>
    body {
      font-family: sans-serif;
    }
    .container {
      display: flex;
      flex-direction: column;
      align-items: center;
    }
    button {
      font-size: 1.5em;
      margin: 10px;
      padding: 10px;
      background-color: lightgray; /* Set the initial background color */
    }
    button.on {
      background-color: green; /* Set the background color when the LED is ON */
    }
    input[type=range] {
      width: 50%;
    }
  </style>
</head>
<body>
  <div class="container">
    <h1>ESP32 Web Server</h1>
    <br>
    <h3>RGB State</h3>
    <button id="button" onclick="toggleRGB()">RGB: OFF</button>
    <br>
    <br>
    <h3>RGB Speed Control</h3>
    <input type="range" id="trackbar" min="0" max="255" step="1" value="0" oninput="setSpeed()">
  </div>
  <script>
    var rgbState = false;
    var rgbSpeed = 0;
    var button = document.getElementById('button');
    var trackbar = document.getElementById('trackbar');
    function toggleRGB() {
      rgbState = !rgbState;
      var xhr = new XMLHttpRequest();
      xhr.open('GET', '/rgb?state=' + (rgbState ? '1' : '0'), true);
      xhr.send();
      button.innerHTML = 'RGB: ' + (rgbState ? 'ON' : 'OFF');
      button.classList.toggle('on', rgbState); // Add or remove the 'on' class based on the LED state
    }
    function setSpeed() {
      rgbSpeed = trackbar.value;
      var xhr = new XMLHttpRequest();
      xhr.open('GET', '/speed?value=' + rgbSpeed, true);
      xhr.send();
    }
  </script>
</body>
</html>
)rawliteral";

void handleRoot() {
  server.send(200, "text/html", html);
}

void toggleRGB() {
  rgb_enabled = server.arg("state").toInt();
  server.send(200, "text/html", String(rgb_enabled));
}
void setRGBSpeed() {
  rgb_speed_override = server.arg("value").toInt();
  server.send(200, "text/html", String(rgb_speed_override));
}


void set_offset() {
  offset = analogRead(TEMP_PIN);
}

void wifi_setup() {
  Serial.println("Starting WiFi Setup...");
  WiFi.mode(WIFI_STA);
  WiFi.disconnect();

  Serial.setTimeout(10000);


  if (wifi_ssid.length() == 0) {
    Serial.print("No SSID provided; ");

    int id = -1;

    while (id < 0) {
      Serial.println("Scanning for WiFi...");
      int count = WiFi.scanNetworks();
      Serial.printf("%d Networks found:\n", count);
      for (int i = 0; i < count; i++) {
        printf("%2d: %-32.32s\n", i + 1, WiFi.SSID(i).c_str());
      }

      Serial.print("Select the WiFi (or 0 to search again): ");
      id = Serial.parseInt() - 1;
      Serial.printf("%2d\n", id + 1);
      Serial.readStringUntil('\n');
    }

    wifi_ssid = WiFi.SSID(id);
  }

  if (wifi_password.length() == 0) {
    Serial.print("Enter password: ");
    String password = Serial.readStringUntil('\n');
    Serial.println(password);
    wifi_password = password;
  }


  Serial.printf("Trying to connect to wifi \"%s\"", wifi_ssid.c_str());
  WiFi.begin(wifi_ssid, wifi_password);

  while (WiFi.status() != WL_CONNECTED) {
    Serial.print(".");
    delay(100);
  }

  Serial.println("\nConnected to the WiFi network");
  Serial.print("Local ESP32 IP: ");
  Serial.println(WiFi.localIP());
}

void rainbow(double phase) {
  phase *= 3.0;

  int stage0 = phase <= 1;
  int stage1 = !stage0 && phase <= 2;
  int stage2 = phase > 2;


  double red = (phase - 2) * stage2 + (1 - phase) * stage0;
  double green = (phase - 0) * stage0 + (2 - phase) * stage1;
  double blue = (phase - 1) * stage1 + (3 - phase) * stage2;

  analogWrite(R_PIN, (int)((1.0 - red) * 256.0));
  analogWrite(G_PIN, (int)((1.0 - green) * 256.0));
  analogWrite(B_PIN, (int)((1.0 - blue) * 256.0));
}

void setup() {
  Serial.begin(9600);

  pinMode(LED_PIN1, OUTPUT);
  pinMode(LED_PIN2, OUTPUT);

  pinMode(RGB_POWER, OUTPUT);
  pinMode(R_PIN, OUTPUT);
  pinMode(G_PIN, OUTPUT);
  pinMode(B_PIN, OUTPUT);


  rgb_timer = timerBegin(0,(uint32_t)1000000,true);

  pinMode(BUTTON_PIN, INPUT);
  set_offset();

  // wifi_setup();

  // server.on("/", handleRoot);
  // server.on("/rgb", toggleRGB);
  // server.on("/speed", setRGBSpeed);

  // server.begin();
}

void loop() {
  // server.handleClient();

  int state = digitalRead(BUTTON_PIN);
  if (state == HIGH) {
    set_offset();
    rgb_enabled = !rgb_enabled;
    Serial.println(rgb_enabled);

    delay(500);
    while (digitalRead(BUTTON_PIN) == state);
  }

  int temp_val = offset - analogRead(TEMP_PIN);
  int poti_val = analogRead(POTI_PIN);

  analogWrite(LED_PIN1, temp_val);
  analogWrite(LED_PIN2, poti_val / 16);

  digitalWrite(RGB_POWER, rgb_enabled);

  if (rgb_enabled) {

    double dt = timerReadSeconds(rgb_timer);
    timerRestart(rgb_timer);
    double speed = 0.0;
    if (rgb_speed_override != 0) {
      speed = ((double)rgb_speed_override) / 256.0;
    } else {
      speed = ((double)analogRead(POTI_PIN)) / 4096.0;
    }

    rgb_phase = rgb_phase + dt * speed;
    if (rgb_phase > 1.0)
      rgb_phase -= 1.0;

    rainbow(rgb_phase);
  }
}

