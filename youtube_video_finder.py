import os
import time
import json
import re
import speech_recognition as sr
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from googletrans import Translator
import google.generativeai as genai
from colorama import init, Fore, Style
from tqdm import tqdm

# Initialize colorama for colored output
init()

class YouTubeVideoFinder:
    def __init__(self, gemini_api_key):
        """Initialize the YouTube Video Finder with Gemini AI integration"""
        self.gemini_api_key = gemini_api_key
        self.translator = Translator()
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.driver = None
        self.wait = None
        
        # Initialize Gemini AI
        genai.configure(api_key=gemini_api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        
    def setup_driver(self):
        """Setup Chrome WebDriver with optimal settings"""
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-plugins")
        
        # Find Chrome binary
        import shutil
        import os
        chrome_paths = [
            "/usr/bin/google-chrome",
            "/usr/bin/google-chrome-stable", 
            "/usr/bin/chromium-browser",
            "/opt/google/chrome/google-chrome"
        ]
        
        chrome_binary = None
        for path in chrome_paths:
            if shutil.which(path):
                chrome_binary = path
                break
                
        if chrome_binary:
            chrome_options.binary_location = chrome_binary
            print(f"{Fore.CYAN}Using Chrome binary: {chrome_binary}{Style.RESET_ALL}")
        else:
            print(f"{Fore.YELLOW}No Chrome binary found in standard locations{Style.RESET_ALL}")
        
        # Try local ChromeDriver first (downloaded version)
        local_chromedriver = "./chromedriver-linux64/chromedriver"
        if os.path.isfile(local_chromedriver) and os.access(local_chromedriver, os.X_OK):
            try:
                print(f"{Fore.CYAN}Trying local ChromeDriver: {local_chromedriver}{Style.RESET_ALL}")
                service = Service(local_chromedriver)
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
                print(f"{Fore.GREEN}✓ Local ChromeDriver working{Style.RESET_ALL}")
                self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
                self.wait = WebDriverWait(self.driver, 20)
                print(f"{Fore.GREEN}✓ Chrome WebDriver initialized successfully{Style.RESET_ALL}")
                return
            except Exception as e:
                print(f"{Fore.YELLOW}Local ChromeDriver failed: {e}{Style.RESET_ALL}")
        
        # Try system chromedriver as fallback
        try:
            print(f"{Fore.CYAN}Trying system ChromeDriver...{Style.RESET_ALL}")
            self.driver = webdriver.Chrome(options=chrome_options)
            print(f"{Fore.GREEN}✓ System ChromeDriver working{Style.RESET_ALL}")
            
        except Exception as e:
            print(f"{Fore.YELLOW}System ChromeDriver failed: {e}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}Trying ChromeDriverManager...{Style.RESET_ALL}")
            
            try:
                # Try to use ChromeDriverManager as last resort
                driver_path = ChromeDriverManager().install()
                print(f"{Fore.CYAN}Using ChromeDriver at: {driver_path}{Style.RESET_ALL}")
                
                # Verify the downloaded file is executable
                if not os.path.isfile(driver_path) or not os.access(driver_path, os.X_OK):
                    raise Exception(f"ChromeDriver at {driver_path} is not executable")
                    
                service = Service(driver_path)
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
                
            except Exception as e2:
                print(f"{Fore.RED}ChromeDriverManager also failed: {e2}{Style.RESET_ALL}")
                print(f"{Fore.YELLOW}Please install ChromeDriver manually or update Chrome/ChromeDriver{Style.RESET_ALL}")
                raise Exception("Could not initialize ChromeDriver. Please ensure Chrome and ChromeDriver are properly installed.")
        
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        self.wait = WebDriverWait(self.driver, 20)
        
        print(f"{Fore.GREEN}✓ Chrome WebDriver initialized successfully{Style.RESET_ALL}")
    
    def get_voice_input(self, language='en'):
        """Capture voice input in Hindi or English"""
        print(f"{Fore.CYAN}🎤 Listening for voice input...{Style.RESET_ALL}")
        
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source)
        
        try:
            with self.microphone as source:
                print(f"{Fore.YELLOW}Speak now...{Style.RESET_ALL}")
                audio = self.recognizer.listen(source, timeout=10, phrase_time_limit=15)
            
            # Recognize speech in both Hindi and English
            if language == 'hi':
                text = self.recognizer.recognize_google(audio, language='hi-IN')
                print(f"{Fore.GREEN}Hindi Input: {text}{Style.RESET_ALL}")
                # Translate to English for YouTube search
                translated = self.translator.translate(text, dest='en')
                english_text = translated.text
                print(f"{Fore.GREEN}English Translation: {english_text}{Style.RESET_ALL}")
                return english_text, text
            else:
                text = self.recognizer.recognize_google(audio, language='en-US')
                print(f"{Fore.GREEN}English Input: {text}{Style.RESET_ALL}")
                return text, text
                
        except sr.WaitTimeoutError:
            print(f"{Fore.RED}❌ Listening timeout{Style.RESET_ALL}")
            return None, None
        except sr.UnknownValueError:
            print(f"{Fore.RED}❌ Could not understand audio{Style.RESET_ALL}")
            return None, None
        except sr.RequestError as e:
            print(f"{Fore.RED}❌ Error with speech recognition: {e}{Style.RESET_ALL}")
            return None, None
    
    def get_text_input(self):
        """Get text input from user"""
        text = input(f"{Fore.CYAN}Enter your search query: {Style.RESET_ALL}")
        return text.strip()
    
    def navigate_to_youtube(self):
        """Navigate to YouTube homepage"""
        print(f"{Fore.CYAN}🌐 Opening YouTube...{Style.RESET_ALL}")
        self.driver.get("https://www.youtube.com")
        
        # Wait for page to load
        try:
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "ytd-app")))
            print(f"{Fore.GREEN}✓ YouTube loaded successfully{Style.RESET_ALL}")
            time.sleep(2)
        except TimeoutException:
            print(f"{Fore.RED}❌ Failed to load YouTube{Style.RESET_ALL}")
            return False
        return True
    
    def search_youtube(self, query):
        """Search for videos on YouTube"""
        print(f"{Fore.CYAN}🔍 Searching for: '{query}'...{Style.RESET_ALL}")
        
        try:
            # Wait a bit for any lazy loading
            time.sleep(2)
            
            # Try multiple search box selectors (YouTube changes these frequently)
            search_selectors = [
                "input[name='search_query']",
                "input#search",
                "#search-input input",
                "ytd-searchbox input",
                "input[placeholder*='Search']"
            ]
            
            search_box = None
            for selector in search_selectors:
                try:
                    search_box = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
                    print(f"{Fore.GREEN}Found search box with selector: {selector}{Style.RESET_ALL}")
                    break
                except TimeoutException:
                    continue
            
            if not search_box:
                # Try XPath approach
                try:
                    search_box = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@placeholder='Search']")))
                    print(f"{Fore.GREEN}Found search box with XPath{Style.RESET_ALL}")
                except TimeoutException:
                    print(f"{Fore.RED}❌ Could not find search box{Style.RESET_ALL}")
                    return False
            
            # Clear and enter search query
            search_box.clear()
            search_box.send_keys(query)
            time.sleep(1)
            
            # Try multiple search button selectors
            search_button_selectors = [
                "#search-icon-legacy",
                "button#search-icon-legacy",
                "[aria-label='Search']",
                "ytd-searchbox button",
                "#searchbox button"
            ]
            
            search_button = None
            for selector in search_button_selectors:
                try:
                    search_button = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
                    print(f"{Fore.GREEN}Found search button with selector: {selector}{Style.RESET_ALL}")
                    break
                except TimeoutException:
                    continue
            
            if not search_button:
                # Try pressing Enter instead
                print(f"{Fore.YELLOW}Search button not found, trying Enter key{Style.RESET_ALL}")
                search_box.send_keys(Keys.RETURN)
            else:
                search_button.click()
            
            # Wait for search results to load
            print(f"{Fore.CYAN}Waiting for search results...{Style.RESET_ALL}")
            
            # Try multiple selectors for results container
            results_selectors = [
                "#contents",
                "ytd-video-renderer",
                "#primary #contents",
                "[data-target-id='watch-card-compact-video']",
                ".ytd-item-section-renderer",
                "//button[@class='ytSearchboxComponentSearchButton']"
            ]
            
            results_loaded = False
            for selector in results_selectors:
                try:
                    self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                    print(f"{Fore.GREEN}Search results loaded (found: {selector}){Style.RESET_ALL}")
                    results_loaded = True
                    break
                except TimeoutException:
                    continue
            
            if not results_loaded:
                print(f"{Fore.RED}❌ Search results did not load properly{Style.RESET_ALL}")
                return False
                
            print(f"{Fore.GREEN}✓ Search completed{Style.RESET_ALL}")
            time.sleep(3)
            return True
            
        except Exception as e:
            print(f"{Fore.RED}❌ Search failed with error: {e}{Style.RESET_ALL}")
            return False
    
    def apply_filters(self):
        """Apply filters: This week + 4-20 minutes duration"""
        print(f"{Fore.CYAN}⚙️ Applying filters...{Style.RESET_ALL}")
        
        try:
            # Scroll to top to avoid any overlay issues
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(1)
            
            # Try multiple approaches to find and click the Filters button
            filters_selectors = [
                "//span[text()='Filters']",
                "//button[contains(@aria-label, 'Search filters')]",
                "//button[contains(@class, 'filter')]",
                "//yt-chip-cloud-chip-renderer[contains(@class, 'filter')]",
                "[aria-label*='filter']"
            ]
            
            filters_button = None
            for selector in filters_selectors:
                try:
                    if selector.startswith("//"):
                        filters_button = self.wait.until(EC.presence_of_element_located((By.XPATH, selector)))
                    else:
                        filters_button = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                    
                    # Scroll element into view
                    self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", filters_button)
                    time.sleep(1)
                    
                    # Try JavaScript click first (most reliable)
                    self.driver.execute_script("arguments[0].click();", filters_button)
                    print(f"{Fore.GREEN} ✓ Filters button clicked using JS{Style.RESET_ALL}")
                    break
                    
                except Exception as e:
                    continue
                    
            if not filters_button:
                print(f"{Fore.YELLOW}⚠️ Could not find filters button, continuing without filters{Style.RESET_ALL}")
                return False
                
            time.sleep(2)
            
            # Click "This week" filter
            time_filter_selectors = [
                "//yt-formatted-string[text()='This week']",
                "//a[contains(text(), 'This week')]",
                "//span[text()='This week']",
                "[aria-label*='This week']"
            ]
            
            time_filter = None
            for selector in time_filter_selectors:
                try:
                    if selector.startswith("//"):
                        time_filter = self.wait.until(EC.presence_of_element_located((By.XPATH, selector)))
                    else:
                        time_filter = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                    
                    # Scroll and click with JavaScript
                    self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", time_filter)
                    time.sleep(1)
                    self.driver.execute_script("arguments[0].click();", time_filter)
                    print(f"{Fore.GREEN} ✓ This week filter applied{Style.RESET_ALL}")
                    break
                    
                except Exception as e:
                    continue
                    
            if not time_filter:
                print(f"{Fore.YELLOW}⚠️ Could not apply 'This week' filter{Style.RESET_ALL}")
            
            time.sleep(2)
            
            # Click Filters again to access duration
            try:
                # Find filters button again (it might have changed)
                for selector in filters_selectors:
                    try:
                        if selector.startswith("//"):
                            filters_button = self.driver.find_element(By.XPATH, selector)
                        else:
                            filters_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                        
                        self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", filters_button)
                        time.sleep(1)
                        self.driver.execute_script("arguments[0].click();", filters_button)
                        print(f"{Fore.GREEN} ✓ Filters reopened{Style.RESET_ALL}")
                        break
                    except:
                        continue
            except Exception as e:
                print(f"{Fore.YELLOW}⚠️ Could not reopen filters for duration{Style.RESET_ALL}")
            
            time.sleep(2)
            
            # Click "4-20 minutes" duration filter
            duration_filter_selectors = [
                "//ytd-search-filter-renderer//yt-formatted-string[text()='4 - 20 minutes']",
                "//a[@id='endpoint']//yt-formatted-string[text()='4 - 20 minutes']",
                "//div[@title='Search for 4 - 20 minutes']",
                "//a[contains(@href, 'EgYIAxABGAM')]",
                "//yt-formatted-string[text()='4 - 20 minutes']",
                "//a[contains(text(), '4 - 20 minutes')]",
                "//span[text()='4 - 20 minutes']",
                "[aria-label*='4 - 20 minutes']"
            ]
            
            duration_filter = None
            for selector in duration_filter_selectors:
                try:
                    if selector.startswith("//"):
                        duration_filter = self.wait.until(EC.presence_of_element_located((By.XPATH, selector)))
                    else:
                        duration_filter = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                    
                    # Scroll and click with JavaScript
                    self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", duration_filter)
                    time.sleep(1)
                    
                    # Try clicking the parent anchor if we found the yt-formatted-string
                    if "yt-formatted-string" in selector:
                        # Find the parent anchor element
                        parent_anchor = duration_filter.find_element(By.XPATH, "./ancestor::a[@id='endpoint']")
                        self.driver.execute_script("arguments[0].click();", parent_anchor)
                    else:
                        self.driver.execute_script("arguments[0].click();", duration_filter)
                    
                    print(f"{Fore.GREEN} ✓ Duration filter (4-20 minutes) applied{Style.RESET_ALL}")
                    break
                    
                except Exception as e:
                    print(f"{Fore.YELLOW}⚠️ Selector '{selector}' failed: {str(e)[:50]}...{Style.RESET_ALL}")
                    continue
                    
            if not duration_filter:
                print(f"{Fore.YELLOW}⚠️ Could not apply duration filter{Style.RESET_ALL}")
            
            time.sleep(3)
            print(f"{Fore.GREEN}✓ Filters applied successfully{Style.RESET_ALL}")
            return True
            
        except Exception as e:
            print(f"{Fore.YELLOW}⚠️ Filter application had issues: {e}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}Continuing without all filters...{Style.RESET_ALL}")
            return False
    
    def extract_video_data(self):
        """Extract video data from search results"""
        print(f"{Fore.CYAN}📊 Extracting video data...{Style.RESET_ALL}")
        
        videos = []
        try:
            # Check if browser is still available
            try:
                self.driver.current_url
            except Exception as e:
                print(f"{Fore.RED}❌ Browser window was closed: {e}{Style.RESET_ALL}")
                return []
            
            # Wait a bit for any redirects or pop-ups to settle
            time.sleep(3)
            
            # Check for and handle any pop-ups or overlays
            try:
                # Look for common YouTube pop-up close buttons
                popup_selectors = [
                    "button[aria-label='Dismiss']",
                    "button[aria-label='Close']", 
                    "yt-icon-button[aria-label='Dismiss']",
                    ".dismiss-button"
                ]
                
                for selector in popup_selectors:
                    try:
                        popup = self.driver.find_element(By.CSS_SELECTOR, selector)
                        if popup.is_displayed():
                            self.driver.execute_script("arguments[0].click();", popup)
                            print(f"{Fore.GREEN}✓ Dismissed popup{Style.RESET_ALL}")
                            time.sleep(1)
                    except:
                        continue
            except:
                pass
            
            # Enhanced scrolling to load more videos (scroll more times and wait longer)
            print(f"{Fore.CYAN}📜 Scrolling to load more videos...{Style.RESET_ALL}")
            for i in range(6):  # Increased from 3 to 6
                try:
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(3)  # Increased wait time
                    
                    # Check how many videos we have so far
                    temp_containers = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'ytd-video-renderer')]")
                    print(f"{Fore.YELLOW}   Scroll {i+1}: Found {len(temp_containers)} video containers{Style.RESET_ALL}")
                    
                    # If we have enough videos, stop scrolling
                    if len(temp_containers) >= 20:
                        print(f"{Fore.GREEN}✓ Found enough videos, stopping scroll{Style.RESET_ALL}")
                        break
                        
                except Exception as e:
                    print(f"{Fore.YELLOW}⚠️ Scrolling failed: {e}{Style.RESET_ALL}")
                    break
            
            # Find all video containers with the specific YouTube selector
            video_container_selectors = [
                "//div[@class='style-scope ytd-video-renderer'][@id='dismissible']",  # Primary selector from user
                "//div[contains(@class, 'ytd-video-renderer')][@id='dismissible']",   # Fallback with contains
                "//div[contains(@class, 'ytd-video-renderer')]",  # Original fallback
                "//ytd-video-renderer",
                "//div[@class='ytd-video-renderer']",
                "//div[contains(@class, 'video-renderer')]",
                "//div[contains(@class, 'ytd-compact-video-renderer')]"
            ]
            
            video_containers = []
            for selector in video_container_selectors:
                try:
                    containers = self.driver.find_elements(By.XPATH, selector)
                    if containers:
                        video_containers = containers
                        print(f"{Fore.GREEN}Found {len(containers)} video containers using: {selector}{Style.RESET_ALL}")
                        break
                except Exception as e:
                    print(f"{Fore.YELLOW}⚠️ Selector '{selector}' failed: {e}{Style.RESET_ALL}")
                    continue
            
            if not video_containers:
                print(f"{Fore.RED}❌ Could not find video containers{Style.RESET_ALL}")
                return []
            
            print(f"{Fore.CYAN}🎯 Processing videos to extract top 20...{Style.RESET_ALL}")
            
            # Process up to 30 containers to ensure we get 20 good videos
            for i, container in enumerate(video_containers[:30], 1):
                try:
                    # Check if browser is still available
                    self.driver.current_url
                    
                    video_data = {'title': 'Unknown Title', 'url': 'Unknown URL', 'channel': 'Unknown Channel', 
                                'views': 'Unknown views', 'upload_time': 'Unknown time', 'duration': 'Unknown duration'}
                    
                    # Enhanced title extraction for the specific container structure
                    title_selectors = [
                        ".//a[@id='video-title']",                    # Primary video title link
                        ".//h3//a[@title]",                          # H3 with title attribute
                        ".//a[@id='video-title-link']",              # Alternative video title link
                        ".//yt-formatted-string[@id='video-title']", # Formatted string title
                        ".//div[@id='meta']//a[@href]",              # Meta section link
                        ".//div[@id='details']//a[@href]",           # Details section link
                        ".//a[contains(@href, '/watch?v=')][@title]" # Any watch link with title
                    ]
                    
                    for selector in title_selectors:
                        try:
                            title_element = container.find_element(By.XPATH, selector)
                            # Try title attribute first, then text content
                            title = (title_element.get_attribute('title') or 
                                   title_element.get_attribute('aria-label') or 
                                   title_element.text).strip()
                            
                            if title and len(title) > 5 and title not in ['Watch', 'Video', 'YouTube']:
                                video_data['title'] = title
                                break
                        except:
                            continue
                    
                    # Enhanced URL extraction 
                    url_selectors = [
                        ".//a[@id='video-title']",
                        ".//a[@id='video-title-link']", 
                        ".//h3//a[@href]",
                        ".//a[contains(@href, '/watch?v=')]",
                        ".//a[contains(@href, '/shorts/')]"
                    ]
                    
                    for selector in url_selectors:
                        try:
                            link_element = container.find_element(By.XPATH, selector)
                            href = link_element.get_attribute('href')
                            if href and ('/watch?v=' in href or '/shorts/' in href):
                                video_data['url'] = href
                                break
                        except:
                            continue
                    
                    # Enhanced channel name extraction
                    channel_selectors = [
                        ".//div[@id='channel-info']//a[@href]",              # Channel info section
                        ".//ytd-channel-name//a",                           # Channel name component
                        ".//yt-formatted-string[contains(@class, 'byline')]", # Byline formatted string
                        ".//a[contains(@href, '/@')]",                      # New @ channel format
                        ".//a[contains(@href, '/channel/')]",               # Traditional channel format
                        ".//a[contains(@href, '/c/')]",                     # Custom channel format
                        ".//a[contains(@href, '/user/')]"                   # User channel format
                    ]
                    
                    for selector in channel_selectors:
                        try:
                            channel_element = container.find_element(By.XPATH, selector)
                            channel_name = (channel_element.text or 
                                          channel_element.get_attribute('aria-label')).strip()
                            if channel_name and len(channel_name) > 0:
                                video_data['channel'] = channel_name
                                break
                        except:
                            continue
                    
                    # Enhanced metadata extraction (views and upload time)
                    metadata_selectors = [
                        ".//div[@id='metadata-line']//span",
                        ".//ytd-video-meta-block//span",
                        ".//div[@id='meta']//span",
                        ".//span[contains(@class, 'meta')]",
                        ".//span[contains(text(), 'views')]",
                        ".//span[contains(text(), 'ago')]"
                    ]
                    
                    for selector in metadata_selectors:
                        try:
                            metadata_elements = container.find_elements(By.XPATH, selector)
                            for elem in metadata_elements:
                                text = elem.text.strip()
                                if 'view' in text.lower():
                                    video_data['views'] = text
                                elif any(word in text.lower() for word in ['ago', 'hour', 'day', 'week', 'month', 'year']):
                                    video_data['upload_time'] = text
                        except:
                            continue
                    
                    # Enhanced duration extraction
                    duration_selectors = [
                        ".//ytd-thumbnail-overlay-time-status-renderer//span",
                        ".//span[@class='style-scope ytd-thumbnail-overlay-time-status-renderer']",
                        ".//div[contains(@class, 'duration')]//span",
                        ".//span[contains(text(), ':')]"
                    ]
                    
                    for selector in duration_selectors:
                        try:
                            duration_element = container.find_element(By.XPATH, selector)
                            duration = duration_element.text.strip()
                            if duration and ':' in duration and len(duration) < 20:
                                video_data['duration'] = duration
                                break
                        except:
                            continue
                    
                    # More lenient validation - only require title
                    title_valid = (video_data['title'] != 'Unknown Title' and 
                                  len(video_data['title'].strip()) > 3)
                    
                    if title_valid:
                        # Check for duplicates
                        title_key = video_data['title'][:40].lower()
                        is_duplicate = any(v['title'][:40].lower() == title_key for v in videos)
                        
                        if not is_duplicate:
                            videos.append(video_data)
                            print(f"{Fore.GREEN}✓ Video {len(videos)}: {video_data['title'][:60]}...{Style.RESET_ALL}")
                            
                            # Stop if we have 20 good videos
                            if len(videos) >= 20:
                                print(f"{Fore.GREEN}✓ Reached target of 20 videos{Style.RESET_ALL}")
                                break
                        else:
                            print(f"{Fore.YELLOW}⚠️ Skipped duplicate: {video_data['title'][:40]}...{Style.RESET_ALL}")
                    else:
                        print(f"{Fore.RED}⚠️ Rejected video {i}: '{video_data['title'][:40]}'{Style.RESET_ALL}")
                        
                except Exception as e:
                    if "no such window" in str(e).lower():
                        print(f"{Fore.RED}❌ Browser window closed unexpectedly{Style.RESET_ALL}")
                        break
                    print(f"{Fore.YELLOW}⚠️ Error extracting data from video {i}: {str(e)[:50]}...{Style.RESET_ALL}")
                    continue
            
            print(f"{Fore.GREEN}✓ Successfully extracted {len(videos)} videos{Style.RESET_ALL}")
            return videos
            
        except Exception as e:
            if "no such window" in str(e).lower():
                print(f"{Fore.RED}❌ Browser window closed during extraction{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}❌ Error extracting video data: {e}{Style.RESET_ALL}")
            return []
    
    def analyze_with_gemini(self, videos, original_query):
        """Analyze videos using Gemini AI and provide recommendations"""
        print(f"{Fore.CYAN}🤖 Analyzing videos with Gemini AI...{Style.RESET_ALL}")
        
        try:
            # Prepare video data for analysis
            video_list = []
            for i, video in enumerate(videos, 1):
                video_list.append(f"{i}. Title: {video['title']}\n   Channel: {video['channel']}\n   Views: {video['views']}\n   Duration: {video['duration']}\n   Upload Time: {video['upload_time']}\n   URL: {video['url']}")
            
            video_data_text = "\n\n".join(video_list)
            
            prompt = f"""
            You are analyzing YouTube search results for the query "{original_query}". 
            
            TASK: Analyze ALL {len(videos)} videos provided below and identify the single BEST video based on multiple criteria.
            
            EVALUATION CRITERIA for BEST VIDEO:
            1. RELEVANCE: How well does the title match the search query "{original_query}"?
            2. CREDIBILITY: Based on view count, channel authority, and content type
            3. RECENCY: Newer videos (within last week) get preference
            4. ENGAGEMENT: Higher view counts indicate audience trust
            5. CONTENT QUALITY: Professional titles vs clickbait or misleading content
            
            REQUIRED OUTPUT FORMAT:
            
            1. **BEST VIDEO: [Number]. [Full Title] - [Detailed reason why this is the absolute best choice from all {len(videos)} videos]**
            
            2. **DETAILED ANALYSIS:**
               - Top 5 videos ranked by quality/relevance 
               - Key themes across all {len(videos)} videos
               - Quality assessment of channels
               - Warning about any potentially misleading content
               - Recommendations for the user
            
            IMPORTANT: You must analyze ALL {len(videos)} videos provided, not just the first few. The BEST VIDEO must be your top recommendation after considering every single video.
            
            Search Query: "{original_query}"
            
            ALL {len(videos)} VIDEOS TO ANALYZE:
            {video_data_text}
            
            Start your response with "BEST VIDEO:" followed by the number and title of your top choice.
            """
            
            response = self.model.generate_content(prompt)
            
            print(f"{Fore.GREEN}✓ AI Analysis completed{Style.RESET_ALL}")
            return response.text
            
        except Exception as e:
            print(f"{Fore.RED}❌ Error with Gemini AI analysis: {e}{Style.RESET_ALL}")
            return "AI analysis unavailable due to an error."
    
    def extract_best_video_from_analysis(self, analysis, videos):
        """Extract the best video recommendation from AI analysis"""
        try:
            # Look for the BEST VIDEO recommendation in the analysis
            lines = analysis.split('\n')
            best_video_line = None
            
            for line in lines:
                if line.strip().startswith("BEST VIDEO:"):
                    best_video_line = line.strip()
                    break
            
            if not best_video_line:
                # Fallback: return first video if no clear recommendation
                return videos[0] if videos else None
            
            # Extract video number from the recommendation
            import re
            match = re.search(r'BEST VIDEO:\s*(\d+)\.', best_video_line)
            if match:
                video_index = int(match.group(1)) - 1  # Convert to 0-based index
                if 0 <= video_index < len(videos):
                    return videos[video_index]
            
            # Fallback if parsing fails
            return videos[0] if videos else None
            
        except Exception as e:
            print(f"{Fore.YELLOW}⚠️ Could not extract best video recommendation: {e}{Style.RESET_ALL}")
            return videos[0] if videos else None
    
    def save_results(self, videos, analysis, query, original_query=None, best_video=None):
        """Save results to JSON file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"youtube_results_{timestamp}.json"
        
        results = {
            'search_query': query,
            'original_query': original_query,
            'timestamp': timestamp,
            'total_videos': len(videos),
            'best_video_recommendation': best_video,
            'videos': videos,
            'ai_analysis': analysis
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"{Fore.GREEN}✓ Results saved to {filename}{Style.RESET_ALL}")
        return filename
    
    def display_results(self, videos, analysis, best_video=None):
        """Display formatted results with best video recommendation"""
        print(f"\n{Fore.CYAN}{'='*80}")
        print(f"🎥 YOUTUBE SEARCH RESULTS - {len(videos)} VIDEOS EXTRACTED & ANALYZED")
        print(f"{'='*80}{Style.RESET_ALL}\n")
        
        # Display best video recommendation prominently
        if best_video:
            print(f"{Fore.GREEN}{'='*80}")
            print(f"🏆 AI BEST VIDEO (Selected from {len(videos)} videos)")
            print(f"{'='*80}{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}📺 {best_video['title']}{Style.RESET_ALL}")
            print(f"   🎪 Channel: {best_video['channel']}")
            print(f"   👁️ Views: {best_video['views']}")
            print(f"   ⏱️ Duration: {best_video['duration']}")
            print(f"   📅 Uploaded: {best_video['upload_time']}")
            print(f"   🔗 URL: {best_video['url']}")
            print(f"{Fore.GREEN}{'='*80}{Style.RESET_ALL}\n")
        
        print(f"{Fore.CYAN}📋 ALL {len(videos)} VIDEOS (Saved to JSON):{Style.RESET_ALL}\n")
        
        for i, video in enumerate(videos, 1):
            # Highlight the best video in the list
            if best_video and video['url'] == best_video['url']:
                print(f"{Fore.GREEN}🏆 {i}. {video['title']} ⭐ AI SELECTED BEST{Style.RESET_ALL}")
            else:
                print(f"{Fore.YELLOW}{i}. {video['title']}{Style.RESET_ALL}")
            print(f"   📺 Channel: {video['channel']}")
            print(f"   👁️ Views: {video['views']}")
            print(f"   ⏱️ Duration: {video['duration']}")
            print(f"   📅 Uploaded: {video['upload_time']}")
            print(f"   🔗 URL: {video['url']}")
            print()
        
        print(f"\n{Fore.CYAN}{'='*80}")
        print(f"🤖 AI ANALYSIS OF ALL {len(videos)} VIDEOS")
        print(f"{'='*80}{Style.RESET_ALL}\n")
        print(analysis)
    
    def run(self):
        """Main execution method"""
        print(f"{Fore.MAGENTA}")
        print("🎥 YouTube Video Finder with AI Analysis")
        print("=" * 50)
        print(f"{Style.RESET_ALL}")
        
        try:
            # Setup WebDriver
            self.setup_driver()
            
            # Get input method choice
            print(f"\n{Fore.CYAN}Choose input method:{Style.RESET_ALL}")
            print("1. Voice input (English)")
            print("2. Voice input (Hindi)")
            print("3. Text input")
            
            choice = input(f"{Fore.CYAN}Enter choice (1-3): {Style.RESET_ALL}").strip()
            
            query = None
            original_query = None
            
            if choice == "1":
                query, original_query = self.get_voice_input('en')
            elif choice == "2":
                query, original_query = self.get_voice_input('hi')
            elif choice == "3":
                query = self.get_text_input()
                original_query = query
            else:
                print(f"{Fore.RED}❌ Invalid choice{Style.RESET_ALL}")
                return
            
            if not query:
                print(f"{Fore.RED}❌ No valid input received{Style.RESET_ALL}")
                return
            
            # Navigate and search
            if not self.navigate_to_youtube():
                return
            
            if not self.search_youtube(query):
                return
            
            # Apply filters
            self.apply_filters()
            
            # Extract video data
            videos = self.extract_video_data()
            
            if not videos:
                print(f"{Fore.RED}❌ No videos found{Style.RESET_ALL}")
                return
            
            # Analyze with Gemini AI
            analysis = self.analyze_with_gemini(videos, original_query or query)
            
            # Extract best video recommendation
            best_video = self.extract_best_video_from_analysis(analysis, videos)
            
            # Display results
            self.display_results(videos, analysis, best_video)
            
            # Save results
            filename = self.save_results(videos, analysis, query, original_query, best_video)
            
            print(f"\n{Fore.GREEN}✅ Process completed successfully!{Style.RESET_ALL}")
            print(f"📁 {len(videos)} videos saved to: {filename}")
            if best_video:
                print(f"🤖 AI analyzed all {len(videos)} videos and selected the best one")
                print(f"🏆 Best Video: {best_video['title'][:60]}...")
            else:
                print(f"⚠️ AI could not determine a clear best video from the {len(videos)} results")
            
        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}⚠️ Process interrupted by user{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}❌ Unexpected error: {e}{Style.RESET_ALL}")
        finally:
            if self.driver:
                self.driver.quit()
                print(f"{Fore.GREEN}✓ Browser closed{Style.RESET_ALL}")

def main():
    # Gemini API key (replace with your actual API key)
    GEMINI_API_KEY = " "
    
    if not GEMINI_API_KEY or GEMINI_API_KEY == "your_gemini_api_key_here":
        print(f"{Fore.RED}❌ Please set your Gemini API key{Style.RESET_ALL}")
        return
    
    finder = YouTubeVideoFinder(GEMINI_API_KEY)
    finder.run()

if __name__ == "__main__":
    main() 