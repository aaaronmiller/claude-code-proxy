"""
Crosstalk CLI Integration - Interactive and Command-Line Interface
"""

import sys
import os
import asyncio
from typing import List, Dict, Optional

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.conversation.crosstalk import crosstalk_orchestrator
from src.core.config import config


def handle_crosstalk_operations(args) -> bool:
    """
    Handle crosstalk-related CLI operations.

    Returns:
        True if operation was handled and we should exit, False to continue
    """
    # Check for any crosstalk operation
    if not any([
        args.crosstalk_init,
        args.crosstalk_models,
        args.big_system_prompt,
        args.middle_system_prompt,
        args.small_system_prompt,
        args.crosstalk_iterations,
        args.crosstalk_topic,
        args.crosstalk_paradigm,
    ]):
        return False

    # Run the appropriate crosstalk operation
    if args.crosstalk_init:
        run_interactive_setup()
        return True
    elif args.crosstalk_models:
        run_quick_crosstalk(args)
        return True
    else:
        print("❌ Error: --crosstalk requires --crosstalk-init or --crosstalk-models")
        return True


def run_interactive_setup():
    """Run the interactive crosstalk setup wizard."""
    print("\n" + "="*70)
    print("╔" + "="*68 + "╗")
    print("║" + " "*10 + "🤖 MODEL-TO-MODEL CROSSTALK SETUP WIZARD" + " "*18 + "║")
    print("║" + " "*68 + "║")
    print("╚" + "="*68 + "╝")
    print("="*70)
    print()

    # Step 1: Select Models
    print("📋 Step 1: Select Models for Conversation")
    print("-" * 70)
    print("Available models (configured in config):")
    print(f"  • BIG: {config.big_model}")
    print(f"  • MIDDLE: {config.middle_model}")
    print(f"  • SMALL: {config.small_model}")
    print()

    while True:
        models_input = input("Enter model IDs separated by comma (e.g., big,small): ").strip()
        models = [m.strip().lower() for m in models_input.split(',')]
        valid_models = ['big', 'middle', 'small']

        if all(m in valid_models for m in models) and len(models) >= 2:
            selected_models = models
            print(f"✓ Selected models: {', '.join(selected_models)}\n")
            break
        else:
            print("❌ Invalid input. Please enter valid model IDs (big, middle, small)")
            print("   Must select at least 2 models\n")

    # Step 2: Configure System Prompts
    print("📝 Step 2: Configure System Prompts")
    print("-" * 70)
    system_prompts = {}

    for model in selected_models:
        print(f"\nConfigure system prompt for {model.upper()} model:")
        print("  Option 1: Enter 'file:/path/to/file.txt' to load from file")
        print("  Option 2: Enter text directly for inline prompt")
        print("  Option 3: Press Enter to skip")

        prompt = input(f"System prompt for {model} (or press Enter to skip): ").strip()

        if prompt:
            if prompt.startswith('file:'):
                file_path = prompt[5:].strip()
                try:
                    with open(file_path, 'r') as f:
                        system_prompts[model] = f.read().strip()
                    print(f"✓ Loaded system prompt from {file_path}")
                except FileNotFoundError:
                    print(f"❌ File not found: {file_path}")
                    system_prompts[model] = ""
                except Exception as e:
                    print(f"❌ Error loading file: {e}")
                    system_prompts[model] = ""
            else:
                system_prompts[model] = prompt
                print(f"✓ Set inline system prompt ({len(prompt)} chars)")

    # Step 3: Select Paradigm
    print("\n\n💬 Step 3: Select Communication Paradigm")
    print("-" * 70)
    paradigms = {
        '1': ('memory', 'Models analyze independently and share insights'),
        '2': ('report', 'Sequential reporting between models'),
        '3': ('relay', 'Chain communication through all models'),
        '4': ('debate', 'Contradictory reasoning with challenges'),
    }

    print("Available paradigms:")
    for key, (name, desc) in paradigms.items():
        print(f"  {key}. {name.upper():8s} - {desc}")
    print()

    while True:
        choice = input("Select paradigm (1-4, default=3 for relay): ").strip()
        if not choice:
            choice = '3'

        if choice in paradigms:
            paradigm = paradigms[choice][0]
            print(f"✓ Selected paradigm: {paradigm.upper()}\n")
            break
        else:
            print("❌ Invalid choice. Please enter 1-4\n")

    # Step 4: Iterations
    print("🔄 Step 4: Configure Iterations")
    print("-" * 70)

    while True:
        try:
            iterations_input = input("Number of conversation iterations (5-100, default=20): ").strip()
            if not iterations_input:
                iterations = 20
            else:
                iterations = int(iterations_input)

            if 5 <= iterations <= 100:
                print(f"✓ Set iterations to {iterations}\n")
                break
            else:
                print("❌ Please enter a number between 5 and 100\n")
        except ValueError:
            print("❌ Please enter a valid number\n")

    # Step 5: Topic
    print("💡 Step 5: Initial Topic")
    print("-" * 70)
    topic = input("Enter initial topic or message (default='Hello, lets talk'): ").strip()
    if not topic:
        topic = "Hello, let's talk"
    print(f"✓ Topic: {topic}\n")

    # Step 6: Confirm and Run
    print("\n" + "="*70)
    print("📊 CROSSTALK CONFIGURATION SUMMARY")
    print("="*70)
    print(f"Models:        {', '.join(selected_models)}")
    print(f"Paradigm:      {paradigm.upper()}")
    print(f"Iterations:    {iterations}")
    print(f"Topic:         {topic}")
    print(f"System Prompts: {'Yes' if system_prompts else 'No'}")
    for model, prompt in system_prompts.items():
        print(f"  - {model}: {len(prompt)} chars")
    print("="*70)
    print()

    confirm = input("Start crosstalk conversation? (y/n, default=y): ").strip().lower()
    if confirm == 'n':
        print("❌ Crosstalk cancelled")
        return

    # Run crosstalk
    asyncio.run(run_crosstalk_async(selected_models, system_prompts, paradigm, iterations, topic))


