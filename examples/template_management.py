#!/usr/bin/env python3
"""
Example: Template management with clean architecture.
"""

import asyncio
from blogus.interfaces.web.container import get_container
from blogus.application.dto import CreateTemplateRequest, RenderTemplateRequest


async def main():
    """Demonstrate template management capabilities."""

    print("=== Template Management Example ===\n")

    # Get the container and services
    container = get_container()
    template_service = container.get_template_service()

    # 1. Create a template
    print("1. Creating a template...")

    create_request = CreateTemplateRequest(
        template_id="email-response",
        name="Customer Email Response",
        description="Template for responding to customer inquiries",
        content="""
Dear {{customer_name}},

Thank you for contacting us about {{inquiry_topic}}.

{{response_content}}

If you have any further questions, please don't hesitate to reach out.

Best regards,
{{agent_name}}
{{company_name}} Support Team
        """.strip(),
        category="customer-service",
        tags=["email", "customer-support", "response"],
        author="support-team"
    )

    try:
        response = await template_service.create_template(create_request)
        template = response.template
        print(f"   ✅ Created template: {template.name}")
        print(f"      ID: {template.id}")
        print(f"      Variables: {template.variables}")
        print(f"      Category: {template.category}")
        print()
    except Exception as e:
        print(f"   ❌ Failed to create template: {e}")
        return

    # 2. Render the template with variables
    print("2. Rendering template with variables...")

    render_request = RenderTemplateRequest(
        template_id="email-response",
        variables={
            "customer_name": "John Smith",
            "inquiry_topic": "product pricing",
            "response_content": "Our premium plan starts at $29/month and includes all advanced features. I've attached a detailed pricing guide to help you choose the best option for your needs.",
            "agent_name": "Sarah Johnson",
            "company_name": "Blogus"
        }
    )

    try:
        render_response = await template_service.render_template(render_request)
        print("   ✅ Template rendered successfully!")
        print("   📧 Rendered email:")
        print("   " + "="*50)
        print("   " + render_response.rendered_content.replace("\n", "\n   "))
        print("   " + "="*50)
        print()
    except Exception as e:
        print(f"   ❌ Failed to render template: {e}")

    # 3. List templates by category
    print("3. Listing templates by category...")

    try:
        templates = await template_service.list_templates(category="customer-service")
        print(f"   ✅ Found {len(templates)} templates in 'customer-service' category:")

        for template in templates:
            print(f"      - {template.name} ({template.id})")
            print(f"        Variables: {', '.join(template.variables)}")
            print(f"        Tags: {', '.join(template.tags)}")
        print()
    except Exception as e:
        print(f"   ❌ Failed to list templates: {e}")

    # 4. Get template categories and tags
    print("4. Getting available categories and tags...")

    try:
        categories = await template_service.get_categories()
        tags = await template_service.get_tags()

        print(f"   ✅ Available categories: {', '.join(categories)}")
        print(f"   ✅ Available tags: {', '.join(tags)}")
        print()
    except Exception as e:
        print(f"   ❌ Failed to get categories/tags: {e}")

    # 5. Validate template content
    print("5. Validating template content...")

    test_content = "Hello {{name}}, your order {{order_id}} is {{status}}. Missing variable: {{missing_var}}"

    try:
        issues = await template_service.validate_template_content(test_content)
        if issues:
            print("   ⚠️  Template validation issues found:")
            for issue in issues:
                print(f"      - {issue}")
        else:
            print("   ✅ Template content is valid!")
        print()
    except Exception as e:
        print(f"   ❌ Failed to validate template: {e}")

    # 6. Create a second template for demonstration
    print("6. Creating another template...")

    create_request2 = CreateTemplateRequest(
        template_id="product-description",
        name="Product Description Generator",
        description="Template for generating product descriptions",
        content="""
{{product_name}} - {{tagline}}

{{description}}

Key Features:
{{#features}}
• {{feature}}
{{/features}}

Price: {{price}}
Category: {{category}}
        """.strip(),
        category="marketing",
        tags=["product", "description", "marketing"],
        author="marketing-team"
    )

    try:
        response = await template_service.create_template(create_request2)
        print(f"   ✅ Created template: {response.template.name}")
        print()
    except Exception as e:
        print(f"   ❌ Failed to create second template: {e}")

    # 7. Final template listing
    print("7. Final template inventory...")

    try:
        all_templates = await template_service.list_templates()
        print(f"   📚 Total templates: {len(all_templates)}")

        categories = {}
        for template in all_templates:
            if template.category not in categories:
                categories[template.category] = []
            categories[template.category].append(template.name)

        print("   📂 Templates by category:")
        for category, template_names in categories.items():
            print(f"      {category}: {', '.join(template_names)}")
    except Exception as e:
        print(f"   ❌ Failed to list all templates: {e}")


if __name__ == "__main__":
    print("🚀 Blogus Template Management Example")
    print("=" * 50)
    asyncio.run(main())
    print("\n✅ Example complete!")