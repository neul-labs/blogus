#!/usr/bin/env python3
"""
Example: Basic prompt analysis and execution with clean architecture.
"""

import asyncio
from blogus.interfaces.web.container import get_container
from blogus.application.dto import AnalyzePromptRequest, ExecutePromptRequest


async def main():
    """Demonstrate basic prompt analysis and execution."""

    # Get the container and services
    container = get_container()
    prompt_service = container.get_prompt_service()

    # Define a prompt to analyze
    prompt = "You are a helpful assistant that provides concise and accurate responses."

    print("=== Prompt Analysis Example ===")
    print(f"Prompt: {prompt}")
    print()

    # Create analysis request
    analysis_request = AnalyzePromptRequest(
        prompt_text=prompt,
        judge_model="gpt-4",
        goal="Provide helpful and accurate responses"
    )

    try:
        # Analyze the prompt
        analysis_response = await prompt_service.analyze_prompt(analysis_request)
        analysis = analysis_response.analysis

        print(f"Overall Goal Alignment: {analysis.goal_alignment}/10")
        print(f"Estimated Effectiveness: {analysis.effectiveness}/10")
        print(f"Status: {analysis.status}")

        if analysis.inferred_goal:
            print(f"Inferred Goal: {analysis.inferred_goal}")

        print("\nSuggested Improvements:")
        for i, suggestion in enumerate(analysis.suggestions, 1):
            print(f"  {i}. {suggestion}")

        if analysis_response.fragments:
            print(f"\nPrompt Fragments Found: {len(analysis_response.fragments)}")
            for i, fragment in enumerate(analysis_response.fragments, 1):
                print(f"  {i}. {fragment.fragment_type}: {fragment.text[:50]}...")

    except Exception as e:
        print(f"❌ Analysis failed: {e}")

    print("\n=== Prompt Execution Example ===")

    # Execute the prompt with a test question
    test_question = "What is the capital of France?"
    full_prompt = f"{prompt}\n\nUser: {test_question}"

    # Create execution request
    execution_request = ExecutePromptRequest(
        prompt_text=full_prompt,
        target_model="gpt-3.5-turbo"
    )

    try:
        # Execute the prompt
        execution_response = await prompt_service.execute_prompt(execution_request)

        print(f"Question: {test_question}")
        print(f"Model Used: {execution_response.model_used}")
        print(f"Duration: {execution_response.duration:.2f}s")
        print(f"Response: {execution_response.result}")

    except Exception as e:
        print(f"❌ Execution failed: {e}")


if __name__ == "__main__":
    print("🚀 Blogus Basic Analysis Example")
    print("=" * 50)
    asyncio.run(main())
    print("\n✅ Example complete!")