def run_quick_crosstalk(args):
    """Run crosstalk from command-line arguments."""
    import argparse

    # Parse models
    models = [m.strip().lower() for m in args.crosstalk_models.split(',')]
    valid_models = ['big', 'middle', 'small']

    if not all(m in valid_models for m in models) or len(models) < 2:
        print(f"❌ Error: Invalid models. Must be comma-separated from {valid_models}")
        print(f"   Example: --crosstalk big,small")
        return

    # Build system prompts
    system_prompts = {}
    if args.big_system_prompt:
        system_prompts['big'] = get_model_system_prompt(args.big_system_prompt)
    if args.middle_system_prompt:
        system_prompts['middle'] = get_model_system_prompt(args.middle_system_prompt)
    if args.small_system_prompt:
        system_prompts['small'] = get_model_system_prompt(args.small_system_prompt)

    # Get other settings
    paradigm = args.crosstalk_paradigm or 'relay'
    iterations = args.crosstalk_iterations or 20
    topic = args.crosstalk_topic or "Hello, let's talk"

    # Run crosstalk
    print(f"\n🚀 Starting crosstalk with {len(models)} models...")
    print(f"   Models: {', '.join(models)}")
    print(f"   Paradigm: {paradigm}")
    print(f"   Iterations: {iterations}")
    print()

    asyncio.run(run_crosstalk_async(models, system_prompts, paradigm, iterations, topic))


async def run_crosstalk_async(models: List[str], system_prompts: Dict[str, str],
                                paradigm: str, iterations: int, topic: str):
    """Async wrapper for running crosstalk."""
    try:
        # Setup crosstalk
        print("⚙️  Setting up crosstalk session...")
        session_id = await crosstalk_orchestrator.setup_crosstalk(
            models=models,
            system_prompts=system_prompts,
            paradigm=paradigm,
            iterations=iterations,
            topic=topic
        )
        print(f"✓ Session created: {session_id}\n")

        # Execute crosstalk
        print("💬 Starting conversation...\n")
        print("="*70)

        import time
        start_time = time.time()

        conversation = await crosstalk_orchestrator.execute_crosstalk(session_id)

        duration = time.time() - start_time

        # Print results
        print("="*70)
        print(f"\n✓ Crosstalk completed in {duration:.2f} seconds")
        print(f"✓ Total messages: {len(conversation)}")
        print(f"✓ Paradigm: {paradigm.upper()}")
        print("\n" + "="*70)
        print("CONVERSATION TRANSCRIPT")
        print("="*70)

        for i, msg in enumerate(conversation, 1):
            print(f"\n[{i}] {msg['speaker'].upper()} → {msg['listener'].upper()} "
                  f"(iteration {msg['iteration']})")
            if msg.get('confidence'):
                print(f"    Confidence: {msg['confidence']:.2f}")
            print(f"    {msg['content'][:200]}{'...' if len(msg['content']) > 200 else ''}")

        print("\n" + "="*70)

        # Save to file
        import json
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"crosstalk_{paradigm}_{timestamp}.json"

        output = {
            "session_id": session_id,
            "timestamp": timestamp,
            "models": models,
            "paradigm": paradigm,
            "iterations": iterations,
            "topic": topic,
            "duration_seconds": duration,
            "message_count": len(conversation),
            "conversation": conversation
        }

        with open(filename, 'w') as f:
            json.dump(output, f, indent=2)

        print(f"\n💾 Full transcript saved to: {filename}")
        print()

    except Exception as e:
        print(f"\n❌ Error running crosstalk: {str(e)}")
        import traceback
        traceback.print_exc()
        print()


def print_crosstalk_help():
    """Print help message for crosstalk commands."""
    print("\n" + "="*70)
    print("CROSSTALK - Model-to-Model Conversation System")
    print("="*70)
    print()
    print("USAGE:")
    print("  # Interactive setup wizard (recommended for first time)")
    print("  python start_proxy.py --crosstalk-init")
    print()
    print("  # Quick start with command-line arguments")
    print("  python start_proxy.py \\")
    print("    --crosstalk big,small \\")
    print("    --system-prompt-big path:alice.txt \\")
    print("    --system-prompt-small path:bob.txt \\")
    print("    --crosstalk-iterations 20 \\")
    print("    --crosstalk-topic 'hery whats up' \\")
    print("    --crosstalk-paradigm debate")
    print()
    print("OPTIONS:")
    print("  --crosstalk-init              Interactive setup wizard")
    print("  --crosstalk MODELS            Comma-separated models (big,small,middle)")
    print("  --system-prompt-big PROMPT    System prompt for BIG model")
    print("  --system-prompt-middle PROMPT System prompt for MIDDLE model")
    print("  --system-prompt-small PROMPT  System prompt for SMALL model")
    print("  --crosstalk-iterations N      Number of iterations (5-100, default=20)")
    print("  --crosstalk-topic TEXT        Initial topic/message")
    print("  --crosstalk-paradigm PARADIGM Communication paradigm:")
    print("                                 - memory: Independent analysis")
    print("                                 - report: Sequential reporting")
    print("                                 - relay: Chain communication (default)")
    print("                                 - debate: Contradictory reasoning")
    print()
    print("SYSTEM PROMPT FORMATS:")
    print("  • File: path:prompts/alice.txt")
    print("  • Inline: You are Alice, a helpful assistant...")
    print()
    print("="*70)
