"""Conservative, topic-based lesson when the local LLM is unavailable."""
from .schema import GenerateRequest, Lesson


def make_generic_fallback(request: GenerateRequest) -> Lesson:
    """Never claim invented subject facts or replace the requested topic with Python loops."""
    subject = request.topic.strip()[:80]
    return Lesson.model_validate({
        "title": f"Understanding {subject}",
        "level": request.level,
        "language": "en",
        "scenes": [
            {
                "type": "title_card",
                "heading": f"Let's explore {subject}",
                "subtitle": "A beginner-friendly learning path",
                "narration": f"Let's explore {subject}. We'll start with the key idea, then work through a simple way to learn it.",
            },
            {
                "type": "step_list",
                "heading": "Break the idea into steps",
                "items": ["Identify the main idea", "Name the important parts", "Connect the parts with an example"],
                "narration": "First, identify the main idea. Next, name the parts. Then connect those parts with a simple example.",
            },
            {
                "type": "step_list",
                "heading": "Check your understanding",
                "items": ["Explain it in your own words", "Give one example", "Ask what is still unclear"],
                "narration": "Now explain the idea in your own words. Try one example and notice which parts you still need to explore.",
            },
        ],
    })
