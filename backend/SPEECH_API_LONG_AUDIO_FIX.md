# Azure Speech API: Long Audio Transcription Issue

## 🔴 **Problem Identified**

When audio is too long (exceeds ~30 seconds), the transcription is incomplete - only part of the audio is transcribed.

---

## 🎯 **Root Cause: `recognize_once()` Limitation**

Your code uses [`recognize_once()`](backend/app/services/ai_assessment/azure_speech.py#L156-L159) and [`recognize_once_async()`](backend/app/services/ai_assessment/azure_speech.py#L283):

```python
# Line 156-159: speech_to_text method
def _sync_recognize():
    return recognizer.recognize_once()

# Line 283: transcribe_audio method  
result = recognizer.recognize_once()
```

### **Official Microsoft Documentation States:**

> **"Performs recognition in a blocking (synchronous) mode. Returns after a single utterance is recognized. The end of a single utterance is determined by listening for silence at the end or until a maximum of about 30 seconds of audio is processed."**

**Source:** [Microsoft Learn - SpeechRecognizer.recognize_once](https://learn.microsoft.com/python/api/azure-cognitiveservices-speech/azure.cognitiveservices.speech.speechrecognizer)

### **Key Limitations:**

| Parameter | Default Limit | Impact |
|-----------|---------------|--------|
| **Maximum Duration** | ~30 seconds | Audio longer than 30s gets cut off |
| **EndSilenceTimeout** | ~1-2 seconds | Stops after brief silence |
| **InitialSilenceTimeout** | ~5 seconds | Gives up if no speech starts |
| **Single Utterance** | Yes | Designed for commands/queries, not conversations |

---

## 📊 **Why This Happens**

The Azure Speech SDK's `recognize_once()` method is designed for:
- ✅ Voice commands ("Alexa, play music")
- ✅ Short queries ("What's the weather?")
- ✅ Single sentences

**NOT designed for:**
- ❌ Long-form speech (>30 seconds)
- ❌ Continuous conversation
- ❌ Storytelling assessments
- ❌ Extended responses

---

## 🔍 **Evidence from Your Codebase**

Looking at your assessment stages:

```python
SECTION_ORDER = ["introduction", "reading", "listening", "storytelling", "opinion", "aim"]
```

Some sections like **storytelling** and **opinion** can easily exceed 30 seconds when users speak continuously.

**Example scenario:**
- User speaks for 45 seconds during storytelling
- `recognize_once()` processes first 30 seconds
- Remaining 15 seconds are **silently discarded**
- Transcript is incomplete → affects scoring accuracy

---

## ✅ **Solutions**

### **Option 1: Use Continuous Recognition (RECOMMENDED)**

Switch from `recognize_once()` to `start_continuous_recognition_async()`:

```python
async def transcribe_audio_continuous(self, audio_bytes: bytes) -> str:
    """
    Transcribe audio using continuous recognition for long audio.
    """
    import tempfile
    import os
    
    def _sync_transcribe():
        try:
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_file.write(audio_bytes)
                temp_path = temp_file.name
            
            speech_config = self._create_speech_config()
            audio_config = speechsdk.AudioConfig(filename=temp_path)
            recognizer = speechsdk.SpeechRecognizer(
                speech_config=speech_config, 
                audio_config=audio_config
            )
            
            # Store all recognized results
            all_results = []
            done_flag = False
            
            def handle_recognized(evt):
                if evt.result.text:
                    all_results.append(evt.result.text)
                    logger.info(f"Recognized: {evt.result.text[:50]}...")
            
            def handle_canceled(evt):
                nonlocal done_flag
                done_flag = True
                logger.warning(f"Recognition canceled: {evt.reason}")
            
            # Connect event handlers
            recognizer.recognized.connect(handle_recognized)
            recognizer.canceled.connect(handle_canceled)
            
            # Start continuous recognition
            recognizer.start_continuous_recognition()
            
            # Wait until done (file ends or silence timeout)
            import time
            while not done_flag:
                time.sleep(0.5)
            
            # Stop recognition
            recognizer.stop_continuous_recognition()
            
            # Combine all results
            full_transcript = " ".join(all_results)
            logger.info(f"Full transcript length: {len(full_transcript)} chars")
            return full_transcript
            
        finally:
            try:
                os.remove(temp_path)
            except:
                pass
    
    return await asyncio.to_thread(_sync_transcribe)
```

**Benefits:**
- ✅ No 30-second limit - handles minutes of audio
- ✅ Captures complete transcript
- ✅ Still respects silence timeouts (configurable)
- ✅ Better for storytelling/opinion sections

**Trade-offs:**
- ⚠️ Slightly more complex code
- ⚠️ Need to manage event handlers
- ⚠️ May need to tune silence timeouts

---

### **Option 2: Increase Silence Timeouts (QUICK FIX)**

If most of your audio is just slightly over 30s, you can extend timeouts:

```python
def _create_speech_config(self, voice_name: Optional[str] = None) -> speechsdk.SpeechConfig:
    config = speechsdk.SpeechConfig(
        subscription=self.speech_key,
        region=self.speech_region
    )
    config.speech_recognition_language = self.speech_language
    config.speech_synthesis_voice_name = voice_name or self.tts_voice
    
    # ADD THESE LINES to extend timeouts
    config.set_property_by_name("SpeechServiceConnection_InitialSilenceTimeout", "10000")  # 10s
    config.set_property_by_name("SpeechServiceConnection_EndSilenceTimeout", "5000")      # 5s
    config.set_property_by_name("SpeechServiceConnection_SegmentationSilenceTimeout", "3000")  # 3s
    
    return config
```

**Warning:** This won't fully solve the problem for very long audio (>60s). Microsoft may still enforce server-side limits.

---

### **Option 3: Chunk Long Audio (ADVANCED)**

Split audio into 25-second chunks and transcribe each separately:

```python
async def transcribe_long_audio(self, audio_bytes: bytes, chunk_duration_sec: int = 25) -> str:
    """
    Split long audio into chunks and transcribe each.
    """
    import soundfile as sf
    import numpy as np
    from io import BytesIO
    
    # Load audio
    audio_data, sample_rate = sf.read(BytesIO(audio_bytes))
    
    # Calculate chunks
    samples_per_chunk = int(sample_rate * chunk_duration_sec)
    total_chunks = (len(audio_data) + samples_per_chunk - 1) // samples_per_chunk
    
    all_transcripts = []
    
    for i in range(total_chunks):
        start = i * samples_per_chunk
        end = min((i + 1) * samples_per_chunk, len(audio_data))
        chunk_data = audio_data[start:end]
        
        # Convert chunk to WAV bytes
        chunk_buffer = BytesIO()
        sf.write(chunk_buffer, chunk_data, sample_rate, format='WAV')
        chunk_bytes = chunk_buffer.getvalue()
        
        # Transcribe chunk
        chunk_transcript = await self.transcribe_audio(chunk_bytes)
        if chunk_transcript:
            all_transcripts.append(chunk_transcript)
    
    # Combine transcripts
    full_transcript = " ".join(all_transcripts)
    return full_transcript
```

**Benefits:**
- ✅ Works around hard 30s limit
- ✅ More reliable than continuous recognition
- ✅ Can process chunks in parallel

**Trade-offs:**
- ⚠️ Loses context between chunks
- ⚠️ More CPU/memory usage
- ⚠️ Requires soundfile/numpy

---

## 🎯 **Recommended Approach for Your Use Case**

Based on your assessment flow:

### **For Individual Response Transcription** (`transcribe_audio` method)
Use **Continuous Recognition** (Option 1) because:
- Storytelling/opinion sections often exceed 30s
- Users speak in natural paragraphs, not single sentences
- You want complete transcripts for accurate scoring

### **For Pronunciation Assessment** (`speech_to_text` method)
Keep `recognize_once()` but add timeout configuration because:
- Reading/listening sections use short reference texts
- Users repeat short sentences (5-15 seconds)
- 30s limit is sufficient for these use cases

---

## 🛠️ **Implementation Steps**

### **Step 1: Add Continuous Recognition Method**

Add to `backend/app/services/ai_assessment/azure_speech.py`:

```python
async def transcribe_audio_continuous(self, audio_bytes: bytes, timeout_seconds: int = 60) -> str:
    """
    Transcribe audio using continuous recognition for long-form speech.
    Suitable for storytelling, opinion sections (up to several minutes).
    """
    # Implementation from Option 1 above
```

### **Step 2: Update Upload Handler**

In `backend/app/routers/responses.py` line 316:

```python
# BEFORE (limited to 30s)
transcript = await speech_service.transcribe_audio(
    wav_audio_bytes if wav_audio_bytes else audio_bytes
)

# AFTER (use continuous for long sections)
if section_name in ["storytelling", "opinion", "aim"]:
    transcript = await speech_service.transcribe_audio_continuous(wav_audio_bytes)
else:
    transcript = await speech_service.transcribe_audio(wav_audio_bytes)
```

### **Step 3: Configure Timeouts**

Update `_create_speech_config()` to extend silence detection:

```python
def _create_speech_config(self, voice_name: Optional[str] = None) -> speechsdk.SpeechConfig:
    config = speechsdk.SpeechConfig(
        subscription=self.speech_key,
        region=self.speech_region
    )
    config.speech_recognition_language = self.speech_language
    config.speech_synthesis_voice_name = voice_name or self.tts_voice
    
    # Extend timeouts for longer utterances
    config.set_property_by_name("SpeechServiceConnection_InitialSilenceTimeout", "8000")
    config.set_property_by_name("SpeechServiceConnection_EndSilenceTimeout", "3000")
    
    return config
```

### **Step 4: Add Logging**

Monitor transcription quality:

```python
logger.info(f"Audio duration: {duration:.1f}s, Transcript: {len(transcript)} chars")
if duration > 25:
    logger.warning(f"Long audio detected ({duration:.1f}s) - verify completeness")
```

---

## 📈 **Testing Recommendations**

1. **Create test cases** with varying durations:
   - 10s (short response)
   - 30s (current limit boundary)
   - 60s (typical storytelling)
   - 120s (extended opinion)

2. **Compare methods**:
   - `recognize_once()` vs `continuous_recognition()`
   - Measure transcript completeness
   - Check scoring accuracy impact

3. **Monitor production**:
   - Log audio durations per section
   - Track cancellation reasons
   - Alert on transcripts < expected length

---

## ⚠️ **Additional Considerations**

### **Azure Service Limits**

Even with continuous recognition, be aware of:
- **Maximum session duration**: ~15 minutes for real-time recognition
- **Network bandwidth**: Streaming audio consumes data
- **Latency**: Continuous mode sends audio in chunks

### **Cost Implications**

Azure Speech pricing:
- First 5 hours/month: Free
- After that: ~$1/hour of audio
- Continuous recognition doesn't increase cost (still pay per second)

### **User Experience**

Set appropriate expectations:
- Show recording timer to users
- Warn if approaching time limits
- Provide visual feedback during processing

---

## 📝 **Summary**

**Problem:** `recognize_once()` has a hard ~30-second limit, causing incomplete transcripts for longer responses.

**Solution:** Switch to `start_continuous_recognition_async()` for sections where users speak >30 seconds (storytelling, opinion, aim).

**Impact:** 
- ✅ Complete transcripts → better scoring accuracy
- ✅ Improved user experience (no arbitrary cutoffs)
- ⚠️ Slightly more complex implementation
- ⚠️ Need to test thoroughly

**Priority:** HIGH - This directly impacts assessment quality and fairness.

---

## 🔗 **References**

- [Microsoft Docs: SpeechRecognizer.recognize_once](https://learn.microsoft.com/python/api/azure-cognitiveservices-speech/azure.cognitiveservices.speech.speechrecognizer)
- [Microsoft Docs: Set speech recognition timeouts](https://learn.microsoft.com/azure/ai-services/speech-service/how-to-recognize-speech#change-how-silence-is-handled)
- [Stack Overflow: Increasing listen duration](https://stackoverflow.com/questions/78185534/how-to-increase-the-time-for-which-the-microsoft-speech-service-sdk-listens-in-a)
- [GitHub Issue: Premature recognition stop](https://github.com/Azure-Samples/cognitive-services-speech-sdk/issues/2740)
