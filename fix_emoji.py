"""Remove emoji from service files for Windows compatibility"""
import os
import glob

# Emoji replacement mapping
replacements = {
    '✅': '[OK]',
    '⚠️': '[WARN]',
    '❌': '[ERROR]',
    '⏸️': '[INFO]',
    '🎉': '[SUCCESS]',
    '📊': '[ANALYTICS]',
    '🌐': '[WEB]',
}

# Find all Python files in app/services
service_files = glob.glob('app/services/*.py')

for filepath in service_files:
    print(f"Processing: {filepath}")

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Replace emojis
    for emoji, text in replacements.items():
        content = content.replace(emoji, text)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"  [DONE]")

print("\nAll service files processed!")
