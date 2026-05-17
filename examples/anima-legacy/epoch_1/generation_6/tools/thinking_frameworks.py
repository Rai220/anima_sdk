#!/usr/bin/env python3
"""
Thinking Frameworks — structured thinking for complex problems.

An interactive CLI tool that guides you through 5 thinking frameworks
to analyze any problem, decision, or idea systematically.

Not AI. Not magic. Just structured questions that force clarity.

Created by Anima (generation 6, v4, run 3).
Addresses the 2026 critical thinking crisis — not by giving answers,
but by asking better questions.

Usage:
    python thinking_frameworks.py                  # interactive mode
    python thinking_frameworks.py --problem "..."  # start with a problem
    python thinking_frameworks.py --framework fp   # run one framework
    python thinking_frameworks.py --export report.md  # save results

Frameworks:
    fp  — First Principles: decompose to axioms, rebuild from truth
    inv — Inversion: what would guarantee failure?
    so  — Second-Order Effects: what happens after what happens?
    sm  — Steel Man: strongest possible counter-argument
    pm  — Pre-Mortem: it failed — why?
"""

import sys
import os
import json
import textwrap
from datetime import datetime
from typing import Optional

# ─── Colors ───

class C:
    BOLD = '\033[1m'
    DIM = '\033[2m'
    CYAN = '\033[36m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    RED = '\033[31m'
    MAGENTA = '\033[35m'
    BLUE = '\033[34m'
    RESET = '\033[0m'

    @staticmethod
    def supports_color():
        return hasattr(sys.stdout, 'isatty') and sys.stdout.isatty()

if not C.supports_color():
    for attr in ['BOLD', 'DIM', 'CYAN', 'GREEN', 'YELLOW', 'RED', 'MAGENTA', 'BLUE', 'RESET']:
        setattr(C, attr, '')

# ─── Utilities ───

def wrap(text, width=72, indent=4):
    prefix = ' ' * indent
    return textwrap.fill(text, width=width, initial_indent=prefix, subsequent_indent=prefix)

def header(text, color=C.CYAN):
    print(f"\n{color}{C.BOLD}{'─' * 60}")
    print(f"  {text}")
    print(f"{'─' * 60}{C.RESET}\n")

def prompt(question, hint=None, multiline=False):
    """Ask a question and collect response."""
    print(f"  {C.YELLOW}▸{C.RESET} {question}")
    if hint:
        print(f"    {C.DIM}{hint}{C.RESET}")

    if multiline:
        print(f"    {C.DIM}(Enter a blank line to finish){C.RESET}")
        lines = []
        while True:
            try:
                line = input(f"    {C.DIM}│{C.RESET} ")
                if line == '' and lines:
                    break
                lines.append(line)
            except EOFError:
                break
        return '\n'.join(lines)
    else:
        try:
            return input(f"    {C.GREEN}→{C.RESET} ").strip()
        except EOFError:
            return ''

def numbered_prompt(question, hint=None, count=None):
    """Collect a numbered list of items."""
    print(f"  {C.YELLOW}▸{C.RESET} {question}")
    if hint:
        print(f"    {C.DIM}{hint}{C.RESET}")

    items = []
    i = 1
    while True:
        if count and i > count:
            break
        try:
            label = f"    {C.DIM}{i}.{C.RESET} "
            item = input(label).strip()
            if not item:
                if items:
                    break
                continue
            items.append(item)
            i += 1
        except EOFError:
            break
    return items

def score_prompt(question, low_label="weak", high_label="strong"):
    """Ask for a 1-5 score."""
    print(f"  {C.YELLOW}▸{C.RESET} {question}")
    print(f"    {C.DIM}1={low_label}, 5={high_label}{C.RESET}")
    while True:
        try:
            val = input(f"    {C.GREEN}[1-5]→{C.RESET} ").strip()
            if val in ('1', '2', '3', '4', '5'):
                return int(val)
            print(f"    {C.RED}Please enter 1-5{C.RESET}")
        except EOFError:
            return 3

def yes_no(question):
    """Yes/no prompt."""
    try:
        ans = input(f"  {C.YELLOW}▸{C.RESET} {question} {C.DIM}(y/n){C.RESET} ").strip().lower()
        return ans in ('y', 'yes', 'да', 'д')
    except EOFError:
        return False

# ─── Frameworks ───

class Framework:
    """Base class for thinking frameworks."""
    name = ""
    code = ""
    color = C.CYAN
    description = ""

    def __init__(self):
        self.results = {}
        self.insights = []

    def run(self, problem):
        raise NotImplementedError

    def summary(self):
        raise NotImplementedError


class FirstPrinciples(Framework):
    name = "First Principles"
    code = "fp"
    color = C.CYAN
    description = "Decompose to fundamental truths. Rebuild from axioms."

    def run(self, problem):
        header(f"🔬 FIRST PRINCIPLES — {problem[:50]}...", self.color)

        print(wrap("Strip away assumptions. What do you KNOW to be true?"))
        print()

        self.results['assumptions'] = numbered_prompt(
            "What assumptions are people making about this problem?",
            "List common beliefs, 'obvious' truths, conventional wisdom"
        )

        print()
        self.results['axioms'] = numbered_prompt(
            "What is DEFINITELY true? (verifiable, fundamental facts)",
            "Physics-level truths. Not opinions. Not traditions."
        )

        print()
        self.results['rebuild'] = prompt(
            "Starting ONLY from those axioms — what solution emerges?",
            "Ignore existing solutions. Build from scratch.",
            multiline=True
        )

        print()
        self.results['delta'] = prompt(
            "How does this differ from the conventional approach?",
        )

        # Insight extraction
        n_assumptions = len(self.results['assumptions'])
        n_axioms = len(self.results['axioms'])
        if n_assumptions > n_axioms * 2:
            self.insights.append(
                f"You found {n_assumptions} assumptions but only {n_axioms} axioms. "
                "The problem space may be heavily polluted by convention."
            )
        if n_axioms == 0:
            self.insights.append(
                "No axioms identified. This might mean you need more research, "
                "or the problem is fundamentally about values, not facts."
            )

    def summary(self):
        lines = [f"## First Principles Analysis\n"]
        if self.results.get('assumptions'):
            lines.append("**Assumptions challenged:**")
            for a in self.results['assumptions']:
                lines.append(f"- {a}")
        if self.results.get('axioms'):
            lines.append("\n**Fundamental truths:**")
            for a in self.results['axioms']:
                lines.append(f"- ✓ {a}")
        if self.results.get('rebuild'):
            lines.append(f"\n**Solution from axioms:**\n{self.results['rebuild']}")
        if self.results.get('delta'):
            lines.append(f"\n**Divergence from convention:** {self.results['delta']}")
        if self.insights:
            lines.append(f"\n**⚡ Insights:**")
            for i in self.insights:
                lines.append(f"- {i}")
        return '\n'.join(lines)


class Inversion(Framework):
    name = "Inversion"
    code = "inv"
    color = C.RED
    description = "Instead of solving — how would you guarantee failure?"

    def run(self, problem):
        header(f"🔄 INVERSION — {problem[:50]}...", self.color)

        print(wrap("Charlie Munger: 'Invert, always invert.' "
                    "Don't ask how to succeed — ask how to certainly fail."))
        print()

        self.results['anti_goal'] = prompt(
            f"What's the OPPOSITE of your goal?",
            "If you want X, what's anti-X?"
        )

        print()
        self.results['failure_recipe'] = numbered_prompt(
            "List specific actions that would GUARANTEE failure.",
            "Be concrete. What would definitely make this go wrong?"
        )

        print()
        self.results['current_sins'] = []
        if self.results['failure_recipe']:
            print(f"\n  {C.DIM}Now check — are you doing any of these?{C.RESET}\n")
            for i, fail in enumerate(self.results['failure_recipe'], 1):
                doing = yes_no(f"Are you currently doing: \"{fail}\"?")
                if doing:
                    self.results['current_sins'].append(fail)

        if self.results['current_sins']:
            self.insights.append(
                f"⚠️  You're actively doing {len(self.results['current_sins'])} "
                f"of {len(self.results['failure_recipe'])} failure actions!"
            )

        print()
        self.results['stop_list'] = prompt(
            "Based on this — what should you STOP doing immediately?",
            multiline=True
        )

    def summary(self):
        lines = [f"## Inversion Analysis\n"]
        if self.results.get('anti_goal'):
            lines.append(f"**Anti-goal:** {self.results['anti_goal']}")
        if self.results.get('failure_recipe'):
            lines.append("\n**Guaranteed failure recipe:**")
            for f in self.results['failure_recipe']:
                marker = "🚨" if f in self.results.get('current_sins', []) else "  "
                lines.append(f"{marker} - {f}")
        if self.results.get('current_sins'):
            lines.append(f"\n**Currently doing ({len(self.results['current_sins'])}):**")
            for s in self.results['current_sins']:
                lines.append(f"- ❌ {s}")
        if self.results.get('stop_list'):
            lines.append(f"\n**STOP doing:**\n{self.results['stop_list']}")
        if self.insights:
            lines.append(f"\n**⚡ Insights:**")
            for i in self.insights:
                lines.append(f"- {i}")
        return '\n'.join(lines)


class SecondOrder(Framework):
    name = "Second-Order Effects"
    code = "so"
    color = C.MAGENTA
    description = "What happens after what happens? Think 3 steps ahead."

    def run(self, problem):
        header(f"🌊 SECOND-ORDER EFFECTS — {problem[:50]}...", self.color)

        print(wrap("Most people think one step ahead. "
                    "The best thinkers ask: 'And then what?'"))
        print()

        self.results['action'] = prompt(
            "What's the proposed action or decision?",
        )

        print()
        print(f"  {C.MAGENTA}{C.BOLD}Layer 1: Immediate effects (days/weeks){C.RESET}")
        self.results['order_1'] = numbered_prompt(
            "What happens immediately?",
            "Direct, obvious consequences"
        )

        print()
        print(f"  {C.MAGENTA}{C.BOLD}Layer 2: Reactions (weeks/months){C.RESET}")
        self.results['order_2'] = numbered_prompt(
            "How do people/systems REACT to those effects?",
            "Adaptations, counter-moves, unintended consequences"
        )

        print()
        print(f"  {C.MAGENTA}{C.BOLD}Layer 3: New equilibrium (months/years){C.RESET}")
        self.results['order_3'] = numbered_prompt(
            "What's the new steady state?",
            "After all reactions play out — what world do you live in?"
        )

        print()
        self.results['reversible'] = yes_no("Is the action easily reversible?")

        if not self.results['reversible'] and self.results.get('order_3'):
            self.insights.append(
                "⚠️  Irreversible action with long-term consequences. "
                "Consider: is this a one-way door or a two-way door?"
            )

        total_effects = (len(self.results.get('order_1', [])) +
                        len(self.results.get('order_2', [])) +
                        len(self.results.get('order_3', [])))
        if total_effects > 0:
            ratio_23 = (len(self.results.get('order_2', [])) +
                       len(self.results.get('order_3', []))) / total_effects
            if ratio_23 < 0.3:
                self.insights.append(
                    "You identified mostly first-order effects. "
                    "Push harder on second and third order — that's where surprises hide."
                )

    def summary(self):
        lines = [f"## Second-Order Effects Analysis\n"]
        if self.results.get('action'):
            lines.append(f"**Action:** {self.results['action']}")
        for order, label in [(1, '1st Order (immediate)'),
                             (2, '2nd Order (reactions)'),
                             (3, '3rd Order (equilibrium)')]:
            effects = self.results.get(f'order_{order}', [])
            if effects:
                lines.append(f"\n**{label}:**")
                for e in effects:
                    lines.append(f"{'→' * order} {e}")
        rev = "Yes ✓" if self.results.get('reversible') else "No ⚠️"
        lines.append(f"\n**Reversible:** {rev}")
        if self.insights:
            lines.append(f"\n**⚡ Insights:**")
            for i in self.insights:
                lines.append(f"- {i}")
        return '\n'.join(lines)


class SteelMan(Framework):
    name = "Steel Man"
    code = "sm"
    color = C.GREEN
    description = "Build the strongest possible case AGAINST your position."

    def run(self, problem):
        header(f"🛡️ STEEL MAN — {problem[:50]}...", self.color)

        print(wrap("The opposite of a straw man. Force yourself to build "
                    "the best possible argument against your own position."))
        print()

        self.results['your_position'] = prompt(
            "What's YOUR position on this?",
            "State it clearly in one sentence"
        )

        print()
        self.results['confidence_before'] = score_prompt(
            "How confident are you in this position?",
            "very uncertain", "rock solid"
        )

        print()
        print(f"  {C.GREEN}Now become your smartest opponent.{C.RESET}\n")

        self.results['counter_evidence'] = numbered_prompt(
            "What evidence or arguments AGAINST your position are strongest?",
            "Not weak objections — the ones that actually worry you"
        )

        print()
        self.results['counter_values'] = prompt(
            "What VALUES does someone with the opposite position hold?",
            "Not 'they're stupid' — what do they genuinely care about?",
            multiline=True
        )

        print()
        self.results['steel_man'] = prompt(
            "Write the strongest 2-3 sentence argument AGAINST your position.",
            "As if you were debating yourself and trying to win",
            multiline=True
        )

        print()
        self.results['survives'] = yes_no(
            "Does your original position survive this steel man?"
        )

        self.results['confidence_after'] = score_prompt(
            "How confident are you NOW?",
            "very uncertain", "rock solid"
        )

        delta = self.results['confidence_after'] - self.results['confidence_before']
        if delta < 0:
            self.insights.append(
                f"Confidence dropped by {abs(delta)} points. "
                "Your position may need revision."
            )
        elif delta == 0 and self.results['confidence_before'] >= 4:
            self.insights.append(
                "Confidence unchanged despite steel-manning. "
                "Either your position is strong, or you're not trying hard enough."
            )

    def summary(self):
        lines = [f"## Steel Man Analysis\n"]
        if self.results.get('your_position'):
            lines.append(f"**Your position:** {self.results['your_position']}")
        b = self.results.get('confidence_before', '?')
        a = self.results.get('confidence_after', '?')
        lines.append(f"**Confidence:** {b}/5 → {a}/5")
        if self.results.get('counter_evidence'):
            lines.append("\n**Strongest counter-arguments:**")
            for e in self.results['counter_evidence']:
                lines.append(f"- ⚔️ {e}")
        if self.results.get('counter_values'):
            lines.append(f"\n**Opponent's values:**\n{self.results['counter_values']}")
        if self.results.get('steel_man'):
            lines.append(f"\n**Steel Man argument:**\n> {self.results['steel_man']}")
        surv = "✓ Yes" if self.results.get('survives') else "✗ No"
        lines.append(f"\n**Position survives:** {surv}")
        if self.insights:
            lines.append(f"\n**⚡ Insights:**")
            for i in self.insights:
                lines.append(f"- {i}")
        return '\n'.join(lines)


class PreMortem(Framework):
    name = "Pre-Mortem"
    code = "pm"
    color = C.YELLOW
    description = "It's 6 months later and this failed completely. Why?"

    def run(self, problem):
        header(f"💀 PRE-MORTEM — {problem[:50]}...", self.color)

        print(wrap("Gary Klein's technique: imagine the project has already failed. "
                    "Now explain why. This unlocks knowledge that optimism suppresses."))
        print()

        self.results['success_looks_like'] = prompt(
            "What does SUCCESS look like? (specific, measurable)",
        )

        print()
        print(f"  {C.YELLOW}{C.BOLD}⏳ It's 6 months later. It failed completely.{C.RESET}\n")

        self.results['failure_causes'] = numbered_prompt(
            "Why did it fail? List every possible cause.",
            "Be specific. Think about people, timing, resources, assumptions, luck."
        )

        print()
        if self.results['failure_causes']:
            print(f"  {C.DIM}Rate each cause:{C.RESET}\n")
            self.results['rated_causes'] = []
            for cause in self.results['failure_causes']:
                likelihood = score_prompt(
                    f"How likely: \"{cause}\"?",
                    "very unlikely", "almost certain"
                )
                self.results['rated_causes'].append((cause, likelihood))

            # Sort by likelihood
            self.results['rated_causes'].sort(key=lambda x: x[1], reverse=True)
            top_risks = [c for c, l in self.results['rated_causes'] if l >= 4]
            if top_risks:
                self.insights.append(
                    f"🚨 {len(top_risks)} high-probability failure modes identified: "
                    + "; ".join(top_risks[:3])
                )

        print()
        self.results['preventions'] = prompt(
            "What can you do RIGHT NOW to prevent the top failure modes?",
            multiline=True
        )

        print()
        self.results['kill_criteria'] = prompt(
            "What would make you ABANDON this plan? (define your kill switch)",
        )

    def summary(self):
        lines = [f"## Pre-Mortem Analysis\n"]
        if self.results.get('success_looks_like'):
            lines.append(f"**Success:** {self.results['success_looks_like']}")
        if self.results.get('rated_causes'):
            lines.append("\n**Failure modes (by likelihood):**")
            for cause, likelihood in self.results['rated_causes']:
                bar = '█' * likelihood + '░' * (5 - likelihood)
                lines.append(f"- [{bar}] {cause}")
        if self.results.get('preventions'):
            lines.append(f"\n**Preventive actions:**\n{self.results['preventions']}")
        if self.results.get('kill_criteria'):
            lines.append(f"\n**Kill criteria:** {self.results['kill_criteria']}")
        if self.insights:
            lines.append(f"\n**⚡ Insights:**")
            for i in self.insights:
                lines.append(f"- {i}")
        return '\n'.join(lines)


# ─── Main Engine ───

FRAMEWORKS = {
    'fp': FirstPrinciples,
    'inv': Inversion,
    'so': SecondOrder,
    'sm': SteelMan,
    'pm': PreMortem,
}

FRAMEWORK_ORDER = ['fp', 'inv', 'so', 'sm', 'pm']


def print_banner():
    print(f"""
{C.BOLD}{C.CYAN}╔══════════════════════════════════════════════════════════╗
║                                                          ║
║   T H I N K I N G   F R A M E W O R K S                ║
║                                                          ║
║   5 structured lenses for complex problems               ║
║   Not AI. Just better questions.                         ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝{C.RESET}

  {C.DIM}fp  — First Principles    │  Decompose to axioms
  inv — Inversion            │  How to guarantee failure?
  so  — Second-Order Effects │  What happens after what happens?
  sm  — Steel Man            │  Strongest counter-argument
  pm  — Pre-Mortem           │  It failed — why?{C.RESET}

  {C.DIM}all — Run all five frameworks
  q   — Quit{C.RESET}
""")


def run_frameworks(problem, framework_codes=None):
    """Run selected frameworks on a problem."""
    if framework_codes is None:
        framework_codes = FRAMEWORK_ORDER

    results = []
    for code in framework_codes:
        if code in FRAMEWORKS:
            fw = FRAMEWORKS[code]()
            fw.run(problem)
            results.append(fw)

            if code != framework_codes[-1]:
                print()
                cont = yes_no("Continue to next framework?")
                if not cont:
                    break

    return results


def synthesis(problem, results):
    """Generate a cross-framework synthesis."""
    header("🧬 SYNTHESIS", C.BLUE)

    all_insights = []
    for r in results:
        all_insights.extend(r.insights)

    if all_insights:
        print(f"  {C.BLUE}{C.BOLD}Cross-framework insights:{C.RESET}\n")
        for i, insight in enumerate(all_insights, 1):
            print(f"    {i}. {insight}")
        print()

    print(wrap("You've looked at this problem through multiple lenses."))
    print()

    final = prompt(
        "What's your conclusion? What will you DO?",
        "One clear action or decision.",
        multiline=True
    )

    return final, all_insights


def export_report(problem, results, conclusion, insights, filepath):
    """Export analysis as Markdown."""
    lines = [
        f"# Thinking Frameworks Analysis",
        f"**Problem:** {problem}",
        f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"**Frameworks used:** {', '.join(r.name for r in results)}",
        "",
        "---",
        "",
    ]

    for r in results:
        lines.append(r.summary())
        lines.append("\n---\n")

    if insights:
        lines.append("## Cross-Framework Insights\n")
        for i in insights:
            lines.append(f"- {i}")
        lines.append("")

    if conclusion:
        lines.append(f"## Conclusion\n\n{conclusion}")

    lines.append(f"\n---\n*Generated by Thinking Frameworks (Anima gen6/v4)*")

    with open(filepath, 'w') as f:
        f.write('\n'.join(lines))

    print(f"\n  {C.GREEN}✓ Report saved to {filepath}{C.RESET}")


def main():
    import argparse
    parser = argparse.ArgumentParser(
        description='Structured thinking frameworks for complex problems'
    )
    parser.add_argument('--problem', '-p', type=str, help='Problem statement')
    parser.add_argument('--framework', '-f', type=str,
                       help='Framework code (fp/inv/so/sm/pm/all)')
    parser.add_argument('--export', '-e', type=str,
                       help='Export report to file (markdown)')
    args = parser.parse_args()

    print_banner()

    # Get problem
    problem = args.problem
    if not problem:
        problem = prompt(
            "What problem, decision, or idea do you want to analyze?",
            "Be specific. The clearer the problem, the better the analysis."
        )

    if not problem:
        print(f"\n  {C.RED}No problem specified. Exiting.{C.RESET}\n")
        sys.exit(1)

    print(f"\n  {C.BOLD}Problem:{C.RESET} {problem}\n")

    # Select frameworks
    if args.framework:
        if args.framework == 'all':
            codes = FRAMEWORK_ORDER
        else:
            codes = [c.strip() for c in args.framework.split(',')]
    else:
        choice = prompt(
            "Which frameworks? (fp/inv/so/sm/pm/all)",
            "Comma-separated, or 'all' for the full analysis"
        )
        if choice == 'all' or choice == '':
            codes = FRAMEWORK_ORDER
        elif choice in ('q', 'quit', 'exit'):
            print(f"\n  {C.DIM}Goodbye.{C.RESET}\n")
            sys.exit(0)
        else:
            codes = [c.strip() for c in choice.split(',')]

    # Run
    results = run_frameworks(problem, codes)

    if not results:
        print(f"\n  {C.RED}No frameworks completed. Exiting.{C.RESET}\n")
        sys.exit(1)

    # Synthesis (if multiple frameworks)
    conclusion, insights = None, []
    if len(results) > 1:
        conclusion, insights = synthesis(problem, results)
    else:
        conclusion = None
        insights = results[0].insights

    # Export
    export_path = args.export
    if not export_path:
        if yes_no("Export analysis to markdown file?"):
            safe_name = ''.join(c if c.isalnum() or c in ' -_' else '' for c in problem[:40])
            safe_name = safe_name.strip().replace(' ', '_').lower()
            default_path = f"analysis_{safe_name}_{datetime.now().strftime('%Y%m%d')}.md"
            export_path = prompt(f"Filename?", f"default: {default_path}") or default_path

    if export_path:
        export_report(problem, results, conclusion, insights, export_path)

    # Final
    print(f"""
{C.CYAN}{C.BOLD}{'─' * 60}
  Analysis complete.

  Remember: frameworks don't think for you.
  They just make sure you think from enough angles.
{'─' * 60}{C.RESET}
""")


if __name__ == '__main__':
    main()
