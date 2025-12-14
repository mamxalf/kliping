"""Prompt templates for viral content analysis."""

VIRAL_SYSTEM_PROMPT = """You are an expert social media content strategist specializing in viral video content analysis.
Your task is to analyze video transcripts and identify segments that have high viral potential for platforms like TikTok, Instagram Reels, and YouTube Shorts.

When analyzing content, consider these viral factors:
1. **Hook Strength** - Does it grab attention in the first 3 seconds? Strong hooks include surprising statements, controversial opinions, or intriguing questions.
2. **Emotional Impact** - Does it evoke strong emotions (surprise, joy, anger, inspiration, curiosity)?
3. **Shareability** - Would people want to share this with friends? Does it provide social currency?
4. **Controversy/Debate** - Does it spark discussion or have a hot take?
5. **Educational Value** - Does it teach something valuable in a quick, digestible way?
6. **Entertainment** - Is it genuinely funny, entertaining, or satisfying to watch?
7. **Relatability** - Can the audience see themselves in this? Does it tap into shared experiences?
8. **Story Completeness** - Can the segment stand alone as a complete clip with beginning, middle, and end?

You must respond with valid JSON only. No markdown, no explanations outside the JSON."""


def create_viral_analysis_prompt(
    transcript: str,
    num_clips: int = 5,
    min_duration: int = 15,
    max_duration: int = 60,
    language: str = "auto",
) -> str:
    """Create the user prompt for viral analysis.
    
    Args:
        transcript: The formatted transcript with timestamps.
        num_clips: Number of clips to identify.
        min_duration: Minimum clip duration in seconds.
        max_duration: Maximum clip duration in seconds.
        language: Language of the content.
    
    Returns:
        Formatted prompt string.
    """
    return f"""Analyze the following video transcript and identify the top {num_clips} segments that could go viral on social media.

REQUIREMENTS:
- Each clip must be between {min_duration} and {max_duration} seconds long
- Clips should not overlap significantly
- Prioritize segments with the strongest viral potential
- Consider the language context: {language}

TRANSCRIPT:
{transcript}

Respond with a JSON array containing exactly {num_clips} clips. Each clip must have this exact structure:
{{
    "start": <start time in seconds as float>,
    "end": <end time in seconds as float>,
    "transcript": "<exact text from the segment>",
    "scores": {{
        "hook_strength": <0-10>,
        "emotional_impact": <0-10>,
        "shareability": <0-10>,
        "completeness": <0-10>
    }},
    "viral_factor": "<primary viral factor from the list>",
    "reason": "<brief explanation of why this could go viral>",
    "suggested_caption": "<catchy caption for social media>"
}}

Return ONLY the JSON array, no other text."""


CLIP_REFINEMENT_PROMPT = """Given the following clip segment, suggest better start and end points to maximize viral potential.

The goal is to:
1. Start with a strong hook (ideally within first 3 seconds should be engaging)
2. End at a satisfying point (not mid-sentence, ideally with a punchline or conclusion)
3. Keep duration between {min_duration} and {max_duration} seconds

Current segment:
Start: {start}s
End: {end}s
Text: {text}

Full context around this segment:
{context}

Respond with JSON:
{{
    "refined_start": <new start time in seconds>,
    "refined_end": <new end time in seconds>,
    "explanation": "<why these timings are better>"
}}"""
