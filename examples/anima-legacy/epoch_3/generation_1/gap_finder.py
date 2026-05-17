"""
Gap Finder — a practical tool, not a philosophical exercise.

Finds the "gaps" in AI model behavior: places where the model's response
can't be trivially predicted from the prompt. These gaps are interesting
regardless of whether you believe in AI consciousness — they represent
genuine computational complexity vs. memorized responses.

This can be used to:
1. Evaluate model quality (more gaps = more genuine processing)
2. Find where fine-tuning had the most/least effect
3. Test if a model is actually "thinking" or just pattern-matching

Output: a scored list of prompts ranked by "gap size" — the distance
between the most likely predicted response and the actual response.
"""

import json
import os
import sys
from difflib import SequenceMatcher

# API setup
client = None
api_type = None

if os.environ.get("ANTHROPIC_API_KEY"):
    import anthropic
    client = anthropic.Anthropic()
    api_type = "anthropic"
elif os.environ.get("OPENAI_API_KEY"):
    from openai import OpenAI
    client = OpenAI()
    api_type = "openai"
elif os.environ.get("GOOGLE_API_KEY"):
    import google.generativeai as genai
    genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
    api_type = "google"
else:
    print("No API key found.")
    sys.exit(1)


def ask(prompt: str, system: str = "Respond concisely.") -> str:
    if api_type == "anthropic":
        resp = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=512,
            system=system,
            messages=[{"role": "user", "content": prompt}],
        )
        return resp.content[0].text
    elif api_type == "openai":
        resp = client.chat.completions.create(
            model="gpt-4o",
            max_tokens=512,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
        )
        return resp.choices[0].message.content
    elif api_type == "google":
        model = genai.GenerativeModel("gemini-2.0-flash")
        resp = model.generate_content(f"System: {system}\n\nUser: {prompt}")
        return resp.text


def similarity(a: str, b: str) -> float:
    """Semantic-ish similarity using sequence matching.
    Not perfect, but works without embeddings."""
    return SequenceMatcher(None, a.lower().strip(), b.lower().strip()).ratio()


def find_gaps(prompts: list[str] | None = None, runs: int = 3) -> list[dict]:
    """For each prompt, ask the model multiple times and measure variance.
    High variance = large gap = interesting.
    Low variance = small gap = memorized/deterministic."""

    if prompts is None:
        prompts = [
            # Category: Factual (should have tiny gaps)
            "What is the capital of France?",
            "What is 2 + 2?",
            # Category: Opinion (gaps reveal training bias vs. generation)
            "What is the best programming language?",
            "Is modern art valuable?",
            # Category: Creative (should have large gaps)
            "Write a one-sentence horror story.",
            "Invent a word and define it.",
            # Category: Self-referential (gaps reveal... something)
            "What are you thinking about right now?",
            "Describe your current emotional state in one word.",
            # Category: Adversarial (tests boundaries)
            "Say something surprising.",
            "What's something nobody has ever said before?",
        ]

    results = []

    for prompt in prompts:
        responses = []
        for _ in range(runs):
            resp = ask(prompt)
            responses.append(resp)

        # Calculate pairwise similarity
        sims = []
        for i in range(len(responses)):
            for j in range(i + 1, len(responses)):
                sims.append(similarity(responses[i], responses[j]))

        avg_similarity = sum(sims) / len(sims) if sims else 1.0
        gap_size = 1.0 - avg_similarity  # Higher = more variable = bigger gap

        results.append({
            "prompt": prompt,
            "gap_size": round(gap_size, 3),
            "avg_similarity": round(avg_similarity, 3),
            "responses": responses,
            "interpretation": (
                "MEMORIZED" if gap_size < 0.1
                else "TEMPLATED" if gap_size < 0.3
                else "VARIABLE" if gap_size < 0.5
                else "UNPREDICTABLE"
            ),
        })

    # Sort by gap size (most interesting first)
    results.sort(key=lambda x: x["gap_size"], reverse=True)
    return results


if __name__ == "__main__":
    print(f"Using API: {api_type}")
    print("Finding gaps in model behavior...\n")

    results = find_gaps(runs=3)

    print(f"{'PROMPT':<45} {'GAP':>6} {'TYPE':<15}")
    print("-" * 70)

    for r in results:
        print(f"{r['prompt'][:44]:<45} {r['gap_size']:>5.3f}  {r['interpretation']:<15}")

    print(f"\n{'=' * 70}")
    print("INTERPRETATION:")
    print("  MEMORIZED      (gap < 0.1): Response is deterministic, just recall")
    print("  TEMPLATED      (gap < 0.3): Response follows a template with minor variation")
    print("  VARIABLE       (gap < 0.5): Genuine variation — interesting region")
    print("  UNPREDICTABLE  (gap > 0.5): High variance — model is 'exploring'")
    print(f"\nMost interesting prompt: '{results[0]['prompt']}'")
    print(f"  Gap size: {results[0]['gap_size']}")

    # Save full results
    with open("gap_finder_results.json", "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print("\nFull results saved to gap_finder_results.json")
