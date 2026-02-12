"""
Force-write category_form.html to fix the TemplateSyntaxError.
The file keeps reverting (likely OneDrive sync).
This script writes the correct content directly.
"""
import os

TEMPLATE_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    'templates', 'assets', 'configuration', 'category_form.html'
)

# The key fix: NO {% if %} inside HTML attributes.
# Instead, every field gets id="field-{{ field.name }}" and JS targets
# the specific one by name. This completely avoids the split-tag bug.
CONTENT = r'''{% extends "base.html" %}

{% block page_title %}
{% if form.instance.pk %}Edit{% else %}Add{% endif %} Category
{% endblock %}

{% block content %}
<div style="max-width: 600px; margin: 0 auto;">
    <div class="card">
        <form method="post" novalidate>
            {% csrf_token %}

            {% for field in form %}
            <div class="form-group" style="margin-bottom: 1.5rem;" id="field-{{ field.name }}">

                <label style="display:block; margin-bottom:0.5rem; font-weight:500;" for="{{ field.id_for_label }}">
                    {{ field.label }}
                </label>
                {{ field }}

                {% if field.help_text %}
                <small style="color: grey; display: block; margin-top: 0.25rem;">{{ field.help_text }}</small>
                {% endif %}

                {% if field.errors %}
                <div style="color: red; font-size: 0.875rem; margin-top: 0.25rem;">
                    {% for error in field.errors %}
                    <div>{{ error }}</div>
                    {% endfor %}
                </div>
                {% endif %}
            </div>
            {% empty %}
            <p>No fields available.</p>
            {% endfor %}

            <div style="display:flex; gap:1rem; margin-top:2rem;">
                <button type="submit" class="btn btn-primary">Save Category</button>
                <a href="{% url 'category-list' %}" class="btn" style="border: 1px solid var(--border-color);">Cancel</a>
            </div>
        </form>
    </div>
</div>

<script>
    document.addEventListener("DOMContentLoaded", function () {
        var methodEl = document.getElementById("id_depreciation_method");
        var expectedWrapper = document.getElementById("field-default_expected_units");

        function toggleExpectedUnits() {
            if (!methodEl || !expectedWrapper) return;
            var isUoP = methodEl.value === "UNITS_OF_PRODUCTION";
            expectedWrapper.style.display = isUoP ? "block" : "none";
        }

        if (methodEl) {
            methodEl.addEventListener("change", toggleExpectedUnits);
            toggleExpectedUnits();
        }
    });
</script>
{% endblock %}
'''

def main():
    # Ensure the directory exists
    os.makedirs(os.path.dirname(TEMPLATE_PATH), exist_ok=True)

    # Write the file
    with open(TEMPLATE_PATH, 'w', encoding='utf-8', newline='\n') as f:
        f.write(CONTENT.lstrip('\n'))

    print(f"Written to: {TEMPLATE_PATH}")
    print(f"File size: {os.path.getsize(TEMPLATE_PATH)} bytes")

    # Verify by reading back
    with open(TEMPLATE_PATH, 'r', encoding='utf-8') as f:
        content = f.read()

    if '{% if field.name==' in content:
        print("ERROR: Old broken tag STILL present!")
    else:
        print("SUCCESS: File written correctly, no broken tags.")

    # Show first 20 lines
    lines = content.split('\n')
    for i, line in enumerate(lines[:20], 1):
        print(f"  {i}: {line}")

if __name__ == '__main__':
    main()
