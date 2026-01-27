# Assessment System Components - Detailed Guide

This document provides a comprehensive breakdown of all components used in the assessment system, organized by phase/stage, with explanations of their purpose and usage.

---

## Table of Contents
1. [Assessment Overview](#assessment-overview)
2. [Assessment Phases](#assessment-phases)
3. [Frontend Components](#frontend-components)
4. [Backend Services](#backend-services)
5. [Data Flow](#data-flow)
6. [Component Usage by Phase](#component-usage-by-phase)

---

## Assessment Overview

The assessment system is a conversational English language assessment platform that evaluates:
- **Fluency** (20 points)
- **Pronunciation** (10 points)
- **Grammar** (10 points)
- **Confidence** (20 points)
- **Hesitation** (-10 penalty)
- **Storytelling** (20 points)
- **Vision Clarity** (10 points)

**Total Score: 100 points**

---

## Assessment Phases

The assessment consists of 7 stages:

1. **Welcome** - Initial setup and permissions
2. **Introduction** - Professional background introduction
3. **Reading** - Reading passage aloud
4. **Listening** - Listening comprehension and response
5. **Storytelling** - Narrative creation
6. **Opinion** - Opinion expression
7. **Aim** - Goals and aspirations discussion

---

## Frontend Components

### Core Assessment Components

#### 1. **Assessment.jsx** (Main Page)
**Location:** `frontend/src/pages/Assessment.jsx`

**Purpose:** Main orchestrator for the entire assessment flow

**Key Responsibilities:**
- Manages assessment lifecycle (start, progress, complete)
- Coordinates audio/video capture
- Handles stage transitions
- Plays AI greetings and responses
- Manages UI state (recording, processing, playing)

**Key Features:**
- Progress tracking with visual progress bar
- Real-time status indicators (recording, processing, AI speaking)
- Video feed monitoring
- Audio playback controls

**Why Used:** Central hub that coordinates all assessment activities and provides unified user experience.

---

#### 2. **useAssessment Hook**
**Location:** `frontend/src/hooks/useAssessment.js`

**Purpose:** State management for assessment flow

**Key Functions:**
- `startAssessment()` - Creates new assessment via API
- `saveStageResponse()` - Saves user response for current stage
- `nextStage()` - Advances to next assessment stage
- `completeAssessment()` - Finalizes assessment and generates scores
- `getAIResponse()` - Fetches AI conversational response

**State Managed:**
- Current assessment object
- Current stage index
- Stage responses history
- Loading/error states
- Completion status
- Score data

**Why Used:** Encapsulates all assessment logic, making it reusable and maintainable. Separates business logic from UI components.

---

#### 3. **useAudioRecorder Hook**
**Location:** `frontend/src/hooks/useAudioRecorder.js`

**Purpose:** Browser audio capture and recording

**Key Functions:**
- `startRecording()` - Begins audio capture from microphone
- `stopRecording()` - Stops recording and returns audio blob
- `pauseRecording()` / `resumeRecording()` - Pause/resume controls
- `resetRecording()` - Clears current recording

**Technical Details:**
- Uses `MediaRecorder` API
- Records in WebM or MP4 format
- Configurable sample rate (default: 16kHz)
- Auto-stops at max duration (5 minutes)
- Real-time duration tracking

**Why Used:** Provides clean interface for audio capture without exposing browser API complexity. Handles permission requests, format conversion, and error handling.

---

#### 4. **useVideoCapture Hook**
**Location:** `frontend/src/hooks/useVideoCapture.js`

**Purpose:** Webcam access and video stream management

**Key Functions:**
- `startStream()` - Initiates camera feed
- `stopStream()` - Stops camera feed
- `captureFrame()` - Captures single frame as image
- `getAverageMetrics()` - Returns aggregated vision metrics

**Metrics Tracked:**
- Face detection status
- Eye contact estimation
- Head stability score
- Face centering
- Confidence level

**Why Used:** Manages camera permissions and provides video stream for monitoring. Tracks visual metrics for assessment scoring (vision clarity).

---

### Stage Components

Each stage has a dedicated component that displays stage-specific content:

#### **WelcomeStage.jsx**
- **Purpose:** Initial welcome screen and permission request
- **Displays:** Welcome message, instructions, "Start Assessment" button
- **Action:** Requests camera/microphone permissions

#### **IntroductionStage.jsx**
- **Purpose:** Professional introduction stage
- **Displays:** Instructions for professional background, hints (Current Role, Key Expertise, Achievements)
- **Why:** Guides user on what to discuss

#### **ReadingStage.jsx**
- **Purpose:** Reading comprehension stage
- **Displays:** Passage to read aloud
- **Why:** Tests pronunciation and reading fluency

#### **ListeningStage.jsx**
- **Purpose:** Listening comprehension
- **Displays:** Instructions for listening task
- **Why:** Evaluates comprehension and response quality

#### **StorytellingStage.jsx**
- **Purpose:** Narrative creation
- **Displays:** Storytelling prompt
- **Why:** Assesses narrative structure and storytelling ability

#### **OpinionStage.jsx**
- **Purpose:** Opinion expression
- **Displays:** Opinion topic prompt
- **Why:** Tests ability to articulate and defend opinions

#### **AimStage.jsx**
- **Purpose:** Goals and aspirations discussion
- **Displays:** Goals discussion prompt
- **Why:** Evaluates future planning and goal articulation

**Why Stage Components:** Each stage needs unique UI/instructions. Separating them improves maintainability and allows stage-specific customization.

---

### Service Layer

#### **assessmentService.js**
**Location:** `frontend/src/services/assessmentService.js`

**Purpose:** API communication for assessment operations

**Key Methods:**
- `startAssessment()` - POST `/api/v1/assessments/`
- `submitResponse()` - Creates response + uploads audio + saves vision metrics
- `completeAssessment()` - POST `/api/v1/assessments/{id}/complete`
- `getAssessmentScore()` - GET `/api/v1/scoring/{id}`

**Why Used:** Centralizes API calls, handles request/response formatting, provides consistent error handling.

---

#### **conversationService.js**
**Location:** `frontend/src/services/conversationService.js`

**Purpose:** AI conversation interaction

**Key Methods:**
- `getGreeting()` - GET `/api/v1/conversation/greeting`
- `generateResponse()` - POST `/api/v1/conversation/generate-response`
- `processSpeech()` - POST `/api/v1/conversation/speech-to-text`

**Why Used:** Handles all AI conversation endpoints, manages conversation history, provides text-to-speech integration.

---

## Backend Services

### API Routers

#### 1. **assessments.py**
**Location:** `backend/app/routers/assessments.py`

**Purpose:** Assessment lifecycle management

**Endpoints:**
- `POST /api/v1/assessments/` - Create new assessment
- `GET /api/v1/assessments/` - List user's assessments
- `GET /api/v1/assessments/{id}` - Get specific assessment
- `POST /api/v1/assessments/{id}/complete` - Complete assessment and generate report
- `DELETE /api/v1/assessments/{id}` - Cancel assessment

**Key Features:**
- Auto-creates user profile if missing (self-healing)
- Generates final report on completion
- Calculates total score from all responses
- Saves detailed scores to `assessment_scores` table

**Why Used:** Manages assessment CRUD operations and triggers final scoring/reporting.

---

#### 2. **responses.py**
**Location:** `backend/app/routers/responses.py`

**Purpose:** Response submission and processing

**Endpoints:**
- `POST /api/v1/responses/` - Create response record
- `POST /api/v1/responses/{id}/audio` - Upload audio and process conversation
- `POST /api/v1/responses/{id}/vision` - Save vision metrics
- `GET /api/v1/responses/{id}` - Get response data

**Key Processing Flow (Audio Upload):**
1. Validates response exists
2. Gets/creates session for conversation tracking
3. Transcribes user audio (STT)
4. Gets AI agent response
5. Generates AI audio (TTS)
6. Merges conversation audio if transitioning
7. Uploads final audio to blob storage
8. Updates database with conversation history

**Why Used:** Handles the core conversational assessment logic - processes audio, manages AI interaction, tracks conversation state.

---

#### 3. **conversation.py**
**Location:** `backend/app/routers/conversation.py`

**Purpose:** AI conversation endpoints

**Endpoints:**
- `GET /api/v1/conversation/greeting` - Get section greeting
- `POST /api/v1/conversation/generate-response` - Generate AI response
- `POST /api/v1/conversation/speech-to-text` - Convert speech to text
- `POST /api/v1/conversation/upload-audio` - Upload audio to blob

**Why Used:** Provides conversational AI capabilities - greetings, responses, speech recognition. Used for initial greetings and standalone conversation features.

---

### AI Services

#### **Data Models**
**Location:** `backend/app/services/ai_assessment/models.py`

**Purpose:** Defines data structures for AI analysis results

**Key Models:**
- `AssessmentStepScore` - Individual response scores (fluency, pronunciation, grammar, etc.)
- `AIAnalysisResult` - Complete analysis result with transcript, scores, and AI response

**Why Used:** Provides type safety and structure for AI scoring results. Ensures consistent data format across the system.

#### 1. **ConversationalAgent**
**Location:** `backend/app/agents/conversational_agent.py`

**Purpose:** AI conversation management and flow control

**Key Methods:**
- `get_response()` - Generates AI response and determines section transition
- `generate_greeting()` - Creates initial greeting
- `generate_section_intro()` - Creates section transition messages

**Features:**
- Uses GPT-4o for natural conversation
- Tracks conversation history
- Determines when to transition to next section
- Calculates completeness score (1-10)
- Requires minimum 2 turns before allowing transition

**Transition Logic:**
- `should_transition = True` if:
  - Completeness score >= 6
  - Turn count >= 2
  - AI determines response is sufficient

**Why Used:** Manages natural conversation flow, asks follow-up questions, determines when user has provided sufficient response for each section.

---

#### 1a. **Section Prompts**
**Location:** `backend/app/agents/prompts.py`

**Purpose:** Defines AI behavior and objectives for each assessment section

**Key Features:**
- Section-specific system prompts for GPT-4o
- Defines conversation strategy for each stage
- Sets time limits and transition criteria
- Provides example questions and responses

**Prompt Structure:**
Each prompt includes:
- **Role Definition:** AI's persona (Emma, friendly interviewer)
- **Section Goal:** What to assess in this section
- **Key Information:** What to gather from user
- **Conversation Strategy:** How to conduct the conversation
- **Time Limit:** Expected duration
- **Response Format:** JSON structure required
- **Transition Criteria:** When to move to next section

**Sections Covered:**
- `GREETING_PROMPT` - Initial welcome and setup
- `INTRODUCTION_PROMPT` - Background information gathering
- `READING_PROMPT` - Reading passage and comprehension
- `LISTENING_PROMPT` - Listening comprehension with story
- `STORYTELLING_PROMPT` - Narrative creation
- `OPINION_PROMPT` - Opinion expression and defense
- `AIM_PROMPT` - Goals and aspirations discussion

**Why Used:** Ensures consistent AI behavior across all assessments. Provides clear guidelines for what to assess and how to conduct each section. Makes the AI's role explicit and predictable.

---

#### 2. **ScoringEngine**
**Location:** `backend/app/services/ai_assessment/scoring_engine.py`

**Purpose:** Analyzes individual responses and assigns scores

**Key Method:**
- `analyze_response()` - Evaluates transcript against rubric

**Scoring Rubric:**
- **Fluency** (20): Speaking pace and flow, deducts for pauses
- **Pronunciation** (10): Clarity and accuracy of sounds
- **Grammar** (10): Sentence structure and correctness
- **Confidence** (20): Tone assertiveness and steadiness
- **Hesitation** (-10): Penalty for fillers (um, ah)
- **Storytelling** (20): Narrative quality, structure
- **Vision Clarity** (10): Assumed 10 unless told otherwise

**Process:**
1. Receives user transcript and question context
2. Sends to GPT-4o with scoring rubric prompt
3. Returns structured JSON with scores and feedback
4. Calculates total step score (max 100)

**Why Used:** Provides AI-powered evaluation of each response against standardized rubric. More consistent and scalable than human evaluators.

---

#### 3. **ReportGenerator**
**Location:** `backend/app/services/ai_assessment/report_generator.py`

**Purpose:** Aggregates scores and generates final report

**Key Method:**
- `generate_report()` - Creates comprehensive assessment report

**Process:**
1. Receives list of all step scores from assessment
2. Calculates average scores across all responses
3. Sends averages to GPT-4o for qualitative analysis
4. Generates:
   - Overall summary
   - Strengths list
   - Weaknesses list
   - Recommendations list

**Why Used:** Provides holistic view of performance across all sections. Generates actionable feedback for improvement.

---

### Speech Services

#### **AzureSpeechService**
**Location:** `backend/app/services/ai_assessment/azure_speech.py`

**Purpose:** Speech-to-Text (STT) and Text-to-Speech (TTS)

**Key Methods:**
- `transcribe_audio()` - Converts audio to text
- `synthesize_speech()` - Converts text to speech (uploads to blob)
- `synthesize_speech_bytes()` - Converts text to speech (returns bytes)

**Technical Details:**
- Uses Azure Cognitive Services Speech SDK
- Converts audio formats (WebM → WAV) using ffmpeg
- Standardizes to 16kHz, mono, PCM WAV for STT
- Configurable voice for TTS

**Why Used:** Provides accurate speech recognition and natural-sounding speech synthesis. Essential for conversational assessment.

---

### Storage Services

#### **AzureStorageService**
**Location:** `backend/app/services/ai_assessment/azure_storage.py`

**Purpose:** Azure Blob Storage management

**Key Methods:**
- `upload_file()` - Uploads file to blob storage
- `generate_sas_url()` - Creates secure access URL

**Why Used:** Stores audio files (user recordings, AI responses, merged conversations) securely in cloud storage.

---

### Session Management

#### **SessionManager**
**Location:** `backend/app/services/session_manager.py`

**Purpose:** In-memory session state for ongoing conversations

**Key Methods:**
- `get_session()` - Gets or creates session for response_id
- `update_session()` - Updates session data
- `clear_session()` - Cleans up completed session

**Session Data:**
- `audio_merger` - Merges user and AI audio clips
- `conversation_history` - List of user/agent exchanges
- `turn_count` - Number of exchanges
- `section` - Current section name
- `started_at` - Session start timestamp

**Why Used:** Tracks conversation state across multiple turns. Allows merging all audio into single conversation file when section completes.

---

#### **AudioMerger**
**Location:** `backend/app/services/audio_merger.py`

**Purpose:** Merges multiple audio clips into single conversation

**Key Methods:**
- `add_clip()` - Adds audio clip (user or agent)
- `merge_conversation()` - Combines all clips into single WAV file

**Why Used:** Creates complete conversation audio file for storage and review. Maintains chronological order of user and AI speech.

---

### Database Services

#### **SupabaseService**
**Location:** `backend/app/services/supabase_client.py`

**Purpose:** Database operations via Supabase

**Key Operations:**
- Profile management
- Assessment CRUD
- Response storage
- Score storage
- Vision metrics storage

**Why Used:** Provides type-safe database access with RLS (Row Level Security) policies. Handles all persistent data storage.

---

## Data Flow

### Assessment Start Flow

```
User clicks "Start Assessment"
  ↓
Frontend: useAssessment.startAssessment()
  ↓
Frontend: assessmentService.startAssessment()
  ↓
Backend: POST /api/v1/assessments/
  ↓
Backend: Creates assessment record in database
  ↓
Backend: Returns assessment object
  ↓
Frontend: Sets current stage to "welcome"
```

---

### Response Submission Flow

```
User records audio and clicks "Stop & Submit"
  ↓
Frontend: handleStopRecording()
  ↓
Frontend: saveStageResponse({ audio, prompt, metrics })
  ↓
Frontend: assessmentService.submitResponse()
  ↓
Backend: POST /api/v1/responses/ (create response record)
  ↓
Backend: POST /api/v1/responses/{id}/audio (upload audio)
  ↓
Backend: Transcribe audio (Azure Speech STT)
  ↓
Backend: Get AI response (ConversationalAgent)
  ↓
Backend: Generate AI audio (Azure Speech TTS)
  ↓
Backend: Add clips to session (AudioMerger)
  ↓
Backend: If transitioning: Merge audio, upload to blob
  ↓
Backend: Update database with conversation history
  ↓
Backend: Return AI response with audio URL
  ↓
Frontend: Play AI audio response
  ↓
Frontend: If should_transition: Move to next stage
```

---

### Assessment Completion Flow

```
User completes final stage
  ↓
Frontend: completeAssessment()
  ↓
Backend: POST /api/v1/assessments/{id}/complete
  ↓
Backend: Fetch all responses with AI scores
  ↓
Backend: ReportGenerator.generate_report()
  ↓
Backend: Calculate average scores
  ↓
Backend: Generate qualitative feedback (GPT-4o)
  ↓
Backend: Save scores to assessment_scores table
  ↓
Backend: Update assessment status to "completed"
  ↓
Frontend: Navigate to results page
```

---

## Component Usage by Phase

### Phase 1: Welcome

**Frontend Components:**
- `Assessment.jsx` - Main page
- `WelcomeStage.jsx` - Welcome UI
- `useVideoCapture` - Requests camera permission
- `useAudioRecorder` - (Prepared, not active)

**Backend Components:**
- None (client-side only)

**Why:**
- Welcome is informational only
- Sets up permissions for subsequent stages
- No data sent to backend yet

---

### Phase 2: Introduction

**Frontend Components:**
- `Assessment.jsx` - Orchestrates flow
- `IntroductionStage.jsx` - Displays instructions
- `useAudioRecorder` - Records user speech
- `useVideoCapture` - Captures video metrics
- `conversationService` - Fetches AI greeting

**Backend Components:**
- `conversation.py` - `/greeting` endpoint
- `conversational_agent.py` - Generates greeting
- `azure_speech.py` - TTS for greeting audio
- `responses.py` - `/audio` endpoint for processing
- `session_manager.py` - Creates session
- `azure_speech.py` - STT for transcription
- `conversational_agent.py` - Generates AI response
- `azure_speech.py` - TTS for AI response
- `audio_merger.py` - Merges audio clips
- `azure_storage.py` - Stores final audio

**Data Flow:**
1. User sees greeting (AI speaks)
2. User records introduction
3. Audio transcribed → AI responds → Audio merged → Stored

**Why:**
- Tests professional communication
- Evaluates fluency, pronunciation, grammar
- Natural conversation flow with AI

---

### Phase 3: Reading

**Frontend Components:**
- `ReadingStage.jsx` - Displays passage
- `useAudioRecorder` - Records reading
- `useVideoCapture` - Vision metrics

**Backend Components:**
- Same as Introduction (conversational flow)
- `scoring_engine.py` - Scores pronunciation and fluency

**Why:**
- Tests reading fluency
- Evaluates pronunciation accuracy
- Measures reading pace

---

### Phase 4: Listening

**Frontend Components:**
- `ListeningStage.jsx` - Instructions
- `useAudioRecorder` - Records comprehension response
- `useVideoCapture` - Vision metrics

**Backend Components:**
- Same conversational flow
- `conversational_agent.py` - May ask comprehension questions

**Why:**
- Tests listening comprehension
- Evaluates ability to respond to questions
- Measures understanding and recall

---

### Phase 5: Storytelling

**Frontend Components:**
- `StorytellingStage.jsx` - Story prompt
- `useAudioRecorder` - Records narrative
- `useVideoCapture` - Vision metrics

**Backend Components:**
- Same conversational flow
- `scoring_engine.py` - Scores storytelling (20 points)

**Why:**
- Tests narrative structure
- Evaluates storytelling ability
- Measures beginning/middle/end organization

---

### Phase 6: Opinion

**Frontend Components:**
- `OpinionStage.jsx` - Opinion topic
- `useAudioRecorder` - Records opinion
- `useVideoCapture` - Vision metrics

**Backend Components:**
- Same conversational flow
- `conversational_agent.py` - May ask follow-up questions

**Why:**
- Tests opinion articulation
- Evaluates argumentation skills
- Measures confidence in expression

---

### Phase 7: Aim (Goals)

**Frontend Components:**
- `AimStage.jsx` - Goals prompt
- `useAudioRecorder` - Records goals discussion
- `useVideoCapture` - Vision metrics

**Backend Components:**
- Same conversational flow
- Final response triggers completion

**Why:**
- Tests future planning articulation
- Evaluates goal-setting communication
- Final assessment of overall communication skills

---

### Phase 8: Completion & Scoring

**Frontend Components:**
- `Assessment.jsx` - Triggers completion
- Results page (navigated to)

**Backend Components:**
- `assessments.py` - `/complete` endpoint
- `report_generator.py` - Aggregates all scores
- `scoring_engine.py` - (Already scored each response)
- Database - Stores final scores

**Process:**
1. Fetch all responses with AI classification scores
2. Calculate average scores across all sections
3. Generate qualitative report (strengths, weaknesses, recommendations)
4. Save to `assessment_scores` table
5. Update assessment status

**Why:**
- Provides comprehensive evaluation
- Generates actionable feedback
- Creates permanent record for user review

---

## Key Design Decisions

### Why Conversational Flow?
- **Natural Interaction:** Mimics real conversation, reducing test anxiety
- **Follow-up Questions:** AI can probe deeper for accurate assessment
- **Adaptive:** Can adjust based on user responses

### Why Session Management?
- **State Tracking:** Maintains conversation context across multiple turns
- **Audio Merging:** Combines all exchanges into single file
- **Efficiency:** Avoids database writes for every turn

### Why Azure Services?
- **Speech Recognition:** High accuracy for transcription
- **Text-to-Speech:** Natural-sounding AI voice
- **Blob Storage:** Scalable file storage with SAS URLs

### Why GPT-4o for Scoring?
- **Consistent Evaluation:** Standardized rubric application
- **Contextual Understanding:** Considers context, not just keywords
- **Scalable:** No need for human evaluators

### Why Separate Stage Components?
- **Maintainability:** Easy to modify individual stages
- **Customization:** Each stage can have unique UI/instructions
- **Reusability:** Components can be reused or replaced independently

---

## Summary

The assessment system uses a sophisticated architecture combining:
- **Frontend:** React hooks for state management, audio/video capture
- **Backend:** FastAPI routers for API endpoints
- **AI Services:** GPT-4o for conversation and scoring, Azure Speech for STT/TTS
- **Storage:** Azure Blob Storage for audio files, Supabase for structured data
- **Session Management:** In-memory tracking for conversation state

Each component serves a specific purpose in creating a natural, comprehensive English language assessment experience.
