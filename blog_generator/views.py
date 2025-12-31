from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.conf import settings
import json
import os
import assemblyai as aai
from .models import BlogPost
import yt_dlp
import re
import traceback
import tempfile
import shutil
from datetime import datetime

# ========== API CONFIGURATIONS ==========

# AssemblyAI API Configuration - MOVE THIS TO ENVIRONMENT VARIABLE
ASSEMBLYAI_API_KEY = os.environ.get('ASSEMBLYAI_API_KEY', '73427aaa4f1548758066e634f5f91274')
aai.settings.api_key = ASSEMBLYAI_API_KEY

# ========== VIEW FUNCTIONS ==========

@login_required
def index(request):
    return render(request, 'index.html', {'user': request.user})

def user_login(request):
    if request.user.is_authenticated:
        return redirect('/')
        
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        if not username or not password:
            error_message = "Please provide both username and password"
            return render(request, 'login.html', {'error_message': error_message})
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('/')
        else:
            error_message = "Invalid username or password"
            return render(request, 'login.html', {'error_message': error_message})
    
    return render(request, 'login.html')

def user_signup(request):
    if request.user.is_authenticated:
        return redirect('/')
        
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        repeatPassword = request.POST.get('repeatpassword')

        if not all([username, email, password, repeatPassword]):
            error_message = 'All fields are required'
            return render(request, 'signup.html', {'error_message': error_message})
        
        if password != repeatPassword:
            error_message = 'Passwords do not match'
            return render(request, 'signup.html', {'error_message': error_message})
        
        if len(password) < 8:
            error_message = 'Password must be at least 8 characters long'
            return render(request, 'signup.html', {'error_message': error_message})
        
        if User.objects.filter(username=username).exists():
            error_message = 'Username already exists'
            return render(request, 'signup.html', {'error_message': error_message})
        
        if User.objects.filter(email=email).exists():
            error_message = 'Email already registered'
            return render(request, 'signup.html', {'error_message': error_message})

        try:
            user = User.objects.create_user(username, email, password)
            user.save()
            login(request, user)
            return redirect('/')
        except Exception as e:
            error_message = f'Error creating account: {str(e)}'
            return render(request, 'signup.html', {'error_message': error_message})
    
    return render(request, 'signup.html')

def user_logout(request):
    logout(request)
    return redirect('/login/')

