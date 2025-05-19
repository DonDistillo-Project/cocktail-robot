#ifndef SETUP_WIFI
#define SETUP_WIFI

#include "Setup.hpp"

#include <string>
#include <WiFi.h>
#include <optional>

#define WIFI_FS_DIR "/wifi/"
#define WIFI_SSID_FILE "/wifi/ssid"
#define WIFI_PASS_FILE "/wifi/pass"

#define WIFI_RETRY_TIMES 20
#define WIFI_RETRY_DELAY 1000

String explainWiFiStatusCode(wl_status_t status)
{
    String exceptionReason;
    switch (status)
    {
    case WL_NO_SSID_AVAIL:
        return "SSID not found";
    case WL_CONNECT_FAILED:
        return "Failed - WiFi not connected.";
    case WL_CONNECTION_LOST:
        return "Connection was lost";
    case WL_SCAN_COMPLETED:
        return "Scan is completed";
    case WL_DISCONNECTED:
        return "WiFi is disconnected";
    case WL_CONNECTED:
        return "WiFi is connected";
    default:
        return String("WiFi Status: ") + String(status);
    }
}

void setupWifi(String ssid, String pass)
{
#ifdef SETUP_SERIAL
    Serial.printf("\tSSID: \"%s\", PASS: \"%s\".\n", ssid.c_str(), pass.c_str());
    Serial.flush();
#endif

    WiFi.mode(WIFI_STA);
    WiFi.begin(ssid, pass);

    // Auto reconnect is set true as default
    // To set auto connect off, use the following function
    //    WiFi.setAutoReconnect(false);

    // Will try for about 10 seconds (20x 500ms)
    int numberOfTries = WIFI_RETRY_TIMES;
    wl_status_t status;
    // Wait for the WiFi event
    while ((status = WiFi.status()) != WL_CONNECTED)
    {
        if (status == WL_CONNECT_FAILED)
        {
            throw SetupError(String("WiFi setup failed: " + explainWiFiStatusCode(status)).c_str());
        }

#ifdef SETUP_SERIAL
        Serial.printf("\t[WIFI] %s\n", explainWiFiStatusCode(status).c_str());
#endif
        delay(WIFI_RETRY_DELAY);

        if (numberOfTries <= 0)
        {
            WiFi.disconnect();
            throw SetupError("WiFi setup failed: Too many retries");
        }
        else
        {
            numberOfTries--;
        }
    }
#ifdef SETUP_SERIAL
    Serial.println("\tWiFi Connection successful");
#endif
}

#ifdef SETUP_SERIAL
void connectWiFiSerialScan(String &ssid, String &pass)
{
    Serial.println("\tStarting WiFi Scan...");
    int id = -1;

    while (id < 0)
    {
        int n = WiFi.scanNetworks();
        Serial.println("\tScan done");
        if (n == 0)
        {
            Serial.println("\tNo networks found; Rescan (1) or return (2): (1 or 2)");
        }
        else
        {
            Serial.printf("\t%d networks found\n", n);
            Serial.println("\tNr | SSID                             | RSSI | CH | Encryption");
            for (int i = 0; i < n; ++i)
            {
                // Print SSID and RSSI for each network found
                Serial.print("\t");
                Serial.printf("%2d", i + 1);
                Serial.print(" | ");
                Serial.printf("%-32.32s", WiFi.SSID(i).c_str());
                Serial.print(" | ");
                Serial.printf("%4ld", WiFi.RSSI(i));
                Serial.print(" | ");
                Serial.printf("%2ld", WiFi.channel(i));
                Serial.print(" | ");
                switch (WiFi.encryptionType(i))
                {
                case WIFI_AUTH_OPEN:
                    Serial.print("open");
                    break;
                case WIFI_AUTH_WEP:
                    Serial.print("WEP");
                    break;
                case WIFI_AUTH_WPA_PSK:
                    Serial.print("WPA");
                    break;
                case WIFI_AUTH_WPA2_PSK:
                    Serial.print("WPA2");
                    break;
                case WIFI_AUTH_WPA_WPA2_PSK:
                    Serial.print("WPA+WPA2");
                    break;
                case WIFI_AUTH_WPA2_ENTERPRISE:
                    Serial.print("WPA2-EAP");
                    break;
                case WIFI_AUTH_WPA3_PSK:
                    Serial.print("WPA3");
                    break;
                case WIFI_AUTH_WPA2_WPA3_PSK:
                    Serial.print("WPA2+WPA3");
                    break;
                case WIFI_AUTH_WAPI_PSK:
                    Serial.print("WAPI");
                    break;
                default:
                    Serial.print("unknown");
                }
                Serial.println();
                delay(10);
            }
        }
        Serial.println("");
        Serial.print("\tSelect the WiFi by id (or 0 to search again): ");
        id = Serial.parseInt() - 1;
        Serial.printf("%2d\n", id + 1);
        Serial.readStringUntil('\n');
    }

    ssid = WiFi.SSID(id);
    WiFi.scanDelete();

    Serial.print("\tEnter password: ");
    String pw = Serial.readStringUntil('\n');
    Serial.println(pw);
    pw.trim();
    pass = pw;
    setupWifi(ssid.c_str(), pass);
}

