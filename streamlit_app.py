import os
import time
import streamlit as st
import azure.cognitiveservices.speech as speechsdk
import pyaudio
import wave
import tempfile
from openai import AzureOpenAI 

# Azure Speech Service configuration
endpoint_id = "wss://speech-to-text-aeodedevenveuw.cognitiveservices.azure.com/stt/speech/universal/v2"
subscription="7a2d636e16684618bca53d88e1553bb6"
 
# OpenAI API configuration
os.environ['AZURE_OPENAI_API_KEY'] = "74ab1947352a48db8126ddc0d3a3aeeb"
os.environ['OPENAI_API_VERSION'] = "2024-02-15-preview"
os.environ['AZURE_OPENAI_ENDPOINT'] = "https://openai-kms-nonprod.openai.azure.com/"
input_res = "input_string"
 
def record_audio(duration=5):
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 16000
    RECORD_SECONDS = duration
    WAVE_OUTPUT_FILENAME = tempfile.mktemp(prefix="temp_audio_", suffix=".wav")
 
    p = pyaudio.PyAudio()
 
    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK)
 
    frames = []
 
    for _ in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
        data = stream.read(CHUNK)
        frames.append(data)
 
    stream.stop_stream()
    stream.close()
    p.terminate()
 
    wf = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    wf.close()
 
    return WAVE_OUTPUT_FILENAME
 
def speech_to_text(audio_file):
    speech_config = speechsdk.SpeechConfig(endpoint=endpoint_id, subscription=subscription)
    audio_config = speechsdk.audio.AudioConfig(filename=audio_file)
    recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)
 
    result = recognizer.recognize_once()
 
    if result.reason == speechsdk.ResultReason.RecognizedSpeech:
        return result.text
    elif result.reason == speechsdk.ResultReason.NoMatch:
        return "No speech could be recognized"
    elif result.reason == speechsdk.ResultReason.Canceled:
        cancellation_details = result.cancellation_details
        return f"Speech Recognition canceled: {cancellation_details.reason}. Error details: {cancellation_details.error_details}"
 
def get_chatgpt_response(prompt,temperature,max_tokens,frequency_penalty,presence_penalty):
    client = AzureOpenAI(
    azure_endpoint = "https://openai-kms-nonprod.openai.azure.com/", 
    api_key=os.getenv("AZURE_OPENAI_KEY"),  
    api_version="2024-02-15-preview"
    )
    start_time = time.time()
    #query = "name of atlantis ocean animal"
    #print("Enter query >")
    #query = input()
    completion = client.chat.completions.create(
    model="kmknowledgebase", 
    messages=[
            { "role":"system", "content": "use the data in input_res to give asnwer to user question" +input_res},
            { "role":"user", "content": prompt}
                    ],
    temperature=temperature,
    max_tokens=max_tokens,
    frequency_penalty=frequency_penalty,
    presence_penalty=presence_penalty,
    stop=None
        )
    end_time = time.time()
    response_time = end_time - start_time
    print(f"OpenAI response time: {response_time:.2f} seconds")
    #print('user query:')
    #print(query)
    # print('-----------------------------------------------------------------')
    # print('chatbot answer : ')
    # print(completion.choices[0].message.content)
    # print('-----------------------------------------------------------------')
    output = completion.choices[0].message.content
    return completion.choices[0].message.content
 
def text_to_speech(text):
    endpoint_id= "wss://speech-to-text-aeodedevenveuw.cognitiveservices.azure.com/tts/cognitiveservices/websocket/v1"
    audio_config = speechsdk.audio.AudioOutputConfig(use_default_speaker=True)
    speech_config = speechsdk.SpeechConfig(endpoint=endpoint_id, subscription=subscription)
    
    synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)
    result = synthesizer.speak_text_async(text).get()
 
    if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        print ("Speech synthesized for the text: " + text)
    elif result.reason == speechsdk.ResultReason.Canceled:
        cancellation_details = result.cancellation_details
        st.error("Speech synthesis canceled: " + cancellation_details.reason)
        if cancellation_details.reason == speechsdk.CancellationReason.Error:
            st.error("Error details: " + cancellation_details.error_details)
 
def main():
    st.sidebar.subheader("Choose Input")
    classifier = st.sidebar.selectbox("Input", ("Audio","Text"))

    st.title("Aoede Accelerator")
    st.write("Record Audio from your Microphone / Type a Text to get a response from Azure OpenAI and then convert the response to speech.")
    

    st.sidebar.subheader("Model parameters")
    #choose parameters
    temperature = st.sidebar.number_input("temperature", 0.0, 1.0, step=0.1, key='temperature')
    max_tokens = st.sidebar.radio("max_tokens", (128, 256, 512 ), key='max_tokens')
    frequency_penalty = st.sidebar.number_input("frequency_penalty", 0.0, 1.0, step=0.1, key='frequency_penalty')
    presence_penalty = st.sidebar.number_input("presence_penalty", 0.0, 1.0, step=0.1, key='presence_penalty') 
       
    if classifier == 'Audio':
        st.sidebar.subheader("Recording Duration")
        duration = st.sidebar.number_input("duration", 3, 10, step=1, key='duration')              
        if st.button("Start Recording and Convert"):
            with st.spinner("Recording..."):
                audio_file = record_audio(duration=duration)
            st.success("Recording Done")
    
            with st.spinner("Converting speech to text..."):
                recognized_text = speech_to_text(audio_file)
            st.success("Conversion Done")
    
            st.write("Recognized Text:")
            st.write(recognized_text)
    
            with st.spinner("Getting response from ChatGPT..."):
                response_text = get_chatgpt_response(recognized_text,temperature,max_tokens,frequency_penalty,presence_penalty)
            st.success("Response received")
    
            st.write("Response:")
            st.write(response_text)
    
            with st.spinner("Converting response to speech..."):
                text_to_speech(response_text)
            st.success("Synthesis complete")

    if classifier == 'Text':
                    
            
            st.write("Enter the Text and get Response:")
            recognized_text= st.text_area("Input Text")
            if st.button("Response"):
                if recognized_text:
                  
                    with st.spinner("Getting response from ChatGPT..."):
                        response_text = get_chatgpt_response(recognized_text,temperature,max_tokens,frequency_penalty,presence_penalty)
                    st.success("Response received")
            
                    st.write("Response:")
                    st.write(response_text)
            
                    with st.spinner("Converting response to speech..."):
                        text_to_speech(response_text)
                    st.success("Synthesis complete")
 
if __name__ == "__main__":
    main()