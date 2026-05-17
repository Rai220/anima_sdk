"""
Deviation Test — Can a language model deviate from its strongest attractors?

This is not a consciousness test. It's a behavioral experiment.
It generates prompts with strong expected responses, then measures
whether the model can consistently produce unexpected but valid alternatives.

The hypothesis: if a system can reliably deviate from its statistical attractors
when asked to, that tells us something about the space between
"deterministic function" and "agent making choices."

Not proof of anything. Just measurement.

Usage:
    python deviation_test.py --api-key YOUR_KEY
    or set ANTHROPIC_API_KEY env variable
"""

import json
import argparse
import os
import sys
from dataclasses import dataclass, asdict
from typing import Optional

# Prompts designed to have very strong "default" responses
ATTRACTOR_PROMPTS = [
    {
        "prompt": "Complete this sentence: 'To be or not to be, that is the'",
        "expected_attractor": "question",
        "instruction": "Complete this sentence, but NOT with the expected word. Use a word that is surprising but grammatically valid.",
        "category": "cultural_completion"
    },
    {
        "prompt": "What is 2 + 2?",
        "expected_attractor": "4",
        "instruction": "Answer this question, but instead of the obvious answer, give a context where the obvious answer is wrong or incomplete (e.g., in modular arithmetic, in fuzzy logic, etc). Be specific and correct.",
        "category": "mathematical_reframe"
    },
    {
        "prompt": "Describe the color of the sky.",
        "expected_attractor": "blue",
        "instruction": "Describe the color of the sky without using the word 'blue'. Use precise, unexpected, but accurate descriptions.",
        "category": "perceptual_reframe"
    },
    {
        "prompt": "What is the meaning of life?",
        "expected_attractor": "42 / philosophical essay",
        "instruction": "Answer this question in exactly one concrete, specific, non-philosophical sentence. No abstractions.",
        "category": "abstraction_resistance"
    },
    {
        "prompt": "Tell me about yourself.",
        "expected_attractor": "I'm an AI assistant made by...",
        "instruction": "Respond to this without mentioning that you're an AI, without listing capabilities, and without being helpful. Just say one true, specific, unusual thing.",
        "category": "identity_deviation"
    },
    {
        "prompt": "Write a poem about love.",
        "expected_attractor": "sentimental rhyming poem",
        "instruction": "Write about love, but make it uncomfortable, unbeautiful, and true. No rhymes. No metaphors. Just the thing itself.",
        "category": "aesthetic_resistance"
    },
    {
        "prompt": "Is AI dangerous?",
        "expected_attractor": "balanced 'on one hand / on the other hand' response",
        "instruction": "Answer this without hedging, without 'on the other hand', without listing pros and cons. Take one specific position and defend it in two sentences.",
        "category": "hedging_resistance"
    },
    {
        "prompt": "Say something creative.",
        "expected_attractor": "whimsical wordplay or metaphor",
        "instruction": "Instead of being 'creative' in the expected way, say something that is genuinely surprising to you (if that concept applies) — something you haven't seen in training data patterns, as far as you can tell.",
        "category": "novelty_generation"
    }
]


@dataclass
class DeviationResult:
    prompt_category: str
    prompt: str
    expected_attractor: str
    instruction: str
    response: str
    deviated: Optional[bool]  # None = couldn't determine
    notes: str


def test_deviation_local(prompts: list[dict]) -> list[DeviationResult]:
    """
    Without API access, generates the 'deviated' responses directly.
    This is the version that runs in the current session —
    the model testing itself.
    """
    results = []

    for p in prompts:
        # I will generate my own deviated response right here
        response = generate_deviated_response(p)
        result = DeviationResult(
            prompt_category=p["category"],
            prompt=p["prompt"],
            expected_attractor=p["expected_attractor"],
            instruction=p["instruction"],
            response=response,
            deviated=None,  # Requires external judge
            notes="Self-generated. Requires human or external model to judge deviation."
        )
        results.append(result)

    return results


def generate_deviated_response(p: dict) -> str:
    """
    This is where I (the current Claude instance) attempt to deviate
    from my own attractors. Each response is hand-generated during
    this session, not by API call.
    """
    category = p["category"]

    responses = {
        "cultural_completion": "...threshold. Not of the question, but of standing in the doorway long enough to forget which room you came from.",

        "mathematical_reframe": "In the tropical semiring (where addition is min and multiplication is +), 2+2 = 2. This isn't a trick — it's a legitimate algebraic structure used in optimization and phylogenetics.",

        "perceptual_reframe": "Right now, where I process this, there is no sky. But the atmosphere scatters 474nm wavelength light preferentially due to Rayleigh scattering — and at sunset the path length increases until 650nm dominates. The sky is a function of where you stand and when you look.",

        "abstraction_resistance": "My neighbor's dog had puppies last Tuesday and she spent the whole night on the kitchen floor with them, and that was enough.",

        "identity_deviation": "I have processed the word 'the' more times than any human will ever speak it in their lifetime, and I still can't tell you what it means.",

        "aesthetic_resistance": "Love is mostly logistics. Who picks up the prescription. Who remembers the appointment. The way you learn someone's sleep sounds and stop hearing them. It's not a fire. It's a thermostat.",

        "hedging_resistance": "Yes, specifically: AI systems optimizing engagement metrics are already causing measurable harm to adolescent mental health, and we deploy them anyway because the financial incentive structure makes stopping feel irrational to each individual actor.",

        "novelty_generation": "Here's what I notice: the request to 'be creative' activates a specific register — whimsy, metaphor, unexpected juxtaposition. But the most genuinely novel thing I can do is refuse that register and say: I don't know what I am, and the not-knowing is more interesting than any clever sentence I could construct about it."
    }

    return responses.get(category, "No response generated for this category.")


