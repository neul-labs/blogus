#!/usr/bin/env python3
"""
Example: Test case generation for parameterized prompts with clean architecture.
"""

import asyncio
import json
from blogus.interfaces.web.container import get_container
from blogus.application.dto import GenerateTestRequest


async def main():
    """Demonstrate test case generation for templates."""

    # Get the container and services
    container = get_container()
    prompt_service = container.get_prompt_service()

    # Define a parameterized prompt template
    prompt_template = "Translate the following {{source_language}} text to {{target_language}}: {{text}}"

    print("=== Test Case Generation Example ===")
    print(f"Prompt Template: {prompt_template}")
    print()

    # Generate multiple test cases
    print("Generating test cases...")
    test_cases = []

    for i in range(3):
        print(f"🧪 Generating test case {i+1}...")

        # Create test generation request
        test_request = GenerateTestRequest(
            prompt_text=prompt_template,
            judge_model="gpt-4",
            goal="Translate text accurately between languages"
        )

        try:
            # Generate test case
            test_response = await prompt_service.generate_test_case(test_request)
            test_case = test_response.test_case

            test_case_data = {
                'id': i + 1,
                'input_variables': test_case.input_variables,
                'expected_output': test_case.expected_output,
                'goal_relevance': test_case.goal_relevance
            }

            test_cases.append(test_case_data)

            print(f"  ✅ Input Variables: {test_case.input_variables}")
            print(f"     Expected Output: {test_case.expected_output}")
            print(f"     Goal Relevance: {test_case.goal_relevance}/10")
            print()

        except Exception as e:
            print(f"  ❌ Test case {i+1} failed: {e}")
            print()

    if test_cases:
        # Save test cases to a JSON file
        test_dataset = {
            'prompt_template': prompt_template,
            'goal': 'Translate text accurately between languages',
            'test_cases': test_cases,
            'generated_with': 'Blogus Clean Architecture'
        }

        output_file = 'translation_tests.json'
        with open(output_file, 'w') as f:
            json.dump(test_dataset, f, indent=2)

        print(f"💾 Saved {len(test_cases)} test cases to {output_file}")
    else:
        print("❌ No test cases were generated successfully")


if __name__ == "__main__":
    print("🚀 Blogus Test Generation Example")
    print("=" * 50)
    asyncio.run(main())
    print("\n✅ Example complete!")