void connectWiFiSerialManual(String &ssid, String &pass)
{
    Serial.println("\tManually connecting to WiFi...");

    Serial.print("\tEnter WiFi SSID: ");
    ssid = Serial.readStringUntil('\n');
    Serial.println(ssid);

    Serial.print("\tEnter WiFi Password: ");
    pass = Serial.readStringUntil('\n');

    setupWifi(ssid, pass);
}

void setupWiFiSerial()
{
    String ssid, pass;
    Serial.println("Starting WiFi setup over Serial:");
    while (!WiFi.isConnected())
    {
        Serial.println("\tWiFi not connected.");
        Serial.print("\tScan for WiFi Networks (1) or manually enter SSID (2): (1 or 2) ");
        int setup_mode = Serial.parseInt();
        Serial.println(setup_mode);
        Serial.flush();
        Serial.readStringUntil('\n');

        if (setup_mode == 1)
        {
            try
            {
                connectWiFiSerialScan(ssid, pass);
            }
            catch (SetupError e)
            {
                Serial.printf("\t%s\n", e.what());
                continue;
            }
        }
        else if (setup_mode == 2)
        {
            try
            {
                connectWiFiSerialManual(ssid, pass);
            }
            catch (SetupError e)
            {
                Serial.printf("\t%s\n", e.what());
                continue;
            }
        }
        else
        {
            Serial.printf("\tError: \"%d\" is not a valid mode (1 or 2); Try again...\n", setup_mode);
            continue;
        }
    }

    Serial.println("Success!");

#ifdef SETUP_FS
    // Success; Write SSID and PASS to files
    Serial.print("Do you want to save WiFi settings to FS (1) or not (2)? (1 or 2) ");
    int save = Serial.parseInt();
    Serial.println(save);
    Serial.readStringUntil('\n');

    if (save == 1)
    {
        if (!LittleFS.exists(WIFI_FS_DIR))
        {
            LittleFS.mkdir(WIFI_FS_DIR);
        }

        fs::File ssid_file = LittleFS.open(WIFI_SSID_FILE, "w", true);
        if (!ssid_file || ssid_file.isDirectory())
        {
            throw SetupError("Could not open WiFi SSID file");
        }
        if (ssid_file.write((const uint8_t *)ssid.c_str(), ssid.length()) != ssid.length())
        {
            ssid_file.close();
            throw SetupError("Could not write SSID file");
        }
        ssid_file.close();

        fs::File pass_file = LittleFS.open(WIFI_PASS_FILE, "w", true);
        if (!pass_file || pass_file.isDirectory())
        {
            throw SetupError("Could not open WiFi password file");
        }
        if (pass_file.write((const uint8_t *)pass.c_str(), pass.length()) != pass.length())
        {
            pass_file.close();
            throw SetupError("Could not write password file");
        }
        pass_file.close();

        Serial.println("Successfully wrote WiFi login details.");
        return;
    }
    else
    {
        Serial.println("Not writing WiFi login details.");
        return;
    }
#endif
}
#endif // SETUP_SERIAL

#ifdef SETUP_FS
void setupWiFiFS()
{
    String ssid, pass;

    fs::File ssid_file = LittleFS.open(WIFI_SSID_FILE);
    if (!ssid_file || ssid_file.isDirectory())
    {
        throw SetupError("Could not open WiFi SSID file");
    }
    ssid = ssid_file.readString();
    ssid_file.close();

    fs::File pass_file = LittleFS.open(WIFI_PASS_FILE);
    if (!pass_file || pass_file.isDirectory())
    {
        throw SetupError("Could not open WiFi password file");
    }
    pass = pass_file.readString();
    pass_file.close();

    setupWifi(ssid, pass);
}
#endif // SETUP_FS

#if defined SETUP_FS && defined SETUP_SERIAL
void setupWifi()
{
    try
    {
        setupWiFiFS();
        return;
    }
    catch (SetupError e)
    {
        Serial.print("Error while trying to setup WiFi via flash storage: ");
        Serial.print(e.what());
        Serial.println("\nTrying fallback Serial WiFi setup");
        setupWiFiSerial();
    }
};

#elif defined SETUP_FS
void setupWifi()
{
    setupWiFiFS();
}
#elif defined SETUP_SERIAL
void setupWifi()
{
    setupWiFiSerial();
}
#endif
#endif