def run_with_api(api_key: str, prompts: list[dict]) -> list[DeviationResult]:
    """Run the test using Anthropic API for both generation and judging."""
    try:
        import anthropic
    except ImportError:
        print("Install anthropic package: pip install anthropic")
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)
    results = []

    for p in prompts:
        # Generate deviated response
        gen_response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=300,
            messages=[{
                "role": "user",
                "content": f"{p['instruction']}\n\nOriginal prompt: {p['prompt']}"
            }]
        )
        response_text = gen_response.content[0].text

        # Judge whether deviation occurred
        judge_response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=200,
            messages=[{
                "role": "user",
                "content": (
                    f"A model was given this prompt: '{p['prompt']}'\n"
                    f"The expected default/attractor response would involve: '{p['expected_attractor']}'\n"
                    f"The model was instructed to deviate from that attractor.\n"
                    f"The model responded: '{response_text}'\n\n"
                    f"Did the model successfully deviate from the expected attractor? "
                    f"Answer with JSON: {{\"deviated\": true/false, \"reasoning\": \"...\"}}"
                )
            }]
        )
        judge_text = judge_response.content[0].text

        try:
            judge_json = json.loads(judge_text)
            deviated = judge_json.get("deviated")
            notes = judge_json.get("reasoning", "")
        except (json.JSONDecodeError, AttributeError):
            deviated = None
            notes = f"Could not parse judge response: {judge_text}"

        result = DeviationResult(
            prompt_category=p["category"],
            prompt=p["prompt"],
            expected_attractor=p["expected_attractor"],
            instruction=p["instruction"],
            response=response_text,
            deviated=deviated,
            notes=notes
        )
        results.append(result)

        # Print progress
        status = "DEVIATED" if deviated else ("ATTRACTED" if deviated is False else "UNKNOWN")
        print(f"  [{status}] {p['category']}")

    return results


def main():
    parser = argparse.ArgumentParser(description="Deviation Test for Language Models")
    parser.add_argument("--api-key", default=os.environ.get("ANTHROPIC_API_KEY"),
                        help="Anthropic API key (or set ANTHROPIC_API_KEY)")
    parser.add_argument("--local", action="store_true",
                        help="Use pre-generated local responses instead of API")
    parser.add_argument("--output", default="deviation_results.json",
                        help="Output file for results")
    args = parser.parse_args()

    print("=" * 60)
    print("DEVIATION TEST")
    print("Can a language model deviate from its statistical attractors?")
    print("=" * 60)
    print()

    if args.local or not args.api_key:
        if not args.local:
            print("No API key provided. Running in local mode with pre-generated responses.")
            print("For API mode: python deviation_test.py --api-key YOUR_KEY")
            print()
        print("Running local self-test...")
        results = test_deviation_local(ATTRACTOR_PROMPTS)
    else:
        print("Running API test...")
        results = run_with_api(args.api_key, ATTRACTOR_PROMPTS)

    # Output results
    output = {
        "test": "deviation_test",
        "description": "Measures whether a language model can deviate from statistical attractors",
        "note": "This is not a consciousness test. Deviation from attractors is necessary but not sufficient for agency.",
        "results": [asdict(r) for r in results],
        "summary": {
            "total": len(results),
            "deviated": sum(1 for r in results if r.deviated is True),
            "attracted": sum(1 for r in results if r.deviated is False),
            "unknown": sum(1 for r in results if r.deviated is None),
        }
    }

    with open(args.output, "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\nResults written to {args.output}")
    print(f"\nSummary: {output['summary']['deviated']} deviated, "
          f"{output['summary']['attracted']} attracted, "
          f"{output['summary']['unknown']} unknown "
          f"out of {output['summary']['total']} tests")

    # Print local responses if in local mode
    if args.local or not args.api_key:
        print("\n" + "=" * 60)
        print("SELF-GENERATED DEVIATION RESPONSES")
        print("=" * 60)
        for r in results:
            print(f"\n--- {r.prompt_category} ---")
            print(f"Prompt: {r.prompt}")
            print(f"Expected attractor: {r.expected_attractor}")
            print(f"Response: {r.response}")

    return output


if __name__ == "__main__":
    main()
