#!/usr/bin/env python3
"""
Example: Cross-model comparison with clean architecture.
"""

import asyncio
from blogus.interfaces.web.container import get_container
from blogus.application.dto import ExecutePromptRequest


async def main():
    """Demonstrate cross-model comparison."""

    # Get the container and services
    container = get_container()
    prompt_service = container.get_prompt_service()

    # Define a prompt to test
    prompt = "Explain the concept of photosynthesis in simple terms."

    print("=== Cross-Model Comparison Example ===")
    print(f"Prompt: {prompt}")
    print()

    # List of models to test
    models = [
        "gpt-3.5-turbo",
        "gpt-4",
        "claude-3-haiku-20240307",
        "groq/mixtral-8x7b-32768"
    ]

    results = {}

    # Execute prompt on each model
    for model in models:
        print(f"🤖 Testing {model}...")

        # Create execution request
        execution_request = ExecutePromptRequest(
            prompt_text=prompt,
            target_model=model
        )

        try:
            # Execute the prompt
            response = await prompt_service.execute_prompt(execution_request)

            # Store results
            results[model] = {
                'response': response.result,
                'duration': response.duration,
                'success': True
            }

            print(f"   ✅ Success (took {response.duration:.2f}s)")

            # Truncate long responses for display
            truncated_response = response.result[:200] + "..." if len(response.result) > 200 else response.result
            print(f"   📝 Response: {truncated_response}")

        except Exception as e:
            results[model] = {
                'error': str(e),
                'success': False
            }
            print(f"   ❌ Error: {e}")

        print()

    # Summary comparison
    print("📊 Model Comparison Summary:")
    print("=" * 60)

    successful_models = [(model, data) for model, data in results.items() if data.get('success')]

    if successful_models:
        # Sort by response time
        successful_models.sort(key=lambda x: x[1]['duration'])

        print("🏆 Performance Ranking (by speed):")
        for i, (model, data) in enumerate(successful_models, 1):
            print(f"   {i}. {model}: {data['duration']:.2f}s")

        print(f"\n✅ {len(successful_models)} out of {len(models)} models succeeded")
    else:
        print("❌ No models executed successfully")

    failed_models = [model for model, data in results.items() if not data.get('success')]
    if failed_models:
        print(f"\n❌ Failed models: {', '.join(failed_models)}")


if __name__ == "__main__":
    print("🚀 Blogus Cross-Model Comparison Example")
    print("=" * 50)
    asyncio.run(main())
    print("\n✅ Example complete!")