# 🎥 YouTube Video Finder with AI Analysis

An intelligent YouTube video search automation tool that accepts voice or text input in Hindi/English, searches YouTube with advanced filtering, and provides AI-powered analysis using Google's Gemini AI.

## ✨ Features

- **Multi-language Input**: Voice and text input support for Hindi and English
- **Smart Translation**: Automatic translation from Hindi to English for YouTube search
- **Advanced Filtering**: Duration (4-20 minutes) and upload time (This week) filters
- **AI-Powered Analysis**: Comprehensive video analysis using Google Gemini AI
- **Automated Browser Control**: Selenium-based YouTube navigation
- **Rich Output**: Colored console output with JSON export

## 🛠️ Installation

### Prerequisites

- Python 3.8+
- Google Chrome browser
- Microphone (for voice input)
- Google Gemini API key

### Setup Steps

1. **Install Dependencies**
```bash
pip install -r requirements.txt
```

2. **Set Up API Key**
   - Get your Google Gemini API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
   - Open `youtube_video_finder.py`
   - Replace the API key on line 903:
   ```python
   GEMINI_API_KEY = "your_actual_api_key_here"
   ```

3. **Verify Setup**
```bash
python test_setup.py
```

## 🚀 Usage

```bash
python youtube_video_finder.py
```

### Input Options

1. **Voice input (English)** - Speak your search query in English
2. **Voice input (Hindi)** - Speak in Hindi, auto-translated to English  
3. **Text input** - Type your search query

### Example Queries
- "health video"
- "fitness workout"
- "स्वास्थ्य वीडियो" (health video in Hindi)

## 🎯 How It Works

1. **Input**: Voice (Hindi/English) or text input
2. **Translation**: Hindi to English if needed
3. **Search**: YouTube search with filters (4-20 min duration, this week)
4. **Extract**: Top 20 video results with metadata
5. **Analyze**: AI analysis using Google Gemini
6. **Output**: Formatted results + JSON export

## 📁 Output Format

Results saved as `youtube_results_YYYYMMDD_HHMMSS.json`:

```json
{
  "search_query": "health video",
  "timestamp": "20241215_143022",
  "total_videos": 20,
  "best_video_recommendation": {...},
  "videos": [...],
  "ai_analysis": "..."
}
```

## 🤖 AI Features

- Top video recommendations with explanations
- Content theme analysis
- Channel quality assessment
- Personalized suggestions

## 🐛 Troubleshooting

**ChromeDriver Issues:**
```bash
pip install --upgrade webdriver-manager
```

**Audio Issues:**
- Linux: `sudo apt install portaudio19-dev`
- Windows: `pip install pipwin && pipwin install pyaudio`
- macOS: `brew install portaudio`

**API Errors:**
- Verify API key is correct
- Check quota limits
- Ensure internet connection

## 📋 Dependencies

- `selenium` - Web automation
- `webdriver-manager` - Chrome driver management
- `google-generativeai` - Gemini AI integration
- `speechrecognition` - Voice input processing
- `pyaudio` - Audio capture
- `googletrans` - Translation
- `colorama` - Colored output
- `tqdm` - Progress indicators

## 🔐 Privacy

- Voice processed by Google Speech Recognition API
- No local voice data storage
- YouTube browsing follows normal patterns
- Keep API keys secure

## ⚖️ License

Educational and personal use. Respect YouTube's terms of service.

---
**Happy Video Hunting! 🎥✨** 