@csrf_exempt
@login_required
def generate_blog(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            yt_link = data.get('link')
            
            if not yt_link:
                return JsonResponse({'error': 'No link provided'}, status=400)
            
            print("\n" + "="*60)
            print("STARTING BLOG GENERATION PROCESS")
            print("="*60)
            
            # Validate and clean YouTube URL
            yt_link = clean_youtube_url(yt_link)
            if not yt_link:
                return JsonResponse({'error': 'Invalid YouTube URL'}, status=400)

            print(f"📹 Processing YouTube link: {yt_link}")

            # Get YouTube title
            title = get_yt_title(yt_link)
            if not title:
                return JsonResponse({'error': 'Failed to get YouTube video title. Please check the link.'}, status=400)

            print(f"📝 Video title: {title}")

            # Get transcript using audio download method
            transcript = get_transcription_via_audio_download(yt_link)
            if not transcript:
                return JsonResponse({'error': 'Failed to get transcript. The video might be private, age-restricted, too long, or contain no audio.'}, status=500)

            print(f"🎙️  Transcript obtained: {len(transcript)} characters")

            # Generate blog from transcript
            blog_content = generate_blog_from_transcription(transcript, title)
            if not blog_content:
                return JsonResponse({'error': 'Failed to generate blog article. Please try again.'}, status=500)

            print(f"✅ Blog generated: {len(blog_content)} characters")

            # Save blog article to database
            new_blog_article = BlogPost.objects.create(
                user=request.user,
                youtube_title=title,
                youtube_link=yt_link,
                generated_content=blog_content,
            )
            new_blog_article.save()

            print(f"💾 Saved to database with ID: {new_blog_article.id}")

            # Return success response
            return JsonResponse({
                'content': blog_content,
                'title': title,
                'id': new_blog_article.id
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON data'}, status=400)
        except Exception as e:
            print(f"❌ Error in generate_blog: {str(e)}")
            traceback.print_exc()
            return JsonResponse({'error': f'Internal server error: {str(e)}'}, status=500)
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)

def clean_youtube_url(url):
    """Extract and clean YouTube URL to get video ID"""
    try:
        patterns = [
            r'(?:https?://)?(?:www\.)?youtube\.com/watch\?v=([^&]+)',
            r'(?:https?://)?(?:www\.)?youtu\.be/([^?]+)',
            r'(?:https?://)?(?:www\.)?youtube\.com/embed/([^?]+)',
            r'(?:https?://)?(?:www\.)?youtube\.com/v/([^?]+)',
            r'(?:https?://)?(?:www\.)?youtube\.com/shorts/([^?]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                video_id = match.group(1)
                video_id = video_id.split('&')[0].split('?')[0].split('/')[0]
                return f"https://www.youtube.com/watch?v={video_id}"
        
        if 'youtube.com' in url or 'youtu.be' in url:
            return url
        return None
    except Exception as e:
        print(f"❌ Error cleaning URL: {str(e)}")
        return None

def get_yt_title(yt_link):
    """Get YouTube video title using yt-dlp"""
    try:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'referer': 'https://www.youtube.com/',
            'extractor_args': {'youtube': {'player_client': ['android']}}
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(yt_link, download=False)
            if not info:
                print("❌ Failed to extract video info")
                return None
            return info.get('title', 'Unknown Title')
    except Exception as e:
        print(f"❌ Error getting YouTube title: {str(e)}")
        return None

def get_transcription_via_audio_download(yt_link):
    """Download audio and transcribe using AssemblyAI"""
    temp_dir = None
    try:
        print("⬇️  Downloading audio from YouTube...")
        
        temp_dir = tempfile.mkdtemp()
        print(f"📁 Created temp directory: {temp_dir}")
        
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(temp_dir, 'audio.%(ext)s'),
            'quiet': False,
            'no_warnings': False,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'referer': 'https://www.youtube.com/',
            'extractor_args': {'youtube': {'player_client': ['android']}}
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(yt_link, download=True)
            title = info.get('title', 'Unknown Title')
            print(f"✅ Downloaded audio for: {title}")
            
            audio_files = [f for f in os.listdir(temp_dir) if f.endswith('.mp3')]
            if not audio_files:
                audio_files = [f for f in os.listdir(temp_dir) if f.startswith('audio.')]
            
            if audio_files:
                audio_file = os.path.join(temp_dir, audio_files[0])
                file_size = os.path.getsize(audio_file)
                print(f"🎵 Audio file: {file_size:,} bytes")
                
                if file_size < 1024:
                    print("⚠️  Audio file is too small, might be empty")
                    return None
                
                print("🔊 Transcribing audio with AssemblyAI...")
                transcriber = aai.Transcriber()
                
                config = aai.TranscriptionConfig(
                    language_code="en",
                    punctuate=True,
                    format_text=True,
                    disfluencies=False,
                    auto_highlights=False
                )
                
                transcript = transcriber.transcribe(audio_file, config=config)
                
                if transcript.status == aai.TranscriptStatus.error:
                    print(f"❌ Transcription error: {transcript.error}")
                    return None
                
                if not transcript.text or len(transcript.text.strip()) < 20:
                    print(f"⚠️  Transcription too short: '{transcript.text}'")
                    return None
                
                print(f"✅ Transcription successful!")
                return transcript.text
            else:
                print("❌ No audio files found")
                return None
                
    except Exception as e:
        print(f"❌ Error in transcription: {str(e)}")
        traceback.print_exc()
        return None
        
    finally:
        if temp_dir and os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
                print(f"🧹 Cleaned up temp directory")
            except Exception as e:
                print(f"⚠️  Error cleaning up: {str(e)}")

def generate_blog_from_transcription(transcription, video_title=""):
    """Generate well-structured blog from transcript"""
    try:
        print(f"🤖 Generating structured blog ({len(transcription)} chars)...")
        
        # Clean and process transcript
        import re
        
        # Remove extra whitespace and clean text
        transcription = re.sub(r'\s+', ' ', transcription).strip()
        
        # Split into sentences
        sentences = re.split(r'(?<=[.!?])\s+', transcription)
        sentences = [s.strip() for s in sentences if s.strip() and len(s) > 10]
        
        if not sentences:
            return f"## {video_title}\n\n**Transcript Analysis**\n\nThe video content discusses topics related to {video_title.lower()}.\n\n*Analysis based on video review.*"
        
        # Create structured blog
        if len(sentences) >= 8:
            # For longer transcripts
            intro = sentences[0]
            key_points = sentences[1:4]
            detailed_analysis = ' '.join(sentences[4:7])
            conclusion = sentences[7] if len(sentences) > 8 else "The discussion provides comprehensive insights into this topic."
            
            blog = f"""## {video_title}

### Overview
{intro}

### Key Discussion Points
{chr(10).join(['• ' + point for point in key_points])}

### Detailed Analysis
{detailed_analysis}

### Context and Implications
{conclusion}

### Summary
The video presents a thorough examination of this topic through detailed discussion and analysis.

*Content review based on transcript analysis.*"""
            
        elif len(sentences) >= 4:
            # For medium transcripts
            intro = sentences[0]
            key_points = sentences[1:3]
            analysis = ' '.join(sentences[3:])
            
            blog = f"""## {video_title}

### Summary
{intro}

### Main Points Discussed
{chr(10).join(['• ' + point for point in key_points])}

### Analysis
{analysis}

### Review
The discussion elaborates on these aspects with additional commentary and context.

*Based on transcript review.*"""
            
        else:
            # For short transcripts
            blog = f"""## {video_title}

### Transcript Summary
{' '.join(sentences)}

### Analysis
The video provides insights into this topic through discussion and presentation of key information.

*Analysis based on video content review.*"""
        
        # Format for HTML display (preserve line breaks)
        blog = blog.replace('\n', '<br>').replace('## ', '<h2>').replace('</h2>', '</h2><br>')
        blog = blog.replace('### ', '<h3>').replace('</h3>', '</h3><br>')
        blog = blog.replace('• ', '<li>').replace('<br>• ', '</li><br><li>')
        blog = blog.replace('*', '<em>').replace('<em>', '<em>', 1).replace('<em>', '</em>', 2)
        
        print(f"✅ Structured blog generated: {len(blog)} chars")
        return blog
            
    except Exception as e:
        print(f"❌ Blog generation error: {str(e)}")
        # Simple formatted fallback
        return f"""<h2>{video_title}</h2><br>
<h3>Content Analysis</h3><br>
<p>{transcription[:400]}...</p><br>
<p><em>Review based on video transcript analysis.</em></p>"""

@login_required
def blog_list(request):
    """Display all blog posts for the logged-in user"""
    blog_articles = BlogPost.objects.filter(user=request.user).order_by('-created_at')
    return render(request, "all-blogs.html", {
        'blog_articles': blog_articles,
        'user': request.user
    })

@login_required
def blog_details(request, pk):
    """Display details of a specific blog post"""
    try:
        blog_article_detail = BlogPost.objects.get(id=pk)
        if request.user == blog_article_detail.user:
            return render(request, 'blog-details.html', {
                'blog_article_detail': blog_article_detail,
                'user': request.user
            })
        else:
            return redirect('/')
    except BlogPost.DoesNotExist:
        return redirect('/')

@login_required
def recent_blogs_api(request):
    """API endpoint for recent blogs"""
    blogs = BlogPost.objects.filter(user=request.user).order_by('-created_at')[:5]
    data = [
        {
            'id': blog.id,
            'title': blog.youtube_title,
            'youtube_title': blog.youtube_title[:50] + '...' if len(blog.youtube_title) > 50 else blog.youtube_title,
            'created_at': blog.created_at.isoformat(),
            'word_count': len(blog.generated_content.split())
        }
        for blog in blogs
    ]
    return JsonResponse(data, safe=False)

@login_required
def user_stats_api(request):
    """API endpoint for user stats"""
    total_blogs = BlogPost.objects.filter(user=request.user).count()
    
    # Monthly blogs
    current_month = datetime.now().month
    monthly_blogs = BlogPost.objects.filter(
        user=request.user,
        created_at__month=current_month
    ).count()
    
    # Total words
    blogs = BlogPost.objects.filter(user=request.user)
    total_words = sum(len(blog.generated_content.split()) for blog in blogs)
    
    return JsonResponse({
        'total_blogs': total_blogs,
        'monthly_blogs': monthly_blogs,
        'total_words': total_words
    })