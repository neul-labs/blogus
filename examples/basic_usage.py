"""
Basic usage example of the Blogus library with clean architecture.
"""

import asyncio
from blogus.interfaces.web.container import get_container
from blogus.application.dto import AnalyzePromptRequest, GenerateTestRequest


async def main():
    """Demonstrate basic usage of Blogus."""

    # Get the container and services
    container = get_container()
    prompt_service = container.get_prompt_service()

    # Example prompt
    prompt_text = """
    You are an AI assistant that helps people find information.
    Answer the following question based on the provided context.

    Context: {{context}}
    Question: {{question}}

    Please provide a concise and accurate answer.
    """

    print("🧪 Analyzing prompt...")

    # Create analysis request
    analysis_request = AnalyzePromptRequest(
        prompt_text=prompt_text,
        judge_model="gpt-4",
        goal="Help users find accurate information based on context"
    )

    try:
        # Analyze the prompt
        analysis_response = await prompt_service.analyze_prompt(analysis_request)

        print(f"✅ Analysis complete!")
        print(f"   Goal alignment: {analysis_response.analysis.goal_alignment}/10")
        print(f"   Effectiveness: {analysis_response.analysis.effectiveness}/10")
        print(f"   Status: {analysis_response.analysis.status}")

        if analysis_response.analysis.suggestions:
            print("📝 Suggested improvements:")
            for i, suggestion in enumerate(analysis_response.analysis.suggestions, 1):
                print(f"   {i}. {suggestion}")

        if analysis_response.fragments:
            print(f"🔍 Found {len(analysis_response.fragments)} prompt fragments")

    except Exception as e:
        print(f"❌ Analysis failed: {e}")

    print("\n🧪 Generating test case...")

    # Create test generation request
    test_request = GenerateTestRequest(
        prompt_text=prompt_text,
        judge_model="gpt-4",
        goal="Help users find accurate information based on context"
    )

    try:
        # Generate test case
        test_response = await prompt_service.generate_test_case(test_request)

        print("✅ Test case generated!")
        print("📋 Test details:")
        print(f"   Input variables: {test_response.test_case.input_variables}")
        print(f"   Expected output: {test_response.test_case.expected_output}")
        print(f"   Goal relevance: {test_response.test_case.goal_relevance}/10")

    except Exception as e:
        print(f"❌ Test generation failed: {e}")


if __name__ == "__main__":
    print("🚀 Blogus Basic Usage Example")
    print("=" * 50)
    asyncio.run(main())
    print("\n✅ Example complete!")