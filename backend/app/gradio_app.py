from __future__ import annotations

import os

from app.core.config import get_settings
from app.services.ai.providers import HuggingFaceProvider


def _demo_analyze(image) -> str:
    if image is None:
        return "Upload a meal image to begin."
    settings = get_settings()
    provider = HuggingFaceProvider(settings)
    if not provider.configured:
        return (
            "Hugging Face is not configured. Set HUGGINGFACE_API_KEY or HUGGINGFACE_MODEL in the backend environment "
            "before launching the Gradio demo."
        )
    try:
        return provider.generate_text(
            "Describe the visible food in this image and estimate a rough calorie range and meal type.",
            image=image,
            content_type="image/png",
        )
    except Exception as exc:  # pragma: no cover - demo fallback path
        return f"AI processing failed: {exc}"


def build_demo():
    try:
        import gradio as gr
    except ImportError as exc:  # pragma: no cover - dependency should be installed in the app env
        raise RuntimeError("Gradio is not installed. Add gradio to backend requirements.") from exc

    return gr.Interface(
        fn=_demo_analyze,
        inputs=gr.Image(type="pil"),
        outputs="text",
        title="CalTrack AI Demo",
        description=(
            "Upload a meal photo for a rough AI nutrition estimate. "
            "The app keeps Gemini as the main runtime provider and exposes Hugging Face as a configurable fallback."
        ),
    )


if __name__ == "__main__":
    demo = build_demo()
    demo.launch(server_name="0.0.0.0", server_port=int(os.getenv("GRADIO_PORT", "7860")))
