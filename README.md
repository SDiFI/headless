# SDiFI Headless client

This is the headless client for the SDiFI project. It enables telephony communication between users and chatbots.

In development. Expect breakage.

## Implementation
The headless client is implemented as an IVR (interactive voice response) voice API which receives audio data from users using telephony. To achieve this we use [Twilio](https://www.twilio.com/en-us). The Twilio API enables this client to receive phone calls from end users via an open websocket connection between the user's phone and this client. Meanwhile the connection is open the end user and this client can exchange audio data. 

### ASR (Automatic speech recognition)
The `/echo` endpoint uses the [Tiro STT web service](https://docs.tiro.is/reference/grpc_speech_to_text/speech/) to transribe incoming audio.

### TTS (Text-to-speech)
The `/echo` endpoint uses the [Tiro TTS web service](https://tts.tiro.is/) to generate outgoing audio responses. Please refer to the [documentation](https://tts.tiro.is/) before modifying the request code (if you would like to e.g. switch to a different voice).

## Possibilities
An example utilization of this setup would be to receive the end user's voice as audio data, transcribe it using ASR, detect intents and entities, form an answer, create a TTS response and stream it for the end user to hear.

## Installation
This section walks you through how to use this API.

### Twilio setup

In order to use this API you must create a [Twilio](https://www.twilio.com/en-us) __account__ and __phone number__. Create your account and phone number. The phone number will be the number one can call to interact with this API.
<br>
Next get acquainted with [TwiML Bins](https://www.twilio.com/docs/serverless/twiml-bins) and use the Twilio console to create one which looks like this:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<Response>
	<Connect>
		<Stream url="wss://<url-to-your-running-api>/echo" />
	</Connect>
</Response>
```
Here you must replace the `<url-to-your-running-api>` string with an URL to a running instance of this API. Take a note the provided schema: `wss`. This means that your running instance environment must support a _secure websocket_ connection. This can easiliy be achieved by using [ngrok](https://ngrok.com/) as a proxy to your locally running instance. That method is recommended for development and testing.
<br>
P.S. Remember to give your TwiML Bin a friendly name like _Echo test_.
<br><br>
Now you should configure your Twilio phone number so that when a call comes in, the TwiML Bin you just created should be executed. It can be done quite simply in the Twilio console configuration for your phone number. Should it become troublesome, please refer to the [Twilio documentation](https://twilio.com/docs).
<br><br>
Now, when Twilio receives an incoming call to your phonenumber, the TwiML Bin will be executed. As a consequence, the phonecall will be connected to your running instance of this API and communication can commence.

### Environment variables
This API relies on the existence of a few environment variables. Start by adding a new file called `.env.local` and add the following variables along with their values:
```sh
export TIRO_ACCESS_TOKEN=...
export ASR_SERVER_URL=...
export TTS_SERVER_URL=...
export TTS_VOICE_ID=...
export SOCK_SERVER_OPTIONS=...
export PORT=...
```
Note that some of these values have default values which are set in [src/config.py](./src/config.py).

### Environment and dependencies
Now you should install the required dependencies to run this API. Start by setting up an environment and activate it:
```
python3 -m venv .venv
source .venv/bin/activate
```

Now, install the dependencies.
```sh
pip3 install -r requirements.txt
```

Now you are ready to run the API.

## Usage
### Starting the program
Run the API by using the following command:
```sh
./start_dev.sh
```
This command sets the provided environment variables in `.env.local` and runs the API.

### API
When this is written there is only a single endpoint called `/echo`. This is a websocket endpoint which Twilio connects to for data exchange. For additional technical info please refer to the _Implementation_ and _Installation->Twilio setup_ chapters above. This part assumes that you have followed the instructions provided in the _Installation_ chapter above.
<br>
Simply call your Twilio phone number to connect to this endpoint. As you speak, your voice will be ASR-transcribed and the resulting text will be turned into audio using TTS. Finally that resulting TTS audio is sent back to the phone. That way, this endpoint echoes whatever you say using TTS. To close the connection, simply hang up on the phone.

## Editing
If you would like to contribute make sure to format the code using `black` and `isort`. The provided `pyproject.toml` file defines the rules and configurations.

```sh
black --config pyproject.toml <filenames>
isort --settings-path pyproject.toml <filenames>
```
Use branches and create merge requests.

## License
See [LICENSE](./LICENSE).
